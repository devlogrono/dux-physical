
import streamlit as st
import modules.app_config.config as config

from modules.i18n.i18n import t
from modules.reports.plots_individuales import metricas
from modules.ui.ui_components import selection_header
from modules.reports.ui_individual import graficos_individuales, player_block_dux
from modules.db.db_records import get_records_db
from modules.db.db_players import load_players_db
from modules.db.db_competitions import load_competitions_db
from modules.util.db_util import get_isak

config.init_config()
st.header(t("Análisis :red[individual]"), divider="red")

# Load reference data
jug_df = load_players_db()
comp_df = load_competitions_db()
#df = get_records_db()
df_records = get_isak()
#st.dataframe(df_records)
df_filtrado, jugadora, start, end = selection_header(jug_df, comp_df, df_records, modo="reporte")

if not jugadora:
    st.info(t("Selecciona una jugadora para continuar."))
    st.stop()

player_block_dux(jugadora)

if df_filtrado is None or df_filtrado.empty:
    st.info(t("No hay datos en el periodo seleccionado."))
    st.stop()

#st.dataframe(df_filtrado)

metricas(df_filtrado)

graficos_individuales(df_filtrado)
