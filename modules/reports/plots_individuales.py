import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.i18n.i18n import t
from modules.reports.ui_grupal import render_popovers_rangos_antropometria

def _fmt(valor, sufijo=""):
    if pd.isna(valor):
        return "-"
    return f"{valor:.2f} {sufijo}".strip()

def _fmt_val(v, decimals=2, suffix=""):
    if pd.isna(v):
        return "—"
    return f"{v:.{decimals}f}{suffix}"

def _get_comparison_rows_individual(df: pd.DataFrame, periodo: str):
    """
    Devuelve la fila actual y la fila de referencia para individual.

    - Última medición -> última vs anterior
    - Histórico -> última vs primera del periodo
    """
    if df is None or df.empty or "fecha_medicion" not in df.columns:
        return None, None

    out = df.copy()
    out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")

    if "created_at" in out.columns:
        out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")

    sort_cols = ["fecha_medicion"]
    asc_desc = [False]
    asc_asc = [True]

    if "created_at" in out.columns:
        sort_cols.append("created_at")
        asc_desc.append(False)
        asc_asc.append(True)

    if "id_isak" in out.columns:
        sort_cols.append("id_isak")
        asc_desc.append(False)
        asc_asc.append(True)

    out_desc = out.sort_values(sort_cols, ascending=asc_desc).reset_index(drop=True)
    out_asc = out.sort_values(sort_cols, ascending=asc_asc).reset_index(drop=True)

    actual = out_desc.iloc[0] if len(out_desc) >= 1 else None

    if periodo == "Última medición":
        referencia = out_desc.iloc[1] if len(out_desc) >= 2 else None
    else:
        referencia = out_asc.iloc[0] if len(out_asc) >= 2 else None

    return actual, referencia

def _calc_delta_pct(curr, prev):
    if pd.isna(curr) or pd.isna(prev) or prev == 0:
        return None
    return ((curr - prev) / prev) * 100

def _delta_text(delta):
    if delta is None or pd.isna(delta):
        return None
    return f"{delta:+.2f}%"

def build_interpretacion_metricas_individual_table(ultimo: pd.Series) -> pd.DataFrame:
    rows = []

    peso = ultimo.get("peso_bruto_kg")
    talla = ultimo.get("talla_corporal_cm")
    masa_osea = ultimo.get("masa_osea_kg")
    grasa = ultimo.get("ajuste_adiposa_pct")
    musculo = ultimo.get("ajuste_muscular_pct")
    pliegues = ultimo.get("suma_6_pliegues_mm")
    imo = ultimo.get("idx_musculo_oseo")

    # -------------------------
    # DESCRIPTIVAS
    # -------------------------
    rows.append({
        "Métrica": t("Peso"),
        "Valor": f"{peso:.1f} kg" if pd.notna(peso) else "-",
        "Interpretación": "⚪ Descriptivo: Indicador de masa corporal actual."
    })

    rows.append({
        "Métrica": t("Talla"),
        "Valor": f"{talla:.1f} cm" if pd.notna(talla) else "-",
        "Interpretación": "⚪ Descriptivo: Variable estructural de referencia."
    })

    rows.append({
        "Métrica": t("Masa ósea"),
        "Valor": f"{masa_osea:.2f} kg" if pd.notna(masa_osea) else "-",
        "Interpretación": "⚪ Descriptivo: Componente estructural, interpretar en contexto."
    })

    # -------------------------
    # INTERPRETATIVAS
    # -------------------------
    if pd.isna(grasa):
        txt_grasa = "⚪ Sin datos."
    elif grasa < 14:
        txt_grasa = "🟡 Muy bajo (<14%): Vigilar disponibilidad energética y contexto fisiológico."
    elif grasa <= 20:
        txt_grasa = "🟢 Adecuado (14-20%): Rango funcional para fútbol femenino."
    elif grasa <= 24:
        txt_grasa = "🟠 Moderado (20-24%): Con margen de optimización."
    else:
        txt_grasa = "🔴 Elevado (>24%): Por encima del perfil deseado de rendimiento."

    rows.append({
        "Métrica": t("% Grasa"),
        "Valor": f"{grasa:.1f} %" if pd.notna(grasa) else "-",
        "Interpretación": txt_grasa
    })

    if pd.isna(musculo):
        txt_musculo = "⚪ Sin datos."
    elif musculo < 40:
        txt_musculo = "🟠 Bajo (<40%): Nivel de masa muscular mejorable para el alto rendimiento."
    elif musculo <= 45:
        txt_musculo = "🟢 Adecuado (40-45%): Buen nivel de desarrollo muscular para la categoría."
    else:
        txt_musculo = "🟩 Excelente (>45%): Perfil muscular muy favorable para potencia y protección estructural."

    rows.append({
        "Métrica": t("% Muscular"),
        "Valor": f"{musculo:.1f} %" if pd.notna(musculo) else "-",
        "Interpretación": txt_musculo
    })

    if pd.isna(pliegues):
        txt_pliegues = "⚪ Sin datos."
    elif pliegues < 50:
        txt_pliegues = "🟩 Excelente (<50 mm): Perfil de alta competición."
    elif pliegues <= 70:
        txt_pliegues = "🟢 Adecuado (50-70 mm): Rango funcional para la mayoría de posiciones."
    elif pliegues <= 90:
        txt_pliegues = "🟠 Moderado (70-90 mm): Con margen de ajuste nutricional y de carga."
    else:
        txt_pliegues = "🔴 Elevado (>90 mm): Fuera del rango objetivo de rendimiento."

    rows.append({
        "Métrica": t("Suma 6 pliegues"),
        "Valor": f"{pliegues:.1f} mm" if pd.notna(pliegues) else "-",
        "Interpretación": txt_pliegues
    })

    if pd.isna(imo):
        txt_imo = "⚪ Sin datos."
    elif imo < 3.5:
        txt_imo = "🟠 Bajo (<3.5): Relación músculo / óseo por desarrollar."
    elif imo <= 4.2:
        txt_imo = "🟢 Adecuado (3.5-4.2): Relación favorable para el rendimiento."
    else:
        txt_imo = "🟩 Excelente (>4.2): Perfil estructural muy favorable."

    rows.append({
        "Métrica": t("Índice M/O"),
        "Valor": f"{imo:.2f}" if pd.notna(imo) else "-",
        "Interpretación": txt_imo
    })

    return pd.DataFrame(rows)

