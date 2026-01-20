import streamlit as st

from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
from modules.db.db_records import get_records_db
from modules.util.util import clean_df, data_format
from modules.ui.ui_app import (
    filter_df_by_period,
    calc_metric_block,
    render_metric_cards
)

from modules.i18n.i18n import t
import modules.app_config.config as config
config.init_config()

st.header(t("Resumen de :red[1er Equipo]"), divider="red")
#st.session_state.clear()
# ============================================================
# 📦 CARGA DE DATOS
# ============================================================
df_records = get_records_db()
#st.dataframe(df)

if df_records.empty:
    st.warning(t("No hay registros disponibles."))
    st.stop()

df_records = data_format(df_records)
jug_df = load_players_db()
#st.dataframe(df_records)
 
#jug_df = jug_df[jug_df["plantel"] == "1FF"]
   
comp_df = load_competitions_db()
#ausencias_df = load_active_absences_db()

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================

# --- Fila principal de filtros ---
col1, col2, _ = st.columns([2, 1.5, 1])

with col1:
    # Diccionario clave interna → texto traducido
    OPCIONES_PERIODO = {
        "Última sesión": t("Última sesión"),
        "Historico": t("Ultimos 6 meses"),
    }

    periodo_traducido = st.radio(
        t("Periodo:"),
        list(OPCIONES_PERIODO.values()),horizontal=True,
        index=list(OPCIONES_PERIODO.keys()).index("Última sesión"))

    periodo = next(k for k, v in OPCIONES_PERIODO.items() if v == periodo_traducido)
    df_periodo, articulo = filter_df_by_period(df_records, periodo)

#st.dataframe(df, hide_index=True)
#st.dataframe(df_periodo, hide_index=True)

# Cálculos principales

peso_prom, chart_peso, delta_peso = calc_metric_block(df_periodo, periodo, "peso_kg", "mean")
grasa_prom, chart_grasa, delta_grasa = calc_metric_block(df_periodo, periodo, "porcentaje_grasa", "mean")
musculo_prom, chart_musculo, delta_musculo = calc_metric_block(df_periodo, periodo, "porcentaje_muscular", "mean")
indice_mo_prom, chart_mo, delta_mo = calc_metric_block(df_periodo, periodo, "indice_musculo_oseo", "mean")

#alertas_count, total_jugadoras, alertas_pct, chart_alertas, delta_alertas = calc_alertas(df_periodo, df, periodo)

# ============================================================
# 💠 TARJETAS DE MÉTRICAS
# ============================================================
render_metric_cards(
    peso_prom, delta_peso, chart_peso,
    grasa_prom, delta_grasa, chart_grasa,
    musculo_prom, delta_musculo, chart_musculo,
    indice_mo_prom, delta_mo, chart_mo,
    articulo
)
# ============================================================
# 📋 INTERPRETACIÓN Y RESUMEN TÉCNICO
# ============================================================
#show_interpretation(template_prom, rpe_prom, ua_total, alertas_count, alertas_pct, delta_ua, total_jugadoras)

#mostrar_resumen_tecnico(template_prom, rpe_prom, ua_total, alertas_count, total_jugadoras)

# ============================================================
# 📊 REGISTROS DEL PERIODO
# ============================================================

st.divider()
st.markdown(t("**Registros del periodo seleccionado**") + f"(:blue-background[{periodo_traducido}])")

st.dataframe(clean_df(df_periodo))
# # --- Fila principal de filtros ---
# col1, col2, _ = st.columns([1.5, 1.5, 1])

# with col1:
#     competiciones_options = comp_df.to_dict("records")
#     competicion = st.selectbox(
#         t("Plantel"),
#         options=competiciones_options,
#         format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
#         index=3,
#         key="aus_competicion",
#     )
  
# codigo_comp = competicion["codigo"]
# jug_df = jug_df[jug_df["plantel"] == codigo_comp]
# df_periodo = df_periodo[df_periodo["identificacion"].isin(jug_df["identificacion"])]

   
# tabs = st.tabs([
#         t(":material/physical_therapy: Indicadores de bienestar y carga"),
#         t(":material/description: Registros detallados"),
#         t(":material/report_problem: Pendientes de registro")
#     ])

if df_periodo.empty:
    st.info(t("No hay registros disponibles en este periodo."))
    st.stop()
