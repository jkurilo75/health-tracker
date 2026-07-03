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
            UPDATE blood_sugar SET context = 'Before 1st meal' WHERE context = 'Before meal';
        """)
        print("modified blood_sugar.context")
    except sqlite3.OperationalError as e:
        print("failed to modified blood_sugar.context", e)

    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()