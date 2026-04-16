
import streamlit as st
import pandas as pd
import modules.app_config.config as config

from modules.i18n.i18n import t
from modules.reports.plots_individuales import metricas
from modules.ui.ui_components import selection_header
from modules.reports.ui_individual import graficos_individuales, player_block_dux
from modules.db.db_players import load_players_db
from modules.db.db_competitions import load_competitions_db
from modules.util.db_util import get_isak

config.init_config()
st.header(t("Análisis :red[individual]"), divider="red")

# Load reference data
jug_df = load_players_db()
comp_df = load_competitions_db()
df_records = get_isak()

# 👇 leer preselección
jugadora_pre_id = st.session_state.get("jugadora_preseleccionada_id")
jugadora_pre_nombre = st.session_state.get("jugadora_preseleccionada_nombre")

df_filtrado, jugadora, start, end = selection_header(
    jug_df,
    comp_df,
    df_records,
    modo="reporte",
    jugadora_pre_id=jugadora_pre_id,
    jugadora_pre_nombre=jugadora_pre_nombre,
)

# 👇 limpiar preselección después de usarla
st.session_state.pop("jugadora_preseleccionada_id", None)
st.session_state.pop("jugadora_preseleccionada_nombre", None)

if not jugadora:
    st.info(t("Selecciona una jugadora para continuar."))
    st.stop()

# Histórico completo de la jugadora
df_jugadora_full = df_records[
    df_records["identificacion"].astype(str) == str(jugadora["identificacion"])
].copy()

if df_jugadora_full.empty:
    st.info(t("No hay registros antropométricos para la jugadora seleccionada."))
    st.stop()

df_jugadora_full["fecha_medicion"] = pd.to_datetime(
    df_jugadora_full["fecha_medicion"], errors="coerce"
)

player_block_dux(jugadora)

# -------------------------
# Selector de periodo
# -------------------------
st.markdown(f"**{t('Periodo:')}**")

OPCIONES_PERIODO = {
    "Última medición": t("Última medición"),
    "Historico": t("Últimos 6 meses"),
}

periodo_traducido = st.radio(
    t("Periodo"),
    list(OPCIONES_PERIODO.values()),
    horizontal=True,
    index=list(OPCIONES_PERIODO.keys()).index("Última medición"),
    label_visibility="collapsed",
    key="periodo_individual_selector"
)

periodo = next(k for k, v in OPCIONES_PERIODO.items() if v == periodo_traducido)

# -------------------------
# Filtrado por periodo
# -------------------------
if periodo == "Última medición":
    df_periodo = df_jugadora_full.copy()
else:
    fecha_max = df_jugadora_full["fecha_medicion"].max()
    fecha_min = fecha_max - pd.DateOffset(months=6)

    df_periodo = df_jugadora_full[
        df_jugadora_full["fecha_medicion"] >= fecha_min
    ].copy()

if df_periodo is None or df_periodo.empty:
    st.info(t("No hay datos en el periodo seleccionado."))
    st.stop()

# KPIs + interpretación + resumen técnico
metricas(df_periodo, periodo=periodo)

# Gráficos
graficos_individuales(df_periodo, df_records, jugadora)
