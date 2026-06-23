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
            ALTER TABLE password_reset_tokens ADD COLUMN used INTEGER DEFAULT 0;
        """)
        print("added field used to password_reset_tokens")
    except sqlite3.OperationalError as e:
        print("failed to add field used to password_reset_tokens", e)

    try:
        cur.execute(""" 
            CREATE TABLE IF NOT EXISTS password_reset_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                requested_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("created password_reset_requests table")
        
    except sqlite3.OperationalError as e:
        print("failed to create password_reset_requests table", e)
        
    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()