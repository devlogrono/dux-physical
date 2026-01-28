import streamlit as st
import pandas as pd

from modules.db.db_client import query
from modules.db.db_connection import get_connection
from modules.schema import new_base_record

def get_records_db(as_df: bool = True):
    """
    Devuelve sesiones ISAK (COMPLETO) por jugadora.
    """
    sql = """
        SELECT
            i.id_isak,
            i.id_jugadora AS identificacion,
            i.tipo_isak,
            i.fecha_medicion,

            f.nombre,
            f.apellido,
            f.competicion AS plantel,

            i.usuario,
            i.created_at

        FROM antropometria_isak i
        INNER JOIN futbolistas f
            ON i.id_jugadora = f.identificacion

        WHERE f.genero = 'F'
          AND f.id_estado = 1
          AND i.estatus_id IN (1, 2)

        ORDER BY i.fecha_medicion DESC;
    """

    rows = query(sql)
    if not rows:
        return pd.DataFrame() if as_df else []

    df = pd.DataFrame(rows)
    df["fecha_medicion"] = pd.to_datetime(df["fecha_medicion"], errors="coerce")

    rol = st.session_state["auth"]["rol"].lower()
    if rol == "developer":
        df = df[df["usuario"] == "developer"]
    else:
        df = df[df["usuario"] != "developer"]

    df.insert(
        2,
        "nombre_jugadora",
        (df["nombre"] + " " + df["apellido"]).str.strip().str.upper()
    )

    df.drop(columns=["nombre", "apellido"], inplace=True, errors="ignore")
    return df if as_df else df.to_dict("records")

def get_isak_basicos(id_isak: int) -> dict | None:
    sql = """
        SELECT
            peso_bruto_kg,
            talla_corporal_cm,
            talla_sentado_cm,
            envergadura_cm
        FROM antropometria_isak_basicos
        WHERE id_isak = %s;
    """
    rows = query(sql, (id_isak,))
    return rows[0] if rows else None

def get_isak_perimetros(id_isak: int) -> dict | None:
    sql = """
        SELECT
            per_cabeza_cm                AS perimetro_cabeza,
            per_cuello_cm                AS perimetro_cuello,
            per_brazo_relajado_cm        AS perimetro_brazo_relajado,
            per_brazo_flexionado_tension_cm AS perimetro_brazo_flexionado_en_tension,
            per_antebrazo_maximo_cm      AS perimetro_antebrazo_maximo,
            per_muneca_cm                AS perimetro_muneca,
            per_torax_mesoesternal_cm    AS perimetro_torax_mesoesternal,
            per_cintura_minima_cm        AS perimetro_cintura_minima,
            per_abdominal_maxima_cm      AS perimetro_abdominal_maxima,
            per_cadera_maxima_cm         AS perimetro_cadera_maximo,
            per_muslo_maximo_cm          AS perimetro_muslo_maximo,
            per_muslo_medial_cm          AS perimetro_muslo_medial,
            per_pantorrilla_maxima_cm    AS perimetro_pantorrilla_maxima,
            per_tobillo_minima_cm        AS perimetro_tobillo_minima
        FROM antropometria_isak_perimetros
        WHERE id_isak = %s;
    """
    rows = query(sql, (id_isak,))
    return rows[0] if rows else None

def get_isak_pliegues(id_isak: int) -> dict | None:
    sql = """
        SELECT
            pl_triceps_mm         AS pliegue_triceps,
            pl_subescapular_mm    AS pliegue_subescapular,
            pl_biceps_mm          AS pliegue_biceps,
            pl_cresta_iliaca_mm   AS pliegue_cresta_iliaca,
            pl_supraespinal_mm    AS pliegue_supraespinal,
            pl_abdominal_mm       AS pliegue_abdominal,
            pl_muslo_frontal_mm   AS pliegue_muslo_frontal,
            pl_pantorrilla_maxima_mm AS pliegue_pantorrilla_maxima,
            pl_antebrazo_mm       AS pliegue_antebrazo
        FROM antropometria_isak_pliegues
        WHERE id_isak = %s;
    """
    rows = query(sql, (id_isak,))
    return rows[0] if rows else None

