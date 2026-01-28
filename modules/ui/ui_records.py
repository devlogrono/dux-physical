import pandas as pd
import streamlit as st

from modules.db.db_records import build_record_from_isak
from modules.schema import build_empty_record
from modules.ui.form_ui import record_form
from modules.i18n.i18n import t
from modules.ui.ui_components import preview_record
from modules.util.excel_util import analyze_isak_excel_fields, build_record_from_isak_excel_row, inspect_isak_excel, read_isak_excel, reset_normalize_dup_counter, validate_jugadora_from_excel
from modules.util.isak_util import calcular_antropometria, normalize_isak_numeric, normalize_isak_record
from modules.util.ui_util import dialog_confirmar_registro
from modules.isak.ISAKPresentation import ISAKPresentation

def _validate_context(jugadora: dict) -> str | None:
    if not jugadora:
        st.info(t("Selecciona una jugadora para continuar."))
        return None

    jugadora_id = str(jugadora["identificacion"])

    last_jugadora = st.session_state.get("last_jugadora_id")
    if last_jugadora != jugadora_id:
        st.session_state.pop("submitted", None)
        st.session_state.pop("save_error", None)
        st.session_state["last_jugadora_id"] = jugadora_id

    return jugadora_id

def _get_baseline_isak(
    records_df: pd.DataFrame | None,
    jugadora_id: str
) -> dict | None:

    if records_df is None or records_df.empty:
        return None

    df_jugadora = records_df[
        records_df["identificacion"].astype(str) == jugadora_id
    ].copy()

    if "fecha_medicion" in df_jugadora.columns:
        df_jugadora["fecha_medicion"] = pd.to_datetime(
            df_jugadora["fecha_medicion"], errors="coerce"
        )

    baseline_df = (
        df_jugadora[df_jugadora["tipo_isak"] == "COMPLETO"]
        .sort_values("fecha_medicion", ascending=False)
    )

    if baseline_df.empty:
        return None

    return baseline_df.iloc[0].to_dict()

def _resolve_modo(baseline_isak: dict | None) -> str:
    modo = "SEGUIMIENTO" if baseline_isak else "COMPLETO"

    if modo == "COMPLETO":
        st.warning(t("Primer registro ISAK de la jugadora."))
    else:
        st.info(t("Registro ISAK de seguimiento."))

    return modo

def _resolve_modo(baseline_isak: dict | None) -> str:
    modo = "SEGUIMIENTO" if baseline_isak else "COMPLETO"

    if modo == "COMPLETO":
        st.warning(t("Primer registro ISAK de la jugadora."))
    else:
        st.info(t("Registro ISAK de seguimiento."))

    return modo

def _build_base_record(
    modo: str,
    jugadora_id: str,
    username: str,
    baseline_isak: dict | None,
) -> dict:

    if modo == "COMPLETO":
        record = build_empty_record(
            id_jugadora=jugadora_id,
            username=username,
        )
    else:
        record = build_record_from_isak(
            id_isak=baseline_isak["id_isak"],
            id_jugadora=jugadora_id,
            username=username,
        )

    return record

def _inject_metadata(record: dict, jugadora_id: str, modo: str, username: str) -> dict:
    record["_modo"] = modo
    record["id_jugadora"] = jugadora_id
    record["tipo_isak"] = "COMPLETO"
    record["metodo"] = "ISAK"
    record["usuario"] = username
    return record

def _handle_excel_import(record: dict, mapper: dict = None, jugadora: dict = None) -> dict:
    st.subheader(t("Carga desde archivo ISAK"))

    uploaded_file = st.file_uploader(
        t("Selecciona un archivo Excel ISAK"),
        type=["xls", "xlsx"],
        key=f"isak_file_upload_{st.session_state.file_upload_version}"
    )

    if not uploaded_file:
        return record

    # 1️⃣ Inspección
    try:
        info = inspect_isak_excel(uploaded_file)
    except ValueError as e:
        st.error(str(e))
        return record

    col1, _ = st.columns([2, 6])
    with col1:
        sheet = st.selectbox(
            t("Selecciona la hoja ISAK"),
            options=info["sheets"],
            key="isak_excel_sheet"
        )

    # 2️⃣ Lectura
    try:
        reset_normalize_dup_counter()
        df_excel = read_isak_excel(uploaded_file, sheet)

        # result = validate_jugadora_from_excel(df_excel=df_excel,
        #     mapper=mapper, nombre_jugadora_app=jugadora["nombre_jugadora"])
    except ValueError as e:
        st.error(str(e))
        return record

    # 3️⃣ Análisis ISAK
    analysis = analyze_isak_excel_fields(df_excel, 40)
    
   # st.dataframe(analysis)
    
    st.info(t(
            f"Cobertura ISAK: {len(analysis['matched'])} campos "
            f"({analysis['coverage_pct']}%)"))

    if analysis["missing"]:
        st.warning(
            t("Campos ISAK no encontrados en el archivo:")
            + " "
            + ", ".join(analysis["missing"])
        )

    if not analysis["is_valid"]:
        st.error(t("El archivo no contiene suficientes campos ISAK."))
        return record

    # 4️⃣ Construcción del record
    record_excel = build_record_from_isak_excel_row(
        df=df_excel,
        isak_excel_map=analysis["mapper"]
    )

    record.update(record_excel)
    #st.dataframe(record)
    #st.success(t("Datos cargados desde archivo correctamente."))

    return record

