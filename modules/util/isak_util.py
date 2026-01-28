
import pandas as pd
from modules.schema import ISAK_ESTRUCTURALES, ISAK_REPETIBLES, ISAK_DECIMALS, ISAK_Z_REFERENCIAS, ISAK_FIELDS
from decimal import Decimal
import datetime
from modules.i18n.i18n import t
from modules.util.util import f0
import streamlit as st

def normalize_isak_numeric(record: dict) -> dict:
    """
    Normaliza un record ISAK para cálculos:
    - Decimal → float
    - No redondea
    - No elimina campos
    """
    normalized = {}

    for k, v in record.items():
        if isinstance(v, Decimal):
            normalized[k] = float(v)
        else:
            normalized[k] = v

    return normalized

def normalize_isak_record(record: dict) -> dict:
    """
    Normaliza el record ISAK antes de persistir en BD.

    - Redondea valores numéricos según ISAK_DECIMALS
    - Convierte "None" (str) → None
    - Convierte fechas a string ISO (sin microsegundos)
    - Elimina campos internos de UI (_modo, etc.)
    """

    normalized = {}

    for field, value in record.items():

        # -----------------------------
        # 1. Campos internos (UI / control)
        # -----------------------------
        if field.startswith("_"):
            continue

        # -----------------------------
        # 2. "None" string → None real
        # -----------------------------
        if value == "None":
            normalized[field] = None
            continue

        # -----------------------------
        # 3. Normalizar datetime → string ISO
        # -----------------------------
        if field == "fecha_medicion":
            if isinstance(value, datetime.datetime):
                normalized[field] = value.date().isoformat()
                continue

            if isinstance(value, datetime.date):
                normalized[field] = value.isoformat()
                continue

            # Si ya viene como string, se deja pasar
            normalized[field] = value
            continue
        
        if isinstance(value, datetime.datetime):
            normalized[field] = value.replace(microsecond=0).isoformat()
            continue

        if isinstance(value, datetime.date):
            normalized[field] = datetime.datetime.combine(
                value, datetime.time(0, 0)
            ).isoformat()
            continue
        
        # -----------------------------
        # 4. Normalizar floats ISAK
        # -----------------------------
        if field in ISAK_DECIMALS and isinstance(value, (int, float)):
            normalized[field] = round(value, ISAK_DECIMALS[field])
            continue

        # -----------------------------
        # 5. Valor por defecto
        # -----------------------------
        normalized[field] = value

    return normalized

