import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.i18n.i18n import t


def _fmt(valor, sufijo=""):
    if pd.isna(valor):
        return "-"
    return f"{valor:.2f} {sufijo}".strip()

def metricas(df: pd.DataFrame) -> None:

    # -----------------------------
    # Validaciones básicas
    # -----------------------------
    if df is None or df.empty:
        st.info(t("No hay registros antropométricos disponibles."))
        return

    if df.empty:
        st.info(t("No hay registros en el periodo seleccionado."))
        return

    df = df.sort_values("fecha_medicion")

    ultimo = df.iloc[-1]

    # -----------------------------
    # Resumen principal
    # -----------------------------
    st.divider()
    st.markdown(t("### **Resumen antropométrico**"))

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    with k1:
        st.metric(t("Peso (kg)"), _fmt(ultimo.get("peso_bruto_kg"), "kg"))
    with k2:
        st.metric(t("Talla (cm)"), _fmt(ultimo.get("talla_corporal_cm"), "cm"))
    with k3:
        st.metric(t("% Grasa"), _fmt(ultimo.get("ajuste_adiposa_pct"), "%"))
    with k4:
        st.metric(t("% Muscular"), _fmt(ultimo.get("ajuste_muscular_pct"), "%"))
    with k5:
        st.metric(t("Masa ósea (kg)"), _fmt(ultimo.get("masa_osea_kg"), "kg"))
    with k6:
        st.metric(t("Índice M/O"), _fmt(ultimo.get("idx_musculo_oseo"), ""))

    # -----------------------------
    # Resumen técnico interpretado
    # -----------------------------
    resumen = _get_resumen_tecnico_antropometria(df)
    st.markdown(resumen, unsafe_allow_html=True)

def _get_resumen_tecnico_antropometria(df: pd.DataFrame) -> str:
    last = df.iloc[-1]

    grasa = last.get("ajuste_adiposa_pct")
    imo = last.get("idx_musculo_oseo")

    def c(txt, col):
        return f"<b style='color:{col}'>{txt}</b>"

    # % grasa – fútbol femenino adulto
    if grasa is None:
        estado_grasa = c(t("no evaluable"), "#757575")
    elif grasa < 16:
        estado_grasa = c(t("baja"), "#FB8C00")
    elif 16 <= grasa <= 22:
        estado_grasa = c(t("óptima"), "#43A047")
    elif grasa <= 25:
        estado_grasa = c(t("moderadamente elevada"), "#FB8C00")
    else:
        estado_grasa = c(t("elevada"), "#E53935")

    # Índice músculo–óseo
    if imo is None:
        estado_imo = c(t("no disponible"), "#757575")
    elif imo >= 3.2:
        estado_imo = c(t("excelente"), "#43A047")
    elif imo >= 2.8:
        estado_imo = c(t("adecuado"), "#FB8C00")
    else:
        estado_imo = c(t("mejorable"), "#E53935")

    return (
        f"{t(':material/description: **Resumen técnico:**')}"
        f"<div style='text-align: justify;'>"
        f"{t('La composición corporal actual presenta un nivel de grasa corporal')} "
        f"{estado_grasa}, {t('con una relación músculo–ósea')} {estado_imo}. "
        f"{t('La interpretación debe contextualizarse con la posición, fase competitiva y carga acumulada.')}"
        f"</div>"
    )

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

    # -------------------------
    # Preparación de datos
    # -------------------------
    df = df.sort_values("fecha")
    df["fecha_label"] = df["fecha"].dt.strftime("%d %b %Y")

    n = len(df)
    fig = go.Figure()

    # -------------------------
    # RANGO DINÁMICO PESO
    # -------------------------
    peso_min = df["peso_bruto_kg"].min()
    peso_max = df["peso_bruto_kg"].max()

    # Margen adaptativo (antropometría real)
    rango = peso_max - peso_min
    margen = max(0.8, rango * 1.5)  # asegura visibilidad incluso con variación mínima

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
        line=dict(width=3, color="#E74C3C"),
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
            y=-0.25,
            x=0.5,
            xanchor="center"
        ),
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    _alerta_tendencia_grasa(df)

def _alerta_tendencia_grasa(df: pd.DataFrame):
    if len(df) < 3:
        return

    df = df.sort_values("fecha")

    delta = (
        df["ajuste_adiposa_pct"].iloc[-1]
        - df["ajuste_adiposa_pct"].iloc[-3]
    )

    if delta >= 2.0:
        st.warning(
            t(
                "Aumento relevante de % graso en las últimas mediciones. "
                "Revisar nutrición, carga y momento competitivo."
            )
        )
    elif delta <= -2.0:
        st.info(
            t(
                "Descenso marcado de % graso. "
                "Verificar que no comprometa disponibilidad energética."
            )
        )

def grafico_composicion(df):
    df = _prepare_antropometria_df(df)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["ajuste_adiposa_pct"],
        name=t("% Grasa"),
        mode="lines+markers"
    ))

    fig.add_trace(go.Scatter(
        x=df["fecha"],
        y=df["ajuste_muscular_pct"],
        name=t("% Muscular"),
        mode="lines+markers"
    ))

    xmin = df["fecha"].min()
    xmax = df["fecha"].max()

    if pd.notna(xmin) and pd.notna(xmax):
        fig.update_xaxes(range=[xmin, xmax])

    fig.update_layout(
        xaxis=dict(
            type="date",
            tickformat="%d %b %Y"
        ),
        template="plotly_white",
        yaxis_title=t("Porcentaje (%)"),
        legend=dict(orientation="h", y=-0.3),
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

def grafico_indice_musculo_oseo(df):
    df = _prepare_antropometria_df(df)

    if df.empty:
        st.info(t("No hay datos suficientes."))
        return

    usar_barras = len(df) <= 2
    fig = go.Figure()

    if usar_barras:
        fig.add_bar(
            x=df["fecha"],
            y=df["idx_musculo_oseo"],
            name=t("Índice músculo-óseo"),
            width=0.6,  # ⬅️ más ancho para datetime
            showlegend=True
        )
    else:
        fig.add_trace(go.Scatter(
            x=df["fecha"],
            y=df["idx_musculo_oseo"],
            name=t("Índice músculo-óseo"),
            mode="lines+markers",
            showlegend=True
        ))

    # 🔑 SOLO fijar rango si hay más de 1 fecha distinta
    fechas_unicas = df["fecha"].nunique()

    if fechas_unicas > 1:
        fig.update_xaxes(
            range=[df["fecha"].min(), df["fecha"].max()]
        )

    fig.update_layout(
        template="plotly_white",
        yaxis_title=t("Índice M/O"),
        xaxis=dict(
            tickformat="%d %b %Y",
            type="date"
        ),
        legend=dict(orientation="h", y=-0.3),
        bargap=0.4,
        showlegend=True
    )

    st.plotly_chart(fig)

