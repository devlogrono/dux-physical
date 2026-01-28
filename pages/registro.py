
import streamlit as st

from modules.app_config import config
from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
config.init_config()

from modules.auth_system.auth_core import init_app_state, validate_login
from modules.i18n.i18n import t
from modules.db.db_records import get_records_db

from modules.ui.ui_components import selection_header_registro
from modules.ui.ui_records import records_form

# Authentication gate
init_app_state()
is_valid = validate_login()

st.header(t("Registro"), divider="red")


# Load reference data
records_df = get_records_db()
jug_df = load_players_db()
comp_df = load_competitions_db()

jugadora, posicion, record_df, tipo = selection_header_registro(jug_df, comp_df, records_df)

records_form(jugadora, record_df, tipo)
