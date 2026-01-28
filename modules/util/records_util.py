import streamlit as st
import random
from datetime import timedelta, date

def generar_valores_antropometria():
    peso = round(random.uniform(55, 75), 1)
    grasa = round(random.uniform(16, 28), 1)
    muscular = round(random.uniform(38, 48), 1)

    masa_osea = round(random.uniform(2.3, 3.2), 2)
    imo = round(muscular / masa_osea, 2)

    return {
        "peso_bruto_kg": peso,
        "talla_corporal_cm": round(random.uniform(158, 178), 1),
        "suma_6_pliegues_mm": round(random.uniform(45, 85), 1),
        "ajuste_adiposa_pct": grasa,
        "ajuste_muscular_pct": muscular,
        "masa_osea_kg": masa_osea,
        "indice_musculo_oseo": imo,
    }

def generar_fechas(
    fecha_inicio: date,
    fecha_fin: date,
    n: int,
    min_dias_sep: int = 28,
):
    # Validación rango mínimo (6 meses ≈ 180 días)
    if (fecha_fin - fecha_inicio).days < 180:
        raise ValueError("El rango de fechas debe ser de al menos 6 meses.")

    fechas = []
    fecha_actual = fecha_inicio

    for _ in range(n):
        fecha_actual = fecha_actual + timedelta(days=min_dias_sep)
        if fecha_actual > fecha_fin:
            break
        fechas.append(fecha_actual)

    return fechas
