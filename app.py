import os
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "ThisIsASecretKeyForMe:)"
USERNAME = "bilingo"
PASSWORD = "1234"

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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS blood_sugar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            glucose REAL NOT NULL,
            unit TEXT DEFAULT 'mmol/L',
            context TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect("/")
        else:
            return render_template("login.html", error="Wrong login")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
        
    conn = sqlite3.connect(DATABASE)

    # Latest blood pressure
    bp = conn.execute("""
        SELECT systolic, diastolic, pulse, recorded_at
        FROM blood_pressure
        ORDER BY recorded_at DESC
        LIMIT 1
    """).fetchone()

    # Latest blood sugar
    sugar = conn.execute("""
        SELECT glucose, unit, context, recorded_at
        FROM blood_sugar
        ORDER BY recorded_at DESC
        LIMIT 1
    """).fetchone()

    # 7-day BP average
    bp_avg = conn.execute("""
        SELECT
            AVG(systolic),
            AVG(diastolic)
        FROM blood_pressure
        WHERE recorded_at >= datetime('now', '-7 days')
    """).fetchone()

    # 7-day sugar average
    sugar_avg = conn.execute("""
        SELECT AVG(glucose)
        FROM blood_sugar
        WHERE recorded_at >= datetime('now', '-7 days')
    """).fetchone()

    conn.close()

    return render_template(
        "index.html",
        bp=bp,
        sugar=sugar,
        bp_avg=bp_avg,
        sugar_avg=sugar_avg
    )


@app.route("/bp/add", methods=["GET", "POST"])
def add_bp():
    if "user" not in session:
        return redirect("/login")

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
    if "user" not in session:
        return redirect("/login")

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


@app.route("/sugar/add", methods=["GET", "POST"])
def add_sugar():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        glucose = request.form["glucose"]
        unit = request.form["unit"]
        context = request.form["context"]

        conn = sqlite3.connect(DATABASE)

        conn.execute("""
            INSERT INTO blood_sugar (glucose, unit, context)
            VALUES (?, ?, ?)
        """, (glucose, unit, context))

        conn.commit()
        conn.close()

        return redirect("/sugar/history")

    return render_template("add_sugar.html")
    
    
@app.route("/sugar/history")
def sugar_history():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)

    readings = conn.execute("""
        SELECT *
        FROM blood_sugar
        ORDER BY recorded_at DESC
    """).fetchall()

    conn.close()

    return render_template("sugar_history.html", readings=readings)
    

@app.route("/charts")
def charts():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DATABASE)

    bp = conn.execute("""
        SELECT recorded_at, systolic, diastolic
        FROM blood_pressure
        ORDER BY recorded_at DESC
        LIMIT 20
    """).fetchall()

    sugar = conn.execute("""
        SELECT recorded_at, glucose
        FROM blood_sugar
        ORDER BY recorded_at DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    # reverse so charts go left → right in time order
    bp = bp[::-1]
    sugar = sugar[::-1]

    return render_template("charts.html", bp=bp, sugar=sugar)


@app.route("/export/bp")
def export_bp():

    conn = sqlite3.connect(DATABASE)

    rows = conn.execute("""
        SELECT recorded_at, systolic, diastolic, pulse
        FROM blood_pressure
        ORDER BY recorded_at DESC
    """).fetchall()

    conn.close()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Systolic",
        "Diastolic",
        "Pulse"
    ])

    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=blood_pressure.csv"
        }
    )
    

@app.route("/export/sugar")
def export_sugar():

    conn = sqlite3.connect(DATABASE)

    rows = conn.execute("""
        SELECT recorded_at, glucose, unit, context
        FROM blood_sugar
        ORDER BY recorded_at DESC
    """).fetchall()

    conn.close()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Glucose",
        "Unit",
        "Context"
    ])

    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=blood_sugar.csv"
        }
    )
    
    
@app.route("/sw.js")
def sw():
    return send_from_directory(
        "static",
        "sw.js",
        mimetype="application/javascript"
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
