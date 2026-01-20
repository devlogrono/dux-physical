import streamlit as st
import pandas as pd
import json
import datetime

from modules.db.db_catalogs import load_catalog_list_db
from modules.db.db_client import query, execute

def get_records_db(as_df: bool = True):
    """
    Carga registros de antropometría con joins incluidos.
    """

    sql = """
        SELECT
            a.id_antropometria as id,
            a.id_jugadora as identificacion,

            f.nombre,
            f.apellido,
            f.competicion AS plantel,

            a.metodo,
            a.peso_kg,
            a.talla_cm,
            a.suma_6_pliegues_mm,
            a.porcentaje_grasa,
            a.porcentaje_muscular,
            a.masa_osea_kg,
            a.indice_musculo_oseo,

            a.observaciones,
            a.fecha_hora_registro as fecha_sesion,
            a.usuario

        FROM antropometria AS a
        LEFT JOIN futbolistas AS f
            ON a.id_jugadora = f.identificacion

        WHERE f.genero = 'F'
          AND f.id_estado = 1
          AND a.estatus_id <= 2

        ORDER BY a.fecha_hora_registro DESC;
    """

    rows = query(sql)
    if not rows:
        return pd.DataFrame() if as_df else []

    df = pd.DataFrame(rows)

    # Convertir fechas
    df["fecha_sesion"] = pd.to_datetime(
        df["fecha_sesion"], errors="coerce"
    )

    # Filtro por rol
    rol = st.session_state["auth"]["rol"].lower()
    if rol == "developer":
        df = df[df["usuario"] == "developer"]
    else:
        df = df[df["usuario"] != "developer"]

    # Columna nombre_jugadora
    df.insert(
        2,
        "nombre_jugadora",
        (df["nombre"] + " " + df["apellido"])
        .str.strip()
        .str.upper()
    )

    df = df.drop(columns=["nombre", "apellido"], errors="ignore")

    return df if as_df else df.to_dict("records")
   
def upsert_record_db(record: dict) -> bool:
    usuario_actual = st.session_state["auth"]["name"].lower()

    # ============================
    # UPDATE (edición explícita)
    # ============================
    if record.get("id_antropometria"):
        sql = """
            UPDATE antropometria
            SET
                metodo = %(metodo)s,
                peso_kg = %(peso_kg)s,
                talla_cm = %(talla_cm)s,
                suma_6_pliegues_mm = %(suma_6_pliegues_mm)s,
                porcentaje_grasa = %(porcentaje_grasa)s,
                porcentaje_muscular = %(porcentaje_muscular)s,
                masa_osea_kg = %(masa_osea_kg)s,
                indice_musculo_oseo = %(indice_musculo_oseo)s,
                observaciones = %(observaciones)s,
                updated_at = NOW(),
                modified_by = %(modified_by)s
            WHERE id_antropometria = %(id_antropometria)s
              AND deleted_at IS NULL;
        """

        params = {
            **record,
            "modified_by": usuario_actual,
        }

        return execute(sql, params)

    # ============================
    # INSERT
    # ============================
    sql = """
        INSERT INTO antropometria (
            id_jugadora,
            metodo,
            peso_kg,
            talla_cm,
            suma_6_pliegues_mm,
            porcentaje_grasa,
            porcentaje_muscular,
            masa_osea_kg,
            indice_musculo_oseo,
            observaciones,
            usuario,
            fecha_hora_registro,
            created_at,
            estatus_id
        ) VALUES (
            %(id_jugadora)s,
            %(metodo)s,
            %(peso_kg)s,
            %(talla_cm)s,
            %(suma_6_pliegues_mm)s,
            %(porcentaje_grasa)s,
            %(porcentaje_muscular)s,
            %(masa_osea_kg)s,
            %(indice_musculo_oseo)s,
            %(observaciones)s,
            %(usuario)s,
            %(fecha_hora_registro)s,
            NOW(),
            1
        );
    """

    params = {
        **record,
        "usuario": usuario_actual,
    }

    return execute(sql, params)


def delete_record(ids: list[int], deleted_by: str) -> tuple[bool, str]:
    """
    Soft-delete: marca registros de antropometria como eliminados.
    """
    if not ids:
        return False, "No se proporcionaron IDs de antropometría."

    placeholders = ",".join(["%s"] * len(ids))

    sql = f"""
        UPDATE antropometria
        SET
            deleted_at = NOW(),
            deleted_by = %s,
            estatus_id = 3
        WHERE id_antropometria IN ({placeholders});
    """

    params = tuple([deleted_by] + ids)

    ok = execute(sql, params)

    if ok:
        return True, f"Se eliminaron {len(ids)} registro(s) correctamente."
    else:
        return False, "Error al eliminar los registros."
