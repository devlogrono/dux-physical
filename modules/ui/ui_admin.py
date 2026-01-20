
import streamlit as st
from modules.db.db_records import delete_record
from modules.i18n.i18n import t

@st.dialog(t("Eliminar registros filtrados"), width="small")
def dialog_eliminar_todos_filtrados(ids_todos):
    st.error(
        t("Esta acción eliminará TODOS los registros mostrados en la tabla.")
    )

    st.write(
        t("Para confirmar, escriba la palabra") + " **eliminar**"
    )

    confirm_text = st.text_input(
        t("Confirmación"),
        placeholder="eliminar"
    )

    _, col2, col3 = st.columns([1.8, 1, 1])

    with col2:
        if st.button(t(":material/cancel: Cancelar")):
            st.rerun()

    with col3:
        if confirm_text.strip().lower() == "eliminar":
            if st.button(
                t(":material/delete: Eliminar todos"),
                type="primary"
            ):
                deleted_by = st.session_state["auth"]["name"].lower()
                exito, mensaje = delete_record(ids_todos, deleted_by)

                if exito:
                    st.session_state["reload_flag"] = True
                    st.session_state["admin_delete_all"] = True
                else:
                    st.session_state["save_error"] = mensaje

                st.rerun()
        else:
            st.button(
                t(":material/delete: Eliminar todos"),
                disabled=True
            )


# ===============================
# 🔸 Diálogo de confirmación
# ===============================
@st.dialog(t("Confirmar"), width="small")
def dialog_eliminar(ids_seleccionados):
    st.warning(f"¿{t('Está seguro de eliminar')} {len(ids_seleccionados)} {t('elemento')}(s)?")

    _, col2, col3 = st.columns([1.8, 1, 1])
    with col2:
        if st.button(t(":material/cancel: Cancelar")):
            st.rerun()
    with col3:
        if st.button(t(":material/delete: Eliminar"), type="primary"):
            deleted_by = st.session_state["auth"]["name"].lower()
            exito, mensaje = delete_record(ids_seleccionados, deleted_by)

            if exito:
                # Marcar para recarga
                st.session_state["reload_flag"] = True

            st.rerun()