def get_isak_longitudes(id_isak: int) -> dict | None:
    sql = """
        SELECT
            len_acromial_radial_cm                AS acromial_radial,
            len_radial_estiloidea_cm              AS radial_estiloidea,
            len_medial_estiloidea_dactilar_cm     AS medial_estiloidea_dactilar,
            len_ilioespinal_cm                    AS ilioespinal,
            len_trocanterea_cm                    AS trocanterea,
            len_troc_tibial_lateral_cm            AS troc_tibial_lateral,
            len_tibial_lateral_cm                 AS tibial_lateral,
            len_tibial_medial_maleolar_medial_cm  AS tibial_medial_maleolar_medial,
            len_pie_cm                            AS pie
        FROM antropometria_isak_longitudes
        WHERE id_isak = %s;
    """
    rows = query(sql, (id_isak,))
    return rows[0] if rows else None

def get_isak_diametros(id_isak: int) -> dict | None:
    sql = """
        SELECT
            diam_biacromial_cm                AS biacromial,
            diam_torax_transverso_cm          AS torax_transverso,
            diam_torax_anteroposterior_cm     AS torax_antero_posterior,
            diam_biiliocrestideo_cm           AS bi_iliocrestideo,
            diam_humeral_biepicondilar_cm     AS humeral_biepicondilar,
            diam_femoral_biepicondilar_cm     AS femoral_biepicondilar,
            diam_muneca_biestiloideo_cm       AS muneca_biestiloideo,
            diam_tobillo_bimaleolar_cm        AS tobillo_bimaleolar,
            diam_mano_cm                      AS mano
        FROM antropometria_isak_diametros
        WHERE id_isak = %s;
    """
    rows = query(sql, (id_isak,))
    return rows[0] if rows else None

###############################

def insert_isak_session(cursor, record: dict) -> int:
    sql = """
        INSERT INTO antropometria_isak (
            id_jugadora,
            fecha_medicion,
            tipo_isak,
            observaciones,
            usuario,
            estatus_id
        ) VALUES (%s,%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        record["id_jugadora"],
        record["fecha_medicion"],
        record["tipo_isak"],
        record.get("observaciones"),
        record["usuario"],
        record.get("estatus_id", 1),
    ))
    return cursor.lastrowid

def insert_isak_basicos(cursor, id_isak: int, r: dict):
    sql = """
        INSERT INTO antropometria_isak_basicos (
            id_isak,
            peso_bruto_kg,
            talla_corporal_cm,
            talla_sentado_cm,
            envergadura_cm
        ) VALUES (%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        id_isak,
        r.get("peso_bruto_kg"),
        r.get("talla_corporal_cm"),
        r.get("talla_sentado_cm"),
        r.get("envergadura_cm"),
    ))

def insert_isak_longitudes(cursor, id_isak: int, r: dict):
    sql = """
        INSERT INTO antropometria_isak_longitudes (
            id_isak,
            len_acromial_radial_cm,
            len_radial_estiloidea_cm,
            len_medial_estiloidea_dactilar_cm,
            len_ilioespinal_cm,
            len_trocanterea_cm,
            len_troc_tibial_lateral_cm,
            len_tibial_lateral_cm,
            len_tibial_medial_maleolar_medial_cm,
            len_pie_cm
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        id_isak,
        r.get("acromial_radial"),
        r.get("radial_estiloidea"),
        r.get("medial_estiloidea_dactilar"),
        r.get("ilioespinal"),
        r.get("trocanterea"),
        r.get("troc_tibial_lateral"),
        r.get("tibial_lateral"),
        r.get("tibial_medial_maleolar_medial"),
        r.get("pie"),
    ))

def insert_isak_diametros(cursor, id_isak: int, r: dict):
    sql = """
        INSERT INTO antropometria_isak_diametros (
            id_isak,
            diam_biacromial_cm,
            diam_torax_transverso_cm,
            diam_torax_anteroposterior_cm,
            diam_biiliocrestideo_cm,
            diam_humeral_biepicondilar_cm,
            diam_femoral_biepicondilar_cm,
            diam_muneca_biestiloideo_cm,
            diam_tobillo_bimaleolar_cm,
            diam_mano_cm
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        id_isak,
        r.get("biacromial"),
        r.get("torax_transverso"),
        r.get("torax_antero_posterior"),
        r.get("bi_iliocrestideo"),
        r.get("humeral_biepicondilar"),
        r.get("femoral_biepicondilar"),
        r.get("muneca_biestiloideo"),
        r.get("tobillo_bimaleolar"),
        r.get("mano"),
    ))