def clasificar_intensidad_cambio(delta_pct):
    if delta_pct is None or pd.isna(delta_pct):
        return ""

    abs_delta = abs(delta_pct)

    if abs_delta < 2:
        return t("ligero")
    elif abs_delta < 5:
        return t("moderado")
    return t("marcado")


def render_interpretacion_metricas_individual(ultimo: pd.Series) -> None:
    tabla = build_interpretacion_metricas_individual_table(ultimo)

    st.markdown(f"### {t('Interpretación de métricas')}")
    st.dataframe(tabla, hide_index=True, use_container_width=True)


def render_resumen_tecnico_individual(ultimo: pd.Series, anterior: pd.Series | None):
    def color_text(text: str, color: str) -> str:
        return f"<b style='color:{color}'>{text}</b>"

    color_sin_datos = "#757575"
    color_muy_bajo = "#F1C40F"
    color_bajo_moderado = "#F39C12"
    color_adecuado = "#2ECC71"
    color_excelente = "#27AE60"
    color_elevado = "#E74C3C"

    grasa = ultimo.get("ajuste_adiposa_pct")
    musculo = ultimo.get("ajuste_muscular_pct")
    pliegues = ultimo.get("suma_6_pliegues_mm")
    imo = ultimo.get("idx_musculo_oseo")

    if pd.isna(grasa):
        grasa_txt = color_text("sin datos suficientes", color_sin_datos)
    elif grasa < 14:
        grasa_txt = color_text("muy bajo", color_muy_bajo)
    elif grasa <= 20:
        grasa_txt = color_text("adecuado", color_adecuado)
    elif grasa <= 24:
        grasa_txt = color_text("moderado", color_bajo_moderado)
    else:
        grasa_txt = color_text("elevado", color_elevado)

    if pd.isna(musculo):
        musculo_txt = color_text("sin datos suficientes", color_sin_datos)
    elif musculo < 40:
        musculo_txt = color_text("bajo", color_bajo_moderado)
    elif musculo <= 45:
        musculo_txt = color_text("adecuado", color_adecuado)
    else:
        musculo_txt = color_text("excelente", color_excelente)

    if pd.isna(imo):
        imo_txt = color_text("sin datos suficientes", color_sin_datos)
    elif imo < 3.5:
        imo_txt = color_text("bajo", color_bajo_moderado)
    elif imo <= 4.2:
        imo_txt = color_text("adecuado", color_adecuado)
    else:
        imo_txt = color_text("excelente", color_excelente)

    cambios = []

    if anterior is not None:
        grasa_prev = anterior.get("ajuste_adiposa_pct")
        musculo_prev = anterior.get("ajuste_muscular_pct")
        pliegues_prev = anterior.get("suma_6_pliegues_mm")
        imo_prev = anterior.get("idx_musculo_oseo")

        # Grasa
        delta_grasa = _calc_delta_pct(grasa, grasa_prev)
        if delta_grasa is not None:
            intensidad = clasificar_intensidad_cambio(delta_grasa)
            if grasa < grasa_prev:
                cambios.append(f"{intensidad} {t('mejora en grasa corporal')}")
            elif grasa > grasa_prev:
                cambios.append(f"{intensidad} {t('empeoramiento en grasa corporal')}")
            else:
                cambios.append(t("estabilidad en grasa corporal"))

        # Músculo
        delta_musculo = _calc_delta_pct(musculo, musculo_prev)
        if delta_musculo is not None:
            intensidad = clasificar_intensidad_cambio(delta_musculo)
            if musculo > musculo_prev:
                cambios.append(f"{intensidad} {t('mejora muscular')}")
            elif musculo < musculo_prev:
                cambios.append(f"{intensidad} {t('descenso muscular')}")
            else:
                cambios.append(t("estabilidad muscular"))

        # Pliegues
        delta_pliegues = _calc_delta_pct(pliegues, pliegues_prev)
        if delta_pliegues is not None:
            intensidad = clasificar_intensidad_cambio(delta_pliegues)
            if pliegues < pliegues_prev:
                cambios.append(f"{intensidad} {t('reducción de pliegues')}")
            elif pliegues > pliegues_prev:
                cambios.append(f"{intensidad} {t('aumento de pliegues')}")
            else:
                cambios.append(t("estabilidad en pliegues"))

        # IMO
        delta_imo = _calc_delta_pct(imo, imo_prev)
        if delta_imo is not None:
            intensidad = clasificar_intensidad_cambio(delta_imo)
            if imo > imo_prev:
                cambios.append(f"{intensidad} {t('mejora del índice músculo-óseo')}")
            elif imo < imo_prev:
                cambios.append(f"{intensidad} {t('descenso del índice músculo-óseo')}")
            else:
                cambios.append(t("estabilidad del índice músculo-óseo"))

    frase_cambios = ", ".join(cambios[:3]) if cambios else t("sin comparación previa suficiente")

    st.markdown(
        f"""
        :material/description: **{t("Resumen técnico")}:**  
        La jugadora presenta un porcentaje de grasa {grasa_txt}, un porcentaje muscular {musculo_txt} y una relación músculo-ósea {imo_txt}.  
        Respecto a la medición anterior, se observa **{frase_cambios}**.
        """,
        unsafe_allow_html=True
    )

