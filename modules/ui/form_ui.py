import json
import streamlit as st
import datetime
import pandas as pd
from modules.util.io_files import load_catalog_list
from modules.db.db_catalogs import load_catalog_list_db
from modules.schema import DIAS_SEMANA
from modules.i18n.i18n import t
from modules.app_config.styles import template_COLOR_NORMAL, template_COLOR_INVERTIDO
from modules.util.key_builder import KeyBuilder

def validate_record(record: dict) -> tuple[bool, str]:
    if not record.get("metodo"):
        return False, "Selecciona el método de evaluación."

    if record.get("peso_kg") is None or record["peso_kg"] <= 0:
        return False, "El peso es obligatorio."

    if record.get("talla_cm") is None or record["talla_cm"] <= 0:
        return False, "La talla es obligatoria."

    if record.get("porcentaje_grasa") is not None:
        if not (0 < record["porcentaje_grasa"] < 60):
            return False, "Porcentaje de grasa inválido."

    if record.get("porcentaje_muscular") is not None:
        if not (0 < record["porcentaje_muscular"] < 70):
            return False, "Porcentaje muscular inválido."

    return True, ""


@st.fragment
def form_inputs(record: dict, genero: str):
    kb = KeyBuilder()

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

    with col1:
        record["metodo"] = st.selectbox(
            "Método de evaluación",
            ["ISAK", "BIA", "DXA", "Otro"],
            index=0,
            disabled=True
        )

    with col2:
        record["peso_kg"] = st.number_input(
            "Peso (kg)",
            min_value=30.0,
            max_value=150.0,
            step=0.1,
            key=kb.key("peso")
        )

    with col3:
        record["talla_cm"] = st.number_input(
            "Talla (cm)",
            min_value=120.0,
            max_value=220.0,
            step=0.1,
            key=kb.key("talla")
        )

    ##st.divider()

    with col4:
        record["suma_6_pliegues_mm"] = st.number_input(
            "Suma 6 pliegues (mm)",
            min_value=0.0,
            step=0.1,
            key=kb.key("pliegues")
        )

    with col5:
        record["porcentaje_grasa"] = st.number_input(
            "% Grasa",
            min_value=0.0,
            max_value=60.0,
            step=0.1,
            key=kb.key("grasa")
        )

    col6, col7, col8, _,_ = st.columns([1, 1, 1, 1, 1])
    
    with col6:
        record["porcentaje_muscular"] = st.number_input(
            "% Masa muscular",
            min_value=0.0,
            max_value=70.0,
            step=0.1,
            key=kb.key("musculo")
        )


    with col7:
        record["masa_osea_kg"] = st.number_input(
            "Masa ósea (kg)",
            min_value=0.0,
            step=0.01,
            key=kb.key("masa_osea")
        )

    with col8:
        if record.get("masa_osea_kg") and record.get("porcentaje_muscular"):
            record["indice_musculo_oseo"] = round(
                record["porcentaje_muscular"] / record["masa_osea_kg"], 2
            )
            #st.metric("Índice músculo–óseo", record["indice_musculo_oseo"])
            st.text_input("Índice músculo-óseo", value=record["indice_musculo_oseo"], disabled=True)
        else:
            record["indice_musculo_oseo"] = None
            #st.text_input(value="", disabled=True)
            st.text_input("Índice músculo-óseo", value=0, disabled=True)

    st.divider()
    record["observaciones"] = st.text_area("Observaciones")

    is_valid, msg = validate_record(record)
    return record, is_valid, msg

def record_form(record: dict, genero: str) -> tuple[dict, bool, str]:
    record, is_valid, msg = form_inputs(record, genero)
    return record, is_valid, msg