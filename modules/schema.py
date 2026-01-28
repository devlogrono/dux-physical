import datetime
from types import MappingProxyType

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

ISAK_FIELDS = {
    # -----------------
    # BÁSICOS
    # -----------------
    "peso_bruto_kg": {
        "grupo": "basicos",
        "decimals": 1,
        "tipo": "repetible",
        "media": 64.58,
        "sd": 8.6,
    },
    "talla_corporal_cm": {
        "grupo": "basicos",
        "decimals": 1,
        "tipo": "estructural",
        "media": None,
        "sd": None,
    },
    "talla_sentado_cm": {
        "grupo": "basicos",
        "decimals": 1,
        "tipo": "estructural",
        "media": 89.92,
        "sd": 4.5,
    },
    "envergadura_cm": {
        "grupo": "basicos",
        "decimals": 1,
        "tipo": "estructural",
        "media": 172.35,
        "sd": 7.41,
    },

    # -----------------
    # LONGITUDES
    # -----------------
    "acromial_radial": {
        "grupo": "longitudes",
        "decimals": 1,
        "tipo": "estructural",
        "media": 32.53,
        "sd": 1.77,
    },
    "radial_estiloidea": {
        "grupo": "longitudes",
        "decimals": 2,
        "tipo": "estructural",
        "media": 24.57,
        "sd": 1.37,
    },
    "medial_estiloidea_dactilar": {
        "grupo": "longitudes",
        "decimals": 2,
        "tipo": "estructural",
        "media": 18.85,
        "sd": 0.85,
    },
    "ilioespinal": {
        "grupo": "longitudes",
        "decimals": 2,
        "tipo": "estructural",
        "media": 94.11,
        "sd": 4.71,
    },
    "trocanterea": {
        "grupo": "longitudes",
        "decimals": 1,
        "tipo": "estructural",
        "media": 86.4,
        "sd": 4.32,
    },
    "troc_tibial_lateral": {
        "grupo": "longitudes",
        "decimals": 1,
        "tipo": "estructural",
        "media": 41.37,
        "sd": 2.48,
    },
    "tibial_lateral": {
        "grupo": "longitudes",
        "decimals": 1,
        "tipo": "estructural",
        "media": 44.82,
        "sd": 2.56,
    },
    "tibial_medial_maleolar_medial": {
        "grupo": "longitudes",
        "decimals": 2,
        "tipo": "estructural",
        "media": 36.81,
        "sd": 2.1,
    },
    "pie": {
        "grupo": "longitudes",
        "decimals": 2,
        "tipo": "estructural",
        "media": 25.5,
        "sd": 1.16,
    },

    # -----------------
    # DIÁMETROS
    # -----------------
    "biacromial": {
        "grupo": "diametros",
        "decimals": 1,
        "tipo": "estructural",
        "media": 38.04,
        "sd": 1.92,
    },
    "bi_iliocrestideo": {
        "grupo": "diametros",
        "decimals": 1,
        "tipo": "estructural",
        "media": 28.84,
        "sd": 1.75,
    },
    "humeral_biepicondilar": {
        "grupo": "diametros",
        "decimals": 1,
        "tipo": "estructural",
        "media": 6.48,
        "sd": 0.35,
    },
    "femoral_biepicondilar": {
        "grupo": "diametros",
        "decimals": 1,
        "tipo": "estructural",
        "media": 9.52,
        "sd": 0.48,
    },
    "muneca_biestiloideo": {
        "grupo": "diametros",
        "decimals": 2,
        "tipo": "estructural",
        "media": 5.21,
        "sd": 0.28,
    },
    "tobillo_bimaleolar": {
        "grupo": "diametros",
        "decimals": 2,
        "tipo": "estructural",
        "media": 6.68,
        "sd": 0.36,
    },
    "torax_transverso": {
        "grupo": "diametros",
        "decimals": 2,
        "tipo": "estructural",
        "media": 27.92,
        "sd": 1.74,
    },
    "torax_antero_posterior": {
        "grupo": "diametros",
        "decimals": 2,
        "tipo": "estructural",
        "media": 17.5,
        "sd": 1.38,
    },
    "mano": {
        "grupo": "diametros",
        "decimals": 2,
        "tipo": "estructural",
        "media": 8.28,
        "sd": 0.5,
    },

    # -----------------
    # PERÍMETROS
    # -----------------
    "perimetro_cabeza": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 56.0,
        "sd": 1.44,
    },
    "perimetro_cuello": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 34.91,
        "sd": 1.73,
    },
    "perimetro_brazo_relajado": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 26.89,
        "sd": 2.33,
    },
    "perimetro_brazo_flexionado_en_tension": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 29.41,
        "sd": 2.37,
    },
    "perimetro_antebrazo_maximo": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 25.13,
        "sd": 1.41,
    },
    "perimetro_muneca": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 16.35,
        "sd": 0.72,
    },
    "perimetro_torax_mesoesternal": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 87.86,
        "sd": 5.18,
    },
    "perimetro_cintura_minima": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 71.91,
        "sd": 4.45,
    },
    "perimetro_abdominal_maxima": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 79.06,
        "sd": 6.95,
    },
    "perimetro_cadera_maximo": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 94.67,
        "sd": 5.58,
    },
    "perimetro_muslo_maximo": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 55.82,
        "sd": 4.23,
    },
    "perimetro_muslo_medial": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 53.2,
        "sd": 4.56,
    },
    "perimetro_pantorrilla_maxima": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 35.25,
        "sd": 2.3,
    },
    "perimetro_tobillo_minima": {
        "grupo": "perimetros",
        "decimals": 1,
        "tipo": "repetible",
        "media": 21.71,
        "sd": 1.33,
    },

    # -----------------
    # PLIEGUES
    # -----------------
    "pliegue_triceps": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 15.4,
        "sd": 4.47,
    },
    "pliegue_subescapular": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 17.2,
        "sd": 5.07,
    },
    "pliegue_biceps": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 8.0,
        "sd": 2.0,
    },
    "pliegue_cresta_iliaca": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 22.4,
        "sd": 6.8,
    },
    "pliegue_supraespinal": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 15.4,
        "sd": 4.47,
    },
    "pliegue_abdominal": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 25.4,
        "sd": 7.78,
    },
    "pliegue_muslo_frontal": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 27.0,
        "sd": 8.33,
    },
    "pliegue_pantorrilla_maxima": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 16.0,
        "sd": 4.67,
    },
    "pliegue_antebrazo": {
        "grupo": "pliegues",
        "decimals": 1,
        "tipo": "repetible",
        "media": 16.0,
        "sd": 4.67,
    },
}