def metricas(df_base: pd.DataFrame, periodo: str = "Última medición") -> None:
    """
    KPI individual antropométrico:
    - valor principal: última medición del dataframe filtrado
    - delta:
        * Última medición -> última vs anterior
        * Historico -> última vs primera del periodo
    - dos filas de 4 tarjetas
    - tabla de interpretación
    - popover de rangos
    - resumen técnico
    """

    if df_base is None or df_base.empty:
        st.info(t("No hay registros antropométricos disponibles."))
        return

    ultimo, anterior = _get_comparison_rows_individual(df_base, periodo)

    if ultimo is None:
        st.info(t("No hay registros antropométricos disponibles."))
        return

    st.divider()
    st.markdown(t("### **Resumen antropométrico**"))
    st.caption(
        t("Valores actuales de la última medición disponible y variación respecto a la anterior.")
        if periodo == "Última medición"
        else t("Valores actuales de la última medición del periodo y variación respecto al inicio del periodo.")
    )

    # Valores actuales
    peso = ultimo.get("peso_bruto_kg")
    grasa = ultimo.get("ajuste_adiposa_pct")
    musculo = ultimo.get("ajuste_muscular_pct")
    pliegues = ultimo.get("suma_6_pliegues_mm")
    imo = ultimo.get("idx_musculo_oseo")
    talla = ultimo.get("talla_corporal_cm")
    masa_osea = ultimo.get("masa_osea_kg")
    n_med = len(df_base)

    # Valores previos
    peso_prev = anterior.get("peso_bruto_kg") if anterior is not None else None
    grasa_prev = anterior.get("ajuste_adiposa_pct") if anterior is not None else None
    musculo_prev = anterior.get("ajuste_muscular_pct") if anterior is not None else None
    pliegues_prev = anterior.get("suma_6_pliegues_mm") if anterior is not None else None
    imo_prev = anterior.get("idx_musculo_oseo") if anterior is not None else None
    talla_prev = anterior.get("talla_corporal_cm") if anterior is not None else None
    masa_osea_prev = anterior.get("masa_osea_kg") if anterior is not None else None

    # -------------------------
    # FILA 1 · KPIs de alerta / interpretativos
    # -------------------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            t("% Grasa"),
            _fmt_val(grasa, 1, " %"),
            _delta_text(_calc_delta_pct(grasa, grasa_prev)),
            delta_color="inverse",
            border=True,
            help=t("Rangos: Muy bajo <14 · Adecuado 14-20 · Moderado 20-24 · Elevado >24")
        )

    with c2:
        st.metric(
            t("% Muscular"),
            _fmt_val(musculo, 1, " %"),
            _delta_text(_calc_delta_pct(musculo, musculo_prev)),
            border=True,
            help=t("Rangos: Bajo <40 · Adecuado 40-45 · Excelente >45")
        )

    with c3:
        st.metric(
            t("Suma 6 pliegues"),
            _fmt_val(pliegues, 1, " mm"),
            _delta_text(_calc_delta_pct(pliegues, pliegues_prev)),
            delta_color="inverse",
            border=True,
            help=t("Rangos: Excelente <50 · Adecuado 50-70 · Moderado 70-90 · Elevado >90")
        )

    with c4:
        st.metric(
            t("Índice M/O"),
            _fmt_val(imo, 2, ""),
            _delta_text(_calc_delta_pct(imo, imo_prev)),
            border=True,
            help=t("Rangos: Bajo <3.5 · Adecuado 3.5-4.2 · Excelente >4.2")
        )

    # -------------------------
    # FILA 2 · KPIs descriptivos
    # -------------------------
    c5, c6, c7, c8 = st.columns(4)

    with c5:
        st.metric(
            t("Peso"),
            _fmt_val(peso, 1, " kg"),
            _delta_text(_calc_delta_pct(peso, peso_prev)),
            delta_color="off",
            border=True,
            help=t("Indicador descriptivo de masa corporal.")
        )

    with c6:
        st.metric(
            t("Talla"),
            _fmt_val(talla, 1, " cm"),
            _delta_text(_calc_delta_pct(talla, talla_prev)),
            delta_color="off",
            border=True,
            help=t("Variable estructural descriptiva.")
        )

    with c7:
        st.metric(
            t("Masa ósea"),
            _fmt_val(masa_osea, 2, " kg"),
            _delta_text(_calc_delta_pct(masa_osea, masa_osea_prev)),
            delta_color="off",
            border=True,
            help=t("Componente estructural, sin lectura semafórica aislada.")
        )

    with c8:
        st.metric(
            t("Nº mediciones"),
            f"{n_med}",
            None,
            delta_color="off",
            border=True,
            help=t("Número total de controles antropométricos disponibles para la jugadora.")
        )

    render_interpretacion_metricas_individual(ultimo)
    render_popovers_rangos_antropometria()
    render_resumen_tecnico_individual(ultimo, anterior)


def _prepare_antropometria_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalizar fecha → SOLO fecha
    df["fecha"] = (
        pd.to_datetime(df["fecha_medicion"])
        .dt.normalize()
    )

    # 🔧 FORZAR NUMÉRICOS (CLAVE)
    cols_numericas = [
        "peso_bruto_kg",
        "ajuste_adiposa_pct",
        "ajuste_muscular_pct",
        "masa_osea_kg",
        "idx_musculo_oseo",
    ]

    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Orden correcto
    df = df.sort_values("fecha")

    # Eliminar filas realmente vacías
    df = df[
        df[["peso_bruto_kg", "ajuste_adiposa_pct"]]
        .notna()
        .any(axis=1)
    ]

    return df


def grafico_peso_grasa(
    df: pd.DataFrame,
    media_equipo_grasa: float | None = None,
    referencia_posicion_grasa: tuple[float, float] | None = None
):
    df = _prepare_antropometria_df(df)

    if df.empty:
        st.info(t("No hay datos suficientes para graficar."))
        return

    st.caption(
        t(
            "Evolución histórica del peso corporal y del porcentaje de grasa. "
            "Permite contextualizar si los cambios de peso se acompañan de una mejora o empeoramiento de la composición corporal."
        )
    )

    # -------------------------
    # Preparación de datos
    # -------------------------
    df = df.sort_values("fecha")
    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    fig = go.Figure()

    # -------------------------
    # RANGO DINÁMICO PESO
    # -------------------------
    peso_min = df["peso_bruto_kg"].min()
    peso_max = df["peso_bruto_kg"].max()

    rango = peso_max - peso_min
    margen = max(0.5, rango * 0.8)

    # -------------------------
    # PESO → BARRAS
    # -------------------------
    fig.add_trace(go.Bar(
        x=df["fecha_label"],
        y=df["peso_bruto_kg"],
        name=t("Peso (kg)"),
        marker_color="#1F4ED8",
        opacity=0.85,
        width=0.6,
        text=df["peso_bruto_kg"].round(1).astype(str) + " kg",
        textposition="outside",
        hovertemplate=(
            "<b>" + t("Peso") + "</b><br>"
            + "%{x}<br>"
            + "%{y:.1f} kg"
            + "<extra></extra>"
        )
    ))

    # -------------------------
    # % GRASA → LÍNEA + PUNTOS
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df["fecha_label"],
        y=df["ajuste_adiposa_pct"],
        name=t("% Grasa"),
        yaxis="y2",
        mode="lines+markers",
        line=dict(width=3, color="#EF553B",),
        marker=dict(size=10),
        hovertemplate=(
            "<b>" + t("% Grasa") + "</b><br>"
            + "%{x}<br>"
            + "%{y:.1f} %"
            + "<extra></extra>"
        )
    ))

    # -------------------------
    # MEDIA EQUIPO (% grasa)
    # -------------------------
    if media_equipo_grasa is not None:
        fig.add_hline(
            y=media_equipo_grasa,
            yref="y2",
            line_dash="dot",
            line_color="gray",
            annotation_text=t("Media equipo"),
            annotation_position="top right"
        )

    # -------------------------
    # REFERENCIA POSICIÓN (% grasa)
    # -------------------------
    if referencia_posicion_grasa:
        min_ref, max_ref = referencia_posicion_grasa
        fig.add_hrect(
            y0=min_ref,
            y1=max_ref,
            yref="y2",
            fillcolor="green",
            opacity=0.08,
            line_width=0
        )

    # -------------------------
    # LAYOUT FINAL
    # -------------------------
    fig.update_layout(
        template="plotly_white",
        barmode="group",
        bargap=0.25,
        xaxis=dict(
            type="category",
            title=""
        ),
        yaxis=dict(
            title=t("Peso (kg)"),
            range=[peso_min - margen, peso_max + margen],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)"
        ),
        yaxis2=dict(
            title=t("% Grasa"),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            y=-0.20,
            x=0.5,
            xanchor="center"
        ),
        showlegend=True,
        height=520,
        margin=dict(t=40, b=90)
    )

    st.plotly_chart(fig, use_container_width=True)

    _alerta_tendencia_grasa(df)


