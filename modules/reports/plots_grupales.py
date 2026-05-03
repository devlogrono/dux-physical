# src/plots_grupales.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.i18n.i18n import t
from modules.util.records_util import filter_last_record_per_player
from modules.util.util import _title

REQUIRED = {"suma_6_pliegues_mm", "idx_musculo_oseo", "nombre_jugadora"}

METRICAS_DISTRIBUCION = {
    "peso_bruto_kg": t("Peso (kg)"),
    "talla_corporal_cm": t("Talla (cm)"),
    "suma_6_pliegues_mm": t("Suma 6 pliegues (mm)"),
    "ajuste_adiposa_pct": t("% Grasa"),
    "ajuste_muscular_pct": t("% Muscular"),
    "masa_osea_kg": t("Masa ósea (kg)"),
    "idx_musculo_oseo": t("Índice músculo-óseo"),
}

# -------------------------
# ANOTACIONES (inteligentes)
# -------------------------
OFFSET_POSITIONS = [
    (35, -28),   # derecha arriba
    (35, -25),  # izquierda arriba
    (-35, 25),    # derecha abajo
    (-35, 25),   # izquierda abajo
    (0, -10),    # arriba
    (0, 10),     # abajo
]

# -------------------------
# CORTES (según PDF)
# -------------------------
X_CORTE = 70
Y_CORTE = 3.80

X_MIN, X_MAX = 30, 150
Y_MIN, Y_MAX = 3.2, 4.5

# -------------------------
# ASIGNACIÓN DE CUADRANTE Y COLOR
# -------------------------
def cuadrante(row):
    if row["x"] <= X_CORTE and row["y"] >= Y_CORTE:
        return "G1", "#2ECC71"  # verde
    if row["x"] > X_CORTE and row["y"] >= Y_CORTE:
        return "G2", "#F1C40F"  # amarillo
    if row["x"] <= X_CORTE and row["y"] < Y_CORTE:
        return "G3", "#F39C12"  # naranja
    return "G4", "#E74C3C"      # rojo

# -------------------------
# DETECCIÓN DE SOLAPAMIENTO
# -------------------------
def needs_arrow(row, df, dx=6, dy=0.08):
    vecinos = df[
        (abs(df["x"] - row["x"]) < dx) &
        (abs(df["y"] - row["y"]) < dy)
    ]
    return len(vecinos) > 1

def plot_distribuciones(df: pd.DataFrame):
    # -------------------------
    # Preparación
    # -------------------------
    if df is None or df.empty:
        st.info(t("No hay datos disponibles."))
        return

    # Siempre usar última medición por jugadora
    df = filter_last_record_per_player(df)

    metricas = {
        k: v for k, v in METRICAS_DISTRIBUCION.items()
        if k in df.columns and df[k].dropna().any()
    }

    if not metricas:
        st.info(t("No hay métricas disponibles."))
        return

    col1, _ = st.columns([2, 6])

    with col1:
        col = st.selectbox(
            t("Seleccione la métrica"),
            options=list(metricas.keys()),
            format_func=lambda x: metricas[x],
        )

    metricas_descriptivas = [
        "peso_bruto_kg",
        "talla_corporal_cm",
        "talla_sentado_cm",
        "envergadura_cm",
        "masa_osea_kg",
    ]

    caption_text = (
        t("Distribución individual del grupo con valores mínimo, máximo y promedio.")
        if col in metricas_descriptivas
        else t("Distribución individual del grupo respecto a rangos de referencia y valores extremos.")
    )
    st.caption(caption_text)

    data = df[["nombre_jugadora", col]].dropna().copy()
    data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.dropna(subset=[col]).sort_values(col)

    if data.empty:
        st.info(t("No hay datos válidos para la métrica seleccionada."))
        return

    valores = data[col]
    media = valores.mean()
    minimo = valores.min()
    maximo = valores.max()

    # -------------------------
    # Reglas de color y referencia
    # -------------------------
    color_default = "#4A6FBF"
    ref_value = None
    ref_label = None
    resumen_extra = []
    modo_descriptivo = col in metricas_descriptivas

    def color_metrica(valor):
        if modo_descriptivo:
            return color_default

        if col == "ajuste_adiposa_pct":
            if valor < 14:
                return "#F1C40F"
            elif valor <= 20:
                return "#2ECC71"
            elif valor <= 24:
                return "#F39C12"
            return "#E74C3C"

        if col == "ajuste_muscular_pct":
            if valor < 40:
                return "#F39C12"
            elif valor <= 45:
                return "#2ECC71"
            return "#27AE60"

        if col == "idx_musculo_oseo":
            if valor < 3.5:
                return "#F39C12"
            elif valor <= 4.2:
                return "#2ECC71"
            return "#27AE60"

        if col == "suma_6_pliegues_mm":
            if valor < 50:
                return "#27AE60"
            elif valor <= 70:
                return "#2ECC71"
            elif valor <= 90:
                return "#F39C12"
            return "#E74C3C"

        return color_default

    if col == "ajuste_adiposa_pct":
        ref_value = 20
        ref_label = t("Límite adecuado")
        resumen_extra = [
            (t("Muy bajo"), int((valores < 14).sum())),
            (t("Adecuado"), int(((valores >= 14) & (valores <= 20)).sum())),
            (t("Moderado"), int(((valores > 20) & (valores <= 24)).sum())),
            (t("Elevado"), int((valores > 24).sum())),
        ]

    elif col == "ajuste_muscular_pct":
        ref_value = 40
        ref_label = t("Referencia mínima")
        resumen_extra = [
            (t("Bajo"), int((valores < 40).sum())),
            (t("Adecuado"), int(((valores >= 40) & (valores <= 45)).sum())),
            (t("Excelente"), int((valores > 45).sum())),
        ]

    elif col == "idx_musculo_oseo":
        ref_value = 3.5
        ref_label = t("Referencia mínima")
        resumen_extra = [
            (t("Bajo"), int((valores < 3.5).sum())),
            (t("Adecuado"), int(((valores >= 3.5) & (valores <= 4.2)).sum())),
            (t("Excelente"), int((valores > 4.2).sum())),
        ]

    elif col == "suma_6_pliegues_mm":
        ref_value = 70
        ref_label = t("Límite adecuado")
        resumen_extra = [
            (t("Excelente"), int((valores < 50).sum())),
            (t("Adecuado"), int(((valores >= 50) & (valores <= 70)).sum())),
            (t("Moderado"), int(((valores > 70) & (valores <= 90)).sum())),
            (t("Elevado"), int((valores > 90).sum())),
        ]

    data["color_barra"] = data[col].apply(color_metrica)

    # -------------------------
    # Gráfico
    # -------------------------
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data["nombre_jugadora"],
        y=data[col],
        text=data[col].map(lambda x: f"{x:.1f}"),
        textposition="outside",
        marker_color=data["color_barra"],
        hovertemplate=(
            "<b>%{x}</b><br>"
            + f"{metricas[col]}: "
            + "%{y:.1f}<extra></extra>"
        ),
    ))

    if modo_descriptivo:
        fig.add_hline(
            y=media,
            line_dash="dash",
            line_color="#27AE60",
            annotation_text=t("Promedio"),
            annotation_position="top left",
        )
    elif ref_value is not None:
        fig.add_hline(
            y=ref_value,
            line_dash="dot",
            line_color="#7F8C8D",
            annotation_text=ref_label,
            annotation_position="top left",
        )

    fig.update_layout(
        template="plotly_white",
        xaxis_title="",
        yaxis_title=metricas[col],
        height=470,
        margin=dict(t=60, b=120),
        showlegend=False,
    )

    fig.update_xaxes(
        tickangle=-45,
        tickfont=dict(size=10),
    )

    st.plotly_chart(fig, use_container_width=True)

    if col not in metricas_descriptivas:
        render_leyenda_metrica(col)

        # -------------------------
    # Resumen textual mejorado
    # -------------------------
    st.markdown(f"**{metricas[col]}**")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"- **{t('Promedio')}**: {media:.2f}  \n"
            f"- **{t('Mínimo')}**: {minimo:.2f}  \n"
            f"- **{t('Máximo')}**: {maximo:.2f}"
        )

    with c2:
                if resumen_extra:
                    def color_label_by_metric(col_name: str, label: str) -> str:
                        label_l = label.lower()

                        if col_name == "ajuste_adiposa_pct":
                            if label_l == t("muy bajo").lower():
                                return "#F1C40F"
                            if label_l == t("adecuado").lower():
                                return "#2ECC71"
                            if label_l == t("moderado").lower():
                                return "#F39C12"
                            if label_l == t("elevado").lower():
                                return "#E74C3C"

                        elif col_name == "ajuste_muscular_pct":
                            if label_l == t("bajo").lower():
                                return "#F39C12"
                            if label_l == t("adecuado").lower():
                                return "#2ECC71"
                            if label_l == t("excelente").lower():
                                return "#27AE60"

                        elif col_name == "idx_musculo_oseo":
                            if label_l == t("bajo").lower():
                                return "#F39C12"
                            if label_l == t("adecuado").lower():
                                return "#2ECC71"
                            if label_l == t("excelente").lower():
                                return "#27AE60"

                        elif col_name == "suma_6_pliegues_mm":
                            if label_l == t("excelente").lower():
                                return "#27AE60"
                            if label_l == t("adecuado").lower():
                                return "#2ECC71"
                            if label_l == t("moderado").lower():
                                return "#F39C12"
                            if label_l == t("elevado").lower():
                                return "#E74C3C"

                        return "#34495E"

                    extra_html = ""
                    for label, valor in resumen_extra:
                        color = color_label_by_metric(col, label)
                        extra_html += (
                            f"<div style='margin-bottom:6px;'>"
                            f"• <b style='color:{color};'>{label}</b>: {valor}"
                            f"</div>"
                        )

                    st.markdown(extra_html, unsafe_allow_html=True)

