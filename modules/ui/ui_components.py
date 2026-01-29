from decimal import Decimal
from typing import Any
import pandas as pd
import streamlit as st
import datetime
import json
from modules.util.util import get_date_range_input
from modules.i18n.i18n import t
from modules.schema import MAP_POSICIONES
from modules.util.util import load_posiciones_traducidas
from datetime import date

def select_plantel(comp_df: pd.DataFrame, session_id: str | None = None):
    comp_options = comp_df.to_dict("records")

    return st.selectbox(
        t("Plantel"),
        options=comp_options,
        format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
        placeholder=t("Seleccione un plantel"),
        index=3,
        key=f"plantel_antropometria__{session_id}"
    )

def select_posicion(session_id: str, competicion):
    MAP_POSICIONES_TRADUCIDAS = load_posiciones_traducidas()
    MAP_POSICIONES_INVERTIDO = {v: k for k, v in MAP_POSICIONES_TRADUCIDAS.items()}

    posicion_traducida = st.selectbox(
        t("Posición"),
        options=list(MAP_POSICIONES_TRADUCIDAS.values()),
        placeholder=t("Seleccione una posición"),
        index=None,
        key=f"posicion_antropometria__{session_id}"
    )

    clave = MAP_POSICIONES_INVERTIDO.get(posicion_traducida)
    posicion = MAP_POSICIONES.get(clave)

    # Reset jugadora si cambia el filtro
    filtro_actual = (competicion["codigo"] if competicion else None, posicion)
    if st.session_state.get("last_filtro_jugadora_antropo") != filtro_actual:
        st.session_state.pop("jugadora_antropometria", None)
        st.session_state["last_filtro_jugadora_antropo"] = filtro_actual

    return posicion

def filter_jugadoras_base(
    jug_df: pd.DataFrame,
    competicion: dict | None,
    posicion: str | None
) -> pd.DataFrame:

    df = jug_df.copy()

    if competicion:
        df = df[df["plantel"] == competicion["codigo"]]

    if posicion:
        df = df[df["posicion"] == posicion]

    return df

def filter_jugadoras_sin_registro_hoy(
    jug_df: pd.DataFrame,
    records_df: pd.DataFrame | None
) -> pd.DataFrame:

    if records_df is None or records_df.empty:
        return jug_df

    hoy = date.today()

    records_df = records_df.copy()
    records_df["_fecha"] = pd.to_datetime(
        records_df["fecha_medicion"], errors="coerce"
    ).dt.date

    ids_registradas_hoy = (
        records_df[
            (records_df["_fecha"] == hoy)
            & (records_df.get("deleted_at").isna() if "deleted_at" in records_df else True)
        ]["identificacion"]
        .astype(str)
        .unique()
    )

    return jug_df[
        ~jug_df["identificacion"].astype(str).isin(ids_registradas_hoy)
    ]

def select_jugadora(
    jug_df_filtrado: pd.DataFrame,
    records_df: pd.DataFrame | None
):
    if jug_df_filtrado.empty:
        st.error(t("No hay jugadoras disponibles con los filtros seleccionados"))
        return None, None

    jugadora_nombres = (
        jug_df_filtrado["nombre_jugadora"]
        .astype(str)
        .sort_values()
        .tolist()
    )

    jugadora_labels = {
        nombre: f"{i + 1} - {nombre}"
        for i, nombre in enumerate(jugadora_nombres)
    }

    jugadora_nombre = st.selectbox(
        t("Jugadora"),
        options=jugadora_nombres,
        index=None,
        format_func=lambda x: jugadora_labels[x],
        placeholder=t("Seleccione una jugadora")
    )

    if not jugadora_nombre:
        return None, None

    jugadora = jug_df_filtrado[
        jug_df_filtrado["nombre_jugadora"].astype(str) == jugadora_nombre
    ].iloc[0].to_dict()

    df_isak = None
    if records_df is not None and not records_df.empty:
        jugadora_id = str(jugadora.get("identificacion"))
        df_isak = records_df[
            records_df["identificacion"].astype(str) == jugadora_id
        ].copy()

    return jugadora, df_isak

def select_tipo_registro(session_id: str) -> str:
    opciones = ["Formulario", "Archivo"]

    tipo = st.radio(
        t("Tipo de registro"),
        options=opciones,
        horizontal=True,
        index=opciones.index(
            st.session_state.get("tipo_registro", "Formulario")
        ),
        key=f"tipo_registro__{session_id}"
    )

    return tipo.lower()

