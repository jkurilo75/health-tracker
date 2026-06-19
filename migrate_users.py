import sqlite3
from werkzeug.security import generate_password_hash

USERNAME = "bilingo"
PASSWORD = "1234"

conn = sqlite3.connect("health.db")

# Add user_id columns if they don't exist
try:
    conn.execute("ALTER TABLE blood_pressure ADD COLUMN user_id INTEGER")
    print("Added user_id to blood_pressure")
except Exception as e:
    print("blood_pressure:", e)

try:
    conn.execute("ALTER TABLE blood_sugar ADD COLUMN user_id INTEGER")
    print("Added user_id to blood_sugar")
except Exception as e:
    print("blood_sugar:", e)

# Create users table
conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")

# Check if user already exists
user = conn.execute(
    "SELECT id FROM users WHERE username = ?",
    (USERNAME,)
).fetchone()

# Create the user only if it doesn't exist
if user is None:
    conn.execute(
        """
        INSERT INTO users (username, password)
        VALUES (?, ?)
        """,
        (USERNAME, generate_password_hash(PASSWORD))
    )
    print(f"Created user '{USERNAME}'")

    # Fetch the newly created user's ID
    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (USERNAME,)
    ).fetchone()
else:
    print(f"User '{USERNAME}' already exists")

# Assign existing records to this user
if user:
    user_id = user[0]
    print(f"Assigning existing records to user_id={user_id}")

    conn.execute(
        "UPDATE blood_pressure SET user_id = ? WHERE user_id IS NULL",
        (user_id,)
    )

    conn.execute(
        "UPDATE blood_sugar SET user_id = ? WHERE user_id IS NULL",
        (user_id,)
    )

    print("Existing records updated.")
else:
    print(f"User '{USERNAME}' not found. No records updated.")

conn.commit()
conn.close()

print("Migration complete")