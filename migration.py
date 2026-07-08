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
            ALTER TABLE meals ADD COLUMN carbs_grams REAL;

        """)

        cur.execute("""
            ALTER TABLE meals ADD COLUMN protein_grams REAL;
            

        """)

        cur.execute("""
            
            ALTER TABLE meals ADD COLUMN fat_grams REAL
            

        """)

        cur.execute("""
            ALTER TABLE meals ADD COLUMN product_weight_grams REAL

        """)

        print("altered table meals")
    except sqlite3.OperationalError as e:
        print("failed to alter table meals", e)

    conn.commit()
    conn.close()

    print("Migration complete.")


if __name__ == "__main__":
    run_migration()