def _alerta_tendencia_grasa(df: pd.DataFrame):
    if df is None or df.empty or len(df) < 2:
        return

    df = df.sort_values("fecha").copy()

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2] if len(df) >= 2 else None
    primero = df.iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{t('Comparación última vs anterior')}**")

        if anterior is None:
            st.caption(t("No hay suficientes mediciones para comparar."))
        else:
            delta_grasa = pd.to_numeric(ultimo["ajuste_adiposa_pct"], errors="coerce") - pd.to_numeric(anterior["ajuste_adiposa_pct"], errors="coerce")
            delta_peso = pd.to_numeric(ultimo["peso_bruto_kg"], errors="coerce") - pd.to_numeric(anterior["peso_bruto_kg"], errors="coerce")

            if pd.notna(delta_grasa):
                if abs(delta_grasa) < 1:
                    st.markdown(f"- {t('Estabilidad del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                elif delta_grasa > 0:
                    txt = t("Ligero aumento") if abs(delta_grasa) < 2 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                else:
                    txt = t("Ligera reducción") if abs(delta_grasa) < 2 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")

            if pd.notna(delta_peso):
                if abs(delta_peso) < 0.8:
                    st.markdown(f"- {t('Estabilidad del peso corporal')} ({delta_peso:+.1f} kg)")
                elif delta_peso > 0:
                    txt = t("Ligero aumento") if abs(delta_peso) < 1.5 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del peso corporal')} ({delta_peso:+.1f} kg)")
                else:
                    txt = t("Ligera reducción") if abs(delta_peso) < 1.5 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del peso corporal')} ({delta_peso:+.1f} kg)")

    with col2:
        st.markdown(f"**{t('Comparación primera vs última')}**")

        if len(df) < 2:
            st.caption(t("No hay suficientes mediciones para analizar la evolución global."))
        else:
            delta_grasa = pd.to_numeric(ultimo["ajuste_adiposa_pct"], errors="coerce") - pd.to_numeric(primero["ajuste_adiposa_pct"], errors="coerce")
            delta_peso = pd.to_numeric(ultimo["peso_bruto_kg"], errors="coerce") - pd.to_numeric(primero["peso_bruto_kg"], errors="coerce")

            if pd.notna(delta_grasa):
                if abs(delta_grasa) < 1:
                    st.markdown(f"- {t('Estabilidad del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                elif delta_grasa > 0:
                    txt = t("Ligero aumento") if abs(delta_grasa) < 2 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                else:
                    txt = t("Ligera reducción") if abs(delta_grasa) < 2 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")

            if pd.notna(delta_peso):
                if abs(delta_peso) < 0.8:
                    st.markdown(f"- {t('Estabilidad del peso corporal')} ({delta_peso:+.1f} kg)")
                elif delta_peso > 0:
                    txt = t("Ligero aumento") if abs(delta_peso) < 1.5 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del peso corporal')} ({delta_peso:+.1f} kg)")
                else:
                    txt = t("Ligera reducción") if abs(delta_peso) < 1.5 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del peso corporal')} ({delta_peso:+.1f} kg)")



# def grafico_composicion(df):
#     df = _prepare_antropometria_df(df)

#     if df.empty:
#         st.info(t("No hay datos suficientes."))
#         return

#     df = df.sort_values("fecha").reset_index(drop=True).copy()

#     # X indexada
#     df["x_idx"] = df.index
#     df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

#     fig = go.Figure()

#     fig.add_trace(go.Scatter(
#         x=df["x_idx"],
#         y=df["ajuste_adiposa_pct"],
#         name=t("% Grasa"),
#         mode="lines+markers"
#     ))

#     fig.add_trace(go.Scatter(
#         x=df["x_idx"],
#         y=df["ajuste_muscular_pct"],
#         name=t("% Muscular"),
#         mode="lines+markers"
#     ))

#     # -------------------------
#     # EJE X CONTROLADO
#     # -------------------------
#     fig.update_xaxes(
#         tickmode="array",
#         tickvals=df["x_idx"],
#         ticktext=df["fecha_label"],
#         title=t("Fecha de medición"),
#         range=[-0.5, len(df) - 0.5],
#     )

#     fig.update_layout(
#         template="plotly_white",
#         yaxis_title=t("Porcentaje (%)"),
#         legend=dict(orientation="h", y=-0.3),
#         showlegend=True
#     )

#     st.plotly_chart(fig)

def grafico_composicion(df: pd.DataFrame):
    df = _prepare_antropometria_df(df)

    if df.empty:
        st.info(t("No hay datos suficientes para graficar."))
        return

    st.caption(
        t(
            "Evolución histórica del porcentaje graso y muscular. "
            "Permite identificar cambios en la composición corporal a lo largo del tiempo."
        )
    )

    # -------------------------
    # Preparación de datos
    # -------------------------
    df = df.sort_values("fecha").copy()
    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    fig = go.Figure()

    # -------------------------
    # % GRASA → LÍNEA
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df["fecha_label"],
        y=df["ajuste_adiposa_pct"],
        name=t("% Grasa"),
        mode="lines+markers+text",
        line=dict(width=3, color="#EF553B"),
        marker=dict(size=8),
        text=df["ajuste_adiposa_pct"].map(lambda x: f"{x:.1f}"),
        textposition="top center",
        hovertemplate=(
            "<b>" + t("% Grasa") + "</b><br>"
            + "%{x}<br>"
            + "%{y:.1f} %"
            + "<extra></extra>"
        )
    ))

    # -------------------------
    # % MUSCULAR → LÍNEA
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df["fecha_label"],
        y=df["ajuste_muscular_pct"],
        name=t("% Muscular"),
        mode="lines+markers+text",
        line=dict(width=3, color="#636EFA"),
        marker=dict(size=8),
        text=df["ajuste_muscular_pct"].map(lambda x: f"{x:.1f}"),
        textposition="top center",
        hovertemplate=(
            "<b>" + t("% Muscular") + "</b><br>"
            + "%{x}<br>"
            + "%{y:.1f} %"
            + "<extra></extra>"
        )
    ))

    # -------------------------
    # LAYOUT
    # -------------------------
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            type="category",
            title=t("Fecha de medición")
        ),
        yaxis=dict(
            title=t("Porcentaje (%)"),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)"
        ),
        legend=dict(
            orientation="h",
            y=-0.20,
            x=0.5,
            xanchor="center"
        ),
        showlegend=True,
        height=520,
        margin=dict(t=40, b=90)
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # INTERPRETACIÓN
    # -------------------------
    if len(df) < 2:
        return

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2] if len(df) >= 2 else None
    primero = df.iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{t('Comparación última vs anterior')}**")

        if anterior is None:
            st.caption(t("No hay suficientes mediciones para comparar."))
        else:
            delta_grasa = pd.to_numeric(ultimo["ajuste_adiposa_pct"], errors="coerce") - pd.to_numeric(anterior["ajuste_adiposa_pct"], errors="coerce")
            delta_musculo = pd.to_numeric(ultimo["ajuste_muscular_pct"], errors="coerce") - pd.to_numeric(anterior["ajuste_muscular_pct"], errors="coerce")

            if pd.notna(delta_grasa):
                if abs(delta_grasa) < 1:
                    st.markdown(f"- {t('Estabilidad del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                elif delta_grasa > 0:
                    txt = t("Ligero aumento") if abs(delta_grasa) < 2 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                else:
                    txt = t("Ligera reducción") if abs(delta_grasa) < 2 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")

            if pd.notna(delta_musculo):
                if abs(delta_musculo) < 1:
                    st.markdown(f"- {t('Estabilidad del porcentaje muscular')} ({delta_musculo:+.1f} pp)")
                elif delta_musculo > 0:
                    txt = t("Ligero aumento") if abs(delta_musculo) < 2 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del porcentaje muscular')} ({delta_musculo:+.1f} pp)")
                else:
                    txt = t("Ligera reducción") if abs(delta_musculo) < 2 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del porcentaje muscular')} ({delta_musculo:+.1f} pp)")

    with col2:
        st.markdown(f"**{t('Comparación primera vs última')}**")

        if len(df) < 2:
            st.caption(t("No hay suficientes mediciones para analizar la evolución global."))
        else:
            delta_grasa = pd.to_numeric(ultimo["ajuste_adiposa_pct"], errors="coerce") - pd.to_numeric(primero["ajuste_adiposa_pct"], errors="coerce")
            delta_musculo = pd.to_numeric(ultimo["ajuste_muscular_pct"], errors="coerce") - pd.to_numeric(primero["ajuste_muscular_pct"], errors="coerce")

            if pd.notna(delta_grasa):
                if abs(delta_grasa) < 1:
                    st.markdown(f"- {t('Estabilidad del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                elif delta_grasa > 0:
                    txt = t("Ligero aumento") if abs(delta_grasa) < 2 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")
                else:
                    txt = t("Ligera reducción") if abs(delta_grasa) < 2 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del porcentaje graso')} ({delta_grasa:+.1f} pp)")

            if pd.notna(delta_musculo):
                if abs(delta_musculo) < 1:
                    st.markdown(f"- {t('Estabilidad del porcentaje muscular')} ({delta_musculo:+.1f} pp)")
                elif delta_musculo > 0:
                    txt = t("Ligero aumento") if abs(delta_musculo) < 2 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del porcentaje muscular')} ({delta_musculo:+.1f} pp)")
                else:
                    txt = t("Ligera reducción") if abs(delta_musculo) < 2 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del porcentaje muscular')} ({delta_musculo:+.1f} pp)")

def grafico_indice_musculo_oseo(df: pd.DataFrame):
    df = _prepare_antropometria_df(df)

    if df.empty or "idx_musculo_oseo" not in df.columns:
        st.info(t("No hay datos suficientes para graficar el índice músculo-óseo."))
        return

    st.caption(
        t(
            "Evolución histórica del índice músculo-óseo. "
            "Permite seguir la relación entre desarrollo muscular y componente óseo a lo largo del tiempo."
        )
    )

    # -------------------------
    # Preparación de datos
    # -------------------------
    df = df.sort_values("fecha").copy()
    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    fig = go.Figure()

    # -------------------------
    # LÍNEA IMO
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df["fecha_label"],
        y=df["idx_musculo_oseo"],
        name=t("Índice músculo-óseo"),
        mode="lines+markers+text",
        line=dict(width=4, color="#636EFA"),
        marker=dict(size=9),
        text=df["idx_musculo_oseo"].map(lambda x: f"{x:.2f}"),
        textposition="top center",
        hovertemplate=(
            "<b>" + t("Índice músculo-óseo") + "</b><br>"
            + "%{x}<br>"
            + "%{y:.2f}"
            + "<extra></extra>"
        )
    ))

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            type="category",
            title=t("Fecha de medición")
        ),
        yaxis=dict(
            title=t("Índice músculo-óseo"),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)"
        ),
        showlegend=False,
        height=520,
        margin=dict(t=40, b=90)
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # INTERPRETACIÓN
    # -------------------------
    if len(df) < 2:
        return

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2] if len(df) >= 2 else None
    primero = df.iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{t('Comparación última vs anterior')}**")

        if anterior is None:
            st.caption(t("No hay suficientes mediciones para comparar."))
        else:
            delta_imo = pd.to_numeric(ultimo["idx_musculo_oseo"], errors="coerce") - pd.to_numeric(anterior["idx_musculo_oseo"], errors="coerce")

            if pd.notna(delta_imo):
                if abs(delta_imo) < 0.05:
                    st.markdown(f"- {t('Estabilidad del índice músculo-óseo')} ({delta_imo:+.2f})")
                elif delta_imo > 0:
                    txt = t("Ligero aumento") if abs(delta_imo) < 0.15 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del índice músculo-óseo')} ({delta_imo:+.2f})")
                else:
                    txt = t("Ligera reducción") if abs(delta_imo) < 0.15 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del índice músculo-óseo')} ({delta_imo:+.2f})")

    with col2:
        st.markdown(f"**{t('Comparación primera vs última')}**")

        if len(df) < 2:
            st.caption(t("No hay suficientes mediciones para analizar la evolución global."))
        else:
            delta_imo = pd.to_numeric(ultimo["idx_musculo_oseo"], errors="coerce") - pd.to_numeric(primero["idx_musculo_oseo"], errors="coerce")

            if pd.notna(delta_imo):
                if abs(delta_imo) < 0.05:
                    st.markdown(f"- {t('Estabilidad del índice músculo-óseo')} ({delta_imo:+.2f})")
                elif delta_imo > 0:
                    txt = t("Ligero aumento") if abs(delta_imo) < 0.15 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del índice músculo-óseo')} ({delta_imo:+.2f})")
                else:
                    txt = t("Ligera reducción") if abs(delta_imo) < 0.15 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del índice músculo-óseo')} ({delta_imo:+.2f})")

