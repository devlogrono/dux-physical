import re
import unicodedata
from typing import Any, Dict
import os
import pandas as pd
from modules.schema import ISAK_FIELDS

import streamlit as st

from modules.util.util import compare_names, normalize_name
# =========================================================
# Utils
# =========================================================

# 🔒 estado interno SOLO para duplicados Excel
_NORMALIZE_DUP_COUNTER = {}

def reset_normalize_dup_counter():
    _NORMALIZE_DUP_COUNTER.clear()

def normalize_key(value: str) -> str:
    """
    Normaliza strings para matching robusto con ISAK_FIELDS:
    - lower
    - sin acentos
    - conserva unidades (kg, cm, mm) como sufijo
    - convierte separadores semánticos en "_"
    - resuelve duplicados (1º perímetro, 2º pliegue)
    """

    original_value = str(value).strip().lower()

    # --- normalizar acentos ---
    value = unicodedata.normalize("NFD", original_value)
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")

    # --- extraer unidades entre paréntesis ---
    units = ""
    match = re.search(r"\((.*?)\)", value)
    if match:
        units = match.group(1).strip()
        units = re.sub(r"[^a-z0-9]", "", units)

    # --- eliminar paréntesis del texto ---
    value = re.sub(r"\(.*?\)", "", value)

    # --- separadores semánticos ---
    value = value.replace("-", "_").replace("/", "_")

    # --- limpiar caracteres restantes ---
    value = re.sub(r"[^a-z0-9_ ]", "", value)
    value = value.replace(" ", "_")

    # --- añadir unidades ---
    if units:
        value = f"{value}_{units}"

    # --- normalizar underscores ---
    value = re.sub(r"_+", "_", value).strip("_")

    # ==================================================
    # 🔑 LÓGICA DUPLICADOS (Pantorrilla máxima)
    # ==================================================

    # contamos cuántas veces aparece este campo base
    count = _NORMALIZE_DUP_COUNTER.get(value, 0)
    _NORMALIZE_DUP_COUNTER[value] = count + 1

    isak_keys = set(ISAK_FIELDS.keys())

    # 1ª aparición → perímetro
    if count == 0:
        candidate = f"perimetro_{value}"
        if candidate in isak_keys:
            return candidate

    # 2ª aparición → pliegue
    if count == 1:
        candidate = f"pliegue_{value}"
        if candidate in isak_keys:
            return candidate

    # fallback a lógica original
    if not value.startswith("perimetro_"):
        candidate = f"perimetro_{value}"
        if candidate in isak_keys:
            return candidate

    if not value.startswith("pliegue_"):
        candidate = f"pliegue_{value}"
        if candidate in isak_keys:
            return candidate

    return value

def excel_col_to_index(col: str) -> int:
    col = col.upper()
    idx = 0
    for c in col:
        idx = idx * 26 + (ord(c) - ord("A") + 1)
    return idx - 1

def read_excel_cells(
    df: pd.DataFrame,
    row: int,
    cols: list[str]
) -> str | None:
    """
    Lee una o varias columnas de una fila (1-based).
    Concatena valores si hay más de una columna.
    """
    values = []
    r = row - 1

    for col in cols:
        c = excel_col_to_index(col)
        if r < len(df) and c < len(df.columns):
            val = df.iat[r, c]
            if pd.notna(val):
                values.append(str(val))

    return " ".join(values).strip() if values else None

def validate_jugadora_from_excel(
    df_excel: pd.DataFrame,
    mapper: dict,
    nombre_jugadora_app: str
) -> dict:
    """
    Devuelve resultado de validación del nombre.
    """
    config = mapper.get("jugadora_nombre")
    if not config:
        return {"status": "skip"}

    nombre_excel = read_excel_cells(
        df_excel,
        row=config["row"],
        cols=config["cols"],
    )

    if not nombre_excel:
        return {"status": "missing"}

    norm_excel = normalize_name(nombre_excel)
    norm_app = normalize_name(nombre_jugadora_app)

    score = compare_names(norm_excel, norm_app)

    return {
        "status": "ok" if score >= 0.85 else "warning",
        "excel": nombre_excel,
        "app": nombre_jugadora_app,
        "score": round(score * 100, 1),
    }