def render_leyenda_metrica(col: str):
    if col == "ajuste_adiposa_pct":
        st.caption(f"🟡 {t('Muy bajo')}: <14 · 🟢 {t('Adecuado')}: 14–20 · 🟠 {t('Moderado')}: 20–24 · 🔴 {t('Elevado')}: >24")

    elif col == "ajuste_muscular_pct":
        st.caption(f"🟠 {t('Bajo')}: <40 · 🟢 {t('Adecuado')}: 40–45 · 🟩 {t('Excelente')}: >45")

    elif col == "idx_musculo_oseo":
        st.caption(f"🟠 {t('Bajo')}: <3.5 · 🟢 {t('Adecuado')}: 3.5–4.2 · 🟩 {t('Excelente')}: >4.2")

    elif col == "suma_6_pliegues_mm":
        st.caption(f"🟩 {t('Excelente')}: <50 · 🟢 {t('Adecuado')}: 50–70 · 🟠 {t('Moderado')}: 70–90 · 🔴 {t('Elevado')}: >90")


def plot_comparacion_mediciones(df_visual: pd.DataFrame, df_calculo: pd.DataFrame, periodo: str):
    if df_visual is None or df_visual.empty or "fecha_medicion" not in df_visual.columns:
        st.info(t("No hay fechas para comparar mediciones."))
        return

    # -------------------------
    # Caption dinámico
    # -------------------------
    if periodo == "Última sesión":
        st.caption(
            t(
                "La gráfica muestra el cambio porcentual promedio del grupo entre la última y la medición anterior. "
                "Valores positivos indican aumento reciente, mientras que valores negativos indican disminución."
            )
        )
    else:
        st.caption(
            t(
                "La gráfica muestra el cambio porcentual promedio del grupo entre la primera y la última medición del periodo. "
                "Valores positivos indican aumento respecto al inicio del periodo, mientras que valores negativos "
                "indican disminución."
            )
        )

    def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")

        if "created_at" in out.columns:
            out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")

        cols_needed = [
            "identificacion",
            "fecha_medicion",
            "peso_bruto_kg",
            "ajuste_adiposa_pct",
            "ajuste_muscular_pct",
            "suma_6_pliegues_mm",
            "idx_musculo_oseo",
        ]
        cols_present = [c for c in cols_needed if c in out.columns]

        out = out[
            cols_present + [c for c in ["nombre_jugadora", "created_at", "id_isak"] if c in out.columns]
        ].copy()

        for col in [
            "peso_bruto_kg",
            "ajuste_adiposa_pct",
            "ajuste_muscular_pct",
            "suma_6_pliegues_mm",
            "idx_musculo_oseo",
        ]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")

        out = out.dropna(subset=["fecha_medicion"])
        return out

    if periodo == "Última sesión":
        df_base = _prepare_df(df_calculo)
    else:
        df_base = _prepare_df(df_visual)

    if df_base.empty:
        st.info(t("No hay suficientes datos para comparar mediciones."))
        return

    sort_cols = ["identificacion", "fecha_medicion"]
    asc_desc = [True, False]
    asc_asc = [True, True]

    if "created_at" in df_base.columns:
        sort_cols.append("created_at")
        asc_desc.append(False)
        asc_asc.append(True)

    if "id_isak" in df_base.columns:
        sort_cols.append("id_isak")
        asc_desc.append(False)
        asc_asc.append(True)

    # -------------------------
    # Construcción de comparación según periodo
    # -------------------------
    if periodo == "Última sesión":
        df_base = df_base.sort_values(sort_cols, ascending=asc_desc).copy()
        df_base["rank_medicion"] = df_base.groupby("identificacion").cumcount() + 1

        df_curr = df_base[df_base["rank_medicion"] == 1].copy()
        df_prev = df_base[df_base["rank_medicion"] == 2].copy()

    else:
        df_curr = (
            df_base.sort_values(sort_cols, ascending=asc_desc)
            .groupby("identificacion", as_index=False)
            .head(1)
            .copy()
        )

        df_prev = (
            df_base.sort_values(sort_cols, ascending=asc_asc)
            .groupby("identificacion", as_index=False)
            .head(1)
            .copy()
        )

    vars_cmp = [
        "peso_bruto_kg",
        "ajuste_adiposa_pct",
        "ajuste_muscular_pct",
        "suma_6_pliegues_mm",
        "idx_musculo_oseo",
    ]
    vars_cmp = [v for v in vars_cmp if v in df_curr.columns and v in df_prev.columns]

    if not vars_cmp:
        st.info(t("No hay variables disponibles para comparar."))
        return

    df_curr = df_curr[["identificacion"] + vars_cmp].rename(columns={v: f"{v}_curr" for v in vars_cmp})
    df_prev = df_prev[["identificacion"] + vars_cmp].rename(columns={v: f"{v}_prev" for v in vars_cmp})

    df_cmp = df_curr.merge(df_prev, on="identificacion", how="inner")

    if df_cmp.empty:
        st.info(t("No hay suficientes mediciones para comparar."))
        return

    # -------------------------
    # Delta promedio del grupo
    # -------------------------
    deltas = {}
    for v in vars_cmp:
        prev_col = f"{v}_prev"
        curr_col = f"{v}_curr"

        prev_mean = df_cmp[prev_col].mean()
        curr_mean = df_cmp[curr_col].mean()

        if pd.isna(prev_mean) or prev_mean == 0:
            deltas[v] = 0
        else:
            deltas[v] = ((curr_mean - prev_mean) / prev_mean) * 100

    delta_df = pd.DataFrame({
        "variable": list(deltas.keys()),
        "delta_pct": list(deltas.values())
    })

    nombres_vars = {
        "peso_bruto_kg": t("Peso"),
        "ajuste_adiposa_pct": t("Grasa"),
        "ajuste_muscular_pct": t("Músculo"),
        "suma_6_pliegues_mm": t("Pliegues"),
        "idx_musculo_oseo": t("IMO"),
    }
    delta_df["variable"] = delta_df["variable"].map(nombres_vars)

    # -------------------------
    # Colores semánticos
    # -------------------------
    def color_delta(row):
        var = row["variable"]
        val = row["delta_pct"]

        if var == t("Peso"):
            return "#4A6FBF"   # descriptivo / neutro

        if var == t("Grasa"):
            return "#2ECC71" if val < 0 else "#E74C3C"

        if var == t("Músculo"):
            return "#2ECC71" if val > 0 else "#E74C3C"

        if var == t("Pliegues"):
            return "#2ECC71" if val < 0 else "#E74C3C"

        if var == t("IMO"):
            return "#2ECC71" if val > 0 else "#E74C3C"

        return "#4A6FBF"

    delta_df["color"] = delta_df.apply(color_delta, axis=1)

    y_min = delta_df["delta_pct"].min()
    y_max = delta_df["delta_pct"].max()
    padding = max(abs(y_min), abs(y_max)) * 0.15 if len(delta_df) else 1

    # -------------------------
    # Gráfico
    # -------------------------
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=delta_df["variable"],
        y=delta_df["delta_pct"],
        marker_color=delta_df["color"],
        text=delta_df["delta_pct"].map(lambda x: f"{x:+.2f}%"),
        textposition="outside",
        textfont=dict(size=12, color="#2C3E50"),
        hovertemplate="<b>%{x}</b><br>%{y:+.2f}%<extra></extra>",
    ))

    titulo_eje = (
        t("Cambio (%) respecto a la medición anterior")
        if periodo == "Última sesión"
        else t("Cambio (%) respecto al inicio del periodo")
    )

    fig.update_layout(
        uniformtext=dict(minsize=10, mode="show"),
        yaxis=dict(
            title=titulo_eje,
            range=[y_min - padding, y_max + padding],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="#BDC3C7",
        ),
        yaxis_title=titulo_eje,
        xaxis_title="",
        template="plotly_white",
        showlegend=False,
        height=430,
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Interpretación visual
    # -------------------------
    def format_neutro(label, delta):
        return (
            f"<div style='margin-bottom:6px;'>"
            f"• <b>{label}</b>: {delta:+.2f}%"
            f"</div>"
        )

    def format_interpretacion(label, delta, positivo_es_bueno=True):
        if delta == 0:
            return (
                f"<div style='margin-bottom:6px;'>"
                f"• <b>{label}</b>: {t('Sin cambios relevantes')}"
                f"</div>"
            )

        if (delta > 0 and positivo_es_bueno) or (delta < 0 and not positivo_es_bueno):
            color = "#2ECC71"
            simbolo = "✔️"
            texto = t("Mejora")
        else:
            color = "#E74C3C"
            simbolo = "❌"
            texto = t("Empeoramiento")

        return (
            f"<div style='margin-bottom:6px;'>"
            f"• <b>{label}</b>: "
            f"<span style='color:{color}; font-weight:600;'>"
            f"{simbolo} {texto} ({delta:+.2f}%)"
            f"</span>"
            f"</div>"
        )

    html = ""
    html += format_neutro(t("Peso"), deltas.get("peso_bruto_kg", 0))
    html += format_interpretacion(t("Grasa"), deltas.get("ajuste_adiposa_pct", 0), positivo_es_bueno=False)
    html += format_interpretacion(t("Músculo"), deltas.get("ajuste_muscular_pct", 0), positivo_es_bueno=True)
    html += format_interpretacion(t("Pliegues"), deltas.get("suma_6_pliegues_mm", 0), positivo_es_bueno=False)
    html += format_interpretacion(t("Índice músculo-óseo"), deltas.get("idx_musculo_oseo", 0), positivo_es_bueno=True)

    st.markdown(
        f"""
        **{t("Interpretación de los resultados")}**

        {html}
        """,
        unsafe_allow_html=True
    )

def tabla_resumen(df: pd.DataFrame):
    """
    Resumen grupal por jugadora con medias del periodo, nº de mediciones
    y ordenación configurable.
    """

    if df is None or df.empty:
        st.info(t("No hay datos disponibles para resumir."))
        return

    st.caption(
        t("Valores promedio de los controles antropométricos registrados para cada jugadora durante el periodo seleccionado.")
    )

    required_cols = ["nombre_jugadora"]
    if not all(c in df.columns for c in required_cols):
        st.info(t("Faltan columnas necesarias para construir el resumen grupal."))
        return

    out = df.copy()

    cols_numericas = [
        "peso_bruto_kg",
        "ajuste_adiposa_pct",
        "ajuste_muscular_pct",
        "suma_6_pliegues_mm",
        "idx_musculo_oseo",
    ]

    for col in cols_numericas:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    agg_map = {"nombre_jugadora": "first"}

    if "peso_bruto_kg" in out.columns:
        agg_map["peso_bruto_kg"] = "mean"
    if "ajuste_adiposa_pct" in out.columns:
        agg_map["ajuste_adiposa_pct"] = "mean"
    if "ajuste_muscular_pct" in out.columns:
        agg_map["ajuste_muscular_pct"] = "mean"
    if "suma_6_pliegues_mm" in out.columns:
        agg_map["suma_6_pliegues_mm"] = "mean"
    if "idx_musculo_oseo" in out.columns:
        agg_map["idx_musculo_oseo"] = "mean"

    resumen = (
        out.groupby("nombre_jugadora", as_index=False)
        .agg(agg_map)
        .rename(columns={"nombre_jugadora": "Jugadora"})
    )

    # nº mediciones por jugadora
    n_med = (
        out.groupby("nombre_jugadora")
        .size()
        .reset_index(name="n_mediciones")
        .rename(columns={"nombre_jugadora": "Jugadora"})
    )

    resumen = resumen.merge(n_med, on="Jugadora", how="left")

    # Renombrar columnas visibles
    rename_map = {
        "peso_bruto_kg": "Peso medio (kg)",
        "ajuste_adiposa_pct": "% Grasa media",
        "ajuste_muscular_pct": "% Muscular medio",
        "suma_6_pliegues_mm": "6 Pliegues medios (mm)",
        "idx_musculo_oseo": "Índice M/O medio",
        "n_mediciones": "Nº mediciones",
    }
    resumen = resumen.rename(columns=rename_map)

    # Si falta alguna columna, no la mostramos
    columnas_disponibles = [
        c for c in [
            "Jugadora",
            "Peso medio (kg)",
            "% Grasa media",
            "% Muscular medio",
            "6 Pliegues medios (mm)",
            "Índice M/O medio",
            "Nº mediciones",
        ]
        if c in resumen.columns
    ]
    resumen = resumen[columnas_disponibles].copy()

    # -------------------------
    # Selectores de ranking
    # -------------------------
    c1, c2 = st.columns([2, 2])

    opciones_orden = [c for c in resumen.columns if c != "Jugadora"]

    with c1:
        ordenar_por = st.selectbox(
            t("Ordenar por"),
            options=opciones_orden,
            index=0 if opciones_orden else None,
            key="ranking_resumen_grupal_variable",
        )

    with c2:
        sentido = st.selectbox(
            t("Mostrar"),
            options=[t("Mejores primero"), t("Peores primero")],
            index=0,
            key="ranking_resumen_grupal_sentido",
        )

    # Lógica de qué es "mejor" por variable
    mayores_mejor = {
        "Peso medio (kg)": None,  # descriptivo
        "% Grasa media": False,
        "% Muscular medio": True,
        "6 Pliegues medios (mm)": False,
        "Índice M/O medio": True,
        "Nº mediciones": True,
    }

    if ordenar_por:
        if mayores_mejor.get(ordenar_por) is None:
            # descriptivo: mejores primero = descendente por defecto no tiene mucho sentido,
            # así que usamos ascendente/descendente literal sencillo
            ascending = False if sentido == t("Peores primero") else True
        else:
            if sentido == t("Mejores primero"):
                ascending = not mayores_mejor[ordenar_por]
            else:
                ascending = mayores_mejor[ordenar_por]

        resumen = resumen.sort_values(
            by=[ordenar_por, "Jugadora"],
            ascending=[ascending, True],
            na_position="last"
        ).reset_index(drop=True)

    # -------------------------
    # Estilos por columna
    # -------------------------
    def style_metric(col):
        estilos = []

        for v in col:
            if pd.isna(v):
                estilos.append("")
                continue

            # % grasa
            if col.name == "% Grasa media":
                if v < 14:
                    estilos.append("background-color:#F1C40F; color:black; text-align:center;")
                elif v <= 20:
                    estilos.append("background-color:#2ECC71; color:white; text-align:center;")
                elif v <= 24:
                    estilos.append("background-color:#F39C12; color:white; text-align:center;")
                else:
                    estilos.append("background-color:#E74C3C; color:white; text-align:center;")

            # % muscular
            elif col.name == "% Muscular medio":
                if v < 40:
                    estilos.append("background-color:#E74C3C; color:white; text-align:center;")
                elif v <= 45:
                    estilos.append("background-color:#2ECC71; color:white; text-align:center;")
                else:
                    estilos.append("background-color:#27AE60; color:white; text-align:center;")

            # 6 pliegues
            elif col.name == "6 Pliegues medios (mm)":
                if v < 50:
                    estilos.append("background-color:#27AE60; color:white; text-align:center;")
                elif v <= 70:
                    estilos.append("background-color:#2ECC71; color:white; text-align:center;")
                elif v <= 90:
                    estilos.append("background-color:#F39C12; color:white; text-align:center;")
                else:
                    estilos.append("background-color:#E74C3C; color:white; text-align:center;")

            # IMO
            elif col.name == "Índice M/O medio":
                if v < 3.5:
                    estilos.append("background-color:#F39C12; color:white; text-align:center;")
                elif v <= 4.2:
                    estilos.append("background-color:#2ECC71; color:white; text-align:center;")
                else:
                    estilos.append("background-color:#27AE60; color:white; text-align:center;")

            else:
                estilos.append("text-align:center;")

        return estilos

    format_map = {}
    if "Peso medio (kg)" in resumen.columns:
        format_map["Peso medio (kg)"] = "{:.2f}"
    if "% Grasa media" in resumen.columns:
        format_map["% Grasa media"] = "{:.2f}"
    if "% Muscular medio" in resumen.columns:
        format_map["% Muscular medio"] = "{:.2f}"
    if "6 Pliegues medios (mm)" in resumen.columns:
        format_map["6 Pliegues medios (mm)"] = "{:.2f}"
    if "Índice M/O medio" in resumen.columns:
        format_map["Índice M/O medio"] = "{:.2f}"
    if "Nº mediciones" in resumen.columns:
        format_map["Nº mediciones"] = "{:.0f}"

    subset_cols_color = [
        c for c in [
            "% Grasa media",
            "% Muscular medio",
            "6 Pliegues medios (mm)",
            "Índice M/O medio",
        ] if c in resumen.columns
    ]

    subset_cols_center = [
        c for c in [
            "Peso medio (kg)",
            "Nº mediciones",
        ] if c in resumen.columns
    ]

    styled = resumen.style.format(format_map)

    if subset_cols_color:
        styled = styled.apply(style_metric, subset=subset_cols_color)

    if subset_cols_center:
        styled = styled.set_properties(
            subset=subset_cols_center,
            **{"text-align": "center"}
        )

    styled = styled.set_table_styles([
        {"selector": "th", "props": [("text-align", "center")]},
    ])

    st.dataframe(
        styled,
        hide_index=True,
        use_container_width=True,
    )

##########################

def get_interpretacion(df_plot: pd.DataFrame):
    n_g1 = n_g2 = n_g3 = n_g4 = 0

    if df_plot is not None and not df_plot.empty and "grupo" in df_plot.columns:
        counts = df_plot["grupo"].value_counts()
        n_g1 = int(counts.get("G1", 0))
        n_g2 = int(counts.get("G2", 0))
        n_g3 = int(counts.get("G3", 0))
        n_g4 = int(counts.get("G4", 0))

    with st.expander(t("Interpretación del perfil antropométrico"), expanded=False):

        st.markdown(
            f"""
            <div style="line-height:1.6">

            <span style="color:#2ECC71;"><b>G1 · Alto en músculo / Bajo en grasa</b></span> → {n_g1} jugadoras<br>
            Perfil corporal óptimo para el rendimiento deportivo. Se asocia a una mayor eficiencia mecánica,
            buena potencia relativa y menor lastre corporal.

            <span style="color:#F1C40F;"><b>G2 · Alto en músculo / Alto en grasa</b></span> → {n_g2} jugadoras<br>
            Buen desarrollo muscular con margen de mejora en la composición corporal.
            Existe potencial de optimización reduciendo masa grasa sin comprometer la masa muscular.

            <span style="color:#F39C12;"><b>G3 · Bajo en músculo / Bajo en grasa</b></span> → {n_g3} jugadoras<br>
            Perfil corporal ligero con posible déficit estructural.
            Puede limitar la producción de fuerza y la tolerancia a contactos, siendo recomendable un trabajo
            orientado al desarrollo muscular.

            <span style="color:#E74C3C;"><b>G4 · Bajo en músculo / Alto en grasa</b></span> → {n_g4} jugadoras<br>
            Perfil menos favorable para el rendimiento físico.
            Puede afectar a la eficiencia del movimiento y aumentar el lastre corporal,
            siendo prioritaria la intervención desde el entrenamiento y la nutrición.

            </div>
            """,
            unsafe_allow_html=True
        )

def configurar_labels_perfil(df: pd.DataFrame, key_prefix: str = "perfil"):
    """
    Configuración reutilizable de etiquetas para gráficos scatter.
    """

    col1, col2 = st.columns([2, 3])

    with col1:
        modo = st.selectbox(
            t("Etiquetas"),
            options=[
                t("Ocultar todas"),
                t("Mostrar Todas"),
                t("Por cuadrante"),
                t("Seleccionar Jugadoras"),
            ],
            index=0,
            key=f"{key_prefix}_modo_labels",
        )

    cfg = {"modo": modo, "cuadrantes": [], "jugadoras": []}

    with col2:
        if modo == t("Por cuadrante"):
            cfg["cuadrantes"] = st.multiselect(
                t("Cuadrantes a mostrar"),
                options=["G1", "G2", "G3", "G4"],
                default=["G1", "G2", "G3", "G4"],
                key=f"{key_prefix}_cuadrantes_labels",
            )

        elif modo == t("Seleccionar Jugadoras"):
            jugadoras = sorted(df["nombre_jugadora"].dropna().astype(str).unique().tolist())
            cfg["jugadoras"] = st.multiselect(
                t("Jugadoras a mostrar"),
                options=jugadoras,
                default=[],
                key=f"{key_prefix}_jugadoras_labels",
            )

    return cfg

def filtrar_df_labels(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    modo = cfg["modo"]

    if modo == "Ocultar todas":
        return df.iloc[0:0]

    if modo == "Mostrar Todas":
        return df

    if modo == "Por cuadrante":
        return df[df["grupo"].isin(cfg["cuadrantes"])]

    if modo == "Seleccionar Jugadoras":
        return df[df["nombre_jugadora"].isin(cfg["jugadoras"])]

    return df

def plot_perfil_antropometrico(
    df: pd.DataFrame,
    jugadora_destacada: str | None = None,
    mostrar_labels: bool = True,
):
    if not REQUIRED.issubset(df.columns):
        st.warning(t("No hay datos suficientes para generar el perfil antropométrico."))
        return

    # Último registro por jugadora
    df = filter_last_record_per_player(df)

    df = df.copy()
    df["x"] = pd.to_numeric(df["suma_6_pliegues_mm"], errors="coerce")
    df["y"] = pd.to_numeric(df["idx_musculo_oseo"], errors="coerce")
    df = df.dropna(subset=["x", "y"])

    if df.empty:
        st.info(t("No hay valores válidos para el perfil antropométrico."))
        return

    df[["grupo", "color"]] = df.apply(
        lambda r: pd.Series(cuadrante(r)), axis=1
    )

    df["label"] = df.apply(
        lambda r: f'{r["nombre_jugadora"].title()} ({r["x"]:.1f}; {r["y"]:.2f})',
        axis=1
    )

    # Destacada
    if jugadora_destacada is not None:
        df["es_destacada"] = df["nombre_jugadora"].astype(str) == str(jugadora_destacada)
    else:
        df["es_destacada"] = False

    # Labels
    if jugadora_destacada is None:
        cfg_labels = configurar_labels_perfil(df, key_prefix="perfil_antropometrico")
        df_labels = filtrar_df_labels(df, cfg_labels)
    else:
        # En individual: solo label de la jugadora destacada
        df_labels = df[df["es_destacada"]].copy() if mostrar_labels else df.iloc[0:0].copy()

    fig = go.Figure()

    # Grupo base
    df_base = df[~df["es_destacada"]].copy()
    if not df_base.empty:
        fig.add_trace(go.Scatter(
            x=df_base["x"],
            y=df_base["y"],
            mode="markers",
            marker=dict(
                size=10,
                color=df_base["color"],
                line=dict(width=1, color="white"),
                opacity=0.55 if jugadora_destacada is not None else 1.0,
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                + t("Suma 6 pliegues") + ": %{x:.1f} mm<br>"
                + t("Índice músculo/óseo") + ": %{y:.2f}<extra></extra>"
            ),
            customdata=df_base["label"],
            showlegend=False,
        ))

    # Jugadora destacada
    df_hi = df[df["es_destacada"]].copy()
    if not df_hi.empty:
        fig.add_trace(go.Scatter(
            x=df_hi["x"],
            y=df_hi["y"],
            mode="markers",
            marker=dict(
                size=16,
                color="#111827",
                line=dict(width=2, color="white"),
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                + t("Suma 6 pliegues") + ": %{x:.1f} mm<br>"
                + t("Índice músculo/óseo") + ": %{y:.2f}<extra></extra>"
            ),
            customdata=df_hi["label"],
            showlegend=False,
        ))

    # Anotaciones
    offset_index = 0
    for _, row in df_labels.iterrows():
        if needs_arrow(row, df):
            ax, ay = OFFSET_POSITIONS[offset_index % len(OFFSET_POSITIONS)]
            offset_index += 1

            fig.add_annotation(
                x=row["x"],
                y=row["y"],
                text=row["label"],
                showarrow=True,
                arrowhead=2,
                arrowwidth=1,
                arrowcolor="#424245",
                ax=ax,
                ay=ay,
                font=dict(size=9, color="#424245"),
                bgcolor="rgba(255,255,255,0)",
                borderpad=2,
            )
        else:
            fig.add_annotation(
                x=row["x"],
                y=row["y"],
                text=row["label"],
                showarrow=False,
                yshift=10,
                font=dict(size=9, color="#374151"),
            )

    # Líneas y cuadrantes
    fig.add_vline(x=X_CORTE, line_width=1.2, line_color="#9CA3AF")
    fig.add_hline(y=Y_CORTE, line_width=1.2, line_color="#9CA3AF")

    fig.add_annotation(x=40,  y=4.4, text="<b>G1</b>", showarrow=False)
    fig.add_annotation(x=115, y=4.4, text="<b>G2</b>", showarrow=False)
    fig.add_annotation(x=40,  y=3.3, text="<b>G3</b>", showarrow=False)
    fig.add_annotation(x=115, y=3.3, text="<b>G4</b>", showarrow=False)

    y_min = min(Y_MIN, df["y"].min() - 0.1)
    y_max = max(Y_MAX, df["y"].max() + 0.1)

    titulo = (
        t("Perfil antropométrico individual dentro del grupo")
        if jugadora_destacada is not None
        else t("Perfil antropométrico grupal")
    )

    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.02,
            font=dict(size=18),
        ),
        xaxis=dict(
            title=t("Suma 6 pliegues (mm)"),
            range=[X_MIN, X_MAX],
            gridcolor="#ECF0F1",
        ),
        yaxis=dict(
            title=t("Índice músculo / óseo"),
            range=[y_min, y_max],
            gridcolor="#ECF0F1",
        ),
        template="plotly_white",
        height=650,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretación
    if jugadora_destacada is None:
        get_interpretacion(df)
    else:
        if not df_hi.empty:
            row = df_hi.iloc[0]
            grupo = row["grupo"]

            color_map = {
                "G1": "#27AE60",
                "G2": "#F1C40F",
                "G3": "#F39C12",
                "G4": "#E74C3C",
            }
            color_grupo = color_map.get(grupo, "#34495E")

            st.markdown(
                f"""
                <div style="margin-top:8px; line-height:1.7;">
                    <b>{t('Zona actual')}:</b>
                    <span style="color:{color_grupo}; font-weight:700;">{grupo}</span>
                    · <b>{t('Suma 6 pliegues')}:</b> {row['x']:.1f} mm
                    · <b>{t('Índice músculo / óseo')}:</b> {row['y']:.2f}
                </div>
                """,
                unsafe_allow_html=True
            )

            if grupo == "G1":
                texto = t("Perfil favorable, con baja adiposidad subcutánea y buena relación músculo-ósea. Compatible con una composición corporal eficiente para el rendimiento.")
            elif grupo == "G2":
                texto = t("Perfil con buena base muscular, aunque con margen de mejora en adiposidad subcutánea. El foco principal estaría en optimizar la composición corporal sin comprometer la masa funcional.")
            elif grupo == "G3":
                texto = t("Perfil ligero, con baja adiposidad pero menor desarrollo relativo en la relación músculo-ósea. Puede existir margen de mejora estructural y de fuerza.")
            else:
                texto = t("Perfil menos favorable, con mayor adiposidad subcutánea y menor relación músculo-ósea relativa. El foco estaría en mejorar composición corporal y desarrollo funcional.")

            st.markdown(
                f"""
                <div style="margin-top:6px; line-height:1.7;">
                    <b style="color:{color_grupo};">{t('Interpretación')}:</b> {texto}
                </div>
                """,
                unsafe_allow_html=True
            )


def plot_cambios_clave(df_visual: pd.DataFrame, df_calculo: pd.DataFrame, periodo: str):
    """
    Muestra las jugadoras con mayores mejoras y empeoramientos
    para una métrica seleccionada.

    Lógica:
    - Última sesión: última vs anterior usando df_calculo
    - Historico: última vs primera del periodo usando df_visual
    """

    if df_visual is None or df_visual.empty or "fecha_medicion" not in df_visual.columns:
        st.info(t("No hay datos disponibles para analizar cambios clave."))
        return

    st.caption(
        t("Ranking de jugadoras con mayor mejora y mayor empeoramiento según la métrica seleccionada.")
    )

    metricas = {
        "ajuste_adiposa_pct": t("% Grasa"),
        "ajuste_muscular_pct": t("% Muscular"),
        "suma_6_pliegues_mm": t("Suma 6 pliegues"),
        "idx_musculo_oseo": t("Índice músculo-óseo"),
    }

    metricas = {k: v for k, v in metricas.items() if k in (df_calculo.columns if df_calculo is not None else []) or k in df_visual.columns}
    if not metricas:
        st.info(t("No hay métricas disponibles para analizar cambios."))
        return

    col_sel, col_n = st.columns([2, 1])

    with col_sel:
        metrica = st.selectbox(
            t("Selecciona la métrica"),
            options=list(metricas.keys()),
            format_func=lambda x: metricas[x],
            key="cambios_clave_metrica"
        )

    with col_n:
        top_n = st.selectbox(
            t("Mostrar top"),
            options=[3, 5, 10],
            index=1,
            key="cambios_clave_topn"
        )

    def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")

        if "created_at" in out.columns:
            out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")

        keep_cols = ["identificacion", "fecha_medicion", metrica]
        for extra in ["nombre_jugadora", "created_at", "id_isak"]:
            if extra in out.columns and extra not in keep_cols:
                keep_cols.append(extra)

        out = out[keep_cols].copy()
        out[metrica] = pd.to_numeric(out[metrica], errors="coerce")
        out = out.dropna(subset=["fecha_medicion", metrica])

        return out

    if periodo == "Última sesión":
        if df_calculo is None or df_calculo.empty or metrica not in df_calculo.columns:
            st.info(t("No hay suficientes datos históricos para calcular cambios recientes."))
            return
        df_base = _prepare_df(df_calculo)
    else:
        if metrica not in df_visual.columns:
            st.info(t("La métrica seleccionada no está disponible en el periodo visual."))
            return
        df_base = _prepare_df(df_visual)

    if df_base.empty:
        st.info(t("No hay datos suficientes para calcular cambios."))
        return

    sort_cols = ["identificacion", "fecha_medicion"]
    asc_desc = [True, False]
    asc_asc = [True, True]

    if "created_at" in df_base.columns:
        sort_cols.append("created_at")
        asc_desc.append(False)
        asc_asc.append(True)

    if "id_isak" in df_base.columns:
        sort_cols.append("id_isak")
        asc_desc.append(False)
        asc_asc.append(True)

    if periodo == "Última sesión":
        df_base = df_base.sort_values(sort_cols, ascending=asc_desc).copy()
        df_base["rank_medicion"] = df_base.groupby("identificacion").cumcount() + 1

        df_curr = df_base[df_base["rank_medicion"] == 1].copy()
        df_prev = df_base[df_base["rank_medicion"] == 2].copy()

    else:
        df_curr = (
            df_base.sort_values(sort_cols, ascending=asc_desc)
            .groupby("identificacion", as_index=False)
            .head(1)
            .copy()
        )

        df_prev = (
            df_base.sort_values(sort_cols, ascending=asc_asc)
            .groupby("identificacion", as_index=False)
            .head(1)
            .copy()
        )

    curr_cols = ["identificacion", metrica]
    if "nombre_jugadora" in df_curr.columns:
        curr_cols.insert(1, "nombre_jugadora")

    df_curr = df_curr[curr_cols].rename(columns={metrica: "valor_curr"})
    df_prev = df_prev[["identificacion", metrica]].rename(columns={metrica: "valor_prev"})

    df_cmp = df_curr.merge(df_prev, on="identificacion", how="inner")

    if df_cmp.empty:
        st.info(t("No hay suficientes mediciones para comparar."))
        return

    df_cmp["valor_prev"] = pd.to_numeric(df_cmp["valor_prev"], errors="coerce")
    df_cmp["valor_curr"] = pd.to_numeric(df_cmp["valor_curr"], errors="coerce")
    df_cmp = df_cmp.dropna(subset=["valor_prev", "valor_curr"])
    df_cmp = df_cmp[df_cmp["valor_prev"] != 0]

    if df_cmp.empty:
        st.info(t("No hay suficientes datos válidos para calcular cambios."))
        return

    df_cmp["delta_pct"] = ((df_cmp["valor_curr"] - df_cmp["valor_prev"]) / df_cmp["valor_prev"]) * 100
    df_cmp["delta_abs"] = df_cmp["valor_curr"] - df_cmp["valor_prev"]

    # Ajuste semántico: qué significa mejorar
    if metrica in ["ajuste_adiposa_pct", "suma_6_pliegues_mm"]:
        df_cmp["score_mejora"] = -df_cmp["delta_pct"]  # bajar = mejor
    else:
        df_cmp["score_mejora"] = df_cmp["delta_pct"]   # subir = mejor

    if "nombre_jugadora" not in df_cmp.columns:
        df_cmp["nombre_jugadora"] = df_cmp["identificacion"].astype(str)

    top_mejora = (
        df_cmp.sort_values(["score_mejora", "nombre_jugadora"], ascending=[False, True])
        .head(top_n)
        .copy()
    )

    top_empeora = (
        df_cmp.sort_values(["score_mejora", "nombre_jugadora"], ascending=[True, True])
        .head(top_n)
        .copy()
    )

    def _fmt_delta(row):
        return f"{row['delta_pct']:+.2f}%"

    top_mejora["Cambio"] = top_mejora.apply(_fmt_delta, axis=1)
    top_empeora["Cambio"] = top_empeora.apply(_fmt_delta, axis=1)

    top_mejora["Valor inicial"] = top_mejora["valor_prev"]
    top_mejora["Valor final"] = top_mejora["valor_curr"]

    top_empeora["Valor inicial"] = top_empeora["valor_prev"]
    top_empeora["Valor final"] = top_empeora["valor_curr"]

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"### 🟢 {t('Mayores mejoras')}")
        st.dataframe(
            top_mejora[["nombre_jugadora", "Valor inicial", "Valor final", "Cambio"]].rename(
                columns={"nombre_jugadora": t("Jugadora")}
            ),
            hide_index=True,
            use_container_width=True
        )

    with c2:
        st.markdown(f"### 🔴 {t('Mayores empeoramientos')}")
        st.dataframe(
            top_empeora[["nombre_jugadora", "Valor inicial", "Valor final", "Cambio"]].rename(
                columns={"nombre_jugadora": t("Jugadora")}
            ),
            hide_index=True,
            use_container_width=True
        )