def grafico_suma_pliegues(df: pd.DataFrame):
    df = _prepare_antropometria_df(df)

    if df.empty or "suma_6_pliegues_mm" not in df.columns:
        st.info(t("No hay datos suficientes para graficar la suma de 6 pliegues."))
        return

    st.caption(
        t(
            "Evolución histórica de la suma de 6 pliegues. "
            "Permite seguir la adiposidad subcutánea total a lo largo del tiempo."
        )
    )

    # -------------------------
    # Preparación de datos
    # -------------------------
    df = df.sort_values("fecha").copy()
    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    fig = go.Figure()

    # -------------------------
    # LÍNEA SUMA 6 PLIEGUES
    # -------------------------
    fig.add_trace(go.Scatter(
        x=df["fecha_label"],
        y=df["suma_6_pliegues_mm"],
        name=t("Suma 6 pliegues"),
        mode="lines+markers+text",
        line=dict(width=4, color="#636EFA"),
        marker=dict(size=9),
        text=df["suma_6_pliegues_mm"].map(lambda x: f"{x:.1f}"),
        textposition="top center",
        hovertemplate=(
            "<b>" + t("Suma 6 pliegues") + "</b><br>"
            + "%{x}<br>"
            + "%{y:.1f} mm"
            + "<extra></extra>"
        )
    ))

    # -------------------------
    # LÍMITES DE REFERENCIA
    # -------------------------
    fig.add_hline(
        y=50,
        line_dash="dot",
        line_color="#27AE60",
        annotation_text=t("Excelente"),
        annotation_position="top left"
    )

    fig.add_hline(
        y=70,
        line_dash="dot",
        line_color="#2ECC71",
        annotation_text=t("Adecuado"),
        annotation_position="top left"
    )

    fig.add_hline(
        y=90,
        line_dash="dot",
        line_color="#F39C12",
        annotation_text=t("Moderado"),
        annotation_position="top left"
    )

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            type="category",
            title=t("Fecha de medición")
        ),
        yaxis=dict(
            title=t("Suma 6 pliegues (mm)"),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)"
        ),
        showlegend=False,
        height=520,
        margin=dict(t=40, b=90)
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # INTERPRETACIÓN
    # -------------------------
    if len(df) < 2:
        return

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2] if len(df) >= 2 else None
    primero = df.iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{t('Comparación última vs anterior')}**")

        if anterior is None:
            st.caption(t("No hay suficientes mediciones para comparar."))
        else:
            delta = pd.to_numeric(ultimo["suma_6_pliegues_mm"], errors="coerce") - pd.to_numeric(anterior["suma_6_pliegues_mm"], errors="coerce")

            if pd.notna(delta):
                if abs(delta) < 3:
                    st.markdown(f"- {t('Estabilidad de la suma de pliegues')} ({delta:+.1f} mm)")
                elif delta > 0:
                    txt = t("Ligero aumento") if abs(delta) < 8 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('de la suma de pliegues')} ({delta:+.1f} mm)")
                else:
                    txt = t("Ligera reducción") if abs(delta) < 8 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('de la suma de pliegues')} ({delta:+.1f} mm)")

    with col2:
        st.markdown(f"**{t('Comparación primera vs última')}**")

        if len(df) < 2:
            st.caption(t("No hay suficientes mediciones para analizar la evolución global."))
        else:
            delta = pd.to_numeric(ultimo["suma_6_pliegues_mm"], errors="coerce") - pd.to_numeric(primero["suma_6_pliegues_mm"], errors="coerce")

            if pd.notna(delta):
                if abs(delta) < 3:
                    st.markdown(f"- {t('Estabilidad de la suma de pliegues')} ({delta:+.1f} mm)")
                elif delta > 0:
                    txt = t("Ligero aumento") if abs(delta) < 8 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('de la suma de pliegues')} ({delta:+.1f} mm)")
                else:
                    txt = t("Ligera reducción") if abs(delta) < 8 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('de la suma de pliegues')} ({delta:+.1f} mm)")