def validate_isak_record(record: dict) -> tuple[bool, str]:
    """
    Valida una sesión ISAK a nivel matemático / estructural
    (NO fisiológico).
    """

    # -------------------------
    # Campos mínimos de cabecera
    # -------------------------
    required = ["id_jugadora", "fecha_medicion", "tipo_isak", "usuario"]
    missing = [k for k in required if not record.get(k)]

    if missing:
        return False, t("Faltan campos obligatorios: {fields}").format(
            fields=", ".join(missing)
        )

    # -------------------------
    # Blindaje tipo / modo
    # -------------------------
    modo = record.get("_modo")
    tipo = str(record.get("tipo_isak", "")).upper().strip()

    if modo not in ("COMPLETO", "SEGUIMIENTO"):
        return False, t("Modo ISAK inválido")

    # En tu modelo SIEMPRE guardas COMPLETO
    if tipo != "COMPLETO":
        record["tipo_isak"] = "COMPLETO"

    # -------------------------
    # Campos a validar
    # -------------------------
    campos_obligatorios = ISAK_REPETIBLES.copy()

    if modo == "COMPLETO":
        campos_obligatorios += ISAK_ESTRUCTURALES

    # -------------------------
    # Validación numérica básica
    # -------------------------
    faltantes = []

    #st.dataframe(record)

    for field in campos_obligatorios:
        value = record.get(field)
        #print(f"field: {field}, value: {value}")
        if value is None:
            faltantes.append(field)
            continue
          
        if isinstance(value, (int, float)):
            if value <= 0:
                faltantes.append(field)
        else:
            faltantes.append(field)

        
    if faltantes:
        return False, t(
            "Faltan o son inválidos los siguientes campos ISAK: {fields}"
        ).format(fields=", ".join(faltantes))

    # -------------------------
    # Validaciones críticas para fórmulas
    # -------------------------
    # Talla (evita divisiones por cero)
    talla = record.get("talla_corporal_cm")
    if not talla or talla <= 0:
        return False, t("La talla debe ser mayor que 0 para los cálculos")

    # Peso
    peso = record.get("peso_bruto_kg")
    if not peso or peso <= 0:
        return False, t("El peso debe ser mayor que 0 para los cálculos")

    # -------------------------
    # Pliegues usados en suma de 6
    # -------------------------
    pliegues_suma_6 = [
        "pliegue_triceps",
        "pliegue_subescapular",
        "pliegue_supraespinal",
        "pliegue_abdominal",
        "pliegue_muslo_frontal",
        "pliegue_pantorrilla_maxima",
    ]

    faltan_pliegues = [
        p for p in pliegues_suma_6
        if record.get(p) is None or record.get(p) <= 0
    ]

    if faltan_pliegues:
        return False, t(
            "Pliegues necesarios para los cálculos no válidos: {fields}"
        ).format(fields=", ".join(faltan_pliegues))

    # -------------------------
    # fecha_medicion
    # -------------------------
    fm = record["fecha_medicion"]

    if isinstance(fm, str):
        try:
            record["fecha_medicion"] = pd.to_datetime(fm).to_pydatetime()
        except Exception:
            return False, t("fecha_medicion inválida")

    elif isinstance(fm, datetime.date) and not isinstance(fm, datetime.datetime):
        record["fecha_medicion"] = datetime.datetime.combine(
            fm, datetime.time(0, 0)
        )

    elif not isinstance(fm, datetime.datetime):
        return False, t("fecha_medicion debe ser fecha o datetime válido")

    # -------------------------
    # OK
    # -------------------------
    return True, ""

##############
## CALCULOS
##############

def calcular_masa_osea_excel(raw: dict) -> tuple[float, float]:
    """
    Calcula masa ósea TOTAL según el modelo del Excel (cabeza + cuerpo),
    con z-scores y corrección por talla.
    """

    talla_corporal_cm = float(raw["talla_corporal_cm"])
    if talla_corporal_cm <= 0:
        return 0.0, 0.0

    # Factor alométrico de talla (170.18 / talla_corporal_cm)
    factor_talla = 170.18 / talla_corporal_cm

    # -------------------------
    # 1) Masa ósea cabeza (Excel)
    # -------------------------
    per_cabeza = float(raw["perimetro_cabeza"])
    z_cabeza = (per_cabeza - 56.0) / 1.44
    masa_osea_cabeza = (z_cabeza * 0.18) + 1.2

    # -------------------------
    # 2) Masa ósea cuerpo (Excel)
    #    Suma de diámetros:
    #    biacromial + bi_iliocrestideo + 2*humeral_biepicondilar + 2*femoral_biepicondilar
    # -------------------------
    biacromial = float(raw["biacromial"])
    bi_iliocrestideo = float(raw["bi_iliocrestideo"] or 0)
    h_biepicondilar = float(raw["humeral_biepicondilar"] or 0)
    f_biepicondilar = float(raw["femoral_biepicondilar"] or 0)

    suma_diametros = (
        biacromial
        + bi_iliocrestideo
        + (h_biepicondilar * 2.0)
        + (f_biepicondilar * 2.0)
    )

    z_cuerpo = ((suma_diametros * factor_talla) - 98.88) / 5.33
    masa_osea_cuerpo = ((z_cuerpo * 1.34) + 6.7) / (factor_talla ** 3)

    # -------------------------
    # Total
    # -------------------------
    masa_osea_total = masa_osea_cabeza + masa_osea_cuerpo
    return round(masa_osea_total, 4), round(z_cuerpo, 4)

