import datetime
from modules.i18n.i18n import t

# Diccionario de equivalencias
MAP_POSICIONES = {
    "POR": "Portera",
    "DEF": "Defensa",
    "MC": "Centro",
    "DEL": "Delantera"
}

# === Diccionario para traducir días ===
DIAS_SEMANA = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

OPCIONES_TURNO = {
    "Todos": t("Todos"),
    "Turno 1": t("Turno 1"),
    "Turno 2": t("Turno 2"),
    "Turno 3": t("Turno 3")
}

def new_base_record(id_jugadora: str, username: str) -> dict:
    """
    Create a base record structure adapted to antropometria table.
    """

    return {
        # --- PK / FK ---
        "id_jugadora": id_jugadora,

        # --- Antropometría ---
        "metodo": None,                     # varchar(50)
        "peso_kg": None,                    # decimal(5,2)
        "talla_cm": None,                   # decimal(5,2)
        "suma_6_pliegues_mm": None,         # decimal(6,2)
        "porcentaje_grasa": None,           # decimal(5,2)
        "porcentaje_muscular": None,        # decimal(5,2)
        "masa_osea_kg": None,               # decimal(5,3)
        "indice_musculo_oseo": None,        # decimal(4,2)

        # --- Observaciones ---
        "observaciones": "",                # text

        # --- Auditoría ---
        "fecha_hora_registro": datetime.datetime.now().isoformat(),
        "usuario": username,                # varchar(50)
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": None,
        "modified_by": None,

        # --- Control lógico ---
        "estatus_id": 1,                    # FK estatus_registro
        "deleted_at": None,
        "deleted_by": None,
    }



