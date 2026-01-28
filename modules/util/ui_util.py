import time
import streamlit as st
from modules.db.db_records import save_isak_session
from modules.i18n.i18n import t
from modules.util.excel_util import reset_normalize_dup_counter

# ===============================
# 🔸 Diálogo de confirmación de registro
# ===============================
@st.dialog(t("Confirmar registro"), width="small")
def dialog_confirmar_registro(record, jugadora):
    nombre = jugadora["nombre_jugadora"]

    st.warning(
        f"{t('¿Desea confirmar el registro de')}"
        f"{t('para la jugadora')} **{nombre}**?"
    )
    _, col2, col3 = st.columns([1.6, 1, 1])

    with col2:
        if st.button(t(":material/cancel: Cancelar")):
            st.rerun()

    with col3:
        if st.button(t(":material/check: Confirmar"), type="primary"):
            success = save_isak_session(record)
            st.session_state.file_upload_version += 1
            st.session_state.pop("isak_excel_sheet", None)
            reset_normalize_dup_counter()

            if success:
                st.session_state["submitted"] = True
                st.session_state[f"redirect_{st.session_state['client_session_id']}"] = True
            else:
                st.session_state["save_error"] = True

            # ---------------------------------------
            # 7. Redirección segura SOLO para este navegador
            # ---------------------------------------
            if st.session_state.get("submitted"):
                del st.session_state["submitted"]
                st.session_state["target_page"] = "registro"
                time.sleep(2)  # Pequeña pausa para evitar conflictos
                st.switch_page("pages/switch.py")
                #st.rerun()



