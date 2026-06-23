import sqlite3

DB = "health.db"


def run_migration():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    print("Starting migration...")

    # -----------------------------
    # 1. Add email column (safe)
    # -----------------------------
    try:
        cur.execute(""" 
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL
            );        
        """)
        print("created table password_reset_tokens")
    except sqlite3.OperationalError as e:
        print("email column already exists:", e)

    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()