def insert_isak_perimetros(cursor, id_isak: int, r: dict):
    sql = """
        INSERT INTO antropometria_isak_perimetros (
            id_isak,
            per_cabeza_cm,
            per_cuello_cm,
            per_brazo_relajado_cm,
            per_brazo_flexionado_tension_cm,
            per_antebrazo_maximo_cm,
            per_muneca_cm,
            per_torax_mesoesternal_cm,
            per_cintura_minima_cm,
            per_abdominal_maxima_cm,
            per_cadera_maxima_cm,
            per_muslo_maximo_cm,
            per_muslo_medial_cm,
            per_pantorrilla_maxima_cm,
            per_tobillo_minima_cm
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        id_isak,
        r.get("perimetro_cabeza"),
        r.get("perimetro_cuello"),
        r.get("perimetro_brazo_relajado"),
        r.get("perimetro_brazo_flexionado_en_tension"),
        r.get("perimetro_antebrazo_maximo"),
        r.get("perimetro_muneca"),
        r.get("perimetro_torax_mesoesternal"),
        r.get("perimetro_cintura_minima"),
        r.get("perimetro_abdominal_maxima"),
        r.get("perimetro_cadera_maximo"),
        r.get("perimetro_muslo_maximo"),
        r.get("perimetro_muslo_medial"),
        r.get("perimetro_pantorrilla_maxima"),
        r.get("perimetro_tobillo_minima"),
    ))

def insert_isak_pliegues(cursor, id_isak: int, r: dict):
    sql = """
        INSERT INTO antropometria_isak_pliegues (
            id_isak,
            pl_triceps_mm,
            pl_subescapular_mm,
            pl_biceps_mm,
            pl_cresta_iliaca_mm,
            pl_supraespinal_mm,
            pl_abdominal_mm,
            pl_muslo_frontal_mm,
            pl_pantorrilla_maxima_mm,
            pl_antebrazo_mm
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        id_isak,
        r.get("pliegue_triceps"),
        r.get("pliegue_subescapular"),
        r.get("pliegue_biceps"),
        r.get("pliegue_cresta_iliaca"),
        r.get("pliegue_supraespinal"),
        r.get("pliegue_abdominal"),
        r.get("pliegue_muslo_frontal"),
        r.get("pliegue_pantorrilla_maxima"),
        r.get("pliegue_antebrazo"),
    ))

def insert_isak_calculado(cursor, calculos: dict):
    sql = """
        INSERT INTO antropometria_calculada (
            id_jugadora,
            id_isak,
            id_calculo_version,
            metodo,
            peso_kg,
            talla_corporal_cm,
            suma_6_pliegues_mm,
            ajuste_adiposa_pct,
            ajuste_muscular_pct,
            masa_osea_kg,
            indice_musculo_oseo,
            usuario,
            estatus_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    cursor.execute(sql, (
        calculos["id_jugadora"],
        calculos["id_isak"],
        calculos["id_calculo_version"],
        "ISAK",
        calculos.get("peso_bruto_kg"),
        calculos.get("talla_corporal_cm"),
        calculos.get("suma_6_pliegues_mm"),
        calculos.get("ajuste_adiposa_pct"),
        calculos.get("ajuste_muscular_pct"),
        calculos.get("masa_osea_kg"),
        calculos.get("indice_musculo_oseo"),
        calculos.get("usuario"),
        1,
    ))

def save_isak_session(record: dict) -> bool:
    """
    Guarda una sesión ISAK completa (RAW + CALCULADOS) de forma transaccional.
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        # -------------------------------------------------
        # 1. Insert sesión ISAK (cabecera)
        # -------------------------------------------------
        id_isak = insert_isak_session(cursor, record)

        # -------------------------------------------------
        # 2. Insert RAW (1 fila por tabla)
        # -------------------------------------------------
        insert_isak_basicos(cursor, id_isak, record)
        insert_isak_longitudes(cursor, id_isak, record)
        insert_isak_diametros(cursor, id_isak, record)
        insert_isak_perimetros(cursor, id_isak, record)
        insert_isak_pliegues(cursor, id_isak, record)

 
        # -------------------------------------------------
        # 4. Insert CALCULADOS
        # -------------------------------------------------
        #insert_isak_calculado(cursor, calculos)

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        st.error(f"Error guardando ISAK: {e}")
        print(e)
        return False

    finally:
        cursor.close()
        conn.close()


