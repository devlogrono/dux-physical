
import streamlit as st
import pandas as pd
from modules.i18n.i18n import t
from .plots_grupales import (plot_distribuciones, 
                             plot_comparacion_mediciones, 
                             tabla_resumen, plot_perfil_antropometrico, 
                             plot_cambios_clave, plot_evolucion_temporal_grupal, plot_ratios_estructurales,plot_mapa_estructural)
from modules.ui.ui_app import (calc_metric_block)

def group_dashboard(df_filtrado: pd.DataFrame, df_calculo: pd.DataFrame, periodo: str, articulo: str) -> None:
    """
    Dashboard grupal de antropometría con KPIs técnicos, interpretación,
    resumen técnico y gráficos grupales.
    """

    if df_filtrado is None or df_filtrado.empty:
        st.info(t("No hay datos disponibles para el análisis grupal."))
        return

    # =========================
    # KPIs técnicos grupales
    # =========================
    peso_prom, chart_peso, delta_peso = calc_metric_block(df_filtrado, df_calculo, periodo, "peso_bruto_kg", "mean")
    grasa_prom, chart_grasa, delta_grasa = calc_metric_block(df_filtrado, df_calculo, periodo, "ajuste_adiposa_pct", "mean")
    musculo_prom, chart_musculo, delta_musculo = calc_metric_block(df_filtrado, df_calculo, periodo, "ajuste_muscular_pct", "mean")
    indice_mo_prom, chart_mo, delta_mo = calc_metric_block(df_filtrado, df_calculo, periodo, "idx_musculo_oseo", "mean")
    pliegues6_prom, chart_pliegues6, delta_pliegues6 = calc_metric_block(df_filtrado, df_calculo, periodo, "suma_6_pliegues_mm", "mean")

    st.markdown(t("### **Resumen técnico grupal**"))
    caption_text = (
        t("Los valores muestran el estado actual del grupo y la variación respecto a la medición anterior.")
        if periodo == "Última sesión"
        else t("Los valores muestran el promedio del periodo y la variación respecto al inicio del periodo seleccionado.")
    )

    st.caption(caption_text)

    render_metric_cards(
        peso_prom, delta_peso, chart_peso,
        grasa_prom, delta_grasa, chart_grasa,
        musculo_prom, delta_musculo, chart_musculo,
        indice_mo_prom, delta_mo, chart_mo,
        pliegues6_prom, chart_pliegues6, delta_pliegues6,
        articulo
    )

    st.divider()
    render_interpretacion_metricas_table(peso_prom, grasa_prom, musculo_prom, indice_mo_prom, pliegues6_prom)

    st.divider()
    render_resumen_tecnico_antropometria(
        peso_prom, grasa_prom, musculo_prom, indice_mo_prom, pliegues6_prom
    )

    st.divider()

    # =========================
    # Tabs de análisis grupal
    # =========================
    tabs = st.tabs([
        t("Perfil antropométrico"),
        t("Distribución corporal"),
        t("Comparación de mediciones"),
        t("Cambios clave"),
        t("Evolución temporal"),
        t("Perfil estructural"),
        t("Resumen grupal"),
    ])

    with tabs[0]:
        plot_perfil_antropometrico(df_filtrado)

    with tabs[1]:
        plot_distribuciones(df_filtrado)

    with tabs[2]:
        plot_comparacion_mediciones(df_filtrado, df_calculo, periodo)

    with tabs[3]:
        plot_cambios_clave(df_filtrado, df_calculo, periodo)

    with tabs[4]:
        plot_evolucion_temporal_grupal(df_calculo)

    with tabs[5]:
        plot_mapa_estructural(df_calculo)
        st.divider()
        plot_ratios_estructurales(df_calculo)

    with tabs[6]:
        tabla_resumen(df_filtrado)


