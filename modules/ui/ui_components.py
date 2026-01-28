from decimal import Decimal
from typing import Any
import pandas as pd
import streamlit as st
import datetime
import json
from modules.util.key_builder import KeyBuilder
from modules.util.util import get_date_range_input
from modules.i18n.i18n import t
from modules.schema import MAP_POSICIONES
from modules.util.key_builder import KeyBuilder
from modules.util.util import load_posiciones_traducidas

def selection_header(jug_df: pd.DataFrame, comp_df: pd.DataFrame, records_df: pd.DataFrame = None, modo: str = "registro") -> pd.DataFrame:
    """
    Muestra los filtros principales (Competición, Jugadora, Turno, Tipo/Fechas)
    y retorna el DataFrame de registros filtrado según las selecciones.
    """

    kb = KeyBuilder()

    col1, col2, col3 = st.columns([3, 2, 2])

    # --- Selección de competición ---
    with col1:
        competiciones_options = comp_df.to_dict("records")
        competicion = st.selectbox(
            t("Plantel"),
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            index=3,
        )
        #st.session_state["competicion"] = competiciones_options.index(competicion)

    # --- Selección de jugadora ---
    with col2:
        jugadora_opt = None
        disabled_jugadores = True if modo == "reporte_grupal" else False

        if not jug_df.empty:
            codigo_comp = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["plantel"] == codigo_comp]

            # Nombres estables (strings)
            jugadora_nombres = (
                jug_df_filtrado["nombre_jugadora"]
                .astype(str)
                .sort_values()
                .tolist()
            )

            # Resolver índice (permite vacío)
            jugadora_index = None
            if (
                "nombre_jugadora" in st.session_state
                and st.session_state["nombre_jugadora"] in jugadora_nombres
            ):
                jugadora_index = jugadora_nombres.index(
                    st.session_state["nombre_jugadora"]
                )

            jugadora_nombre = st.selectbox(
                t("Jugadora"),
                options=jugadora_nombres,
                format_func=lambda x: f"{jugadora_nombres.index(x) + 1} - {x}",
                index=None,          # None → selector vacío
                placeholder=t("Seleccione una Jugadora"),
                disabled=disabled_jugadores,
                key="jugadora_selector"
            )

            # Persistir estado SOLO si hay selección
            if jugadora_nombre:
                st.session_state["nombre_jugadora"] = jugadora_nombre
            else:
                st.session_state.pop("nombre_jugadora", None)

            # Reconstruir objeto completo solo si hay selección
            if "nombre_jugadora" in st.session_state:
                jugadora_opt = jug_df_filtrado[
                    jug_df_filtrado["nombre_jugadora"].astype(str)
                    == st.session_state["nombre_jugadora"]
                ].iloc[0].to_dict()

        else:
            st.warning(
                ":material/warning: No hay jugadoras cargadas para esta competición."
            )

    # --- Tipo o rango de fechas según modo ---
    start, end = None, None
    with col3:
        # modo == "reporte"
        hoy = datetime.date.today()
        hace_15_dias = hoy - datetime.timedelta(days=15)

        start_default = hace_15_dias 
        end_default = hoy

        start, end = get_date_range_input(t("Rango de fechas"), start_default=start_default, end_default=end_default)

    if modo == "registro":
        return jugadora_opt
    
    # ==================================================
    # 🧮 FILTRADO DEL DATAFRAME
    # ==================================================
    #st.text(t("Filtrando registros..."))
    df_filtrado = filtrar_registros(
        records_df,
        jugadora_opt=jugadora_opt,
        modo=modo,
        start=start,
        end=end,
    )

    return df_filtrado, jugadora_opt, start, end

