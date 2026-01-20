import streamlit as st
import pandas as pd
from modules.reports.plots_individuales import grafico_composicion, grafico_indice_musculo_oseo, grafico_peso_grasa
from modules.util.util import (get_photo, clean_image_url, calcular_edad)
from modules.i18n.i18n import t

def player_block_dux(jugadora_seleccionada: dict, unavailable="N/A"):
    """Muestra el bloque visual con la información principal de la jugadora."""

    # Validar jugadora seleccionada
    if not jugadora_seleccionada or not isinstance(jugadora_seleccionada, dict):
        st.info(t("Selecciona una jugadora para continuar."))
        st.stop()
    
    #st.dataframe(jugadora_seleccionada)
    # Extraer información básica
    nombre_completo = jugadora_seleccionada.get("nombre_jugadora", unavailable).strip().upper()
    #apellido = jugadora_seleccionada.get("apellido", "").strip().upper()
    #nombre_completo = f"{nombre.capitalize()}"
    id_jugadora = jugadora_seleccionada.get("identificacion", unavailable)
    posicion = jugadora_seleccionada.get("posicion", unavailable)
    pais = jugadora_seleccionada.get("nacionalidad", unavailable)
    fecha_nac = jugadora_seleccionada.get("fecha_nacimiento", unavailable)
    genero = jugadora_seleccionada.get("genero", "")
    competicion = jugadora_seleccionada.get("plantel", "")
    dorsal = jugadora_seleccionada.get("dorsal", "")
    url_drive = jugadora_seleccionada.get("foto_url", "")

    dorsal_number = f":red[/ Dorsal #{int(dorsal)}]" if pd.notna(dorsal) else ""

    # Calcular edad
    edad_texto, fnac = calcular_edad(fecha_nac)

    # Color temático
    #color = "violet" if genero.upper() == "F" else "blue"

    # Icono de género
    if genero.upper() == "F":
        genero_icono = ":material/girl:"
        profile_image = "female"
    elif genero.upper() == "H":
        genero_icono = ":material/boy:"
        profile_image = "male"
    else:
        genero_icono = ""
        profile_image = "profile"

    # Bloque visual
    st.markdown(f"### {nombre_completo.title()} {dorsal_number}")
    #st.markdown(f"##### **_:red[Identificación:]_** _{identificacion}_ | **_:red[País:]_** _{pais.upper()}_")

    col1, col2, col3 = st.columns([1.6, 2, 2])

    with col1:
        if pd.notna(url_drive) and url_drive and url_drive != "No Disponible":
            direct_url = clean_image_url(url_drive)
            #st.text(direct_url)
            response = get_photo(direct_url)
            if response and response.status_code == 200 and 'image' in response.headers.get("Content-Type", ""):
                st.image(response.content, width=300)
            else:
                st.image(f"assets/images/{profile_image}.png", width=300)
        else:
            st.image(f"assets/images/{profile_image}.png", width=300)

    with col2:
        #st.markdown(f"**:material/sports_soccer: Competición:** {competicion}")
        #st.markdown(f"**:material/cake: Fecha Nac.:** {fecha_nac}")

        st.metric(label=t(":red[:material/id_card: Identificación]"), value=f"{id_jugadora}", border=True)
        st.metric(label=t(":red[:material/sports_soccer: Plantel]"), value=f"{competicion}", border=True)
        st.metric(label=t(":red[:material/cake: F. Nacimiento]"), value=f"{fecha_nac}", border=True)
                    
    with col3:
        #st.markdown(f"**:material/person: Posición:** {posicion.capitalize()}")
        #st.markdown(f"**:material/favorite: Edad:** {edad if edad != unavailable else 'N/A'} años")

        st.metric(label=t(":red[:material/globe: País]"), value=f"{pais if pais else 'N/A'}", border=True)
        st.metric(label=t(":red[:material/person: Posición]"), value=f"{posicion.capitalize() if posicion else 'N/A'}", border=True)
        st.metric(label=t(":red[:material/favorite: Edad]"), value=f"{edad_texto}", border=True)
          
    #st.divider()

def graficos_individuales(df: pd.DataFrame):

    if df is None or df.empty:
        st.info(t("No hay datos disponibles para graficar."))
        return

    df = df.sort_values("fecha_sesion")

    st.markdown(t("### **Gráficos**"))

    tabs = st.tabs([
        t("Peso y grasa"),
        t("Composición corporal"),
        t("Índice músculo–óseo")
    ])

    with tabs[0]:
        grafico_peso_grasa(df)

    with tabs[1]:
        grafico_composicion(df)

    with tabs[2]:
        grafico_indice_musculo_oseo(df)