ISAK_DECIMALS = {
    k: v["decimals"] for k, v in ISAK_FIELDS.items()
}

ISAK_ESTRUCTURALES = [
    k for k, v in ISAK_FIELDS.items() if v["tipo"] == "estructural"
]

ISAK_REPETIBLES = [
    k for k, v in ISAK_FIELDS.items() if v["tipo"] == "repetible"
]

def build_isak_z_referencias() -> dict:
    """
    Construye el diccionario de referencias Z a partir de ISAK_FIELDS.

    Reglas:
    - Solo incluye campos con media y sd válidos
    - sd debe ser > 0
    - Devuelve estructura inmutable
    """
    z_refs: dict[str, dict] = {}

    for field, meta in ISAK_FIELDS.items():
        media = meta.get("media")
        sd = meta.get("sd")

        if media is None or sd is None:
            continue

        media = float(media)
        sd = float(sd)

        if sd <= 0:
            raise ValueError(
                f"SD inválida para '{field}': {sd}. Debe ser > 0."
            )

        z_refs[field] = {
            "media": media,
            "sd": sd,
            "grupo": meta.get("grupo"),
            "decimals": meta.get("decimals", 2),
            "tipo": meta.get("tipo"),
        }

    # Devuelve diccionario inmutable
    return MappingProxyType(z_refs)

ISAK_Z_REFERENCIAS = build_isak_z_referencias()

def new_base_record(id_jugadora: str, username: str) -> dict:
    """
    Cabecera de sesión ISAK.
    """
    now = datetime.datetime.now()
    #.isoformat()

    return {
        # --- PK / FK ---
        "id_isak": None,
        "id_jugadora": id_jugadora,

        # --- Metadata ISAK ---
        "metodo": "ISAK",
        "tipo_isak": "COMPLETO",             
        "fecha_medicion": now,

        # --- Observaciones ---
        "observaciones": "",

        # --- Auditoría ---
        "usuario": username,
        "created_at": now,
        "updated_at": None,
        "modified_by": None,

        # --- Control lógico ---
        "estatus_id": 1,
        "deleted_at": None,
        "deleted_by": None,
    }

def build_empty_record(id_jugadora: str, username: str) -> dict:
    """
    Record de formulario ISAK vacío (COMPLETO).
    Incluye cabecera + todos los campos raw inicializados.
    """

    # Cabecera ISAK
    record = new_base_record(
        id_jugadora=id_jugadora,
        username=username
    )

    # Modo de formulario
    record["_modo"] = "COMPLETO"

    # ---------------------------------------
    # Datos básicos
    # ---------------------------------------
    record.update({
        "peso_bruto_kg": None,
        "talla_corporal_cm": None,
        "talla_sentado_cm": None,
        "envergadura_cm": None,
    })

    # ---------------------------------------
    # Longitudes
    # ---------------------------------------
    record.update({
        "acromial_radial": None,
        "radial_estiloidea": None,
        "medial_estiloidea_dactilar": None,
        "ilioespinal": None,
        "trocanterea": None,
        "troc_tibial_lateral": None,
        "tibial_lateral": None,
        "tibial_medial_maleolar_medial": None,
        "pie": None,
    })

    # ---------------------------------------
    # Diámetros
    # ---------------------------------------
    record.update({
        "biacromial": None,
        "humeral_biepicondilar": None,
        "femoral_biepicondilar": None,
        "muneca_biestiloideo": None,
        "tobillo_bimaleolar": None,
        "bi_iliocrestideo": None,
        "torax_transverso": None,
        "torax_antero_posterior": None,
        "mano": None,
    })

    # ---------------------------------------
    # Perímetros (repetibles)
    # ---------------------------------------
    record.update({
        "perimetro_cabeza": None,
        "perimetro_cuello": None,
        "perimetro_brazo_relajado": None,
        "perimetro_brazo_flexionado_en_tension": None,
        "perimetro_antebrazo_maximo": None,
        "perimetro_muneca": None,
        "perimetro_torax_mesoesternal": None,
        "perimetro_cintura_minima": None,
        "perimetro_abdominal_maxima": None,
        "perimetro_cadera_maximo": None,
        "perimetro_muslo_maximo": None,
        "perimetro_muslo_medial": None,
        "perimetro_pantorrilla_maxima": None,
        "perimetro_tobillo_minima": None,
    })

    # ---------------------------------------
    # Pliegues (repetibles)
    # ---------------------------------------
    record.update({
        "pliegue_triceps": None,
        "pliegue_subescapular": None,
        "pliegue_biceps": None,
        "pliegue_cresta_iliaca": None,
        "pliegue_supraespinal": None,
        "pliegue_abdominal": None,
        "pliegue_muslo_frontal": None,
        "pliegue_pantorrilla_maxima": None,
        "pliegue_antebrazo": None,
    })

    return record

