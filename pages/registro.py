
import streamlit as st

from modules.app_config import config
from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
config.init_config()

from modules.auth_system.auth_core import init_app_state, validate_login
from modules.i18n.i18n import t
from modules.db.db_records import get_records_db
from modules.db.db_catalogs import load_catalog_list_db

from modules.ui.ui_components import selection_header_registro
from modules.ui.records_ui import records_form

# Authentication gate
init_app_state()
is_valid = validate_login()

##:red[:material/check_in_out:]
st.header(t("Registro"), divider="red")

# Load reference data
records_df = get_records_db()
jug_df = load_players_db()
comp_df = load_competitions_db()

jugadora = selection_header_registro(jug_df, comp_df, records_df)
st.divider()

if st.session_state.get("submitted"):
    st.session_state["submitted"] = False

#st.dataframe(jugadora)
records_form(jugadora)
    