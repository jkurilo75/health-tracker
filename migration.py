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
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                meal_type TEXT, -- Breakfast, Lunch, Dinner, Supper, Snack
                portion_size TEXT, -- Small, Medium, Large
                carbs_pct INTEGER,
                protein_pct INTEGER,
                fat_pct INTEGER,
                photo_path TEXT,
                notes TEXT,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity TEXT NOT NULL,
                intensity TEXT,
                duration_minutes INTEGER,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                medication TEXT NOT NULL, -- Metformin, Viacoram
                dose TEXT,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("created tables meals, exercise, medications")
    except sqlite3.OperationalError as e:
        print("failed to create tables meals, exercise, medications", e)

    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()