def get_excel_engine(file_path) -> str:
    filename = file_path.name if hasattr(file_path, "name") else str(file_path)
    ext = os.path.splitext(filename)[-1].lower()

    if ext == ".xlsx":
        return "openpyxl"
    elif ext == ".xls":
        return "xlrd"
    else:
        raise ValueError("Formato de archivo no soportado.")

# =========================================================
# Validación y Mapper estructura Excel ISAK
# =========================================================

def analyze_isak_excel_fields(df: pd.DataFrame, min_field: int = 40) -> dict:
    """
    Analiza campos ISAK desde un DataFrame vertical (campo / valor).
    Devuelve mapper, matched, missing y cobertura.
    """

    # Campos ISAK canónicos
    isak_fields = set(ISAK_FIELDS.keys())

    # Campos presentes en el Excel
    excel_fields = set(df["campo"].dropna().astype(str))

    matched = excel_fields & isak_fields
    missing = isak_fields - excel_fields
    #st.dataframe(missing)
    total_isak = len(isak_fields)
    coverage_pct = round((len(matched) / total_isak) * 100, 2) if total_isak else 0

    mapper = {field: field for field in matched}

    return {
        "mapper": mapper,
        "matched": sorted(matched),
        "missing": sorted(missing),
        "coverage_pct": coverage_pct,
        "is_valid": len(matched) >= min_field,
    }

# =========================================================
# Inspección y lectura de Excel
# =========================================================

def inspect_isak_excel(file_path) -> dict:
    engine = get_excel_engine(file_path)

    try:
        xls = pd.ExcelFile(file_path, engine=engine)
    except Exception as e:
        raise ValueError("El archivo no es un Excel válido.") from e

    return {
        "sheets": xls.sheet_names,
    }

def validate_isak_sheet(
    file_path,
    sheet_name: str | int
) -> None:
    engine = get_excel_engine(file_path)

    xls = pd.ExcelFile(file_path, engine=engine)

    if isinstance(sheet_name, int):
        if sheet_name < 0 or sheet_name >= len(xls.sheet_names):
            raise ValueError("Índice de hoja fuera de rango.")
    else:
        if sheet_name not in xls.sheet_names:
            raise ValueError(f"La hoja '{sheet_name}' no existe en el archivo.")

def read_isak_excel(file_path, sheet_name):
    """
    Lee una hoja ISAK con layout vertical:
    - Columna A: nombre del campo
    - Columna B: valor
    - Filas 5 a 55
    """

    engine = get_excel_engine(file_path)
    validate_isak_sheet(file_path, sheet_name)

    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        engine=engine,
        header=None,
        usecols=[0, 1],
        skiprows=4,
        nrows=51,
    )

    df = df.dropna(how="all")

    if df.empty:
        raise ValueError("La hoja ISAK no contiene datos válidos.")

    #st.dataframe(df)
    df.columns = ["campo", "valor"]
    df["campo"] = df["campo"].apply(normalize_key)
    #st.dataframe(df)

    # Elimina NaN / None en valor (pero conserva 0)
    df = df[~df["valor"].isna()]

    # Elimina strings vacíos o solo espacios
    df = df[
        ~(
            df["valor"]
            .astype(str)
            .str.strip()
            .eq("")
        )
    ]

    if df.empty:
        raise ValueError("La hoja ISAK no contiene valores utilizables.")

    return df

# =========================================================
# Construcción de record ISAK desde Excel
# =========================================================

def build_record_from_isak_excel_row(
    df: pd.DataFrame,
    isak_excel_map: dict[str, str]
) -> Dict[str, Any]:
    """
    Construye un dict ISAK RAW desde un DataFrame vertical campo/valor.
    """

    record: Dict[str, Any] = {}

    for _, row in df.iterrows():
        campo = row["campo"]
        valor = row["valor"]

        if campo not in isak_excel_map:
            continue

        isak_key = isak_excel_map[campo]

        if pd.isna(valor):
            record[isak_key] = None
            continue

        try:
            value = float(str(valor).replace(",", "."))
        except ValueError:
            record[isak_key] = None
            continue

        decimals = ISAK_FIELDS[isak_key].get("decimals", 1)
        record[isak_key] = round(value, decimals)

    return record