def filtrar_registros(
    records_df: pd.DataFrame,
    jugadora_opt: dict | None = None,
    modo: str = "registros",
    tipo: str | None = None,
    start=None,
    end=None,
) -> pd.DataFrame:
    """
    Filtra el DataFrame de registros según los criterios seleccionados.

    Parámetros:
        records_df: DataFrame original.
        jugadora_opt: dict con datos de la jugadora seleccionada (o None).
        turno: "Todos", "Turno 1", "Turno 2", "Turno 3".
        modo: "registros" o "reporte".
        tipo: string del tipo de registro (solo si modo="registros").
        start: fecha inicio (solo si modo="reporte").
        end: fecha fin (solo si modo="reporte").

    Retorna:
        DataFrame filtrado.
    """

    df_filtrado = records_df.copy()

    if df_filtrado.empty:
        return df_filtrado

    # -------------------------
    # Filtrar por jugadora
    # -------------------------
    if jugadora_opt:
        df_filtrado = df_filtrado[
            df_filtrado["identificacion"] == jugadora_opt["identificacion"]
        ]

    # -------------------------
    # MODO: registros
    # -------------------------
    if modo == "registros" and tipo:
        df_filtrado = df_filtrado[
            df_filtrado["tipo"].str.lower() == tipo.lower()
        ]

    # -------------------------
    # MODO: reporte (rango de fechas)
    # -------------------------
    elif (modo == "reporte" or modo == "reporte_grupal") and start and end:

        # Normalizar tipos de fecha
        if pd.api.types.is_datetime64_any_dtype(df_filtrado["fecha_sesion"]):
            df_filtrado["fecha_sesion"] = df_filtrado["fecha_sesion"].dt.date

        # Normalizar start y end si vienen como Timestamp
        if hasattr(start, "to_pydatetime"):
            start = start.date()
        if hasattr(end, "to_pydatetime"):
            end = end.date()

        df_filtrado = df_filtrado[
            (df_filtrado["fecha_sesion"] >= start)
            & (df_filtrado["fecha_sesion"] <= end)
        ]

    # ===========================================================
    # MODO: AUSENCIAS (usa fecha_inicio y fecha_fin)
    # Detecta solapamiento de intervalos
    # ===========================================================
    elif modo == "ausencias" and start and end:

        # Comprobar columnas esperadas
        if not {"fecha_inicio", "fecha_fin"}.issubset(df_filtrado.columns):
            return df_filtrado

        # Normalizar tipos
        if pd.api.types.is_datetime64_any_dtype(df_filtrado["fecha_inicio"]):
            df_filtrado["fecha_inicio"] = df_filtrado["fecha_inicio"].dt.date
        if pd.api.types.is_datetime64_any_dtype(df_filtrado["fecha_fin"]):
            df_filtrado["fecha_fin"] = df_filtrado["fecha_fin"].dt.date

        if hasattr(start, "to_pydatetime"):
            start = start.date()
        if hasattr(end, "to_pydatetime"):
            end = end.date()

        # Regla de solapamiento:
        # inicio <= fin_filtro AND fin >= inicio_filtro
        df_filtrado = df_filtrado[
            (df_filtrado["fecha_inicio"] <= end)
            & (df_filtrado["fecha_fin"] >= start)
        ]

    return df_filtrado

