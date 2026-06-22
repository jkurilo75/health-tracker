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
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        print("Added column: email")
    except sqlite3.OperationalError as e:
        print("email column already exists:", e)

    # -----------------------------
    # 2. Assign email to existing user
    # -----------------------------
    cur.execute("""
        UPDATE users
        SET email = ?
        WHERE username = ?
    """, ("jkurilo75@gmail.com", "bilingo"))

    print("Updated user email")

    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()