def plot_evolucion_temporal_grupal(df_calculo: pd.DataFrame):
    """
    Muestra la evolución temporal del grupo para una métrica seleccionada.
    Agrupa fechas cercanas (<= 7 días) como una misma ronda de medición.
    """

    if df_calculo is None or df_calculo.empty or "fecha_medicion" not in df_calculo.columns:
        st.info(t("No hay datos históricos disponibles para mostrar evolución temporal."))
        return

    def asignar_bloques_medicion(df: pd.DataFrame, gap_dias: int = 7) -> pd.DataFrame:
        out = df.copy()
        out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")
        out = out.dropna(subset=["fecha_medicion"]).sort_values("fecha_medicion").copy()

        fechas = out["fecha_medicion"].drop_duplicates().sort_values().tolist()

        bloques = []
        bloque_actual = 1
        fecha_prev = None

        for f in fechas:
            if fecha_prev is None:
                bloques.append((f, bloque_actual))
            else:
                if (f - fecha_prev).days > gap_dias:
                    bloque_actual += 1
                bloques.append((f, bloque_actual))
            fecha_prev = f

        map_bloques = {f: b for f, b in bloques}
        out["bloque_medicion"] = out["fecha_medicion"].map(map_bloques)

        return out

    metricas = {
        "ajuste_adiposa_pct": t("% Grasa"),
        "ajuste_muscular_pct": t("% Muscular"),
        "suma_6_pliegues_mm": t("Suma 6 pliegues"),
        "idx_musculo_oseo": t("Índice músculo-óseo"),
        "peso_bruto_kg": t("Peso"),
    }

    metricas = {k: v for k, v in metricas.items() if k in df_calculo.columns}
    if not metricas:
        st.info(t("No hay métricas disponibles para mostrar evolución temporal."))
        return

    st.caption(
        t("Evolución temporal del promedio grupal por ronda de medición, con banda de dispersión mínima y máxima.")
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        metrica = st.selectbox(
            t("Selecciona la métrica"),
            options=list(metricas.keys()),
            format_func=lambda x: metricas[x],
            key="evolucion_temporal_metrica"
        )

    with col2:
        mostrar_rango = st.checkbox(
            t("Mostrar rango min-max"),
            value=True,
            key="evolucion_temporal_rango"
        )

    df = df_calculo.copy()
    df["fecha_medicion"] = pd.to_datetime(df["fecha_medicion"], errors="coerce")
    df[metrica] = pd.to_numeric(df[metrica], errors="coerce")
    df = df.dropna(subset=["fecha_medicion", metrica])

    if df.empty:
        st.info(t("No hay datos válidos para la métrica seleccionada."))
        return

    # Agrupar por bloques de medición (<= 7 días)
    df = asignar_bloques_medicion(df, gap_dias=7)

    df_stats = (
        df.groupby("bloque_medicion")[metrica]
        .agg(["mean", "min", "max", "count"])
        .reset_index()
        .sort_values("bloque_medicion")
    )

    if df_stats.empty:
        st.info(t("No hay suficientes datos agregados para construir la evolución temporal."))
        return

    # Etiquetas por rango de fechas de la ronda
    df_labels = (
        df.groupby("bloque_medicion")["fecha_medicion"]
        .agg(fecha_inicio="min", fecha_fin="max")
        .reset_index()
    )

    df_stats = df_stats.merge(df_labels, on="bloque_medicion", how="left")

    df_stats["label"] = df_stats.apply(
        lambda r: (
            r["fecha_inicio"].strftime("%d/%m")
            if r["fecha_inicio"].date() == r["fecha_fin"].date()
            else f"{r['fecha_inicio'].strftime('%d/%m')} - {r['fecha_fin'].strftime('%d/%m')}"
        ),
        axis=1
    )

    fig = go.Figure()

    if mostrar_rango:
        fig.add_trace(go.Scatter(
            x=df_stats["label"],
            y=df_stats["max"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
            name=t("Máximo"),
        ))

        fig.add_trace(go.Scatter(
            x=df_stats["label"],
            y=df_stats["min"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(74,111,191,0.12)",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
            name=t("Rango"),
        ))

    fig.add_trace(go.Scatter(
        x=df_stats["label"],
        y=df_stats["mean"],
        mode="lines+markers",
        line=dict(width=3, color="#4A6FBF"),
        marker=dict(size=7),
        name=t("Promedio grupal"),
        hovertemplate=(
            "<b>%{x}</b><br>"
            + metricas[metrica]
            + ": %{y:.2f}<extra></extra>"
        ),
    ))

    # Línea de referencia solo para métricas interpretativas
    ref_value = None
    ref_label = None

    if metrica == "ajuste_adiposa_pct":
        ref_value = 20
        ref_label = t("Límite óptimo")
    elif metrica == "ajuste_muscular_pct":
        ref_value = 40
        ref_label = t("Referencia mínima")
    elif metrica == "suma_6_pliegues_mm":
        ref_value = 70
        ref_label = t("Límite adecuado")
    elif metrica == "idx_musculo_oseo":
        ref_value = 3.5
        ref_label = t("Referencia mínima")

    if ref_value is not None:
        fig.add_hline(
            y=ref_value,
            line_dash="dot",
            line_color="#7F8C8D",
            annotation_text=ref_label,
            annotation_position="top left",
        )

    fig.update_layout(
        template="plotly_white",
        xaxis_title=t("Ronda de medición"),
        yaxis_title=metricas[metrica],
        height=430,
        showlegend=False,
        margin=dict(t=50, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(t("Cada punto representa una ronda completa de medición agrupada en ventanas de hasta 7 días."))

    # Resumen inferior
    inicio = df_stats["mean"].iloc[0]
    final = df_stats["mean"].iloc[-1]

    if pd.notna(inicio) and inicio != 0:
        delta_total = ((final - inicio) / inicio) * 100
    else:
        delta_total = 0

    n_rondas = len(df_stats)
    n_registros = int(df_stats["count"].sum())

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"- **{t('Inicio del periodo')}**: {inicio:.2f}  \n"
            f"- **{t('Final del periodo')}**: {final:.2f}  \n"
            f"- **{t('Cambio total')}**: {delta_total:+.2f}%"
        )

    with c2:
        st.markdown(
            f"- **{t('Rondas registradas')}**: {n_rondas}  \n"
            f"- **{t('Registros utilizados')}**: {n_registros}"
        )



def plot_ratios_estructurales(df: pd.DataFrame):
    """
    Distribución grupal de ratios estructurales usando la última medición
    disponible por jugadora.
    """

    if df is None or df.empty:
        st.info(t("No hay datos disponibles para mostrar ratios estructurales."))
        return

    df = filter_last_record_per_player(df).copy()

    required_any = [
        "perimetro_cintura_minima",
        "perimetro_cadera_maximo",
        "perimetro_muslo_maximo",
        "perimetro_pantorrilla_maxima",
        "envergadura_cm",
        "talla_corporal_cm",
        "talla_sentado_cm",
    ]

    if not any(c in df.columns for c in required_any):
        st.info(t("No hay variables estructurales suficientes para construir ratios."))
        return

    # Asegurar numéricos
    cols_num = [
        "perimetro_cintura_minima",
        "perimetro_cadera_maximo",
        "perimetro_muslo_maximo",
        "perimetro_pantorrilla_maxima",
        "envergadura_cm",
        "talla_corporal_cm",
        "talla_sentado_cm",
    ]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ratios
    if {"perimetro_cintura_minima", "perimetro_cadera_maximo"}.issubset(df.columns):
        df["ratio_cintura_cadera"] = (
            df["perimetro_cintura_minima"] / df["perimetro_cadera_maximo"]
        )

    if {"perimetro_muslo_maximo", "perimetro_pantorrilla_maxima"}.issubset(df.columns):
        df["ratio_muslo_pantorrilla"] = (
            df["perimetro_muslo_maximo"] / df["perimetro_pantorrilla_maxima"]
        )

    if {"envergadura_cm", "talla_corporal_cm"}.issubset(df.columns):
        df["ratio_envergadura_talla"] = (
            df["envergadura_cm"] / df["talla_corporal_cm"]
        )

    if {"talla_sentado_cm", "talla_corporal_cm"}.issubset(df.columns):
        df["ratio_tronco_altura"] = (
            df["talla_sentado_cm"] / df["talla_corporal_cm"]
        )

    ratios = {
        "ratio_cintura_cadera": t("Ratio cintura / cadera"),
        "ratio_muslo_pantorrilla": t("Ratio muslo / pantorrilla"),
        "ratio_envergadura_talla": t("Ratio envergadura / talla"),
        "ratio_tronco_altura": t("Ratio tronco / altura"),
    }

    ratios = {k: v for k, v in ratios.items() if k in df.columns and df[k].dropna().any()}

    if not ratios:
        st.info(t("No hay ratios estructurales válidos para mostrar."))
        return

    st.caption(
        t("Distribución grupal de ratios estructurales a partir de la última medición disponible de cada jugadora.")
    )

    c1, _ = st.columns([2, 6])

    with c1:
        ratio_sel = st.selectbox(
            t("Seleccione el ratio"),
            options=list(ratios.keys()),
            format_func=lambda x: ratios[x],
            key="ratio_estructural_selector"
        )

    data = (
        df[["nombre_jugadora", ratio_sel]]
        .dropna()
        .sort_values(ratio_sel)
        .copy()
    )

    if data.empty:
        st.info(t("No hay datos válidos para el ratio seleccionado."))
        return

    valores = pd.to_numeric(data[ratio_sel], errors="coerce")
    media = valores.mean()
    minimo = valores.min()
    maximo = valores.max()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data["nombre_jugadora"],
        y=valores,
        text=valores.map(lambda x: f"{x:.2f}"),
        textposition="outside",
        marker_color="#4A6FBF",
        hovertemplate=(
            "<b>%{x}</b><br>"
            + ratios[ratio_sel]
            + ": %{y:.2f}<extra></extra>"
        ),
    ))

    fig.add_hline(
        y=media,
        line_dash="dash",
        line_color="#27AE60",
        annotation_text=t("Promedio"),
        annotation_position="top left",
    )

    fig.update_layout(
        template="plotly_white",
        xaxis_title="",
        yaxis_title=ratios[ratio_sel],
        height=460,
        margin=dict(t=60, b=120),
        showlegend=False,
    )

    fig.update_xaxes(
        tickangle=-45,
        tickfont=dict(size=10),
    )

    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"- **{t('Promedio')}**: {media:.3f}  \n"
            f"- **{t('Mínimo')}**: {minimo:.3f}  \n"
            f"- **{t('Máximo')}**: {maximo:.3f}"
        )

    with c2:
        if ratio_sel == "ratio_cintura_cadera":
            st.markdown(
                f"""
                **{t('Lectura')}**

                🔽 **{t('Valores bajos')}**  
                {t('Menor cintura relativa respecto a la cadera, asociada a una distribución corporal más favorable.')}

                🔼 **{t('Valores altos')}**  
                {t('Mayor acumulación central o un perfil troncal más dominante.')}
                """
            )

        elif ratio_sel == "ratio_muslo_pantorrilla":
            st.markdown(
                f"""
                **{t('Lectura')}**

                🔽 **{t('Valores bajos')}**  
                {t('Perfil más equilibrado o menor predominio del muslo respecto a la pantorrilla.')}

                🔼 **{t('Valores altos')}**  
                {t('Mayor desarrollo relativo del muslo, asociado a producción de fuerza y potencia en el tren inferior.')}
                """
            )

        elif ratio_sel == "ratio_envergadura_talla":
            st.markdown(
                f"""
                **{t('Lectura')}**

                🔽 **{t('Valores bajos')}**  
                {t('Perfil más compacto con menor envergadura relativa respecto a la talla corporal.')}

                🔼 **{t('Valores altos')}**  
                {t('Mayor envergadura relativa, asociada a ventaja mecánica en alcance, cobertura y amplitud gestual.')}
                """
            )

        elif ratio_sel == "ratio_tronco_altura":
            st.markdown(
                f"""
                **{t('Lectura')}**

                🔽 **{t('Valores bajos')}**  
                {t('Mayor longitud relativa de piernas, asociada a ventajas en economía de carrera y amplitud de zancada.')}

                🔼 **{t('Valores altos')}**  
                {t('Mayor proporción de tronco, lo que puede influir en el centro de masas y la mecánica del movimiento.')}
                """
            )


def plot_mapa_estructural(
    df: pd.DataFrame,
    jugadora_destacada: str | None = None,
    mostrar_labels: bool = True,
):
    """
    Mapa estructural grupal / individual.

    Eje X: ratio envergadura / talla
    Eje Y: ratio muslo / pantorrilla

    Si se pasa jugadora_destacada, se muestra el grupo completo
    destacando esa jugadora.
    """

    required = {
        "nombre_jugadora",
        "envergadura_cm",
        "talla_corporal_cm",
        "perimetro_muslo_maximo",
        "perimetro_pantorrilla_maxima",
    }

    if df is None or df.empty or not required.issubset(df.columns):
        st.warning(t("No hay datos suficientes para generar el perfil estructural."))
        return

    df = filter_last_record_per_player(df).copy()

    df["x"] = (
        pd.to_numeric(df["envergadura_cm"], errors="coerce")
        / pd.to_numeric(df["talla_corporal_cm"], errors="coerce")
    )
    df["y"] = (
        pd.to_numeric(df["perimetro_muslo_maximo"], errors="coerce")
        / pd.to_numeric(df["perimetro_pantorrilla_maxima"], errors="coerce")
    )

    df = df.dropna(subset=["x", "y"])

    if df.empty:
        st.info(t("No hay valores válidos para el perfil estructural."))
        return

    # Cortes por media del grupo
    x_cut = df["x"].mean()
    y_cut = df["y"].mean()

    def cuadrante_estructural(row):
        x = row["x"]
        y = row["y"]

        if x >= x_cut and y >= y_cut:
            return pd.Series(["G1", "#2ECC71"])
        elif x < x_cut and y >= y_cut:
            return pd.Series(["G2", "#F1C40F"])
        elif x < x_cut and y < y_cut:
            return pd.Series(["G3", "#F39C12"])
        else:
            return pd.Series(["G4", "#E74C3C"])

    df[["grupo", "color"]] = df.apply(cuadrante_estructural, axis=1)

    df["label"] = df.apply(
        lambda r: f'{r["nombre_jugadora"].title()} ({r["x"]:.3f}; {r["y"]:.3f})',
        axis=1
    )

    # Destacada
    if jugadora_destacada is not None:
        df["es_destacada"] = df["nombre_jugadora"].astype(str) == str(jugadora_destacada)
    else:
        df["es_destacada"] = False

    # Labels
    if jugadora_destacada is None:
        cfg_labels = configurar_labels_perfil(df, key_prefix="perfil_estructural")
        df_labels = filtrar_df_labels(df, cfg_labels)
    else:
        df_labels = df[df["es_destacada"]].copy() if mostrar_labels else df.iloc[0:0].copy()

    fig = go.Figure()

    # Grupo base
    df_base = df[~df["es_destacada"]].copy()
    if not df_base.empty:
        fig.add_trace(go.Scatter(
            x=df_base["x"],
            y=df_base["y"],
            mode="markers",
            marker=dict(
                size=10,
                color=df_base["color"],
                line=dict(width=1, color="white"),
                opacity=0.55 if jugadora_destacada is not None else 1.0,
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                + t("Ratio envergadura / talla") + ": %{x:.3f}<br>"
                + t("Ratio muslo / pantorrilla") + ": %{y:.3f}<extra></extra>"
            ),
            customdata=df_base["label"],
            showlegend=False,
        ))

    # Jugadora destacada
    df_hi = df[df["es_destacada"]].copy()
    if not df_hi.empty:
        fig.add_trace(go.Scatter(
            x=df_hi["x"],
            y=df_hi["y"],
            mode="markers",
            marker=dict(
                size=16,
                color="#111827",
                line=dict(width=2, color="white"),
            ),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                + t("Ratio envergadura / talla") + ": %{x:.3f}<br>"
                + t("Ratio muslo / pantorrilla") + ": %{y:.3f}<extra></extra>"
            ),
            customdata=df_hi["label"],
            showlegend=False,
        ))

    # Anotaciones
    offset_index = 0
    for _, row in df_labels.iterrows():
        if needs_arrow(row, df):
            ax, ay = OFFSET_POSITIONS[offset_index % len(OFFSET_POSITIONS)]
            offset_index += 1

            fig.add_annotation(
                x=row["x"],
                y=row["y"],
                text=row["label"],
                showarrow=True,
                arrowhead=2,
                arrowwidth=1,
                arrowcolor="#424245",
                ax=ax,
                ay=ay,
                font=dict(size=9, color="#424245"),
                bgcolor="rgba(255,255,255,0)",
                borderpad=2,
            )
        else:
            fig.add_annotation(
                x=row["x"],
                y=row["y"],
                text=row["label"],
                showarrow=False,
                yshift=10,
                font=dict(size=9, color="#374151"),
            )

    fig.add_vline(x=x_cut, line_width=1.2, line_color="#9CA3AF")
    fig.add_hline(y=y_cut, line_width=1.2, line_color="#9CA3AF")

    x_min = df["x"].min() - 0.02
    x_max = df["x"].max() + 0.02
    y_min = df["y"].min() - 0.05
    y_max = df["y"].max() + 0.05

    fig.add_annotation(x=x_min + 0.01, y=y_max - 0.01, text="<b>G1</b>", showarrow=False)
    fig.add_annotation(x=x_max - 0.01, y=y_max - 0.01, text="<b>G2</b>", showarrow=False)
    fig.add_annotation(x=x_min + 0.01, y=y_min + 0.01, text="<b>G3</b>", showarrow=False)
    fig.add_annotation(x=x_max - 0.01, y=y_min + 0.01, text="<b>G4</b>", showarrow=False)

    titulo = (
        t("Perfil estructural individual dentro del grupo")
        if jugadora_destacada is not None
        else t("Perfil estructural grupal")
    )

    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.02,
            font=dict(size=18),
        ),
        xaxis=dict(
            title=t("Ratio envergadura / talla"),
            range=[x_min, x_max],
            gridcolor="#ECF0F1",
        ),
        yaxis=dict(
            title=t("Ratio muslo / pantorrilla"),
            range=[y_min, y_max],
            gridcolor="#ECF0F1",
        ),
        template="plotly_white",
        height=650,
        margin=dict(l=40, r=40, t=80, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretación
    if jugadora_destacada is None:
        counts = df["grupo"].value_counts()
        n_g1 = int(counts.get("G1", 0))
        n_g2 = int(counts.get("G2", 0))
        n_g3 = int(counts.get("G3", 0))
        n_g4 = int(counts.get("G4", 0))

        with st.expander(t("Interpretación del perfil estructural"), expanded=False):
            st.markdown(
                f"""
                <div style="line-height:1.6">

                <span style="color:#2ECC71;"><b>G1 · Mayor envergadura relativa y mayor desarrollo de tren inferior</b></span> → {n_g1} jugadoras<br>
                Perfil estructural favorable para acciones amplias y producción de fuerza en tren inferior.

                <span style="color:#F1C40F;"><b>G2 · Menor envergadura relativa y mayor desarrollo de tren inferior</b></span> → {n_g2} jugadoras<br>
                Perfil más compacto con predominio relativo del tren inferior.

                <span style="color:#F39C12;"><b>G3 · Menor envergadura relativa y menor desarrollo de tren inferior</b></span> → {n_g3} jugadoras<br>
                Perfil más ligero o menos dominante estructuralmente en ambos componentes.

                <span style="color:#E74C3C;"><b>G4 · Mayor envergadura relativa y menor desarrollo de tren inferior</b></span> → {n_g4} jugadoras<br>
                Perfil más longilíneo, con margen potencial de desarrollo en tren inferior.

                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        if not df_hi.empty:
            row = df_hi.iloc[0]
            grupo = row["grupo"]

            color_map = {
                "G1": "#2ECC71",
                "G2": "#F1C40F",
                "G3": "#F39C12",
                "G4": "#E74C3C",
            }
            color_grupo = color_map.get(grupo, "#34495E")

            st.markdown(
                f"""
                <div style="margin-top:8px; line-height:1.7;">
                    <b>{t('Zona actual')}:</b>
                    <span style="color:{color_grupo}; font-weight:700;">{grupo}</span>
                    · <b>{t('Ratio envergadura / talla')}:</b> {row['x']:.3f}
                    · <b>{t('Ratio muslo / pantorrilla')}:</b> {row['y']:.3f}
                </div>
                """,
                unsafe_allow_html=True
            )

            if grupo == "G1":
                texto = t("Perfil con mayor envergadura relativa y buen desarrollo de tren inferior. Compatible con una estructura favorable para amplitud gestual y producción de fuerza.")
            elif grupo == "G2":
                texto = t("Perfil más compacto, con predominio relativo del tren inferior. Puede asociarse a buena base de fuerza en una estructura menos longilínea.")
            elif grupo == "G3":
                texto = t("Perfil más ligero, con menor envergadura relativa y menor desarrollo del tren inferior. Puede existir margen de mejora estructural y funcional.")
            else:
                texto = t("Perfil más longilíneo, con menor desarrollo relativo del tren inferior. El foco puede estar en reforzar la base estructural y la capacidad de fuerza.")

            st.markdown(
                f"""
                <div style="margin-top:6px; line-height:1.7;">
                    <b style="color:{color_grupo};">{t('Interpretación')}:</b> {texto}
                </div>
                """,
                unsafe_allow_html=True
            )

