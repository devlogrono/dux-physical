import streamlit as st
import pandas as pd
from datetime import date, timedelta

from modules.app_config.styles import template_COLOR_NORMAL, template_COLOR_INVERTIDO, get_color_template
from modules.util.util import ordenar_df
from modules.i18n.i18n import t

W_COLS = ["recuperacion", "energia", "sueno", "stress", "dolor"]

# ============================================================
# ⚙️ FUNCIONES BASE
# ============================================================

def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out

def compute_player_template_means(df_in_period_checkin: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve por nombre_jugadora:
      - prom_w_1_5: promedio (1-5) de las 5 variables template
      - dolor_mean: promedio de dolor (1-5)
      - en_riesgo: bool con la lógica consensuada (escala 1 = mejor, 5 = peor)
    Solo usa registros tipo 'checkin' del periodo filtrado.
    """
    if df_in_period_checkin.empty:
        return pd.DataFrame(columns=["nombre_jugadora", "prom_w_1_5", "dolor_mean", "en_riesgo"])

    df = df_in_period_checkin.copy()
    df = _coerce_numeric(df, W_COLS)  # W_COLS = ["recuperacion","energia","sueno","stress","dolor"]

    g = df.groupby("nombre_jugadora", as_index=False)[W_COLS].mean(numeric_only=True)
    g["prom_w_1_5"] = g[W_COLS].mean(axis=1, skipna=True)
    g["dolor_mean"] = g["dolor"]

    # 🔴 Riesgo con escala actual: 1 = mejor, 5 = peor
    g["en_riesgo"] = (g["prom_w_1_5"] > 3) | (g["dolor_mean"] > 3)

    return g[["nombre_jugadora", "prom_w_1_5", "dolor_mean", "en_riesgo"]]

# ============================================================
# 📅 GESTIÓN DE PERIODOS
# ============================================================

# def get_default_period(df: pd.DataFrame) -> str:

#     hoy = date.today()
#     dias_disponibles = df["fecha_dia"].unique()
#     if hoy in dias_disponibles:
#         return "Hoy"
#     elif (hoy - timedelta(days=1)) in dias_disponibles:
#         return "Último día"
#     elif any((hoy - timedelta(days=i)) in dias_disponibles for i in range(2, 8)):
#         return "Semana"
#     else:
#         return "Mes"

def filter_df_by_period(df: pd.DataFrame, periodo: str):
    """
    Filtro de periodos adaptado a antropometría:
    - Última sesión: última medición por jugadora
    - Histórico: últimos 6 meses
    """

    if df.empty:
        return df.copy(), ""

    df = df.copy()

    # -------------------------
    # Normalizar fecha_medicion
    # -------------------------
    df["fecha_medicion"] = pd.to_datetime(
        df["fecha_medicion"],
        errors="coerce"
    )

    df = df.dropna(subset=["fecha_medicion"])

    if df.empty:
        return df.copy(), ""

    # -------------------------
    # Lógica de filtrado
    # -------------------------
    if periodo == "Última sesión":
        df_sorted = df.sort_values("fecha_medicion")
        df_filtrado = (
            df_sorted
            .groupby("identificacion", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )
        texto = t("última sesión")

    else:  # Histórico (6 meses)
        fecha_max = df["fecha_medicion"].max()
        limite = fecha_max - pd.Timedelta(days=180)

        df_filtrado = df[
            df["fecha_medicion"] >= limite
        ].copy()

        texto = t("últimos 6 meses")

    # -------------------------
    # Orden final
    # -------------------------
    df_filtrado = df_filtrado.sort_values(
        by="fecha_medicion", ascending=False
    ).reset_index(drop=True)

    # Limpieza segura
    df_filtrado.drop(columns=["id"], errors="ignore", inplace=True)

    return df_filtrado, texto


# ============================================================
# 📈 FUNCIONES AUXILIARES
# ============================================================

def calc_delta(values):
    if len(values) < 2 or values[-2] == 0:
        return 0
    return round(((values[-1] - values[-2]) / values[-2]) * 100, 1)


def calc_trend(df, by_col, target_col, agg="mean"):
    if agg == "sum":
        g = df.groupby(by_col)[target_col].sum().reset_index(name="valor")
    else:
        g = df.groupby(by_col)[target_col].mean().reset_index(name="valor")
    return g.sort_values(by_col)["valor"].tolist()


def calc_metric_block(df_visual: pd.DataFrame, df_calculo: pd.DataFrame, periodo: str, var: str, agg="mean"):
    """
    KPI antropométrico grupal.

    Valor principal:
    - Última sesión: media del último registro por jugadora en df_visual
    - Historico: media de la media por jugadora en df_visual

    Tendencia:
    - Última sesión: última vs anterior por jugadora usando df_calculo
    - Historico: última vs primera del periodo usando df_visual
    """

    if df_visual is None or df_visual.empty or var not in df_visual.columns:
        return 0, [0, 0], 0

    def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if "fecha_medicion" not in out.columns:
            return pd.DataFrame()

        out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")
        if "created_at" in out.columns:
            out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")

        out = out.dropna(subset=["fecha_medicion"])
        if out.empty:
            return pd.DataFrame()

        out[var] = pd.to_numeric(out[var], errors="coerce")
        return out

    dfv = _prepare_df(df_visual)
    if dfv.empty:
        return 0, [0, 0], 0

    id_col = "identificacion" if "identificacion" in dfv.columns else "nombre_jugadora"
    if id_col not in dfv.columns:
        return 0, [0, 0], 0

    sort_cols = [id_col, "fecha_medicion"]
    ascending_desc = [True, False]
    ascending_asc = [True, True]

    if "created_at" in dfv.columns:
        sort_cols.append("created_at")
        ascending_desc.append(False)
        ascending_asc.append(True)

    if "id_isak" in dfv.columns:
        sort_cols.append("id_isak")
        ascending_desc.append(False)
        ascending_asc.append(True)

    # =========================
    # 1) VALOR PRINCIPAL
    # =========================
    if periodo == "Última sesión":
        df_valor = (
            dfv.sort_values(sort_cols, ascending=ascending_desc)
               .groupby(id_col, as_index=False)
               .head(1)
               .reset_index(drop=True)
        )
    else:
        keep_cols = [id_col]
        if "nombre_jugadora" in dfv.columns:
            keep_cols.append("nombre_jugadora")

        df_valor = (
            dfv.groupby(keep_cols, as_index=False)[var]
               .mean()
               .reset_index(drop=True)
        )

    serie_valor = pd.to_numeric(df_valor[var], errors="coerce").dropna()
    valor = round(serie_valor.mean(), 1) if not serie_valor.empty else 0

    # =========================
    # 2) TENDENCIA
    # =========================
    if periodo == "Última sesión":
        if df_calculo is None or df_calculo.empty or var not in df_calculo.columns:
            return valor, [valor, valor], 0

        dfc = _prepare_df(df_calculo)
        if dfc.empty:
            return valor, [valor, valor], 0

        id_col_calc = "identificacion" if "identificacion" in dfc.columns else "nombre_jugadora"
        if id_col_calc not in dfc.columns:
            return valor, [valor, valor], 0

        sort_cols_calc = [id_col_calc, "fecha_medicion"]
        ascending_desc_calc = [True, False]

        if "created_at" in dfc.columns:
            sort_cols_calc.append("created_at")
            ascending_desc_calc.append(False)

        if "id_isak" in dfc.columns:
            sort_cols_calc.append("id_isak")
            ascending_desc_calc.append(False)

        df_cmp = dfc[[c for c in [id_col_calc, "nombre_jugadora", "fecha_medicion", "created_at", "id_isak", var] if c in dfc.columns]].copy()
        df_cmp = df_cmp.dropna(subset=[var])
        df_cmp = df_cmp.sort_values(sort_cols_calc, ascending=ascending_desc_calc)
        df_cmp["rank_medicion"] = df_cmp.groupby(id_col_calc).cumcount() + 1

        df_curr = df_cmp[df_cmp["rank_medicion"] == 1].copy()
        df_prev = df_cmp[df_cmp["rank_medicion"] == 2].copy()

        df_curr = df_curr[[id_col_calc, var]].rename(columns={var: "valor_curr"})
        df_prev = df_prev[[id_col_calc, var]].rename(columns={var: "valor_prev"})

        df_cmp2 = df_curr.merge(df_prev, on=id_col_calc, how="inner")

    else:
        # Histórico: última vs primera del periodo visual
        df_cmp = dfv[[c for c in [id_col, "nombre_jugadora", "fecha_medicion", "created_at", "id_isak", var] if c in dfv.columns]].copy()
        df_cmp = df_cmp.dropna(subset=[var])

        df_curr = (
            df_cmp.sort_values(sort_cols, ascending=ascending_desc)
                  .groupby(id_col, as_index=False)
                  .head(1)
                  .copy()
        )

        df_prev = (
            df_cmp.sort_values(sort_cols, ascending=ascending_asc)
                  .groupby(id_col, as_index=False)
                  .head(1)
                  .copy()
        )

        df_curr = df_curr[[id_col, var]].rename(columns={var: "valor_curr"})
        df_prev = df_prev[[id_col, var]].rename(columns={var: "valor_prev"})

        df_cmp2 = df_curr.merge(df_prev, on=id_col, how="inner")

    if df_cmp2.empty:
        return valor, [valor, valor], 0

    df_cmp2["valor_prev"] = pd.to_numeric(df_cmp2["valor_prev"], errors="coerce")
    df_cmp2["valor_curr"] = pd.to_numeric(df_cmp2["valor_curr"], errors="coerce")
    df_cmp2 = df_cmp2.dropna(subset=["valor_prev", "valor_curr"])

    if df_cmp2.empty:
        return valor, [valor, valor], 0

    media_prev = df_cmp2["valor_prev"].mean()
    media_curr = df_cmp2["valor_curr"].mean()

    chart = [float(media_prev), float(media_curr)]

    if media_prev == 0 or pd.isna(media_prev):
        delta = 0
    else:
        delta = ((media_curr - media_prev) / media_prev) * 100

    return valor, chart, delta

def calc_alertas(df_periodo: pd.DataFrame, df_completo: pd.DataFrame, periodo: str):
    """
    Calcula el número y porcentaje de jugadoras en riesgo dentro del periodo seleccionado.

    ✔️ Compatible con el nuevo modelo donde 'checkout' sobrescribe 'checkin'.
    ✔️ Usa compute_player_template_means(df_periodo) para coherencia global.
    """

    if df_periodo.empty:
        return 0, 0, 0, [], 0

    # --- Si existen registros tipo 'checkin', los usamos, de lo contrario todo el periodo ---
    if "tipo" in df_periodo.columns:
        df_in = df_periodo[df_periodo["tipo"].str.lower() == "checkin"].copy()
    else:
        df_in = pd.DataFrame()

    # En el modelo actual, el checkout reemplaza el checkin → fallback a todo el periodo
    base_df = df_in if not df_in.empty else df_periodo.copy()

    # --- Calcular riesgo global coherente ---
    try:
        riesgo_df = compute_player_template_means(base_df)
        if riesgo_df.empty or "en_riesgo" not in riesgo_df.columns:
            alertas_count = 0
            total_jugadoras = len(base_df["identificacion"].unique())
        else:
            alertas_count = int(riesgo_df["en_riesgo"].sum())
            total_jugadoras = int(riesgo_df.shape[0])
    except Exception as e:
        st.warning(f"No se pudo calcular el riesgo: {e}")
        alertas_count = 0
        total_jugadoras = len(base_df["identificacion"].unique())

    alertas_pct = round((alertas_count / total_jugadoras) * 100, 1) if total_jugadoras > 0 else 0

    # --- Simulación de 'chart' y 'delta' para compatibilidad con render_metric_cards ---
    chart_alertas = [alertas_pct]
    delta_alertas = 0

    return alertas_count, total_jugadoras, alertas_pct, chart_alertas, delta_alertas




def mostrar_resumen_tecnico(template_prom: float, rpe_prom: float, ua_total: float,
                            alertas_count: int, total_jugadoras: int):
    """
    Muestra en pantalla el resumen técnico del grupo, con interpretación automática
    del estado de bienestar, esfuerzo percibido y riesgo de alerta.
    """

    # 🟢 Estado de bienestar (escala 25)
    estado_bienestar = (
        t("óptimo") if template_prom > 20 else
        t("moderado") if template_prom >= 15 else
        t("en fatiga")
    )

    # 🟡 Nivel de esfuerzo percibido (RPE)
    if pd.isna(rpe_prom) or rpe_prom == 0:
        nivel_rpe = t("sin datos")
    elif rpe_prom < 5:
        nivel_rpe = t("bajo")
    elif rpe_prom <= 7:
        nivel_rpe = t("moderado")
    else:
        nivel_rpe = t("alto")

    # 🔴 Estado de alertas
    if alertas_count == 0:
        estado_alertas = t("sin jugadoras en zona roja")
    elif alertas_count == 1:
        estado_alertas = t("1 jugadora en seguimiento")
    else:
        estado_alertas = f"{alertas_count} {t('jugadoras en zona roja')}"

    # 🧾 Resumen técnico mostrado en Streamlit
    st.markdown(
        f":material/description: **{t('Resumen técnico')}:** "
        f"{t('El grupo muestra un estado de bienestar')} **{estado_bienestar}** "
        f"({template_prom}/25) "
        f"{t('con un esfuerzo percibido')} **{nivel_rpe}** (RPE {rpe_prom}). "
        f"{t('La carga interna total es de')} **{ua_total} UA** "
        f"{t('y actualmente hay')} **{estado_alertas}**, "
        f"{t('debido a que el promedio de bienestar x 5 es menor a 15 puntos')} "
        f"{t('(escala 25)')}, "
        f"{t('indicando fatiga, sobrecarga o molestias significativas que aumentan el riesgo de lesión o bajo rendimiento')}."
    )


def show_interpretation(template_prom, rpe_prom, ua_total, alertas_count, alertas_pct, delta_ua, total_jugadoras):
    # --- INTERPRETACIÓN VISUAL Y BRIEFING ---

    # === Generar tabla interpretativa ===
    interpretacion_data = [
        {
            t("Métrica"): t("Índice de Bienestar Promedio"),
            t("Valor"): f"{template_prom if not pd.isna(template_prom) else 0}/25",
            t("Interpretación"): (
                t("🟢 Óptimo (>20): El grupo mantiene un estado físico y mental adecuado. ") if template_prom > 20 else
                t("🟡 Moderado (15-19): Existen signos leves de fatiga o estrés. ") if 15 <= template_prom <= 19 else
                t("🔴 Alerta (<15): El grupo muestra fatiga o malestar significativo. ")
            )
        },
        {
            t("Métrica"): t("RPE Promedio"),
            t("Valor"): f"{rpe_prom if not pd.isna(rpe_prom) else 0}",
            t("Interpretación"): (
                t("🟢 Controlado (<6): El esfuerzo percibido está dentro de los rangos esperados. ") if rpe_prom < 6 else
                t("🟡 Medio (6-7): Carga elevada, pero dentro de niveles aceptables. ") if 6 <= rpe_prom <= 7 else
                t("🔴 Alto (>7): Percepción de esfuerzo muy alta. ")
            )
        },
        {
            t("Métrica"): t("Carga Total (UA)"),
            t("Valor"): f"{ua_total}",
            t("Interpretación"): (
                t("🟢 Estable: La carga total se mantiene dentro de los márgenes planificados. ") if abs(delta_ua) < 10 else
                t("🟡 Variación moderada (10-20%): Ajustes leves de carga detectados. ") if 10 <= abs(delta_ua) <= 20 else
                t("🔴 Variación fuerte (>20%): Aumento o descenso brusco de la carga. ")
            )
        },
        {
            t("Métrica"): t("Jugadoras en Zona Roja"),
            t("Valor"): f"{alertas_count}/{total_jugadoras} ({alertas_pct}%)",
            t("Interpretación"): (
                t("🟢 Grupo estable: Ninguna jugadora muestra indicadores de riesgo. ") if alertas_pct == 0 else
                t("🟡 Seguimiento leve (<15%): Algunas jugadoras presentan fatiga o molestias leves. ") if alertas_pct <= 15 else
                t("🔴 Riesgo elevado (>15%): Varios casos de fatiga o dolor detectados. ")
            )
        }
    ]

    with st.expander(t("Interpretación de las métricas")):
        df_interpretacion = pd.DataFrame(interpretacion_data)
        df_interpretacion[t("Interpretación")] = df_interpretacion[t("Interpretación")].str.replace("\n", "<br>")
        #st.markdown("**Interpretación de las métricas**")
        st.dataframe(df_interpretacion, hide_index=True)

        st.caption(
        t("🟢 / 🔴 Los colores en los gráficos muestran *variaciones* respecto al periodo anterior "
        "(🔺 sube, 🔻 baja). Los colores en la interpretación reflejan *niveles fisiológicos* "
        "según umbrales deportivos.")
    )


# ============================================================
# 📋 TABLA RESUMEN DEL PERIODO
# ============================================================

def generar_resumen_periodo(df: pd.DataFrame):
    """
    Tabla resumen del periodo (sin separar por tipo),
    manteniendo cálculo de riesgo y colores de template.
    """

    # --- Asegurar tipos numéricos ---
    df_periodo = df.copy()

    if df_periodo.empty:
        st.info("No hay registros disponibles en este periodo.")
        return

    # ======================================================
    # 🧱 Base y preprocesamiento
    # ======================================================
    #df_periodo["Jugadora"] = (
    #    df_periodo["nombre"].fillna("") + " " + df_periodo["apellido"].fillna("")
    #).str.strip()

    cols_template = ["recuperacion", "energia", "sueno", "stress", "dolor"]

    # --- Asegurar tipos numéricos ---
    for c in cols_template + ["rpe", "ua"]:
        if c in df_periodo.columns:
            df_periodo[c] = pd.to_numeric(df_periodo[c], errors="coerce")

    # --- Promedios generales por jugadora ---
    resumen = (
        df_periodo.groupby("nombre_jugadora", as_index=False)
        .agg({
            "recuperacion": "mean",
            "energia": "mean",
            "sueno": "mean",
            "stress": "mean",
            "dolor": "mean",
            "rpe": "mean",
            "ua": "mean",
        })
        .rename(columns={
            "recuperacion": "Recuperación",
            "energia": "Energía",
            "sueno": "Sueño",
            "stress": "Estrés",
            "dolor": "Dolor",
            "rpe": "RPE_promedio",
            "ua": "UA_total",
        })
        .infer_objects(copy=False)
    )

    # --- Añadir columnas de conteo ---
    registros_por_jugadora = (
        df_periodo.groupby("nombre_jugadora", as_index=False)
        .agg(Registros_periodo=("fecha_medicion", "count"))
    )

    dias_periodo = df_periodo["fecha_medicion"].nunique()
    registros_por_jugadora["Dias_periodo"] = dias_periodo

    # Unir al resumen
    resumen = resumen.merge(registros_por_jugadora, on="nombre_jugadora", how="left")

    # Crear columna combinada tipo "15 / 15"
    resumen["Registros/Días"] = (
        resumen["Registros_periodo"].astype(int).astype(str) + " / " + resumen["Dias_periodo"].astype(int).astype(str)
    )

    columna = resumen.pop("Registros/Días")       # Extrae la columna
    resumen.insert(1, "Registros/Días", columna)  # La inserta en la posición 1

    # Eliminar columnas intermedias si no quieres mostrarlas
    resumen.drop(columns=["Registros_periodo", "Dias_periodo"], inplace=True)

    # --- Calcular Promedio template (1–5) ---
    resumen["Promedio_template"] = resumen[
        ["Recuperación", "Energía", "Sueño", "Estrés", "Dolor"]
    ].mean(axis=1, skipna=True)

    # ======================================================
    # Cálculo de riesgo coherente con compute_player_template_means
    # ======================================================
    try:
        riesgo_df = compute_player_template_means(df_periodo)
        if "en_riesgo" in riesgo_df.columns:
            resumen = pd.merge(resumen, riesgo_df[["nombre_jugadora", "en_riesgo"]],
                               on="nombre_jugadora", how="left")
            resumen["En_riesgo"] = resumen["en_riesgo"].fillna(False)
            resumen.drop(columns=["en_riesgo"], inplace=True)
        else:
            resumen["En_riesgo"] = False
    except Exception as e:
        st.warning(f"No se pudo calcular el riesgo: {e}")
        resumen["En_riesgo"] = False

    resumen["En_riesgo"] = resumen["En_riesgo"].apply(lambda x: "Sí" if x else "No")

    resumen = resumen.fillna(0) 
    resumen.index = resumen.index + 1

    # ======================================================
    # 🎨 Colores y estilos
    # ======================================================
    def color_por_variable(col):
        if col.name not in ["Recuperación", "Energía", "Sueño", "Estrés", "Dolor"]:
            return [""] * len(col)
        #cmap = template_COLOR_INVERTIDO if col.name in ["Estrés", "Dolor"] else template_COLOR_NORMAL
        return [
            f"background-color:{get_color_template(v, col.name)}; color:white; text-align:center; font-weight:bold;"
            if pd.notna(v) else ""
            for v in col
        ]

    def color_promedios(col):
        return [
            # 1-2 = bueno
            "background-color:#27AE60; color:white; text-align:center; font-weight:bold;"
                if pd.notna(v) and v < 3 else

            # 3 = medio
            "background-color:#F1C40F; color:black; text-align:center; font-weight:bold;"
                if pd.notna(v) and v == 3 else

            # 4-5 = malo
            "background-color:#E74C3C; color:white; text-align:center; font-weight:bold;"
                if pd.notna(v) and v > 3 else

            ""
            for v in col
        ]

    def color_rpe_ua(col):
        return [
            "background-color:#27AE60; color:white; text-align:center; font-weight:bold;" if pd.notna(v) and v < 5 else
            "background-color:#F1C40F; color:black; text-align:center; font-weight:bold;" if pd.notna(v) and 5 <= v < 7 else
            "background-color:#E74C3C; color:white; text-align:center; font-weight:bold;" if pd.notna(v) and v >= 7 else
            ""
            for v in col
        ]

    def color_riesgo(col):
        return [
            "background-color:#E53935; color:white; text-align:center; font-weight:bold;"  # rojo fuerte
                if v == "Sí" else
            "background-color:#27AE60; color:white; text-align:center; font-weight:bold;"  # verde
                if v == "No" else
            ""
            for v in col
        ]


    # ======================================================
    # Mostrar tabla final
    # ======================================================
    resumen = resumen.rename(columns={
        "nombre_jugadora": t("Jugadora"),
        "Registros/Días": t("Registros/Días"),
        "Recuperación": t("Recuperación"),
        "Energía": t("Energía"),
        "Sueño": t("Sueño"),
        "Estrés": t("Estrés"),
        "Dolor": t("Dolor"),
        "Promedio_template": t("Promedio template"),
        "RPE_promedio": t("RPE promedio"),
        "UA_total": t("UA total"),
        "En_riesgo": t("En riesgo")
    })

    styled = (
        resumen.style
        .apply(color_por_variable, subset=[t("Recuperación"), t("Energía"), t("Sueño"), t("Estrés"), t("Dolor")])
        .apply(color_promedios, subset=[t("Promedio template")])
        .apply(color_rpe_ua, subset=[t("RPE promedio")])
        .apply(color_rpe_ua, subset=[t("UA total")])
        .apply(color_riesgo, subset=[t("En riesgo")])
        .format(precision=2, na_rep="")
    )

    st.dataframe(styled, hide_index=True)


def compute_inicio_alert_kpis(df: pd.DataFrame) -> dict:
    """
    Calcula KPIs ejecutivos de alertas para la portada:
    - valor actual
    - delta absoluto respecto a la medición anterior disponible por jugadora
    """

    res = {
        "grasa_elevada": {"valor": 0, "delta": 0},
        "musculo_bajo": {"valor": 0, "delta": 0},
        "pliegues_elevados": {"valor": 0, "delta": 0},
        "imo_mejorable": {"valor": 0, "delta": 0},
        "empeoramiento_reciente": {"valor": 0, "delta": 0},
    }

    if df is None or df.empty or "fecha_medicion" not in df.columns:
        return res

    out = df.copy()
    out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")

    if "created_at" in out.columns:
        out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")

    id_col = "identificacion" if "identificacion" in out.columns else "nombre_jugadora"
    if id_col not in out.columns:
        return res

    cols_metricas = ["ajuste_adiposa_pct", "ajuste_muscular_pct", "suma_6_pliegues_mm", "idx_musculo_oseo"]
    for col in cols_metricas:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    sort_cols = [id_col, "fecha_medicion"]
    ascending = [True, False]

    if "created_at" in out.columns:
        sort_cols.append("created_at")
        ascending.append(False)

    if "id_isak" in out.columns:
        sort_cols.append("id_isak")
        ascending.append(False)

    out = out.sort_values(sort_cols, ascending=ascending).copy()
    out["rank_medicion"] = out.groupby(id_col).cumcount() + 1

    df_curr = out[out["rank_medicion"] == 1].copy()
    df_prev = out[out["rank_medicion"] == 2].copy()

    # =========================
    # ALERTAS ACTUALES
    # =========================
    curr_grasa = int((df_curr["ajuste_adiposa_pct"] > 24).sum()) if "ajuste_adiposa_pct" in df_curr.columns else 0
    curr_musculo = int((df_curr["ajuste_muscular_pct"] < 40).sum()) if "ajuste_muscular_pct" in df_curr.columns else 0
    curr_pliegues = int((df_curr["suma_6_pliegues_mm"] > 90).sum()) if "suma_6_pliegues_mm" in df_curr.columns else 0
    curr_imo = int((df_curr["idx_musculo_oseo"] < 3.5).sum()) if "idx_musculo_oseo" in df_curr.columns else 0

    # =========================
    # ALERTAS PREVIAS
    # =========================
    prev_grasa = int((df_prev["ajuste_adiposa_pct"] > 24).sum()) if "ajuste_adiposa_pct" in df_prev.columns else 0
    prev_musculo = int((df_prev["ajuste_muscular_pct"] < 40).sum()) if "ajuste_muscular_pct" in df_prev.columns else 0
    prev_pliegues = int((df_prev["suma_6_pliegues_mm"] > 90).sum()) if "suma_6_pliegues_mm" in df_prev.columns else 0
    prev_imo = int((df_prev["idx_musculo_oseo"] < 3.5).sum()) if "idx_musculo_oseo" in df_prev.columns else 0

    res["grasa_elevada"] = {"valor": curr_grasa, "delta": curr_grasa - prev_grasa}
    res["musculo_bajo"] = {"valor": curr_musculo, "delta": curr_musculo - prev_musculo}
    res["pliegues_elevados"] = {"valor": curr_pliegues, "delta": curr_pliegues - prev_pliegues}
    res["imo_mejorable"] = {"valor": curr_imo, "delta": curr_imo - prev_imo}

    # =========================
    # EMPEORAMIENTO RECIENTE
    # =========================
    cols_base = [id_col]
    if "nombre_jugadora" in out.columns and "nombre_jugadora" not in cols_base:
        cols_base.append("nombre_jugadora")

    df_curr_cmp = df_curr[cols_base + cols_metricas].rename(columns={
        "ajuste_adiposa_pct": "grasa_curr",
        "ajuste_muscular_pct": "musculo_curr",
        "suma_6_pliegues_mm": "pliegues_curr",
        "idx_musculo_oseo": "imo_curr",
    })

    df_prev_cmp = df_prev[[id_col] + cols_metricas].rename(columns={
        "ajuste_adiposa_pct": "grasa_prev",
        "ajuste_muscular_pct": "musculo_prev",
        "suma_6_pliegues_mm": "pliegues_prev",
        "idx_musculo_oseo": "imo_prev",
    })

    df_cmp = df_curr_cmp.merge(df_prev_cmp, on=id_col, how="inner")

    if not df_cmp.empty:
        empeora_actual = (
            (df_cmp["grasa_curr"] > df_cmp["grasa_prev"]) |
            (df_cmp["musculo_curr"] < df_cmp["musculo_prev"]) |
            (df_cmp["pliegues_curr"] > df_cmp["pliegues_prev"]) |
            (df_cmp["imo_curr"] < df_cmp["imo_prev"])
        )
        valor_empeora = int(empeora_actual.sum())
    else:
        valor_empeora = 0

    # Como referencia previa, usamos 0 porque "empeoramiento reciente"
    # ya es en sí una comparación entre última y anterior.
    res["empeoramiento_reciente"] = {"valor": valor_empeora, "delta": 0}

    return res

def render_inicio_alert_kpis(kpis: dict) -> None:
    """
    Renderiza KPIs ejecutivos de alertas para la portada.
    """

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            t("Grasa elevada"),
            kpis["grasa_elevada"]["valor"],
            f"{kpis['grasa_elevada']['delta']:+d}",
            delta_color="inverse",
            border=True,
            help=t("Jugadoras con porcentaje de grasa superior a 24%")
        )

    with c2:
        st.metric(
            t("Músculo bajo"),
            kpis["musculo_bajo"]["valor"],
            f"{kpis['musculo_bajo']['delta']:+d}",
            delta_color="inverse",
            border=True,
            help=t("Jugadoras con porcentaje muscular inferior a 40%")
        )

    with c3:
        st.metric(
            t("Pliegues elevados"),
            kpis["pliegues_elevados"]["valor"],
            f"{kpis['pliegues_elevados']['delta']:+d}",
            delta_color="inverse",
            border=True,
            help=t("Jugadoras con suma de 6 pliegues superior a 90 mm")
        )

    with c4:
        st.metric(
            t("IMO mejorable"),
            kpis["imo_mejorable"]["valor"],
            f"{kpis['imo_mejorable']['delta']:+d}",
            delta_color="inverse",
            border=True,
            help=t("Jugadoras con índice músculo / óseo inferior a 3.5")
        )

    with c5:
        st.metric(
            t("Empeoramiento reciente"),
            kpis["empeoramiento_reciente"]["valor"],
            None,
            border=True,
            help=t("Jugadoras cuya última medición empeora respecto a la anterior en alguna variable clave")
        )


def build_empeoramiento_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve tabla con jugadoras que han empeorado recientemente
    y en qué métricas.
    """

    if df is None or df.empty or "fecha_medicion" not in df.columns:
        return pd.DataFrame()

    out = df.copy()
    out["fecha_medicion"] = pd.to_datetime(out["fecha_medicion"], errors="coerce")

    if "created_at" in out.columns:
        out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")

    id_col = "identificacion" if "identificacion" in out.columns else "nombre_jugadora"
    if id_col not in out.columns:
        return pd.DataFrame()

    cols_metricas = ["ajuste_adiposa_pct", "ajuste_muscular_pct", "suma_6_pliegues_mm", "idx_musculo_oseo"]
    for col in cols_metricas:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    sort_cols = [id_col, "fecha_medicion"]
    ascending = [True, False]

    if "created_at" in out.columns:
        sort_cols.append("created_at")
        ascending.append(False)

    if "id_isak" in out.columns:
        sort_cols.append("id_isak")
        ascending.append(False)

    out = out.sort_values(sort_cols, ascending=ascending).copy()
    out["rank"] = out.groupby(id_col).cumcount() + 1

    df_curr = out[out["rank"] == 1].copy()
    df_prev = out[out["rank"] == 2].copy()

    cols_base = [id_col]
    for extra in ["nombre_jugadora", "posicion", "posición", "demarcacion", "demarcación"]:
        if extra in out.columns and extra not in cols_base:
            cols_base.append(extra)

    df_curr = df_curr[cols_base + cols_metricas].rename(columns={
        "ajuste_adiposa_pct": "grasa_curr",
        "ajuste_muscular_pct": "musculo_curr",
        "suma_6_pliegues_mm": "pliegues_curr",
        "idx_musculo_oseo": "imo_curr",
    })

    df_prev = df_prev[[id_col] + cols_metricas].rename(columns={
        "ajuste_adiposa_pct": "grasa_prev",
        "ajuste_muscular_pct": "musculo_prev",
        "suma_6_pliegues_mm": "pliegues_prev",
        "idx_musculo_oseo": "imo_prev",
    })

    df_cmp = df_curr.merge(df_prev, on=id_col, how="inner")
    if df_cmp.empty:
        return pd.DataFrame()

    rows = []

    for _, r in df_cmp.iterrows():
        cambios = {}

        if pd.notna(r.get("grasa_curr")) and pd.notna(r.get("grasa_prev")) and r["grasa_curr"] > r["grasa_prev"]:
            cambios["Grasa"] = f"🔴 +{r['grasa_curr'] - r['grasa_prev']:.1f}"

        if pd.notna(r.get("musculo_curr")) and pd.notna(r.get("musculo_prev")) and r["musculo_curr"] < r["musculo_prev"]:
            cambios["Músculo"] = f"🔴 {r['musculo_curr'] - r['musculo_prev']:.1f}"

        if pd.notna(r.get("pliegues_curr")) and pd.notna(r.get("pliegues_prev")) and r["pliegues_curr"] > r["pliegues_prev"]:
            cambios["Pliegues"] = f"🔴 +{r['pliegues_curr'] - r['pliegues_prev']:.1f}"

        if pd.notna(r.get("imo_curr")) and pd.notna(r.get("imo_prev")) and r["imo_curr"] < r["imo_prev"]:
            cambios["IMO"] = f"🔴 {r['imo_curr'] - r['imo_prev']:.2f}"

        if cambios:
            posicion_val = (
                r.get("posicion")
                if pd.notna(r.get("posicion"))
                else r.get("posición")
                if pd.notna(r.get("posición"))
                else r.get("demarcacion")
                if pd.notna(r.get("demarcacion"))
                else r.get("demarcación")
            )

            rows.append({
                "Identificación": r[id_col],
                "Jugadora": r.get("nombre_jugadora", r[id_col]),
                "Posición": posicion_val if pd.notna(posicion_val) else "—",
                "Nº métricas empeoradas": len(cambios),
                "Grasa": cambios.get("Grasa", "—"),
                "Músculo": cambios.get("Músculo", "—"),
                "Pliegues": cambios.get("Pliegues", "—"),
                "IMO": cambios.get("IMO", "—"),
            })

    if not rows:
        return pd.DataFrame()

    tabla = pd.DataFrame(rows).sort_values(
        by=["Nº métricas empeoradas", "Jugadora"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return tabla

def render_empeoramiento_table(df: pd.DataFrame) -> None:
    tabla = build_empeoramiento_table(df)

    if tabla.empty:
        st.success(t("No hay jugadoras con empeoramiento reciente."))
        return

    st.markdown(t("### 🔍 Jugadoras en empeoramiento reciente"))

    # # Filtro por posición
    # tabla_filtrada = tabla.copy()
    # if "Posición" in tabla_filtrada.columns:
    #     posiciones = sorted([p for p in tabla_filtrada["Posición"].dropna().unique().tolist() if p != "—"])
    #     opciones = [t("Todas")] + posiciones

    #     posicion_sel = st.selectbox(
    #         t("Filtrar por posición"),
    #         options=opciones,
    #         index=0,
    #         key="filtro_posicion_empeoramiento"
    #     )

    #     if posicion_sel != t("Todas"):
    #         tabla_filtrada = tabla_filtrada[tabla_filtrada["Posición"] == posicion_sel].copy()
    tabla_filtrada = tabla.copy()
    st.dataframe(
        tabla_filtrada[["Jugadora", "Nº métricas empeoradas", "Grasa", "Músculo", "Pliegues", "IMO"]],
        hide_index=True,
        use_container_width=True
    )

    # Navegación a individual
    opciones_jugadora = tabla_filtrada["Jugadora"].tolist()
    if opciones_jugadora:
        jugadora_sel = st.selectbox(
            t("Abrir análisis individual de"),
            options=opciones_jugadora,
            index=0,
            key="jugadora_empeoramiento_ir_individual"
        )

        if st.button(t("Ir a análisis individual"), key="btn_ir_individual_desde_alertas"):
            fila = tabla_filtrada[tabla_filtrada["Jugadora"] == jugadora_sel].iloc[0]

            # Guardamos referencias para que la página individual las pueda leer
            st.session_state["jugadora_preseleccionada_nombre"] = fila["Jugadora"]
            st.session_state["jugadora_preseleccionada_id"] = fila["Identificación"]

            try:
                st.switch_page("pages/individual.py")
            except Exception:
                st.info(t("Se ha guardado la jugadora seleccionada. Abre la página Individual para continuar."))