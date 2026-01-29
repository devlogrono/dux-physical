import os
import pandas as pd
import streamlit as st
import bcrypt
import time
from datetime import timedelta, date

# ============================
# INIT CONFIG & AUTH
# ============================

from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
from modules.i18n.i18n import t
import modules.app_config.config as config
from modules.schema import new_base_record
from modules.util.records_util import (
    generar_fechas,
    generar_valores_antropometria,
)

config.init_config()

jug_df = load_players_db()
comp_df = load_competitions_db()

# Acceso solo developer
if st.session_state["auth"]["rol"].lower() != "developer":
    st.switch_page("app.py")

st.header(t(":red[Developer] Area"), divider="red")

# ============================
# SESSION STATE
# ============================

if "dev_gen_running" not in st.session_state:
    st.session_state.dev_gen_running = False
    st.session_state.dev_gen_stop = False
    st.session_state.dev_gen_log = []
    st.session_state.dev_gen_start_ts = None

# ============================
# SECURITY UTILS
# ============================

def hash_password(password: str) -> str:
    if isinstance(password, str):
        password = password.encode("utf-8")
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# ============================
# UI TABS
# ============================

tabs = st.tabs([
    t(":material/user_attributes: Usuarios"),
    t(":material/description: Utilidades"),
    t(":material/science: Generador Antropometría"),
    t(":material/upload: Leer Excel")
])

# ============================================================
# TAB 1 – USUARIOS
# ============================================================

with tabs[0]:
    st.subheader("Generar password bcrypt")

    password_input = st.text_input(
        t("Introduce la contraseña"),
        type="password",
    )

    if st.button(t("Generar hash"), type="primary"):
        if not password_input:
            st.warning(t("Debes escribir una contraseña."))
        else:
            st.code(hash_password(password_input))

# ============================================================
# TAB 2 – UTILIDADES
# ============================================================

with tabs[1]:
    if st.button(t("Reiniciar caché")):
        st.cache_data.clear()
        st.success(t("Caché limpiada correctamente."))

# ============================================================
# TAB 3 – GENERADOR ANTROPOMETRÍA (DEV)
# ============================================================

