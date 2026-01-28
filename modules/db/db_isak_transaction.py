from modules.db.db_connection import get_connection

class IsakTransaction:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = get_connection()
        self.conn.autocommit = False
        self.cursor = self.conn.cursor(dictionary=True)
        return self

    def execute(self, sql: str, params=None):
        self.cursor.execute(sql, params)

    def last_insert_id(self) -> int:
        self.cursor.execute("SELECT LAST_INSERT_ID() AS id;")
        row = self.cursor.fetchone()
        return row["id"]

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.cursor.close()
        except:
            pass
        try:
            self.conn.close()  # vuelve al pool
        except:
            pass
