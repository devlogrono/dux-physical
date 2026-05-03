
import streamlit as st
import modules.app_config.config as config

from modules.i18n.i18n import t
from modules.util.db_util import get_isak

config.init_config()
from modules.ui.ui_app import filter_df_by_period
from modules.ui.ui_components import selection_header
from modules.reports.ui_grupal import group_dashboard
from modules.db.db_records import get_records_db
from modules.db.db_players import load_players_db
from modules.db.db_competitions import load_competitions_db

st.header(t("Análisis :red[grupal]"), divider="red")

# Load reference data
jug_df = load_players_db()
comp_df = load_competitions_db()
#records_df = get_records_db()
df_records = get_isak()
#st.dataframe(template_df, hide_index=True)    

df_filtrado, jugadora, start, end = selection_header(jug_df, comp_df, df_records, modo="reporte_grupal")

#st.dataframe(df, hide_index=True)
# --- Fila principal de filtros ---
col1, col2, _ = st.columns([2, 1.5, 1])

with col1:
    OPCIONES_PERIODO = {
        "Última sesión": t("Última medición"),
        "Historico": t("Ultimos 6 meses"),
    }

    periodo_traducido = st.radio(
        t("Periodo:"),
        list(OPCIONES_PERIODO.values()),
        horizontal=True,
        index=list(OPCIONES_PERIODO.keys()).index("Última sesión")
    )

    periodo = next(k for k, v in OPCIONES_PERIODO.items() if v == periodo_traducido)

# 👇 FUERA del with
df_periodo, articulo = filter_df_by_period(df_records, periodo)
group_dashboard(df_periodo, df_records, periodo, articulo)