def calcular_masa_piel_excel(raw: dict) -> float:
    """
    Masa de la Piel (kg) EXACTA del Excel (Proc datos brutos).
    B67 = (constante * peso^0.425 * talla^0.725) / 10000
    B68 = (B67 * grosor_piel * 1.05)
    """
    peso = float(raw["peso_bruto_kg"])
    talla_corporal_cm = float(raw["talla_corporal_cm"])

    # Sexo: en el Excel I2=1 masculino, I2=2 femenino.
    # En tu sistema normalmente es femenino, pero lo dejo flexible.
    sexo_id = raw.get("sexo_id", None)  # 1=M, 2=F
    sexo = str(raw.get("sexo", "")).strip().upper()  # "M" / "F" si existe
    edad = raw.get("edad", None)

    if sexo_id == 1 or sexo == "M":
        grosor_piel = 2.07
        constante = 68.308
    else:
        grosor_piel = 1.96
        constante = 73.074

    # Si manejas <12 años (en tu contexto casi seguro no aplica)
    try:
        if edad is not None and float(edad) < 12:
            constante = 70.691
    except Exception:
        pass

    area_superficial = (constante * (peso ** 0.425) * (talla_corporal_cm ** 0.725)) / 10000.0
    masa_piel = area_superficial * grosor_piel * 1.05

    return round(masa_piel, 4)

def calcular_masa_residual_excel(raw: dict) -> tuple[float, float]:
    """
    Masa Residual (kg) EXACTA del Excel (Proc datos brutos).
    B86 = cintura - (pliegue_abdominal*0.3141)
    B87 = torax_transverso + torax_antero_posterior + B86
    B88 = (B87*(89.92/talla_sentado) - 109.35)/7.08
    B89 = ((B88*1.24)+6.1)/(89.92/talla_sentado)^3
    """
    talla_sentado = float(raw["talla_sentado_cm"])
    if talla_sentado <= 0:
        return 0.0, 0.0

    cintura = float(raw["perimetro_cintura_minima"])
    pl_abd = float(raw["pliegue_abdominal"])
    torax_trans = float(raw["torax_transverso"])
    antero_post = float(raw["torax_antero_posterior"])

    per_cintura_corregido = cintura - (pl_abd * 0.3141)
    suma_torax = torax_trans + antero_post + per_cintura_corregido

    factor = 89.92 / talla_sentado
    z_residual = ((suma_torax * factor) - 109.35) / 7.08
    masa_residual = ((z_residual * 1.24) + 6.1) / (factor ** 3)

    return round(masa_residual, 4), round(z_residual, 4)

def calcular_masa_muscular_excel(raw: dict) -> tuple[float, float]:
    """
    Masa muscular (kg) EXACTA del Excel (Proc datos brutos).
    NO se calcula por diferencia.
    """

    talla_corporal_cm = float(raw["talla_corporal_cm"])
    if talla_corporal_cm <= 0:
        return 0.0, 0.0

    # Datos necesarios
    per_brazo = float(raw["perimetro_brazo_relajado"])
    per_antebrazo = float(raw["perimetro_antebrazo_maximo"])
    per_muslo = float(raw["perimetro_muslo_maximo"])
    per_pantorrilla = float(raw["perimetro_pantorrilla_maxima"])
    per_torax = float(raw["perimetro_torax_mesoesternal"])

    pl_triceps = float(raw["pliegue_triceps"])
    pl_muslo = float(raw["pliegue_muslo_frontal"])
    pl_pantorrilla = float(raw["pliegue_pantorrilla_maxima"])
    pl_subescapular = float(raw["pliegue_subescapular"])

    # Correcciones
    pi = 3.141
    brazo_corr = per_brazo - ((pl_triceps * pi) / 10.0)
    #print(brazo_corr)
    
    muslo_corr = per_muslo - ((pl_muslo * pi) / 10.0)
    #print(muslo_corr)
    
    pantorrilla_corr = per_pantorrilla - ((pl_pantorrilla * pi) / 10.0)
    #print(pantorrilla_corr)

    torax_corr = per_torax - ((pl_subescapular * pi) / 10.0)
    
    suma_muscular = brazo_corr + per_antebrazo + muslo_corr + pantorrilla_corr + torax_corr
    
    factor_talla = 170.18 / talla_corporal_cm

    z_muscular = ((suma_muscular * factor_talla) - 207.21) / 13.74

    masa_muscular = ((z_muscular * 5.4) + 24.5) / (factor_talla ** 3)

    return round(masa_muscular, 4), round(z_muscular, 4)

