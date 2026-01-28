# src/plots_grupales.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.i18n.i18n import t

# ============================================================
# 🧭 Función auxiliar de fecha
# ============================================================
def _ensure_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura columna 'fecha_medicion' y añade 'semana', 'anio' y 'rango_semana'."""
    df = df.copy()
    if "fecha_medicion" not in df.columns:
        st.warning("El DataFrame no contiene la columna 'fecha_medicion'.")
        return df

    df["fecha_medicion"] = pd.to_datetime(df["fecha_medicion"], errors="coerce")
    df["anio"] = df["fecha_medicion"].dt.year
    df["semana"] = df["fecha_medicion"].dt.isocalendar().week

    # Etiqueta más amigable: rango de lunes a domingo
    df["inicio_semana"] = df["fecha_medicion"] - pd.to_timedelta(df["fecha_medicion"].dt.weekday, unit="d")
    df["fin_semana"] = df["inicio_semana"] + pd.Timedelta(days=6)
    df["rango_semana"] = df["inicio_semana"].dt.strftime("%d %b") + "–" + df["fin_semana"].dt.strftime("%d %b")

    return df

def plot_distribuciones(df: pd.DataFrame):
    df = df.copy()

    columnas = {
        "peso_bruto_kg": t("Peso (kg)"),
        "talla_corporal_cm": t("Talla (cm)"),
        "suma_6_pliegues_mm": t("Suma 6 pliegues (mm)"),
        "ajuste_adiposa_pct": t("% Grasa"),
        "ajuste_muscular_pct": t("% Muscular"),
        "masa_osea_kg": t("Masa ósea (kg)"),
        "indice_musculo_oseo": t("Índice músculo–óseo"),
    }

    for col, titulo in columnas.items():
        if col not in df.columns or df[col].dropna().empty:
            continue

        valores = pd.to_numeric(df[col], errors="coerce").dropna()

        fig = px.histogram(
            valores,
            nbins=12,
            title=f"{titulo} — {t('Distribución grupal')}",
            color_discrete_sequence=["#2E86C1"],
        )

        fig.add_vline(
            x=valores.mean(),
            line_dash="dash",
            line_color="green",
            annotation_text=t("Promedio"),
        )

        fig.update_layout(
            xaxis_title=titulo,
            yaxis_title=t("Número de jugadoras"),
            template="plotly_white",
        )

        st.plotly_chart(fig)

def plot_comparacion_mediciones(df: pd.DataFrame):
    if "fecha_medicion" not in df.columns:
        st.info(t("No hay fechas para comparar mediciones."))
        return

    # -------------------------
    # CAPTION (DESCRIPCIÓN DEL GRÁFICO)
    # -------------------------
    st.caption(
        t(
            "La gráfica muestra el cambio porcentual promedio del grupo entre la primera y la segunda medición. "
            "Valores positivos indican aumento respecto a la primera medición, mientras que valores negativos "
            "indican disminución."
        )
    )

    df = df.sort_values("fecha_medicion")

    df["orden_medicion"] = (
        df.groupby("identificacion").cumcount() + 1
    )

    df = df[df["orden_medicion"].isin([1, 2])]

    if df["orden_medicion"].nunique() < 2:
        st.info(t("No hay suficientes mediciones para comparar."))
        return

    resumen = (
        df.groupby("orden_medicion")
        .agg(
            peso=("peso_bruto_kg", "mean"),
            pliegues=("suma_6_pliegues_mm", "mean"),
            imo=("indice_musculo_oseo", "mean"),
        )
    )

    base = resumen.loc[1]
    actual = resumen.loc[2]

    delta = ((actual - base) / base) * 100

    delta_df = delta.reset_index()
    delta_df.columns = ["variable", "delta_pct"]

    # -------------------------
    # COLORES SEMÁNTICOS
    # -------------------------
    delta_df["color"] = delta_df["delta_pct"].apply(
        lambda x: "#2ECC71" if x > 0 else "#E74C3C"
    )

    y_min = delta_df["delta_pct"].min()
    y_max = delta_df["delta_pct"].max()

    padding = max(abs(y_min), abs(y_max)) * 0.15  # 15% de margen
    # -------------------------
    # GRÁFICO
    # -------------------------
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=delta_df["variable"],
        y=delta_df["delta_pct"],
        marker_color=delta_df["color"],
        text=delta_df["delta_pct"].map(lambda x: f"{x:+.2f}%"),
        textposition="outside",
    textfont=dict(size=12, color="#2C3E50"),
    ))

    fig.update_layout(
        uniformtext=dict(
        minsize=10,
        mode="show"),
        yaxis=dict(
            title=t("Cambio (%) respecto a la 1ª medición"),
            range=[y_min - padding, y_max + padding],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="#BDC3C7",
        ),
        #title=t("Variación porcentual entre mediciones"),
        yaxis_title=t("Cambio (%) respecto a la 1ª medición"),
        xaxis_title="",
        template="plotly_white",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # TEXTO EXPLICATIVO (INTERPRETACIÓN)
    # -------------------------
    frases = []

    if delta["peso"] > 0:
        frases.append(t("un ligero aumento del peso corporal"))
    elif delta["peso"] < 0:
        frases.append(t("una ligera disminución del peso corporal"))
    else:
        frases.append(t("estabilidad del peso corporal"))

    if delta["pliegues"] < 0:
        frases.append(t("una reducción de los pliegues cutáneos"))
    elif delta["pliegues"] > 0:
        frases.append(t("un aumento de los pliegues cutáneos"))

    if delta["imo"] > 0:
        frases.append(t("una mejora del índice músculo-óseo"))
    elif delta["imo"] < 0:
        frases.append(t("un descenso del índice músculo-óseo"))

    texto_explicativo = (
        t("Entre la primera y la segunda medición se observa ")
        + ", ".join(frases)
        + "."
    )

    st.markdown(
        f"""
        **{t("Interpretación de los resultados:")}**
        {texto_explicativo}
        """
    )


def tabla_resumen(df: pd.DataFrame):
    resumen = (
        df.groupby("nombre_jugadora", as_index=False)
        .agg(
            peso=("peso_bruto_kg", "mean"),
            grasa=("ajuste_adiposa_pct", "mean"),
            pliegues=("ajuste_muscular_pct", "mean"),
            imo=("idx_musculo_oseo", "mean"),
        )
    )

    for col in ["peso", "grasa", "pliegues", "imo"]:
        resumen[col] = resumen[col].map(
            lambda x: f"{x:.2f}" if pd.notna(x) else "-"
        )


    st.caption(
        t(
            "Valores promedio de los controles antropométricos registrados "
            "para cada jugadora durante el periodo seleccionado."
        )
    )

    st.dataframe(
        resumen.rename(columns={
            "nombre_jugadora": t("Jugadora"),
            "peso": t("Peso medio (kg)"),
            "grasa": t("% Grasa media"),
            "pliegues": t("6 Pliegues medios (mm)"),
            "imo": t("Índice M/O medio"),
        }),
        hide_index=True,
    )