def grafico_pliegue_individual(df: pd.DataFrame):
    df = _prepare_antropometria_df(df)

    metricas_pliegues = {
        "pliegue_triceps": t("Tríceps"),
        "pliegue_subescapular": t("Subescapular"),
        "pliegue_biceps": t("Bíceps"),
        "pliegue_cresta_iliaca": t("Cresta ilíaca"),
        "pliegue_supraespinal": t("Supraespinal"),
        "pliegue_abdominal": t("Abdominal"),
        "pliegue_muslo_frontal": t("Muslo frontal"),
        "pliegue_pantorrilla_maxima": t("Pantorrilla máxima"),
        "pliegue_antebrazo": t("Antebrazo"),
    }

    metricas_pliegues = {
        k: v for k, v in metricas_pliegues.items()
        if k in df.columns and df[k].dropna().any()
    }

    if df.empty or not metricas_pliegues:
        st.info(t("No hay datos suficientes para graficar pliegues individuales."))
        return

    st.caption(
        t(
            "Detalle histórico de uno o varios pliegues seleccionados. "
            "Permite analizar la evolución específica por zona anatómica."
        )
    )

    pliegues_sel = st.multiselect(
        t("Seleccione uno o varios pliegues"),
        options=list(metricas_pliegues.keys()),
        default=[list(metricas_pliegues.keys())[0]],
        format_func=lambda x: metricas_pliegues[x],
        key="pliegue_individual_selector"
    )

    if not pliegues_sel:
        st.info(t("Selecciona al menos un pliegue."))
        return

    df = df.sort_values("fecha").copy()
    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    fig = go.Figure()

    for col in pliegues_sel:
        df_plot = df.dropna(subset=[col]).copy()

        if df_plot.empty:
            continue

        fig.add_trace(go.Scatter(
            x=df_plot["fecha_label"],
            y=df_plot[col],
            name=metricas_pliegues[col],
            mode="lines+markers+text",
            line=dict(width=3),
            marker=dict(size=8),
            text=df_plot[col].map(lambda x: f"{x:.1f}"),
            textposition="top center",
            hovertemplate=(
                "<b>" + metricas_pliegues[col] + "</b><br>"
                + "%{x}<br>"
                + "%{y:.1f} mm"
                + "<extra></extra>"
            )
        ))

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            type="category",
            title=t("Fecha de medición")
        ),
        yaxis=dict(
            title=t("Pliegue (mm)"),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)"
        ),
        legend=dict(
            orientation="h",
            y=-0.20,
            x=0.5,
            xanchor="center"
        ),
        showlegend=True,
        height=520,
        margin=dict(t=40, b=90)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretación solo si hay un pliegue seleccionado
    if len(pliegues_sel) != 1:
        return

    pliegue_sel = pliegues_sel[0]
    df_interp = df.dropna(subset=[pliegue_sel]).copy()

    if len(df_interp) < 2:
        return

    ultimo = df_interp.iloc[-1]
    anterior = df_interp.iloc[-2] if len(df_interp) >= 2 else None
    primero = df_interp.iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{t('Comparación última vs anterior')}**")

        if anterior is None:
            st.caption(t("No hay suficientes mediciones para comparar."))
        else:
            delta = pd.to_numeric(ultimo[pliegue_sel], errors="coerce") - pd.to_numeric(anterior[pliegue_sel], errors="coerce")

            if pd.notna(delta):
                if abs(delta) < 1:
                    st.markdown(f"- {t('Estabilidad del pliegue')} ({delta:+.1f} mm)")
                elif delta > 0:
                    txt = t("Ligero aumento") if abs(delta) < 3 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del pliegue')} ({delta:+.1f} mm)")
                else:
                    txt = t("Ligera reducción") if abs(delta) < 3 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del pliegue')} ({delta:+.1f} mm)")

    with col2:
        st.markdown(f"**{t('Comparación primera vs última')}**")

        delta = pd.to_numeric(ultimo[pliegue_sel], errors="coerce") - pd.to_numeric(primero[pliegue_sel], errors="coerce")

        if pd.notna(delta):
            if abs(delta) < 1:
                st.markdown(f"- {t('Estabilidad del pliegue')} ({delta:+.1f} mm)")
            elif delta > 0:
                txt = t("Ligero aumento") if abs(delta) < 3 else t("Aumento marcado")
                st.markdown(f"- {txt} {t('del pliegue')} ({delta:+.1f} mm)")
            else:
                txt = t("Ligera reducción") if abs(delta) < 3 else t("Reducción marcada")
                st.markdown(f"- {txt} {t('del pliegue')} ({delta:+.1f} mm)")


