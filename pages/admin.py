import streamlit as st
import modules.app_config.config as config
from modules.ui.ui_admin import dialog_eliminar, dialog_eliminar_todos_filtrados
config.init_config()

from modules.db.db_catalogs import load_catalog_list_db
from modules.ui.ui_components import selection_header
from modules.i18n.i18n import t
from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
from modules.db.db_records import get_records_db

if st.session_state["auth"]["rol"].lower() not in ["admin", "developer"]:
    st.switch_page("app.py")
    
st.header(t("Administrador de :red[registros]"), divider="red")

# Load reference data
jug_df = load_players_db()
comp_df = load_competitions_db()
records_df = get_records_db()
tipo_ausencia_df = load_catalog_list_db("tipo_ausencia", as_df=True)

#st.dataframe(template_df)

records_df, jugadora, start, end = selection_header(jug_df, comp_df, records_df, modo="reporte")

if records_df.empty:
    st.error(t("No se encontraron registros"))
    st.stop()

disabled = records_df.columns.tolist()

columna = t("seleccionar")

# --- Agregar columna de selección si no existe ---
if columna not in records_df.columns:
    records_df.insert(0, columna, False)

#records_vista = records.drop("id", axis=1)

df_edited = st.data_editor(records_df, 
        column_config={
            columna: st.column_config.CheckboxColumn(columna, default=False)},   
        num_rows="fixed", hide_index=True, disabled=disabled)
st.caption(f"{len(records_df)} registros encontrados")

ids_seleccionados = df_edited.loc[df_edited[columna], "id"].tolist()

if st.session_state["auth"]["rol"].lower() in ["developer"]:
    st.write(t("Registros seleccionados:"), ids_seleccionados)

#st.dataframe(records, hide_index=True)
# save_if_modified(records, df_edited)
csv_data = records_df.to_csv(index=False).encode("utf-8")

exito, mensaje = False, ""


if st.session_state.get("reload_flag") and exito:     
    st.success(mensaje)
    st.session_state["reload_flag"] = False

col1, col2, col3, col4, _ = st.columns([1.6, 1.8, 1.8, 1.8,.1])
with col1:
    # --- Botón principal para abrir el diálogo ---
    if st.button(t(":material/delete: Eliminar seleccionados"), disabled=len(ids_seleccionados) == 0):
        dialog_eliminar(ids_seleccionados)
with col2:
    st.download_button(
            label=t(":material/download: Descargar registros en CSV"),
            data=csv_data, file_name="registros_template.csv", mime="text/csv")

if st.session_state["auth"]["rol"].lower() in ["developer"]:
    with col3:
            # Convertir a JSON (texto legible, sin índices)
            json_data = records_df.to_json(orient="records", force_ascii=False, indent=2)
            json_bytes = json_data.encode("utf-8")

            # Botón de descarga
            st.download_button(
                label=t(":material/download: Descargar registros en JSON"),
                data=json_bytes, file_name="registros_template.json", mime="application/json"
            )
    with col4:
        if st.button(
            t(":material/delete_forever: Eliminar Todos los registros"),
            disabled=records_df.empty):
            dialog_eliminar_todos_filtrados(records_df["id"].tolist())
