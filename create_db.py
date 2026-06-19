import sqlite3

DATABASE = "health.db"

def create_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS blood_pressure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            systolic INTEGER NOT NULL,
            diastolic INTEGER NOT NULL,
            pulse INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS blood_sugar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            glucose REAL NOT NULL,
            unit TEXT DEFAULT 'mmol/L',
            context TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database schema created successfully.")

if __name__ == "__main__":
    create_db()