def calcular_masa_adiposa_excel(
    suma_6: float,
    talla_corporal_cm: float,
    peso_kg: float,
) -> tuple[float, float]:
    """
    Modelo ISAK alométrico EXACTO usado en el Excel.
    Devuelve:
    - masa_adiposa_kg
    - pct_adiposo
    """

    if talla_corporal_cm <= 0 or peso_kg <= 0:
        return 0.0, 0.0

    # Factor alométrico de talla
    factor_talla = 170.18 / talla_corporal_cm

    # Z-score de pliegues
    z_pliegues = (suma_6 * factor_talla - 116.41) / 34.79

    # Masa adiposa relativa
    masa_adiposa_rel = ((z_pliegues * 5.85) + 25.6) / (factor_talla ** 3)

    return round(masa_adiposa_rel, 4), round(z_pliegues, 4)

def indice_masa(masa: float, talla_m: float) -> float:
    """
    Índice masa / talla² (ISAK).
    Protegido contra división por cero y None.
    """
    try:
        masa = float(masa)
        talla_m = float(talla_m)
    except (TypeError, ValueError):
        return 0.0

    if talla_m <= 0:
        return 0.0

    return round(masa / (talla_m ** 2), 4)

def indice_musculo_oseo(masa_muscular, masa_osea):
    if masa_osea <= 0:
        return None
    return round(masa_muscular / masa_osea, 4)

def indice_musculo_lastre(musculo, adiposa, residual):
    lastre = adiposa + residual
    if lastre <= 0:
        return None
    return round(musculo / lastre, 4)

def calcular_indice_lastre(masa_muscular_kg: float, suma_5_masas_kg: float, talla_corporal_cm: float) -> float | None:

    if talla_corporal_cm <= 0:
        return None

    lastre = suma_5_masas_kg - masa_muscular_kg

    idx = (lastre * 1000) / (talla_corporal_cm ** 2)

    return round(idx, 4)

def calcular_imc(peso_kg: float, talla_m: float) -> float:
    if talla_m <= 0:
        return None
    return round(peso_kg / (talla_m ** 2), 3)

def calcular_suma_3_pliegues(raw: dict) -> float:
    suma = (
        raw["pliegue_subescapular"]
        + raw["pliegue_supraespinal"]
        + raw["pliegue_abdominal"]
    )
    return round(suma, 2)

def indice_cintura_cadera(cintura_cm: float, cadera_cm: float) -> float:
    if cadera_cm <= 0:
        return None
    return round(cintura_cm / cadera_cm, 3)

def indice_cintura_talla(cintura_cm: float, talla_corporal_cm: float) -> float:
    if talla_corporal_cm <= 0:
        return None
    return round(cintura_cm / talla_corporal_cm, 3)