with tabs[2]:
    st.subheader(t("Generador de datos antropométricos (DEV)"))

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        competiciones = comp_df.to_dict("records")
        competicion = st.selectbox(
            t("Plantel"),
            options=competiciones,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            index=3,
            disabled=st.session_state.dev_gen_running,
        )

    with col2:
        n_registros = st.number_input(
            t("Registros por jugadora"),
            min_value=1,
            max_value=12,
            value=6,
            disabled=st.session_state.dev_gen_running,
        )

    with col3:
        fecha_inicio = st.date_input(
            t("Fecha inicio"),
            value=date.today() - timedelta(days=365),
            disabled=st.session_state.dev_gen_running,
        )

    with col4:
        fecha_fin = st.date_input(
            t("Fecha fin"),
            value=date.today(),
            disabled=st.session_state.dev_gen_running,
        )

    st.warning(
        t(
            "⚠️ Esta acción insertará registros reales en la base de datos "
            "con el usuario developer."
        )
    )

    # ----------------------------
    # BOTONES
    # ----------------------------
    col_run, col_stop, _ = st.columns([1, 1, 4.5])

    with col_run:
        start_clicked = st.button(
            t("Generar registros"),
            type="primary",
            disabled=st.session_state.dev_gen_running,
        )

    with col_stop:
        stop_clicked = st.button(
            t("Detener proceso"),
            type="secondary",
            disabled=not st.session_state.dev_gen_running,
        )

    if stop_clicked and st.session_state.dev_gen_running:
        st.session_state.dev_gen_stop = True

    # ============================================================
    # PROCESO PRINCIPAL
    # ============================================================

    if start_clicked:

        # ---- VALIDACIONES ----
        if fecha_fin <= fecha_inicio:
            st.error(t("La fecha fin debe ser posterior a la fecha inicio."))
            st.stop()

        if (fecha_fin - fecha_inicio).days < 180:
            st.error(t("El rango debe ser de al menos 6 meses."))
            st.stop()

        st.session_state.dev_gen_running = True
        st.session_state.dev_gen_stop = False
        st.session_state.dev_gen_log = []
        st.session_state.dev_gen_start_ts = time.time()

        progress = st.progress(0.0)
        counter = st.empty()
        log_box = st.empty()

        try:
            codigo = competicion["codigo"]

            jugadoras = jug_df[
                jug_df["plantel"] == codigo
            ]["identificacion"].tolist()

            if not jugadoras:
                st.warning(t("No hay jugadoras en este plantel."))
                st.stop()

            total_previsto = len(jugadoras) * n_registros
            procesados = 0
            insertados = 0

            with st.spinner(t("Generando registros antropométricos…")):

                for id_jugadora in jugadoras:

                    if st.session_state.dev_gen_stop:
                        break

                    fechas = generar_fechas(
                        fecha_inicio,
                        fecha_fin,
                        n_registros,
                    )

                    for fecha in fechas:

                        if st.session_state.dev_gen_stop:
                            break

                        base = new_base_record(
                            id_jugadora=id_jugadora,
                            username="developer",
                        )

                        valores = generar_valores_antropometria()

                        record = {
                            **base,
                            **valores,
                            "metodo": "ISAK",
                            "fecha_hora_registro": fecha.isoformat(),
                            "observaciones": "Registro generado automáticamente (DEV)",
                        }

                        ok = upsert_record_db(record)

                        procesados += 1
                        if ok:
                            insertados += 1

                        progress.progress(
                            min(procesados / total_previsto, 1.0)
                        )

                        counter.markdown(
                            t(
                                f"**Procesados:** {procesados}/{total_previsto}  \n"
                                f"**Insertados:** {insertados}"
                            )
                        )

                        st.session_state.dev_gen_log.append(
                            f"{id_jugadora} · {fecha} · {'OK' if ok else 'ERROR'}"
                        )

                        log_box.text(
                            "\n".join(st.session_state.dev_gen_log[-10:])
                        )

            elapsed = time.time() - st.session_state.dev_gen_start_ts

            if st.session_state.dev_gen_stop:
                st.warning(
                    t(
                        f"Proceso detenido manualmente.  \n"
                        f"Insertados: {insertados}  \n"
                        f"Tiempo: {elapsed:.1f}s"
                    )
                )
            else:
                st.success(
                    t(
                        f"Proceso completado correctamente.  \n"
                        f"Insertados: {insertados}  \n"
                        f"Tiempo total: {elapsed:.1f}s"
                    )
                )

        except Exception as e:
            st.error(str(e))

        finally:
            st.session_state.dev_gen_running = False
            st.session_state.dev_gen_stop = False

with tabs[3]:
    st.subheader("📂 Leer archivo Excel")

    uploaded_file = st.file_uploader(
        "Cargar archivo Excel",
        type=["xlsx", "xls"],
        accept_multiple_files=False
    )

    if uploaded_file is None:
        st.info("Carga un archivo .xls o .xlsx para visualizar su contenido")
        st.stop()

    try:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        # Selección automática del engine
        if file_ext == ".xls":
            engine = "xlrd"
        else:
            engine = "openpyxl"

        # Leer Excel
        xls = pd.ExcelFile(uploaded_file, engine=engine)

        sheet_name = st.selectbox(
            "Selecciona la hoja",
            options=xls.sheet_names
        )

        df = pd.read_excel(
            xls,
            sheet_name=sheet_name
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Filas", df.shape[0])
        col2.metric("Columnas", df.shape[1])
        col3.metric("Hoja", sheet_name)

        st.divider()

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:
        st.error("Error al leer el archivo Excel")
        st.exception(e)
