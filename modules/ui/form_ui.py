import streamlit as st
from modules.i18n.i18n import t
from modules.util.isak_util import validate_isak_record
from modules.util.key_builder import KeyBuilder
from modules.util.util import f0

@st.fragment
def form_inputs(record: dict):
    kb = KeyBuilder()

    modo = "SEGUIMIENTO" if record.get("_modo") == "SEGUIMIENTO" else "COMPLETO"
    is_seguimiento = modo == "SEGUIMIENTO"

    min_value_ = 0.00
    # =========================
    # Datos básicos
    # =========================
    with st.container(border=False):
        st.subheader(t("Datos básicos"), divider="red")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            record["metodo"] = st.selectbox(
                t("Método de evaluación"),
                ["ISAK", "BIA", "DXA", t("Otro")],
                index=0,
                disabled=True
            )

        with col2:
            record["peso_bruto_kg"] = st.number_input(
                t("Peso bruto (kg)"),
                min_value=min_value_,
                max_value=150.0,
                step=0.1,
                value=f0(record.get("peso_bruto_kg"))
            )

        with col3:
            record["talla_corporal_cm"] = st.number_input(
                t("Talla corporal (cm)"),
                min_value=min_value_,
                max_value=220.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("talla_corporal_cm"))
            )

        with col4:
            record["talla_sentado_cm"] = st.number_input(
                t("Talla sentado (cm)"),
                min_value=min_value_,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("talla_sentado_cm"))
            )

        with col5:
            record["envergadura_cm"] = st.number_input(
                t("Envergadura (cm)"),
                min_value=min_value_,
                max_value=250.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("envergadura_cm"))
            )

    # =========================
    # Longitudes y segmentos
    # =========================
    with st.container(border=False):
        st.subheader(t("Longitudes y segmentos (cm)"), divider="red")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            record["acromial_radial"] = st.number_input(
                t("Acromial-Radial"),
                min_value=min_value_,
                max_value=70.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("acromial_radial"))
            )
            record["troc_tibial_lateral"] = st.number_input(
                t("Trocantérea-Tibial lateral"),
                min_value=min_value_,
                max_value=60.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("troc_tibial_lateral"))
            )
            
        with col2:
            record["radial_estiloidea"] = st.number_input(
                t("Radial-Estiloidea"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("radial_estiloidea"))
            )
            record["tibial_lateral"] = st.number_input(
                t("Tibial lateral"),
                min_value=min_value_,
                max_value=70.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("tibial_lateral"))
            )

        with col3:
            record["medial_estiloidea_dactilar"] = st.number_input(
                t("Medial estiloidea-Dactilar"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("medial_estiloidea_dactilar"))
            )
            record["tibial_medial_maleolar_medial"] = st.number_input(
                t("Tibial medial-maleolar medial"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("tibial_medial_maleolar_medial"))
            )

        with col4:
            record["ilioespinal"] = st.number_input(
                t("Ilioespinal"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("ilioespinal"))
            )
            record["pie"] = st.number_input(
                t("Pie"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("pie"))
            )

        with col5:
            record["trocanterea"] = st.number_input(
                t("Trocantérea"),
                min_value=min_value_,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("trocanterea"))
            )

    # =========================
    # Diámetros
    # =========================
    with st.container(border=False):
        st.subheader(t("Diámetros óseos (cm)"), divider="red")
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            record["biacromial"] = st.number_input(
                t("Biacromial"),
                min_value=min_value_,
                max_value=70.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("biacromial"))
            )
            record["muneca_biestiloideo"] = st.number_input(
                t("Muñeca (biestiloideo)"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("muneca_biestiloideo"))
            )

        with col2:
            record["torax_transverso"] = st.number_input(
                t("Tórax transverso"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("torax_transverso"))
            )
            record["tobillo_bimaleolar"] = st.number_input(
                t("Tobillo (bimaleolar)"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("tobillo_bimaleolar"))
            )

        with col3:
            record["torax_antero_posterior"] = st.number_input(
                t("Tórax antero-posterior"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("torax_antero_posterior"))
            )
            record["mano"] = st.number_input(
                t("Mano"),
                min_value=min_value_,
                step=0.01,
                disabled=is_seguimiento,
                value=f0(record.get("mano"))
            )

        with col4:
            record["bi_iliocrestideo"] = st.number_input(
                t("Bi-iliocrestídeo"),
                min_value=min_value_,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("bi_iliocrestideo"))
            )

        with col5:
            record["humeral_biepicondilar"] = st.number_input(
                t("Humeral (biepicondilar)"),
                min_value=min_value_,
                max_value=60.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("humeral_biepicondilar"))
            )

        with col6:
            record["femoral_biepicondilar"] = st.number_input(
                t("Femoral (biepicondilar)"),
                min_value=min_value_,
                max_value=70.0,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("femoral_biepicondilar"))
            )

    # =========================
    # Perímetros
    # =========================
    with st.container(border=False):
        st.subheader(t("Perímetros corporales (cm)"), divider="red")
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            record["perimetro_cabeza"] = st.number_input(
                t("Cabeza"),
                min_value=min_value_,
                step=0.1,
                disabled=is_seguimiento,
                value=f0(record.get("perimetro_cabeza"))
            )

        with col2:
            record["perimetro_cuello"] = st.number_input(
                t("Cuello"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_cuello"))
            )

        with col3:
            record["perimetro_brazo_relajado"] = st.number_input(
                t("Brazo relajado"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_brazo_relajado"))
            )
        
        with col4:
            record["perimetro_brazo_flexionado_en_tension"] = st.number_input(
                t("Brazo flex. en tensión"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_brazo_flexionado_en_tension"))
            )

        with col5:
            record["perimetro_antebrazo_maximo"] = st.number_input(
                t("Antebrazo máximo"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_antebrazo_maximo"))
            )
        
        with col6:
            record["perimetro_muneca"] = st.number_input(
                t("Muñeca"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_muneca"))
            )

        with col1:
            record["perimetro_torax_mesoesternal"] = st.number_input(
                t("Tórax"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_torax_mesoesternal"))
            )
        
        with col2:
            record["perimetro_cintura_minima"] = st.number_input(
                t("Cintura (min)"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_cintura_minima"))
            )

        with col3:
            record["perimetro_abdominal_maxima"] = st.number_input(
                t("Abdominal (max)"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_abdominal_maxima"))
            )

        with col4:
            record["perimetro_cadera_maximo"] = st.number_input(
                t("Cadera (max)"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_cadera_maximo"))
            )

        with col5:
            record["perimetro_muslo_maximo"] = st.number_input(
                t("Muslo (max)"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_muslo_maximo"))
            )
        
        with col6:
            record["perimetro_muslo_medial"] = st.number_input(
                t("Muslo medial"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_muslo_medial"))
            )

        with col1:
            record["perimetro_pantorrilla_maxima"] = st.number_input(
                t("Pantorrilla (max)"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_pantorrilla_maxima"))
            )
        
        with col2:
            record["perimetro_tobillo_minima"] = st.number_input(
                t("Tobillo (max)"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("perimetro_tobillo_minima"))
            )


    # =========================
    # Pliegues cutáneos (mm)
    # =========================
    with st.container(border=False):
        st.subheader(t("Pliegues cutáneos (mm)"), divider="red")
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            record["pliegue_triceps"] = st.number_input(
                t("Tríceps"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_triceps"))
            )
        
        with col2:
            record["pliegue_subescapular"] = st.number_input(
                t("Subescapular"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_subescapular"))
            )

        with col3:
            record["pliegue_biceps"] = st.number_input(
                t("Bíceps"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_biceps"))
            )

        with col4:
            record["pliegue_cresta_iliaca"] = st.number_input(
                t("Cresta ilíaca"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_cresta_iliaca"))
            )

        with col5:
            record["pliegue_supraespinal"] = st.number_input(
                t("Supraespinal"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_supraespinal"))
            )

        with col6:
            record["pliegue_abdominal"] = st.number_input(
                t("Abdominal"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_abdominal"))
            )

        with col1:
            record["pliegue_muslo_frontal"] = st.number_input(
                t("Muslo frontal"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_muslo_frontal"))
            )

        with col2:
            record["pliegue_pantorrilla_maxima"] = st.number_input(
                t("Pantorrilla"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_pantorrilla_maxima"))
            )

        with col3:
            record["pliegue_antebrazo"] = st.number_input(
                t("Antebrazo"),
                min_value=min_value_,
                step=0.1,
                value=f0(record.get("pliegue_antebrazo"))
            )

    is_valid, msg = validate_isak_record(record)
    return record, is_valid, msg

def record_form(record: dict) -> tuple[dict, bool, str]:

    record, is_valid, msg = form_inputs(record)
    return record, is_valid, msg