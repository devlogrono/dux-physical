
import streamlit as st
import pandas as pd
from modules.i18n.i18n import t
from .plots_grupales import (plot_distribuciones, plot_comparacion_mediciones, tabla_resumen, plot_perfil_antropometrico)

def group_dashboard(df_filtrado: pd.DataFrame):
    """Panel grupal de antropometría."""

    if df_filtrado.empty:
        st.info(t("No hay datos antropométricos en el periodo seleccionado."))
        st.stop()

    st.divider()
    tabs = st.tabs([
        t(":material/scatter_plot: Perfil antropométrico"),
        t(":material/monitor_weight: Distribución corporal"),
        t(":material/compare: Comparación mediciones"),
        t(":material/table_chart: Resumen grupal"),
    ])

    with tabs[0]:
        plot_perfil_antropometrico(df_filtrado)

    with tabs[1]:
        plot_distribuciones(df_filtrado)

    with tabs[2]:
        plot_comparacion_mediciones(df_filtrado)

    with tabs[3]:
        tabla_resumen(df_filtrado)