def build_interpretacion_metricas_table(
    peso_prom,
    grasa_prom,
    musculo_prom,
    indice_mo_prom,
    pliegues6_prom
) -> pd.DataFrame:
    """
    Construye una tabla de interpretación de métricas antropométricas
    con nomenclatura homogénea para toda la app.
    """

    rows = []

    # Peso
    if pd.isna(peso_prom):
        interpretacion = "⚪ Sin datos: No hay datos suficientes para valorar el peso medio."
    else:
        interpretacion = "⚪ Descriptivo: Indicador de la masa corporal total media del equipo."

    rows.append({
        "Métrica": "Peso medio del grupo",
        "Valor": f"{peso_prom:.1f} kg" if not pd.isna(peso_prom) else "-",
        "Interpretación": interpretacion,
    })

    # % Grasa
    if pd.isna(grasa_prom):
        interpretacion = "⚪ Sin datos."
    elif grasa_prom < 14:
        interpretacion = "🟡 Muy bajo (<14%): Vigilar disponibilidad energética y contexto fisiológico."
    elif grasa_prom <= 20:
        interpretacion = "🟢 Adecuado (14-20%): Rango funcional para fútbol femenino."
    elif grasa_prom <= 24:
        interpretacion = "🟠 Moderado (20-24%): Con margen de optimización."
    else:
        interpretacion = "🔴 Elevado (>24%): Por encima del perfil deseado de rendimiento."

    rows.append({
        "Métrica": "Porcentaje de grasa medio",
        "Valor": f"{grasa_prom:.1f} %" if not pd.isna(grasa_prom) else "-",
        "Interpretación": interpretacion,
    })

    # % Muscular
    if pd.isna(musculo_prom):
        interpretacion = "⚪ Sin datos."
    elif musculo_prom < 40:
        interpretacion = "🟠 Bajo (<40%): Nivel de masa muscular mejorable para el alto rendimiento."
    elif musculo_prom <= 45:
        interpretacion = "🟢 Adecuado (40-45%): Buen nivel de desarrollo muscular para la categoría."
    else:
        interpretacion = "🟩 Excelente (>45%): Perfil muscular muy favorable para potencia y protección estructural."

    rows.append({
        "Métrica": "Porcentaje muscular medio",
        "Valor": f"{musculo_prom:.1f} %" if not pd.isna(musculo_prom) else "-",
        "Interpretación": interpretacion,
    })

    # Índice músculo / óseo
    if pd.isna(indice_mo_prom):
        interpretacion = "⚪ Sin datos."
    elif indice_mo_prom < 3.5:
        interpretacion = "🟠 Bajo (<3.5): Relación músculo / óseo por desarrollar."
    elif indice_mo_prom <= 4.2:
        interpretacion = "🟢 Adecuado (3.5-4.2): Relación favorable para el rendimiento."
    else:
        interpretacion = "🟩 Excelente (>4.2): Perfil estructural muy favorable."

    rows.append({
        "Métrica": "Índice músculo / óseo medio",
        "Valor": f"{indice_mo_prom:.2f}" if not pd.isna(indice_mo_prom) else "-",
        "Interpretación": interpretacion,
    })

    # Suma 6 pliegues
    if pd.isna(pliegues6_prom):
        interpretacion = "⚪ Sin datos."
    elif pliegues6_prom < 50:
        interpretacion = "🟩 Excelente (<50 mm): Perfil de alta competición."
    elif pliegues6_prom <= 70:
        interpretacion = "🟢 Adecuado (50-70 mm): Rango funcional para la mayoría de posiciones."
    elif pliegues6_prom <= 90:
        interpretacion = "🟠 Moderado (70-90 mm): Con margen de ajuste nutricional y de carga."
    else:
        interpretacion = "🔴 Elevado (>90 mm): Fuera del rango objetivo de rendimiento."

    rows.append({
        "Métrica": "Suma 6 pliegues",
        "Valor": f"{pliegues6_prom:.1f} mm" if not pd.isna(pliegues6_prom) else "-",
        "Interpretación": interpretacion,
    })

    return pd.DataFrame(rows)


def render_interpretacion_metricas_table(peso_prom, grasa_prom, musculo_prom, indice_mo_prom, pliegues6_prom) -> None:
    """
    Muestra la tabla de interpretación de métricas antropométricas.
    """

    tabla = build_interpretacion_metricas_table(peso_prom, grasa_prom, musculo_prom, indice_mo_prom, pliegues6_prom)

    if tabla.empty:
        st.info(t("No hay métricas disponibles para interpretar."))
        return

    st.markdown(t("### **Interpretación de métricas**"))

    st.dataframe(tabla, hide_index=True, use_container_width=True)
    st.caption("Consulta los rangos de referencia de cada métrica 👇")

    render_popovers_rangos_antropometria()

