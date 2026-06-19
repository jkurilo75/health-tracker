import sqlite3

DATABASE = "health.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    return conn


def query(sql, params=(), one=False):
    conn = get_connection()
    cur = conn.execute(sql, params)

    if one:
        row = cur.fetchone()
        conn.close()
        return row

    rows = cur.fetchall()
    conn.close()
    return rows


def execute(sql, params=()):
    conn = get_connection()
    cur = conn.execute(sql, params)
    conn.commit()
    conn.close()
    return cur.lastrowid