###############################

def delete_records_by_jugadora(id_jugadora: str, deleted_by: str) -> tuple[bool, str]:
    """
    Soft-delete de TODOS los ISAK de una jugadora.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        cursor.execute("""
            SELECT id_isak
            FROM antropometria_isak
            WHERE id_jugadora = %s
              AND deleted_at IS NULL
              AND estatus_id IN (1, 2);
        """, (id_jugadora,))

        ids_isak = [r["id_isak"] for r in cursor.fetchall()]

        if not ids_isak:
            return False, "No se encontraron registros para eliminar"

        for id_isak in ids_isak:
            delete_isak_session(cursor, id_isak, deleted_by)

        conn.commit()
        return True, f"{len(ids_isak)} registros eliminados correctamente"

    except Exception as e:
        conn.rollback()
        return False, f"Error eliminando ISAKs de jugadora: {e}"

    finally:
        cursor.close()
        conn.close()

def delete_records_by_ids(ids_isak: list[int], deleted_by: str) -> tuple[bool, str]:
    """
    Soft-delete de ISAKs seleccionados.
    """
    if not ids_isak:
        return False, "No hay registros seleccionados"

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        for id_isak in ids_isak:
            delete_isak_session(cursor, id_isak, deleted_by)

        conn.commit()
        return True, f"{len(ids_isak)} registros eliminados correctamente"

    except Exception as e:
        conn.rollback()
        return False, f"Error eliminando registros ISAK: {e}"

    finally:
        cursor.close()
        conn.close()

def delete_isak_session(cursor, id_isak: int, deleted_by: str):
    # # 1. Calculados
    # cursor.execute("""
    #     UPDATE antropometria_calculada
    #     SET deleted_at = NOW(), deleted_by = %s, estatus_id = 3
    #     WHERE id_isak = %s
    #       AND deleted_at IS NULL;
    # """, (deleted_by, id_isak))

    # 2. Raw
    for table in [
        "antropometria_isak_basicos",
        "antropometria_isak_perimetros",
        "antropometria_isak_pliegues",
        "antropometria_isak_longitudes",
        "antropometria_isak_diametros",
    ]:
        cursor.execute(f"""
            UPDATE {table}
            SET deleted_at = NOW(), deleted_by = %s, estatus_id = 3
            WHERE id_isak = %s
              AND deleted_at IS NULL;
        """, (deleted_by, id_isak))

    # 4. ISAK sesión
    cursor.execute("""
        UPDATE antropometria_isak
        SET deleted_at = NOW(), deleted_by = %s, estatus_id = 3
        WHERE id_isak = %s
          AND deleted_at IS NULL;
    """, (deleted_by, id_isak))

#########################

def build_record_from_isak(id_isak: int, id_jugadora: str, username: str) -> dict:
    record = new_base_record(id_jugadora=id_jugadora, username=username)
    record["_modo"] = "SEGUIMIENTO"

    for getter in (
        get_isak_basicos,
        get_isak_perimetros,
        get_isak_pliegues,
        get_isak_longitudes,
        get_isak_diametros,
    ):
        data = getter(id_isak)
        if data:
            record.update(data)

    return record

def get_isak_full(as_df: bool = True):
    """
    Devuelve un DataFrame ISAK completo usando únicamente
    las funciones get_isak_* existentes.
    """

    base_df = get_records_db(as_df=True)

    if base_df.empty:
        return base_df if as_df else []

    rows = []

    for _, row in base_df.iterrows():
        id_isak = row["id_isak"]

        data = row.to_dict()

        # ---------------------------
        # Enriquecer con ISAK
        # ---------------------------
        for getter in (
            get_isak_basicos,
            get_isak_perimetros,
            get_isak_pliegues,
            get_isak_longitudes,
            get_isak_diametros,
        ):
            values = getter(id_isak)
            if values:
                data.update(values)

        rows.append(data)

    df = pd.DataFrame(rows)
    
    return df if as_df else df.to_dict("records")
