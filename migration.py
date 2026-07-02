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
            ALTER TABLE users ADD COLUMN google_id TEXT;
        """)
        print("added field google_id to users")
    except sqlite3.OperationalError as e:
        print("failed to add field google_id to users", e)

    try:
        cur.execute(""" 
            ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local';
        """)
        print("added field auth_provider to users")
        
    except sqlite3.OperationalError as e:
        print("failed to add field auth_provider to users", e)
        
    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()