def select_jugadora_simple(
    jug_df_filtrado: pd.DataFrame,
    key: str,
    disabled: bool = False,
    persist: bool = False,
):
    if jug_df_filtrado.empty:
        st.warning(t("No hay jugadoras disponibles"))
        return None

    nombres = (
        jug_df_filtrado["nombre_jugadora"]
        .astype(str)
        .sort_values()
        .tolist()
    )

    labels = {n: f"{i+1} - {n}" for i, n in enumerate(nombres)}

    nombre = st.selectbox(
        t("Jugadora"),
        options=nombres,
        index=None,
        format_func=lambda x: labels[x],
        placeholder=t("Seleccione una jugadora"),
        disabled=disabled,
        key=key,
    )

    if not nombre:
        if persist:
            st.session_state.pop("nombre_jugadora", None)
        return None

    if persist:
        st.session_state["nombre_jugadora"] = nombre

    return jug_df_filtrado[
        jug_df_filtrado["nombre_jugadora"].astype(str) == nombre
    ].iloc[0].to_dict()

def selection_header_registro(jug_df, comp_df, records_df=None):
    session_id = st.session_state.get("client_session_id", "default")
    col1, col2, col3, col4 = st.columns([2, 1, 2, 1.5])

    with col1:
        competicion = select_plantel(comp_df, session_id)

    with col2:
        posicion = select_posicion(session_id, competicion)

    with col3:
        df_jug = filter_jugadoras_base(jug_df, competicion, posicion)
        df_jug = filter_jugadoras_sin_registro_hoy(df_jug, records_df)

        jugadora = select_jugadora_simple(
            df_jug,
            key=f"jugadora_antropometria__{session_id}",
            persist=False
        )

        df_isak = None
        if jugadora and records_df is not None:
            df_isak = records_df[
                records_df["identificacion"].astype(str)
                == str(jugadora["identificacion"])
            ].copy()

    with col4:
        tipo = select_tipo_registro(session_id)

    return jugadora, posicion, df_isak, tipo

#######################################
#######################################

def selection_header(jug_df, comp_df, records_df=None, modo="reporte"):
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        competicion = select_plantel(comp_df)

    with col2:
        df_jug = filter_jugadoras_base(jug_df, competicion, posicion=None)

        jugadora = select_jugadora_simple(
            df_jug,
            key="jugadora_selector",
            disabled=(modo == "reporte_grupal"),
            persist=True
        )

    with col3:
        hoy = datetime.date.today()
        start, end = get_date_range_input(
            t("Rango de fechas"),
            start_default=hoy - datetime.timedelta(days=15),
            end_default=hoy,
        )

    df_filtrado = filtrar_registros_reporte(
        records_df,
        jugadora=jugadora,
        start=start,
        end=end,
        modo=modo,
    )

    return df_filtrado, jugadora, start, end

def filtrar_registros_reporte(
    df: pd.DataFrame,
    jugadora: dict | None = None,
    start=None,
    end=None,
    modo: str = "reporte",
) -> pd.DataFrame:

    if df is None or df.empty:
        return df

    df_filtrado = df.copy()

    # --- Jugadora ---
    if jugadora:
        df_filtrado = df_filtrado[
            df_filtrado["identificacion"] == jugadora["identificacion"]
        ]

    # --- Rango de fechas ---
    if start and end and "fecha_sesion" in df_filtrado:

        if pd.api.types.is_datetime64_any_dtype(df_filtrado["fecha_sesion"]):
            df_filtrado["fecha_sesion"] = df_filtrado["fecha_sesion"].dt.date

        start = start.date() if hasattr(start, "to_pydatetime") else start
        end = end.date() if hasattr(end, "to_pydatetime") else end

        df_filtrado = df_filtrado[
            (df_filtrado["fecha_sesion"] >= start)
            & (df_filtrado["fecha_sesion"] <= end)
        ]

    return df_filtrado

#######################################
#######################################

def normalize_for_ui(obj: Any) -> Any:
    """
    Convierte Decimal → float y procesa estructuras anidadas
    para visualización / JSON / Streamlit.
    """
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, dict):
        return {k: normalize_for_ui(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [normalize_for_ui(v) for v in obj]

    return obj

def preview_record(record: dict) -> None:
    jug = record.get("id_jugadora", "-")
    fecha = record.get("fecha_sesion", "-")
    #turno = record.get("turno", "-")
    tipo = record.get("tipo_isak", "-")
    st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha} |  **Tipo:** {tipo}")
    with st.expander("Ver registro JSON", expanded=True):
        record_ui = normalize_for_ui(record)
        st.code(json.dumps(record_ui, ensure_ascii=False, indent=2), language="json")