def ajustar_masas_por_masa_osea_ref(
    *,
    peso_kg: float,
    aj_adiposa: dict,
    aj_muscular: dict,
    aj_osea: dict,
    aj_residual: dict,
    aj_piel: dict,
    aj_peso_estructurado: dict,
    masa_osea_ref_kg: float | None,
) -> dict:
    """
    Reajuste por Masa Ósea de Referencia (MOR).
    Devuelve masas finales coherentes y agregados necesarios para índices.
    """

    # -------------------------------------------------
    # 1. Masa ósea final (MOR)
    # -------------------------------------------------
    masa_osea_actual = f0(aj_osea.get("masa_ajustada_kg"))
    mor = f0(masa_osea_ref_kg) if masa_osea_ref_kg is not None else masa_osea_actual
    mor = max(0.0, mor)

    delta_osea = mor - masa_osea_actual

    # -------------------------------------------------
    # 2. Suma de las 4 masas NO óseas (cruda)
    # -------------------------------------------------
    suma_4_cruda = (
        f0(aj_adiposa.get("masa_ajustada_kg"))
        + f0(aj_muscular.get("masa_ajustada_kg"))
        + f0(aj_residual.get("masa_ajustada_kg"))
        + f0(aj_piel.get("masa_ajustada_kg"))
    )

    # Caso degenerado → no se puede repartir
    if suma_4_cruda <= 0:
        suma_5 = mor
        return {
            "masa_adiposa_kg": 0.0,
            "masa_muscular_kg": 0.0,
            "masa_residual_kg": 0.0,
            "masa_piel_kg": 0.0,
            "masa_osea_kg": round(mor, 3),
            "peso_estructurado_kg": round(f0(peso_kg), 3),
            "suma_4_masas_kg": 0.0,
            "suma_5_masas_kg": round(suma_5, 3),
            "delta_osea_kg": round(delta_osea, 3),
        }

    # -------------------------------------------------
    # 3. Porcentajes reales de las 4 masas (0–1)
    # -------------------------------------------------
    pct4_adiposa = f0(aj_adiposa.get("masa_ajustada_kg")) / suma_4_cruda
    pct4_muscular = f0(aj_muscular.get("masa_ajustada_kg")) / suma_4_cruda
    pct4_residual = f0(aj_residual.get("masa_ajustada_kg")) / suma_4_cruda
    pct4_piel = f0(aj_piel.get("masa_ajustada_kg")) / suma_4_cruda

    # -------------------------------------------------
    # 4. Corrección por delta óseo
    # -------------------------------------------------
    adiposa_corr = f0(aj_adiposa.get("masa_ajustada_kg")) - delta_osea * pct4_adiposa
    muscular_corr = f0(aj_muscular.get("masa_ajustada_kg")) - delta_osea * pct4_muscular
    residual_corr = f0(aj_residual.get("masa_ajustada_kg")) - delta_osea * pct4_residual
    piel_corr = f0(aj_piel.get("masa_ajustada_kg")) - delta_osea * pct4_piel

    # Seguridad: no permitir masas negativas
    adiposa_corr = max(0.0, adiposa_corr)
    muscular_corr = max(0.0, muscular_corr)
    residual_corr = max(0.0, residual_corr)
    piel_corr = max(0.0, piel_corr)

    # -------------------------------------------------
    # 5. Sumas finales
    # -------------------------------------------------
    suma_4_corr = adiposa_corr + muscular_corr + residual_corr + piel_corr
    suma_5_corr = suma_4_corr + mor

    # -------------------------------------------------
    # 6. Resultado FINAL
    # -------------------------------------------------
    return {
        "masa_adiposa_kg": round(adiposa_corr, 3),
        "masa_muscular_kg": round(muscular_corr, 3),
        "masa_residual_kg": round(residual_corr, 3),
        "masa_piel_kg": round(piel_corr, 3),
        "masa_osea_kg": round(mor, 3),

        # porcentajes internos (0–1)
        "pct_4_adiposo": round(pct4_adiposa, 5),
        "pct_4_muscular": round(pct4_muscular, 5),
        "pct_4_residual": round(pct4_residual, 5),
        "pct_4_piel": round(pct4_piel, 5),

        # agregados CLAVE
        "suma_4_masas_kg": round(suma_4_corr, 3),
        "suma_5_masas_kg": round(suma_5_corr, 3),

        # auditoría
        "delta_osea_kg": round(delta_osea, 3),
        "peso_estructurado_kg": round(f0(peso_kg), 3),
    }

def ajustar_masa_por_porcentaje(
    *,
    masa_kg: float,
    peso_estructurado_kg: float,
    diferencia_peso_kg: float,
) -> dict:
    """
    Replica EXACTAMENTE las columnas C, D y E del Excel:

    C (%): pct_actual = masa / peso_estructurado
    D (Ajuste): (pct_objetivo - pct_actual) * peso_estructurado
    E (Kg): masa ajustada
    """

    if peso_estructurado_kg <= 0:
        return {
            "pct": None,
            "ajuste_kg": 0.0,
            "masa_ajustada_kg": masa_kg,
        }

    pct_actual = masa_kg / peso_estructurado_kg
    ajuste_kg = diferencia_peso_kg * pct_actual
    masa_ajustada = masa_kg - ajuste_kg

    return {
        "pct": round(pct_actual * 100, 2),     # columna C (%)
        "ajuste_kg": round(ajuste_kg, 3),      # columna D (Ajustes)
        "masa_ajustada_kg": round(masa_ajustada, 3),  # columna E (Kg)
    }

