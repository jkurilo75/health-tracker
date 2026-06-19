import os
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, Response
import sqlite3
from flask import send_from_directory
from flask import jsonify
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime
from db import query, execute
from auth import login_required, login_user, logout_user, current_user_id

app = Flask(__name__)
app.secret_key = "ThisIsASecretKeyForMe:)"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = query(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,),
            one=True
        )
        
        if user and check_password_hash(user[2], password):
            login_user((user[0], user[1]))
            return redirect("/")
        else:
            return render_template("login.html",
                                   error="Wrong login")

    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing = query(
            "SELECT id FROM users WHERE username = ?",
            (username,),
            one=True
        )

        if existing:
            return render_template("register.html", error="Username already exists")

        hashed = generate_password_hash(password)

        execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )

        return redirect("/login")

    return render_template("register.html")
    
    
@app.route("/")
@login_required
def home():
    # Latest blood pressure
    bp = query("""
            SELECT systolic, diastolic, pulse, recorded_at
            FROM blood_pressure
            WHERE user_id = ?
            ORDER BY recorded_at DESC
            LIMIT 1
        """, (current_user_id(),), one=True)

    # Latest blood sugar
    sugar = query("""
        SELECT glucose, unit, context, recorded_at
        FROM blood_sugar
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """, (current_user_id(),), one=True)

    # 7-day BP average
    bp_avg = query("""
        SELECT
            AVG(systolic),
            AVG(diastolic)
        FROM blood_pressure
        WHERE user_id = ? AND recorded_at >= datetime('now', '-7 days')
        """, (current_user_id(),), one=True)

    # 7-day sugar average
    sugar_avg = query("""
        SELECT AVG(glucose)
        FROM blood_sugar
        WHERE user_id = ? AND recorded_at >= datetime('now', '-7 days')
        """, (current_user_id(),), one=True)

    return render_template(
        "index.html",
        bp=bp,
        sugar=sugar,
        bp_avg=bp_avg,
        sugar_avg=sugar_avg
    )


@app.route("/bp/add", methods=["GET", "POST"])
@login_required
def add_bp():
    if request.method == "POST":

        systolic = request.form["systolic"]
        diastolic = request.form["diastolic"]
        pulse = request.form["pulse"]

        execute("""
        INSERT INTO blood_pressure (user_id, systolic, diastolic, pulse, recorded_at)
        VALUES (?, ?, ?, ?, ?)
        """, (current_user_id(), systolic, diastolic, pulse, datetime.now()))

        return redirect("/bp/history")

    return render_template("add_bp.html")


@app.route("/bp/history")
@login_required
def bp_history():
    readings = query(
        """
        SELECT *
        FROM blood_pressure
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        """, (current_user_id(),), one=False)

    return render_template(
        "bp_history.html",
        readings=readings
    )


@app.route("/sugar/add", methods=["GET", "POST"])
@login_required
def add_sugar():
    if request.method == "POST":

        glucose = request.form["glucose"]
        unit = request.form["unit"]
        context = request.form["context"]

        execute("""
            INSERT INTO blood_sugar (user_id, glucose, unit, context, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """,
        (
            current_user_id(),
            glucose,
            unit,
            context,
            datetime.now()
        ))

        return redirect("/sugar/history")

    return render_template("add_sugar.html")
    
    
@app.route("/sugar/history")
@login_required
def sugar_history():
    readings = query("""
        SELECT *
        FROM blood_sugar
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        """, (current_user_id(),), one=False)

    return render_template("sugar_history.html", readings=readings)
    

@app.route("/charts")
@login_required
def charts():
    bp = query("""
        SELECT recorded_at, systolic, diastolic
        FROM blood_pressure
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 20
        """, (current_user_id(),), one=False)

    sugar = query("""
        SELECT recorded_at, glucose
        FROM blood_sugar
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 20
        """, (current_user_id(),), one=False)

    # reverse so charts go left → right in time order
    bp = bp[::-1]
    sugar = sugar[::-1]

    return render_template("charts.html", bp=bp, sugar=sugar)


@app.route("/export/bp")
@login_required
def export_bp():
    rows = query("""
        SELECT recorded_at, systolic, diastolic, pulse
        FROM blood_pressure
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        """, (current_user_id(),), one=False)

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
@login_required
def export_sugar():
    rows = query("""
        SELECT recorded_at, glucose, unit, context
        FROM blood_sugar
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        """, (current_user_id(),), one=False)

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

@app.route("/notify-sugar")
def notify_sugar():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
