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
    st.caption(
        t("Distribución individual del grupo con valores mínimo, máximo y promedio.")
    )

    metricas = {
        k: v for k, v in METRICAS_DISTRIBUCION.items()
        if k in df.columns and df[k].dropna().any()
    }

    if not metricas:
        st.info(t("No hay métricas disponibles."))
        return

    col1, col2 = st.columns([2, 6])

    with col1:
        col = st.selectbox(
            t("Seleccione la métrica"),
            options=list(metricas.keys()),
            format_func=lambda x: metricas[x],
        )

    # -------------------------
    # Datos
    # -------------------------
    data = (
        df[["nombre_jugadora", col]]
        .dropna()
        .sort_values(col)
    )

    valores = pd.to_numeric(data[col], errors="coerce")

    media = valores.mean()
    minimo = valores.min()
    maximo = valores.max()

    # -------------------------
    # Gráfico
    # -------------------------
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=data["nombre_jugadora"],
        y=valores,
        text=valores.map(lambda x: f"{x:.1f}"),
        textposition="outside",
        marker_color="#4A6FBF",
    ))

    # Línea de promedio
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
        yaxis_title=metricas[col],
        height=450,
        margin=dict(t=60, b=120),
        showlegend=False,
    )

    fig.update_xaxes(
        tickangle=-45,
        tickfont=dict(size=10),
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Resumen textual (como PDF)
    # -------------------------
    st.markdown(
        f"""
        **{metricas[col]}**

        - **{t("Promedio")}**: {media:.2f}  
        - **{t("Mínimo")}**: {minimo:.2f}  
        - **{t("Máximo")}**: {maximo:.2f}
        """
    )

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
            imo=("idx_musculo_oseo", "mean"),
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

##########################

def get_interpretacion():

    with st.expander(t("Interpretación del perfil antropométrico"), expanded=False):

        st.markdown(
            f"""
            <div style="line-height:1.6">

            <span style="color:#2ECC71;"><b>G1 · Alto en músculo / Bajo en grasa</b></span><br>
            Perfil corporal óptimo para el rendimiento deportivo. Se asocia a una mayor eficiencia mecánica,
            buena potencia relativa y menor lastre corporal.

            <span style="color:#F1C40F;"><b>G2 · Alto en músculo / Alto en grasa</b></span><br>
            Buen desarrollo muscular con margen de mejora en la composición corporal.
            Existe potencial de optimización reduciendo masa grasa sin comprometer la masa muscular.

            <span style="color:#F39C12;"><b>G3 · Bajo en músculo / Bajo en grasa</b></span><br>
            Perfil corporal ligero con posible déficit estructural.
            Puede limitar la producción de fuerza y la tolerancia a contactos, siendo recomendable un trabajo
            orientado al desarrollo muscular.

            <span style="color:#E74C3C;"><b>G4 · Bajo en músculo / Alto en grasa</b></span><br>
            Perfil menos favorable para el rendimiento físico.
            Puede afectar a la eficiencia del movimiento y aumentar el lastre corporal,
            siendo prioritaria la intervención desde el entrenamiento y la nutrición.

            </div>
            """,
            unsafe_allow_html=True
        )

def configurar_labels_perfil(df: pd.DataFrame) -> dict:
    """
    Devuelve la configuración seleccionada para mostrar etiquetas.
    """
    with st.expander(t(":material/settings: Opciones avanzadas de etiquetas"), expanded=False):

        col1, col2, _ = st.columns([1.2, 2, 2])

        with col1:
            modo = st.selectbox(
                t("Configuración de etiquetas"),
                options=[
                    "Mostrar Todas",
                    "Por cuadrante",
                    "Seleccionar Jugadoras",
                    "Ocultar todas",
                ],
                index=0,
            )

        cuadrantes = []
        jugadoras = []

        with col2:
            if modo == "Por cuadrante":
                cuadrantes = st.multiselect(
                    t("Cuadrantes"),
                    options=["G1", "G2", "G3", "G4"],
                    default=["G1"],
                )

            elif modo == "Seleccionar Jugadoras":
                jugadoras = st.multiselect(
                    t("Jugadoras"),
                    options=sorted(df["nombre_jugadora"].unique()),
                    placeholder=t("Seleccione jugadoras para mostrar etiquetas"),
                )

    return {
        "modo": modo,
        "cuadrantes": cuadrantes,
        "jugadoras": jugadoras,
    }

def filtrar_df_labels(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    modo = cfg["modo"]

    if modo == "Ocultar todas":
        return df.iloc[0:0]

    if modo == "Todas":
        return df

    if modo == "Por cuadrante":
        return df[df["grupo"].isin(cfg["cuadrantes"])]

    if modo == "Seleccionar Jugadoras":
        return df[df["nombre_jugadora"].isin(cfg["jugadoras"])]

    return df

def plot_perfil_antropometrico(df: pd.DataFrame):

    if not REQUIRED.issubset(df.columns):
        st.warning(t("No hay datos suficientes para generar el perfil antropométrico."))
        return

    # --------------------------------------------------
    # FILTRO: ÚLTIMO REGISTRO POR JUGADORA
    # --------------------------------------------------
    #st.dataframe(df[["identificacion", "nombre_jugadora", "fecha_sesion"]], hide_index=True)
    df = filter_last_record_per_player(df)
    #st.text("Último registro por jugadora:")
    #st.dataframe(df[["identificacion", "nombre_jugadora", "fecha_sesion"]], hide_index=True)

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

    # --------------------------------------------------
    # CONFIGURACIÓN DE ETIQUETAS (UI)
    # --------------------------------------------------
    cfg_labels = configurar_labels_perfil(df)
    df_labels = filtrar_df_labels(df, cfg_labels)

    # --------------------------------------------------
    # FIGURA
    # --------------------------------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["x"],
        y=df["y"],
        mode="markers",
        marker=dict(
            size=10,
            color=df["color"],
            line=dict(width=1, color="white"),
        ),
        hovertemplate=(
            "<b>%{customdata}</b><br>"
            + t("Suma 6 pliegues") + ": %{x:.1f} mm<br>"
            + t("Índice músculo/óseo") + ": %{y:.2f}<extra></extra>"
        ),
        customdata=df["label"],
        showlegend=False,
    ))

    # --------------------------------------------------
    # ANOTACIONES
    # --------------------------------------------------
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

    # --------------------------------------------------
    # ELEMENTOS FIJOS
    # --------------------------------------------------
    fig.add_vline(x=X_CORTE, line_width=1.2, line_color="#9CA3AF")
    fig.add_hline(y=Y_CORTE, line_width=1.2, line_color="#9CA3AF")

    fig.add_annotation(x=40,  y=4.4, text="<b>G1</b>", showarrow=False)
    fig.add_annotation(x=115, y=4.4, text="<b>G2</b>", showarrow=False)
    fig.add_annotation(x=40,  y=3.3, text="<b>G3</b>", showarrow=False)
    fig.add_annotation(x=115, y=3.3, text="<b>G4</b>", showarrow=False)

    y_min = min(Y_MIN, df["y"].min() - 0.1)
    y_max = max(Y_MAX, df["y"].max() + 0.1)

    fig.update_layout(
        title=dict(
            text=t("Perfil antropométrico grupal"),
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

    get_interpretacion()


# def plot_perfil_antropometrico(df: pd.DataFrame):

#     if not REQUIRED.issubset(df.columns):
#         st.warning(t("No hay datos suficientes para generar el perfil antropométrico."))
#         return

#     df = df.copy()
#     df["x"] = pd.to_numeric(df["suma_6_pliegues_mm"], errors="coerce")
#     df["y"] = pd.to_numeric(df["idx_musculo_oseo"], errors="coerce")
#     df = df.dropna(subset=["x", "y"])

#     #st.dataframe(df["idx_musculo_oseo"])

#     if df.empty:
#         st.info(t("No hay valores válidos para el perfil antropométrico."))
#         return

#     df[["grupo", "color"]] = df.apply(
#         lambda r: pd.Series(cuadrante(r)), axis=1
#     )

#     # Label final
#     df["label"] = df.apply(
#         lambda r: f'{r["nombre_jugadora"].title()} ({r["x"]:.1f}; {r["y"]:.2f})',
#         axis=1
#     )

#     # st.write(
#     #     df[["nombre_jugadora", "x", "y"]]
#     # )
#     # -------------------------
#     # FIGURA
#     # -------------------------
#     fig = go.Figure()

#     # --- SOLO puntos ---
#     fig.add_trace(go.Scatter(
#         x=df["x"],
#         y=df["y"],
#         mode="markers",
#         marker=dict(
#             size=10,
#             color=df["color"],
#             line=dict(width=1, color="white"),
#         ),
#         hovertemplate=(
#             "<b>%{customdata}</b><br>"
#             + t("Suma 6 pliegues") + ": %{x:.1f} mm<br>"
#             + t("Índice músculo/óseo") + ": %{y:.2f}<extra></extra>"
#         ),
#         customdata=df["label"],
#         showlegend=False,
#     ))


#     offset_index = 0

#     for _, row in df.iterrows():

#         if needs_arrow(row, df):
#             ax, ay = OFFSET_POSITIONS[offset_index % len(OFFSET_POSITIONS)]
#             offset_index += 1

#             fig.add_annotation(
#                 x=row["x"],
#                 y=row["y"],
#                 text=row["label"],
#                 showarrow=True,
#                 arrowhead=2,
#                 arrowwidth=1,
#                 arrowcolor="#424245",
#                 ax=ax,
#                 ay=ay,
#                 font=dict(size=9, color="#424245"),
#                 bgcolor="rgba(255,255,255,0)",
#                 borderpad=2,
#             )
#         else:
#             fig.add_annotation(
#                 x=row["x"],
#                 y=row["y"],
#                 text=row["label"],
#                 showarrow=False,
#                 yshift=10,
#                 font=dict(size=9, color="#374151"),
#             )

#     # -------------------------
#     # LÍNEAS DE CORTE
#     # -------------------------
#     fig.add_vline(x=X_CORTE, line_width=1.2, line_color="#9CA3AF")
#     fig.add_hline(y=Y_CORTE, line_width=1.2, line_color="#9CA3AF")

#     # -------------------------
#     # ETIQUETAS DE CUADRANTE
#     # -------------------------
#     fig.add_annotation(x=40,  y=4.4, text="<b>G1</b>", showarrow=False)
#     fig.add_annotation(x=115, y=4.4, text="<b>G2</b>", showarrow=False)
#     fig.add_annotation(x=40,  y=3.3, text="<b>G3</b>", showarrow=False)
#     fig.add_annotation(x=115, y=3.3, text="<b>G4</b>", showarrow=False)

#     y_min = min(Y_MIN, df["y"].min() - 0.1)
#     y_max = max(Y_MAX, df["y"].max() + 0.1)
#     # -------------------------
#     # ESTILO GENERAL
#     # -------------------------
#     fig.update_layout(
#         title=dict(
#             text=t("Perfil antropométrico grupal"),
#             x=0.02,
#             font=dict(size=18),
#         ),
#         xaxis=dict(
#             title=t("Suma 6 pliegues (mm)"),
#             range=[X_MIN, X_MAX],
#             gridcolor="#ECF0F1",
#         ),
#         yaxis=dict(
#             title=t("Índice músculo / óseo"),
#             range=[y_min, y_max],
#             gridcolor="#ECF0F1",
#         ),
#         template="plotly_white",
#         height=650,
#         margin=dict(l=40, r=40, t=80, b=40),
#     )

#     st.plotly_chart(fig, use_container_width=True)

#     get_interpretacion()