def sumar_ajustes_masas(*ajustes_masas: dict) -> dict:
    suma_pct = 0.0
    suma_ajuste = 0.0
    suma_kg = 0.0

    
    for ajuste in ajustes_masas:
        if not isinstance(ajuste, dict):
            continue

        suma_pct += f0(ajuste.get("pct"))
        suma_ajuste += f0(ajuste.get("ajuste_kg"))
        suma_kg += f0(ajuste.get("masa_ajustada_kg"))

    return {
        "pct": round(suma_pct),
        "ajuste_kg": round(suma_ajuste, 2),
        "masa_ajustada_kg": round(suma_kg, 2)
    }

##################
## PRESENTACION ##
##################

def ajuste_alometrico(valor: float, talla_cm: float, tipo: int) -> float:
    """
    Ajuste alométrico ISAK / Phantom:
    valor * (170.18 / talla)^3
    """

    if talla_cm <= 0:
        raise ValueError("La talla debe ser > 0")

    if tipo == 1:
        result =  round(valor * (170.18 / talla_cm) ** 3, 2)
    else:
        result =  round(valor * (170.18 / talla_cm), 2)

    #print(f"ajuste_alometrico = valor: {valor}, talla_cm: {talla_cm} = {result}")
    return result

def calcular_zscore(clave: str, valor: float, media: float, sd: float, decimals: int = 2) -> float:
    if sd <= 0:
        raise ValueError("SD debe ser > 0")
    
    result = round((valor - media) / sd, decimals)
    #print(f"z_score: clave: {clave}, valor: {valor}, media: {media}, sd: {sd} = {result}")
    return result

def calcular_z_raw(raw: dict, isak_z_refs: dict) -> dict:
    """
    Calcula Z-scores ISAK (columna K),
    replicando exactamente la lógica Excel:
    - Ajuste alométrico SOLO si corresponde
    - Luego Z-score contra media y SD
    """

    z_raw: dict[str, float] = {}

    talla = raw.get("talla_corporal_cm")
    if talla is None:
        return z_raw

    try:
        talla = float(talla)
    except (TypeError, ValueError):
        return z_raw

    if talla <= 0:
        return z_raw

    for clave, ref in isak_z_refs.items():
        valor_raw = raw.get(clave)
        if valor_raw is None:
            continue

        try:
            valor_raw = float(valor_raw)
        except (TypeError, ValueError):
            continue
        
        #print(clave)
        media = ref["media"]
        sd = ref["sd"]
        #decimals = ref.get("decimals", 4)
        tipo = 1 if clave == "peso_bruto_kg" else 2

        # --- Columna F: ajuste alométrico ---
        #if media != None:
        valor_usado = ajuste_alometrico(valor_raw, talla, tipo)
        #else:
        #    valor_usado = valor_raw


        # --- Columna K: Z-score ---
        try:
            z_raw[clave] = calcular_zscore(
                clave=clave,
                valor=valor_usado,
                media=media,
                sd=sd
            )
        except ValueError:
            print(f"se omite el calculo para {clave}")
            continue

    return z_raw

