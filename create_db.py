import sqlite3

DATABASE = "health.db"

def create_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            google_id TEXT,
            auth_provider TEXT DEFAULT 'local'
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

    conn.execute(""" 
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            used INTEGER DEFAULT 0
        );        
    """)

    conn.execute(""" 
        CREATE TABLE IF NOT EXISTS password_reset_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.execute("""
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity TEXT NOT NULL,
            intensity TEXT,
            duration_minutes INTEGER,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medication TEXT NOT NULL, -- Metformin, Viacoram
            dose TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("Database schema created successfully.")

if __name__ == "__main__":
    create_db()