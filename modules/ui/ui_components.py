import pandas as pd
import streamlit as st
import datetime
import json
from modules.util.key_builder import KeyBuilder
from modules.util.util import get_date_range_input
from modules.i18n.i18n import t
from modules.schema import MAP_POSICIONES, OPCIONES_TURNO
from modules.util.key_builder import KeyBuilder

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

def preview_record(record: dict) -> None:
    jug = record.get("identificacion", "-")
    fecha = record.get("fecha_sesion", "-")
    turno = record.get("turno", "-")
    tipo = record.get("tipo", "-")
    st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Turno:** {turno}  |  **Tipo:** {tipo}")
    with st.expander("Ver registro JSON", expanded=True):
        st.code(json.dumps(record, ensure_ascii=False, indent=2), language="json")

def load_posiciones_traducidas() -> dict:
    return {key: t(valor_es) for key, valor_es in MAP_POSICIONES.items()}

def selection_header_registro(
    jug_df: pd.DataFrame,
    comp_df: pd.DataFrame,
    records_df: pd.DataFrame | None = None
):
    """
    Header Antropometría:
    Plantel → Posición → Jugadora

    Si records_df está disponible:
      - excluye jugadoras que YA tienen registro en fecha_objetivo (por defecto: hoy)
    """

    session_id = st.session_state.get("client_session_id", "default")
    fecha_objetivo = datetime.date.today()

    col1, col2, col3 = st.columns([2, 1.5, 2])

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

        # reset jugadora si cambia filtro
        filtro_actual = (competicion["codigo"] if competicion else None, posicion)
        if st.session_state.get("last_filtro_jugadora_antropo") != filtro_actual:
            st.session_state.pop("jugadora_antropometria", None)
            st.session_state["last_filtro_jugadora_antropo"] = filtro_actual

    # ======================================================
    # 3) JUGADORA (con exclusión por fecha)
    # ======================================================
    with col3:
        # Base filtrada por plantel/posición
        if competicion:
            codigo_comp = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["plantel"] == codigo_comp].copy()
        else:
            jug_df_filtrado = jug_df.copy()

        if posicion:
            jug_df_filtrado = jug_df_filtrado[jug_df_filtrado["posicion"] == posicion]

        # --- Excluir jugadoras que ya tienen registro hoy (fecha_objetivo) ---
        if records_df is not None and not records_df.empty:
            df_r = records_df.copy()

            # Asegurar fecha como date
            if "fecha_sesion" in df_r.columns:
                df_r["fecha_sesion"] = pd.to_datetime(df_r["fecha_sesion"], errors="coerce").dt.date
            elif "fecha_hora_registro" in df_r.columns:
                df_r["fecha_sesion"] = pd.to_datetime(df_r["fecha_hora_registro"], errors="coerce").dt.date
            else:
                df_r["fecha_sesion"] = None

            ids_registrados = set(
                df_r[df_r["fecha_sesion"] == fecha_objetivo]["identificacion"].astype(str).unique()
            )

            # En jug_df la columna suele ser "identificacion"
            if "identificacion" in jug_df_filtrado.columns:
                jug_df_filtrado = jug_df_filtrado[
                    ~jug_df_filtrado["identificacion"].astype(str).isin(ids_registrados)
                ]

        if jug_df_filtrado.empty:
            st.error(t("No hay jugadoras disponibles para registrar en la fecha seleccionada"))
            return None, posicion, pd.DataFrame()

        # Lista estable de nombres
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

        jugadora_index = None
        if (
            "jugadora_antropometria" in st.session_state
            and st.session_state["jugadora_antropometria"] in jugadora_nombres
        ):
            jugadora_index = jugadora_nombres.index(st.session_state["jugadora_antropometria"])

        jugadora_nombre = st.selectbox(
            t("Jugadora"),
            options=jugadora_nombres,
            index=jugadora_index,
            format_func=lambda x: jugadora_labels[x],
            placeholder=t("Seleccione una jugadora"),
            key=f"jugadora_antropometria__{session_id}"
        )

        # Persistir selección
        if jugadora_nombre:
            st.session_state["jugadora_antropometria"] = jugadora_nombre
        else:
            st.session_state.pop("jugadora_antropometria", None)

        jugadora_seleccionada = None
        if "jugadora_antropometria" in st.session_state:
            jugadora_seleccionada = jug_df_filtrado[
                jug_df_filtrado["nombre_jugadora"].astype(str) == st.session_state["jugadora_antropometria"]
            ].iloc[0].to_dict()

    return jugadora_seleccionada