#################
#################
def calcular_antropometria(raw: dict) -> dict:
    """
    Calcula composición corporal ISAK completa (modelo clásico).
    Devuelve SOLO valores calculados.
    """
    # -------------------------
    # Básicos
    # -------------------------
    peso = float(raw["peso_bruto_kg"])
    talla_corporal_cm = float(raw["talla_corporal_cm"])
    talla_m = talla_corporal_cm / 100

    # -------------------------
    # Suma 6 pliegues
    # -------------------------
    suma_6 = (
        raw["pliegue_triceps"]
        + raw["pliegue_subescapular"]
        + raw["pliegue_supraespinal"]
        + raw["pliegue_abdominal"]
        + raw["pliegue_muslo_frontal"]
        + raw["pliegue_pantorrilla_maxima"]
    )

    # -------------------------
    # Masa adiposa
    # -------------------------
    masa_adiposa, z_adiposa = calcular_masa_adiposa_excel(suma_6=suma_6, talla_corporal_cm=talla_corporal_cm, peso_kg=peso)

    # -------------------------
    # Masa ósea
    # -------------------------
    
    masa_osea, z_osea = calcular_masa_osea_excel(raw) or 0

    # -------------------------
    # Masas fijas
    # -------------------------
    masa_residual, z_residual = calcular_masa_residual_excel(raw)
    masa_piel = calcular_masa_piel_excel(raw)

    # -------------------------
    # Masa muscular
    # -------------------------
    masa_muscular, z_muscular = calcular_masa_muscular_excel(raw)

    # -------------------------
    # Peso estructurado
    # -------------------------
    peso_estructurado = (
        masa_adiposa
        + masa_muscular
        + masa_osea
        + masa_residual
        + masa_piel
    )
    
    diferencia_peso = (peso_estructurado - peso)

    if peso > 0:
        diferencia_pct = ((peso_estructurado - peso) / peso) * 100
    else:
        diferencia_pct = 0.0

    ajuste_adiposa = ajustar_masa_por_porcentaje(
        masa_kg=masa_adiposa,
        peso_estructurado_kg=peso_estructurado,
        diferencia_peso_kg=diferencia_peso
    )

    ajuste_muscular = ajustar_masa_por_porcentaje(
        masa_kg=masa_muscular,
        peso_estructurado_kg=peso_estructurado,
        diferencia_peso_kg=diferencia_peso
    )

    ajuste_osea = ajustar_masa_por_porcentaje(
        masa_kg=masa_osea,
        peso_estructurado_kg=peso_estructurado,
        diferencia_peso_kg=diferencia_peso
    )

    ajuste_residual = ajustar_masa_por_porcentaje(
        masa_kg=masa_residual,
        peso_estructurado_kg=peso_estructurado,
        diferencia_peso_kg=diferencia_peso
    )

    ajuste_piel = ajustar_masa_por_porcentaje(
        masa_kg=masa_piel,
        peso_estructurado_kg=peso_estructurado,
        diferencia_peso_kg=diferencia_peso
    )

    ajuste_peso_estructurado = sumar_ajustes_masas(
        ajuste_adiposa,
        ajuste_muscular,
        ajuste_residual,
        ajuste_piel,
        ajuste_osea,
    )

    ajuste_peso_estructurado["ajuste_alometrico"] = ajuste_alometrico(valor=ajuste_peso_estructurado["masa_ajustada_kg"], talla_cm=talla_corporal_cm, tipo=1)

    ajuste = ajustar_masas_por_masa_osea_ref(
        peso_kg=peso,
        aj_adiposa=ajuste_adiposa,
        aj_muscular=ajuste_muscular,
        aj_osea=ajuste_osea,
        aj_residual=ajuste_residual,
        aj_piel=ajuste_piel,
        aj_peso_estructurado=ajuste_peso_estructurado,
        masa_osea_ref_kg=float(ajuste_osea.get("masa_ajustada_kg", 0.0))
    )

    # # Sobrescribes las masas por las corregidas (como Excel)
    # masa_adiposa = ajuste["masa_adiposa_kg"]
    # masa_muscular = ajuste["masa_muscular_kg"]
    # masa_residual = ajuste["masa_residual_kg"]
    # masa_piel = ajuste["masa_piel_kg"]
    # masa_osea = ajuste["masa_osea_kg"]
 
    # -------------------------
    # Índices (helpers)
    # -------------------------
    idx_adiposo = indice_masa(ajuste["masa_adiposa_kg"], talla_m)
    idx_muscular = indice_masa(ajuste["masa_muscular_kg"], talla_m)
    idx_oseo = indice_masa(ajuste["masa_osea_kg"], talla_m)
    idx_residual = indice_masa(ajuste["masa_residual_kg"], talla_m)
    idx_piel = indice_masa(ajuste["masa_piel_kg"], talla_m)

    idx_musculo_oseo = indice_musculo_oseo(ajuste["masa_muscular_kg"], ajuste["masa_osea_kg"])
    idx_musculo_lastre = indice_musculo_lastre(
        ajuste["masa_muscular_kg"], ajuste["masa_adiposa_kg"], ajuste["masa_residual_kg"]
    )

    idx_lastre = calcular_indice_lastre(ajuste["masa_muscular_kg"], ajuste["suma_5_masas_kg"], talla_corporal_cm)
    
    #suma_3 = calcular_suma_3_pliegues(raw)
    #imc = calcular_imc(peso, talla_m)

    z_raw = calcular_z_raw(raw, ISAK_Z_REFERENCIAS)

    # -------------------------
    # Resultado
    # -------------------------
    return {
        # --- Metadata ---
        "metodo": "ISAK",
        "metodo_masa_osea": "ROCHA",

        # --- Básicos ---
        #"peso_bruto_kg": round(peso, 2),
        #"talla_corporal_cm": round(talla_corporal_cm, 2),

        # --- Pliegues ---
        #"suma_3_pliegues_mm": suma_3,
        "suma_6_pliegues_mm": round(suma_6, 2),


        # --- Índices generales ---
        #"imc": imc,
        #"indice_cintura_cadera": idx_cintura_cadera,
        #"indice_cintura_talla": idx_cintura_talla,

        # --- Masas ---
        "masa_adiposa_kg": round(masa_adiposa, 2),
        "z_adiposa": round(z_adiposa, 2),
        "ajuste_adiposa": ajuste_adiposa,
        "masa_muscular_kg": round(masa_muscular, 2),
        "z_muscular": round(z_muscular, 2),
        "ajuste_muscular": ajuste_muscular,
        "masa_osea_kg": round(masa_osea, 2),
        "z_osea": round(z_osea, 2),
        "ajuste_osea": ajuste_osea,
        "masa_residual_kg": round(masa_residual, 2),
        "z_residual": round(z_residual, 2),
        "ajuste_residual": ajuste_residual,
        "masa_piel_kg": round(masa_piel, 2),
        "ajuste_piel": ajuste_piel,


        # # --- Porcentajes ---
        # "pct_adiposo": round((masa_adiposa / peso) * 100, 2),
        # "pct_muscular": round((masa_muscular / peso) * 100, 2),
        # "pct_oseo": round((masa_osea / peso) * 100, 2),
        # "pct_residual": round((masa_residual / peso) * 100, 2),
        # "pct_piel": round((masa_piel / peso) * 100, 2),

        # --- Índices estructurales ---
        "idx_adiposo": idx_adiposo,
        "idx_muscular": idx_muscular,
        "idx_oseo": idx_oseo,
        "idx_residual": idx_residual,
        "idx_piel": idx_piel,

        "idx_musculo_oseo": idx_musculo_oseo,
        "idx_musculo_lastre": idx_musculo_lastre,
        "idx_lastre": idx_lastre,

        # --- Control ---
        "peso_estructurado_kg": round(peso_estructurado, 3),
        "diferencia_peso": round(diferencia_peso, 3),
        "diferencia_peso_pct": round(diferencia_pct, 2),
        "ajuste_peso_estructurado": ajuste_peso_estructurado,
        #"ajuste_masa_osea": ajuste,
        "z_raw": z_raw
    }

def build_record_antropometrico(raw_record: dict) -> dict:
    """
    Construye un registro antropométrico completo a partir
    de un registro ISAK crudo (1 sesión).
    """

    # 1. Normalización estructural
    record = normalize_isak_record(raw_record)

    # 2. Normalización numérica
    record_numeric = normalize_isak_numeric(record)

    #st.dataframe(record_numeric)
    # 3. Cálculos ISAK
    calculos = calcular_antropometria(record_numeric)

    # 4. Ensamblado final
    return {
        **record_numeric,
        **calculos,
    }