def _render_form_tab(record: dict, jugadora: dict):
    #st.dataframe(record)
    record, is_valid, validation_msg = record_form(record)
    
    record = normalize_isak_record(record)
    record_persist = normalize_isak_numeric(record)
    #preview_record(record_persist)
    calculos = None

    if is_valid:
        calculos = calcular_antropometria(record_persist)
        record_persist["calculos"] = calculos

    st.divider()
    if st.button(f":material/save: {t('Guardar')}", key="btn_reg_isak"):
        #print(f"enviando: {is_valid}")
        if not is_valid:
            st.warning(validation_msg)
            return
        dialog_confirmar_registro(record=record, jugadora=jugadora)

    if st.session_state["auth"]["rol"].lower() == "developer":
        st.divider()
        if st.checkbox(t("Previsualización")):
            preview_record(record_persist)
    
    return record_persist

def _render_preview_tab(record_persist: dict):

    if not record_persist or "calculos" not in record_persist:
        st.info(t("Completa el formulario para ver la previsualización."))
        return
    
    presentacion = ISAKPresentation.build(record_persist)

    with st.expander(":material/dataset: Datos Raw"):
        for bloque in presentacion:
            ISAKPresentation.render_bloque_simple(bloque)

    with st.expander(":material/analytics: Datos Presentación"):
        ISAKPresentation.render_fraccionamiento_5_componentes(
            record_persist["calculos"]
        )
        ISAKPresentation.render_resumen(record_persist)

def records_form(jugadora, records_df=None, tipo="formulario"):

    if "file_upload_version" not in st.session_state:
        st.session_state.file_upload_version = 0

    if st.session_state.get("save_error"):
        st.error(t("Error al guardar el registro. Inténtalo nuevamente."))
        st.session_state.pop("save_error", None)
    elif st.session_state.get("submitted"):
        st.success(t("Registro guardado correctamente."))
        st.session_state.pop("submitted", None)

    jugadora_id = _validate_context(jugadora)
    if not jugadora_id:
        return

    baseline_isak = _get_baseline_isak(records_df, jugadora_id)
    modo = _resolve_modo(baseline_isak)

    username = st.session_state["auth"]["name"].lower()

    record = _build_base_record(
        modo, jugadora_id, username, baseline_isak
    )

    record = _inject_metadata(record, jugadora_id, modo, username)

    if tipo == "archivo":
        record = _handle_excel_import(record)
        # with st.expander(":material/settings: Advanced Settings"):
        #     #st.caption(t("Configuración avanzada de mapeo RAW del archivo"))

        #     col1, col2 = st.columns(2)

        #     with col1:
        #         row_nombre = st.number_input(
        #             t("Fila del nombre de la jugadora"),
        #             min_value=1,
        #             value=2,
        #             step=1,
        #             key="raw_nombre_row"
        #         )

        #     with col2:
        #         cols_nombre = st.text_input(
        #             t("Columnas del nombre (ej: B,C)"),
        #             value="B,C",
        #             key="raw_nombre_cols"
        #         )

        #     raw_mapper = {
        #         "jugadora_nombre": {
        #             "row": row_nombre,
        #             "cols": [c.strip() for c in cols_nombre.split(",") if c.strip()],
        #         }
        #     }

        #record, result = _handle_excel_import(record)

        # if result["status"] == "warning":
        #     st.warning(
        #         t(
        #             f"El nombre del archivo ({result['excel']}) "
        #             f"no coincide con la jugadora seleccionada "
        #             f"({result['app']}). "
        #             f"Similitud: {result['score']}%"
        #         )
        #     )
        # elif result["status"] == "ok":
        #     st.success(
        #         t(
        #             f"Nombre del archivo verificado "
        #             f"(similitud {result['score']}%)"
        #         )
        #     )
        # elif result["status"] == "missing":
        #   st.info(t("No se pudo leer el nombre de la jugadora desde el archivo."))

        
    tabs = st.tabs([t("Formulario"), t("Previsualizar")])
    
    with tabs[0]:
        record_persist = _render_form_tab(record, jugadora)
    with tabs[1]:
        _render_preview_tab(record_persist)
