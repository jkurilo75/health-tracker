from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DATABASE = "health.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS blood_pressure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            systolic INTEGER NOT NULL,
            diastolic INTEGER NOT NULL,
            pulse INTEGER
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bp/add", methods=["GET", "POST"])
def add_bp():

    if request.method == "POST":

        systolic = request.form["systolic"]
        diastolic = request.form["diastolic"]
        pulse = request.form["pulse"]

        conn = sqlite3.connect(DATABASE)

        conn.execute(
            """
            INSERT INTO blood_pressure
            (systolic, diastolic, pulse)
            VALUES (?, ?, ?)
            """,
            (systolic, diastolic, pulse)
        )

        conn.commit()
        conn.close()

        return redirect("/bp/history")

    return render_template("add_bp.html")


@app.route("/bp/history")
def bp_history():

    conn = sqlite3.connect(DATABASE)

    readings = conn.execute(
        """
        SELECT *
        FROM blood_pressure
        ORDER BY recorded_at DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "bp_history.html",
        readings=readings
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)