def resumen_ratios_estructurales(df: pd.DataFrame):
    df = _prepare_antropometria_df(df)

    if df.empty:
        return

    df = df.sort_values("fecha").copy()

    # Ratios
    if {"perimetro_cintura_minima", "perimetro_cadera_maximo"}.issubset(df.columns):
        df["ratio_cintura_cadera"] = (
            pd.to_numeric(df["perimetro_cintura_minima"], errors="coerce") /
            pd.to_numeric(df["perimetro_cadera_maximo"], errors="coerce")
        )

    if {"perimetro_muslo_maximo", "perimetro_pantorrilla_maxima"}.issubset(df.columns):
        df["ratio_muslo_pantorrilla"] = (
            pd.to_numeric(df["perimetro_muslo_maximo"], errors="coerce") /
            pd.to_numeric(df["perimetro_pantorrilla_maxima"], errors="coerce")
        )

    if {"envergadura_cm", "talla_corporal_cm"}.issubset(df.columns):
        df["ratio_envergadura_talla"] = (
            pd.to_numeric(df["envergadura_cm"], errors="coerce") /
            pd.to_numeric(df["talla_corporal_cm"], errors="coerce")
        )

    if {"talla_sentado_cm", "talla_corporal_cm"}.issubset(df.columns):
        df["ratio_tronco_altura"] = (
            pd.to_numeric(df["talla_sentado_cm"], errors="coerce") /
            pd.to_numeric(df["talla_corporal_cm"], errors="coerce")
        )

    if len(df) == 0:
        return

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2] if len(df) >= 2 else None

    def delta_text(curr, prev):
        if anterior is None or pd.isna(curr) or pd.isna(prev):
            return None
        return f"{(curr - prev):+.3f}"

    st.caption(
        t("Ratios estructurales actuales y variación respecto a la medición anterior.")
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        curr = pd.to_numeric(ultimo.get("ratio_cintura_cadera"), errors="coerce")
        prev = pd.to_numeric(anterior.get("ratio_cintura_cadera"), errors="coerce") if anterior is not None else None
        st.metric(
            t("Cintura / cadera"),
            f"{curr:.3f}" if pd.notna(curr) else "—",
            delta_text(curr, prev),
            delta_color="off",
            border=True,
            help=t("Relación entre cintura mínima y cadera máxima.")
        )

    with c2:
        curr = pd.to_numeric(ultimo.get("ratio_muslo_pantorrilla"), errors="coerce")
        prev = pd.to_numeric(anterior.get("ratio_muslo_pantorrilla"), errors="coerce") if anterior is not None else None
        st.metric(
            t("Muslo / pantorrilla"),
            f"{curr:.3f}" if pd.notna(curr) else "—",
            delta_text(curr, prev),
            delta_color="off",
            border=True,
            help=t("Relación entre perímetro de muslo máximo y pantorrilla máxima.")
        )

    with c3:
        curr = pd.to_numeric(ultimo.get("ratio_envergadura_talla"), errors="coerce")
        prev = pd.to_numeric(anterior.get("ratio_envergadura_talla"), errors="coerce") if anterior is not None else None
        st.metric(
            t("Envergadura / talla"),
            f"{curr:.3f}" if pd.notna(curr) else "—",
            delta_text(curr, prev),
            delta_color="off",
            border=True,
            help=t("Relación entre envergadura y talla corporal.")
        )

    with c4:
        curr = pd.to_numeric(ultimo.get("ratio_tronco_altura"), errors="coerce")
        prev = pd.to_numeric(anterior.get("ratio_tronco_altura"), errors="coerce") if anterior is not None else None
        st.metric(
            t("Tronco / altura"),
            f"{curr:.3f}" if pd.notna(curr) else "—",
            delta_text(curr, prev),
            delta_color="off",
            border=True,
            help=t("Relación entre talla sentado y talla corporal.")
        )


def grafico_perfil_estructural(df: pd.DataFrame):
    df = _prepare_antropometria_df(df)

    if df.empty:
        st.info(t("No hay datos suficientes para graficar el perfil estructural."))
        return

    # -------------------------
    # Cálculo de ratios
    # -------------------------
    if {"perimetro_cintura_minima", "perimetro_cadera_maximo"}.issubset(df.columns):
        df["ratio_cintura_cadera"] = (
            pd.to_numeric(df["perimetro_cintura_minima"], errors="coerce") /
            pd.to_numeric(df["perimetro_cadera_maximo"], errors="coerce")
        )

    if {"perimetro_muslo_maximo", "perimetro_pantorrilla_maxima"}.issubset(df.columns):
        df["ratio_muslo_pantorrilla"] = (
            pd.to_numeric(df["perimetro_muslo_maximo"], errors="coerce") /
            pd.to_numeric(df["perimetro_pantorrilla_maxima"], errors="coerce")
        )

    if {"envergadura_cm", "talla_corporal_cm"}.issubset(df.columns):
        df["ratio_envergadura_talla"] = (
            pd.to_numeric(df["envergadura_cm"], errors="coerce") /
            pd.to_numeric(df["talla_corporal_cm"], errors="coerce")
        )

    if {"talla_sentado_cm", "talla_corporal_cm"}.issubset(df.columns):
        df["ratio_tronco_altura"] = (
            pd.to_numeric(df["talla_sentado_cm"], errors="coerce") /
            pd.to_numeric(df["talla_corporal_cm"], errors="coerce")
        )

    ratios = {
        "ratio_cintura_cadera": t("Ratio cintura / cadera"),
        "ratio_muslo_pantorrilla": t("Ratio muslo / pantorrilla"),
        "ratio_envergadura_talla": t("Ratio envergadura / talla"),
        "ratio_tronco_altura": t("Ratio tronco / altura"),
    }

    ratios = {
        k: v for k, v in ratios.items()
        if k in df.columns and df[k].dropna().any()
    }

    if not ratios:
        st.info(t("No hay ratios estructurales válidos para mostrar."))
        return

    st.caption(
        t(
            "Evolución histórica de un ratio estructural seleccionado. "
            "Permite seguir cambios en proporciones corporales relevantes para el perfil físico."
        )
    )

    ratio_sel = st.selectbox(
        t("Seleccione el ratio"),
        options=list(ratios.keys()),
        format_func=lambda x: ratios[x],
        key="ratio_estructural_individual_selector"
    )

    df = df.sort_values("fecha").copy()
    df = df.dropna(subset=[ratio_sel])

    if df.empty:
        st.info(t("No hay datos válidos para el ratio seleccionado."))
        return

    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["fecha_label"],
        y=df[ratio_sel],
        name=ratios[ratio_sel],
        mode="lines+markers+text",
        line=dict(width=4, color="#636EFA"),
        marker=dict(size=9),
        text=df[ratio_sel].map(lambda x: f"{x:.3f}"),
        textposition="top center",
        hovertemplate=(
            "<b>" + ratios[ratio_sel] + "</b><br>"
            + "%{x}<br>"
            + "%{y:.3f}"
            + "<extra></extra>"
        )
    ))

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            type="category",
            title=t("Fecha de medición")
        ),
        yaxis=dict(
            title=ratios[ratio_sel],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)"
        ),
        showlegend=False,
        height=520,
        margin=dict(t=40, b=90)
    )

    st.plotly_chart(fig, use_container_width=True)

    if len(df) < 2:
        return

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2] if len(df) >= 2 else None
    primero = df.iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{t('Comparación última vs anterior')}**")

        if anterior is None:
            st.caption(t("No hay suficientes mediciones para comparar."))
        else:
            delta = pd.to_numeric(ultimo[ratio_sel], errors="coerce") - pd.to_numeric(anterior[ratio_sel], errors="coerce")

            if pd.notna(delta):
                if abs(delta) < 0.01:
                    st.markdown(f"- {t('Estabilidad del ratio')} ({delta:+.3f})")
                elif delta > 0:
                    txt = t("Ligero aumento") if abs(delta) < 0.03 else t("Aumento marcado")
                    st.markdown(f"- {txt} {t('del ratio')} ({delta:+.3f})")
                else:
                    txt = t("Ligera reducción") if abs(delta) < 0.03 else t("Reducción marcada")
                    st.markdown(f"- {txt} {t('del ratio')} ({delta:+.3f})")

    with col2:
        st.markdown(f"**{t('Comparación primera vs última')}**")

        delta = pd.to_numeric(ultimo[ratio_sel], errors="coerce") - pd.to_numeric(primero[ratio_sel], errors="coerce")

        if pd.notna(delta):
            if abs(delta) < 0.01:
                st.markdown(f"- {t('Estabilidad del ratio')} ({delta:+.3f})")
            elif delta > 0:
                txt = t("Ligero aumento") if abs(delta) < 0.03 else t("Aumento marcado")
                st.markdown(f"- {txt} {t('del ratio')} ({delta:+.3f})")
            else:
                txt = t("Ligera reducción") if abs(delta) < 0.03 else t("Reducción marcada")
                st.markdown(f"- {txt} {t('del ratio')} ({delta:+.3f})")