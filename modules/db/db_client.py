import streamlit as st
from modules.db.db_connection import get_connection

# ============================================================
#  🔹 FUNCIÓN GENÉRICA PARA EJECUTAR SELECT
# ============================================================

def query(sql: str, params=None, fetch="all", conn=None, cursor=None):
    """
    Executes a SELECT query using a pooled MySQL connection.

    Args:
        sql (str): SQL query.
        params (tuple | dict | None): Query parameters.
        fetch (str): "all", "one", or None.

    Returns:
        list[dict] | dict | True | None:
            - list of rows (dict) if fetch="all"
            - single row (dict) if fetch="one"
            - True for no-fetch operations
            - None on error
    """
    internal_conn = False

    try:
        if conn is None:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            internal_conn = True

        cursor.execute(sql, params)

        if fetch == "all":
            result = cursor.fetchall()
        elif fetch == "one":
            result = cursor.fetchone()
        else:
            result = True

        return result

    except Exception as e:
        st.error(f"Error ejecutando operación: {e} - SQL: {sql}")
        return None

    finally:
        if internal_conn:
            try:
                cursor.close()
                conn.close()
            except:
                pass

# ============================================================
#  🔹 FUNCIÓN GENÉRICA PARA EJECUTAR INSERT / UPDATE / DELETE
# ============================================================

def execute(sql: str, params=None, conn=None, cursor=None):

    """
    Executes an INSERT, UPDATE, or DELETE query.

    Args:
        sql (str): SQL statement.
        params (tuple | dict | None): Query parameters.

    Returns:
        bool: True if committed successfully, False on error.
    """
    internal_conn = False

    try:
        if conn is None:
            conn = get_connection()
            cursor = conn.cursor()
            internal_conn = True

        cursor.execute(sql, params)

        if internal_conn:
            conn.commit()

        return True

    except Exception as e:
        st.error(f"Error ejecutando operación: {e}")
        if internal_conn and conn:
            conn.rollback()
        return False

    finally:
        if internal_conn:
            try:
                cursor.close()
                conn.close()
            except:
                pass