def selection_header_registro(
    jug_df: pd.DataFrame,
    comp_df: pd.DataFrame,
    records_df: pd.DataFrame | None = None
):
    """
    Header Antropometría:
    Plantel → Posición → Jugadora

    Responsabilidad:
    - Filtrar jugadoras
    - Resolver jugadora seleccionada
    - Filtrar cabeceras ISAK (antropometria_isak) de esa jugadora

    Devuelve:
        - jugadora_seleccionada (dict | None)
        - posicion (str | None)
        - df_isak_jugadora (DataFrame | None)
    """

    session_id = st.session_state.get("client_session_id", "default")

    col1, col2, col3, col4 = st.columns([2, 1, 2, 1.5])

    # ======================================================
    # 1) PLANTEL
    # ======================================================
    with col1:
        comp_options = comp_df.to_dict("records")

        competicion = st.selectbox(
            t("Plantel"),
            options=comp_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder=t("Seleccione un plantel"),
            index=3,
            key=f"plantel_antropometria__{session_id}"
        )

    # ======================================================
    # 2) POSICIÓN
    # ======================================================
    with col2:
        MAP_POSICIONES_TRADUCIDAS = load_posiciones_traducidas()
        MAP_POSICIONES_INVERTIDO = {v: k for k, v in MAP_POSICIONES_TRADUCIDAS.items()}

        posicion_traducida = st.selectbox(
            t("Posición"),
            options=list(MAP_POSICIONES_TRADUCIDAS.values()),
            placeholder=t("Seleccione una posición"),
            index=None,
            key=f"posicion_antropometria__{session_id}"
        )

        clave = MAP_POSICIONES_INVERTIDO.get(posicion_traducida)
        posicion = MAP_POSICIONES.get(clave)

        # Reset jugadora si cambia filtro
        filtro_actual = (competicion["codigo"] if competicion else None, posicion)
        if st.session_state.get("last_filtro_jugadora_antropo") != filtro_actual:
            st.session_state.pop("jugadora_antropometria", None)
            st.session_state["last_filtro_jugadora_antropo"] = filtro_actual

    # ======================================================
    # 3) JUGADORA
    # ======================================================
    with col3:
        # --- Filtrado base ---
        if competicion:
            codigo_comp = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["plantel"] == codigo_comp].copy()
        else:
            jug_df_filtrado = jug_df.copy()

        if posicion:
            jug_df_filtrado = jug_df_filtrado[jug_df_filtrado["posicion"] == posicion]

        if jug_df_filtrado.empty:
            st.error(t("No hay jugadoras disponibles con los filtros seleccionados"))
            return None, posicion, None

        # --- Lista estable de nombres ---
        jugadora_nombres = (
            jug_df_filtrado["nombre_jugadora"]
            .astype(str)
            .sort_values()
            .tolist()
        )

        jugadora_labels = {
            nombre: f"{i + 1} - {nombre}"
            for i, nombre in enumerate(jugadora_nombres)
        }

        jugadora_nombre = st.selectbox(
            t("Jugadora"),
            options=jugadora_nombres,
            index=None,
            format_func=lambda x: jugadora_labels[x],
            placeholder=t("Seleccione una jugadora")
        )

        # ==================================================
        # Resultado final
        # ==================================================
        jugadora_seleccionada = None
        df_isak_jugadora = None

        if jugadora_nombre:
            jugadora_seleccionada = jug_df_filtrado[
                jug_df_filtrado["nombre_jugadora"].astype(str) == jugadora_nombre
            ].iloc[0].to_dict()

            if records_df is not None and not records_df.empty:
                jugadora_id = str(jugadora_seleccionada.get("identificacion"))
                df_isak_jugadora = records_df[
                    records_df["identificacion"].astype(str) == jugadora_id
                ].copy()

    with col4:
        opciones_tipo = ["Formulario", "Archivo"]
        tipo = st.radio(
            t("Tipo de registro"),
            options=opciones_tipo,
            horizontal=True,
            index=opciones_tipo.index(st.session_state.get("tipo_registro", "Formulario")),
            key=f"tipo_registro__{session_id}"
        )

    return jugadora_seleccionada, posicion, df_isak_jugadora, tipo.lower()

#######################################
#######################################

def normalize_for_ui(obj: Any) -> Any:
    """
    Convierte Decimal → float y procesa estructuras anidadas
    para visualización / JSON / Streamlit.
    """
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, dict):
        return {k: normalize_for_ui(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [normalize_for_ui(v) for v in obj]

    return obj

def preview_record(record: dict) -> None:
    jug = record.get("id_jugadora", "-")
    fecha = record.get("fecha_sesion", "-")
    #turno = record.get("turno", "-")
    tipo = record.get("tipo_isak", "-")
    st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha} |  **Tipo:** {tipo}")
    with st.expander("Ver registro JSON", expanded=True):
        record_ui = normalize_for_ui(record)
        st.code(json.dumps(record_ui, ensure_ascii=False, indent=2), language="json")