def render_resumen_tecnico_antropometria(
    peso_prom,
    grasa_prom,
    musculo_prom,
    indice_mo_prom,
    pliegues6_prom
) -> None:
    """
    Muestra un resumen técnico grupal de antropometría alineado
    con la tabla de interpretación homogénea.
    """

    def color_text(text: str, color: str) -> str:
        return f"<b style='color:{color}'>{text}</b>"

    color_descriptivo = "#607D8B"
    color_sin_datos = "#757575"
    color_muy_bajo = "#F1C40F"
    color_bajo_moderado = "#F39C12"
    color_adecuado = "#2ECC71"
    color_excelente = "#27AE60"
    color_elevado = "#E74C3C"

    # % grasa
    if pd.isna(grasa_prom):
        grasa_txt = color_text("sin datos suficientes", color_sin_datos)
    elif grasa_prom < 14:
        grasa_txt = color_text("muy bajo", color_muy_bajo)
    elif grasa_prom <= 20:
        grasa_txt = color_text("adecuado", color_adecuado)
    elif grasa_prom <= 24:
        grasa_txt = color_text("moderado", color_bajo_moderado)
    else:
        grasa_txt = color_text("elevado", color_elevado)

    # % muscular
    if pd.isna(musculo_prom):
        musculo_txt = color_text("sin datos suficientes", color_sin_datos)
    elif musculo_prom < 40:
        musculo_txt = color_text("bajo", color_bajo_moderado)
    elif musculo_prom <= 45:
        musculo_txt = color_text("adecuado", color_adecuado)
    else:
        musculo_txt = color_text("excelente", color_excelente)

    # Índice músculo / óseo
    if pd.isna(indice_mo_prom):
        imo_txt = color_text("sin datos suficientes", color_sin_datos)
    elif indice_mo_prom < 3.5:
        imo_txt = color_text("bajo", color_bajo_moderado)
    elif indice_mo_prom <= 4.2:
        imo_txt = color_text("adecuado", color_adecuado)
    else:
        imo_txt = color_text("excelente", color_excelente)

    # Suma 6 pliegues
    if pd.isna(pliegues6_prom):
        pliegues_txt = color_text("sin datos suficientes", color_sin_datos)
    elif pliegues6_prom < 50:
        pliegues_txt = color_text("excelente", color_excelente)
    elif pliegues6_prom <= 70:
        pliegues_txt = color_text("adecuado", color_adecuado)
    elif pliegues6_prom <= 90:
        pliegues_txt = color_text("moderado", color_bajo_moderado)
    else:
        pliegues_txt = color_text("elevado", color_elevado)

    peso_val = (
        color_text(f"{peso_prom:.1f} kg", color_descriptivo)
        if not pd.isna(peso_prom)
        else color_text("-", color_descriptivo)
    )
    grasa_val = (
        color_text(f"{grasa_prom:.1f}%", color_descriptivo)
        if not pd.isna(grasa_prom)
        else color_text("-", color_descriptivo)
    )
    musculo_val = (
        color_text(f"{musculo_prom:.1f}%", color_descriptivo)
        if not pd.isna(musculo_prom)
        else color_text("-", color_descriptivo)
    )
    imo_val = (
        color_text(f"{indice_mo_prom:.2f}", color_descriptivo)
        if not pd.isna(indice_mo_prom)
        else color_text("-", color_descriptivo)
    )
    pliegues_val = (
        color_text(f"{pliegues6_prom:.1f} mm", color_descriptivo)
        if not pd.isna(pliegues6_prom)
        else color_text("-", color_descriptivo)
    )

    resumen = (
        f"{t(':material/description: **Resumen técnico:**')} "
        f"El grupo presenta un peso medio de {peso_val}, "
        f"con un porcentaje de grasa {grasa_txt} ({grasa_val}) "
        f"y un porcentaje muscular {musculo_txt} ({musculo_val}). "
        f"El índice músculo / óseo medio se sitúa en un nivel {imo_txt} ({imo_val}), "
        f"mientras que la suma de 6 pliegues refleja un perfil {pliegues_txt} ({pliegues_val})."
    )

    st.markdown(resumen, unsafe_allow_html=True)


# ============================================================
# 💠 TARJETAS DE MÉTRICAS
# ============================================================

def render_metric_cards(
    peso_prom, delta_peso, chart_peso,
    grasa_prom, delta_grasa, chart_grasa,
    musculo_prom, delta_musculo, chart_musculo,
    indice_mo_prom, delta_indice_mo, chart_indice_mo,
    pliegues6_prom, chart_pliegues6, delta_pliegues6,
    articulo
):
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            t("Peso medio del grupo"),
            f"{peso_prom:.1f} kg" if not pd.isna(peso_prom) else "0 kg",
            f"{delta_peso:+.2f}%",
            chart_data=chart_peso,
            chart_type="line",
            border=True,
             delta_color="off",
            help=f"{t('Promedio de peso corporal del grupo')} ({articulo})."
        )

    with col2:
        st.metric(
            t("Porcentaje de grasa medio"),
            f"{grasa_prom:.1f} %" if not pd.isna(grasa_prom) else "0 %",
            f"{delta_grasa:+.2f}%",
            chart_data=chart_grasa,
            chart_type="area",
            border=True,
            delta_color="inverse",
            help=f"{t('Promedio de grasa corporal del grupo')} ({articulo})."
        )

    with col3:
        st.metric(
            t("Porcentaje muscular medio"),
            f"{musculo_prom:.1f} %" if not pd.isna(musculo_prom) else "0 %",
            f"{delta_musculo:+.2f}%",
            chart_data=chart_musculo,
            chart_type="area",
            border=True,
            help=f"{t('Promedio de masa muscular del grupo')} ({articulo})."
        )

    with col4:
        st.metric(
            t("Índice músculo / óseo medio"),
            f"{indice_mo_prom:.2f}" if not pd.isna(indice_mo_prom) else "0",
            f"{delta_indice_mo:+.2f}%",
            chart_data=chart_indice_mo,
            chart_type="line",
            border=True,
            help=f"{t('Relación promedio entre masa muscular y masa ósea del grupo')} ({articulo})."
        )

    with col5:
        st.metric(
            t("Suma 6 pliegues"),
            f"{pliegues6_prom:.1f}",
            f"{delta_pliegues6:+.2f}%",
            chart_data=chart_pliegues6,
            chart_type="line",
            border=True,
            delta_color="inverse",
            help=t("Suma de los 6 pliegues cutáneos (mm). Indica el nivel de grasa subcutánea del grupo")
        )


def render_popovers_rangos_antropometria():

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        with st.popover(t("% Grasa")):
            st.markdown(f"🟡 **{t('Muy bajo')}**: <14%")
            st.markdown(f"🟢 **{t('Adecuado')}**: 14–20%")
            st.markdown(f"🟠 **{t('Moderado')}**: 20–24%")
            st.markdown(f"🔴 **{t('Elevado')}**: >24%")

    with c2:
        with st.popover(t("% Muscular")):
            st.markdown(f"🟠 **{t('Bajo')}**: <40%")
            st.markdown(f"🟢 **{t('Adecuado')}**: 40–45%")
            st.markdown(f"🟩 **{t('Excelente')}**: >45%")

    with c3:
        with st.popover(t("Índice M/O")):
            st.markdown(f"🟠 **{t('Bajo')}**: <3.5")
            st.markdown(f"🟢 **{t('Adecuado')}**: 3.5–4.2")
            st.markdown(f"🟩 **{t('Excelente')}**: >4.2")

    with c4:
        with st.popover(t("6 pliegues")):
            st.markdown(f"🟩 **{t('Excelente')}**: <50 mm")
            st.markdown(f"🟢 **{t('Adecuado')}**: 50–70 mm")
            st.markdown(f"🟠 **{t('Moderado')}**: 70–90 mm")
            st.markdown(f"🔴 **{t('Elevado')}**: >90 mm")