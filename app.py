import os
import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, Response, url_for
import sqlite3
from flask import send_from_directory
from flask import jsonify
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from db import query, execute, get_connection
from models import User
import smtplib
import ssl
from email.message import EmailMessage
import secrets
from dotenv import load_dotenv
import requests
import re
from authlib.integrations.flask_client import OAuth

project_folder = os.path.expanduser('~/health_tracker')
load_dotenv(os.path.join(project_folder, '.env'))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
#print("EMAIL_ADDRESS:", EMAIL_ADDRESS)
#print("EMAIL_PASSWORD loaded:", EMAIL_PASSWORD is not None)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
#print("CLIENT_ID:", GOOGLE_CLIENT_ID)
#print("CLIENT_SECRET loaded:", GOOGLE_CLIENT_SECRET is not None)

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
app.secret_key = "ThisIsASecretKeyForMe:)"

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "email profile"},
)

#google = oauth.register(
#    name="google",
#    client_id=os.getenv("GOOGLE_CLIENT_ID"),
#    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
#    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
#    client_kwargs={"scope": "openid email profile"},
#)


@login_manager.user_loader
def load_user(user_id):

    row = query(
        """
        SELECT id, username, password
        FROM users
        WHERE id = ?
        """,
        (user_id,),
        one=True
    )

    if row is None:
        return None

    return User(
        row["id"],
        row["username"],
        row["password"]
    )
    
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = query(
            """SELECT id, username, email, password
            FROM users
            WHERE email = ? OR username = ?
            """,
            (username, username),
            one=True
        )
        
        if user and check_password_hash(user["password"], password):
            login_user(
                User(
                    user["id"],
                    user["username"],
                    user["password"]
                )
            )
            return redirect("/")
        else:
            return render_template("login.html",
                                   error="Wrong login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@app.route("/login/google")
def login_google():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()

    #user_info = token["userinfo"]
    #user_info = google.get("userinfo").json()
    resp = google.get("userinfo")
    user_info = resp.json()

    google_id = user_info["id"]
    email = user_info["email"]
    username = user_info.get("name", email.split("@")[0])

    # Find by Google ID first
    user = query("""
        SELECT *
        FROM users
        WHERE google_id = ?
    """, (google_id,), one=True)

    # Existing local account? Link it.
    if user is None:
        user = query("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,), one=True)

        if user:
            execute("""
                UPDATE users
                SET google_id = ?, auth_provider = 'google'
                WHERE id = ?
            """, (google_id, user["id"]))

            user = query(
                "SELECT * FROM users WHERE id = ?",
                (user["id"],),
                one=True
            )

    # Brand new Google user
    if user is None:
        execute("""
            INSERT INTO users (username, email, google_id, auth_provider)
            VALUES (?, ?, ?, 'google')
        """, (username, email, google_id))

        user = query("""
            SELECT *
            FROM users
            WHERE google_id = ?
        """, (google_id,), one=True)

    login_user(User(user["id"], user["username"], user["password"]))

    return redirect("/")


EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

def is_valid_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email) is not None
    
    
    
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

        email = request.form.get("username", "").strip()

        if email and not is_valid_email(email):
            email = None

        execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, hashed, email if email else None)
        )

        return redirect("/login")

    return render_template("register.html")
    

def cleanup_expired_reset_tokens():
    conn = get_connection()
    conn.execute("""
        DELETE FROM password_reset_tokens
        WHERE expires_at < datetime('now')
    """)
    conn.commit()
    conn.close()
    

def log_reset_request(email):
    conn = get_connection()
    conn.execute("""
        INSERT INTO password_reset_requests (email)
        VALUES (?)
    """, (email,))
    conn.commit()
    conn.close()
    
    
def can_request_reset(email):
    conn = get_connection()

    cur = conn.execute("""
        SELECT COUNT(*)
        FROM password_reset_requests
        WHERE email = ?
          AND requested_at > datetime('now', '-10 minutes')
    """, (email,))

    count = cur.fetchone()[0]
    conn.close()

    return count < 3


def cleanup_reset_requests():
    execute("""
        DELETE FROM password_reset_requests
        WHERE requested_at < datetime('now', '-1 day')
    """)

    
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        cleanup_expired_reset_tokens()
        cleanup_reset_requests()
        email = request.form["email"]

        if not can_request_reset(email):
            return "Too many requests. Try again later."
        
        log_reset_request(email)
        
        user = query(
            "SELECT id, email FROM users WHERE email = ?",
            (email,),
            one=True
        )

        if not user:
            return render_template(
                "forgot_password.html",
                error="Email not found"
            )

        # generate token
        token = secrets.token_urlsafe(32)

        expires = datetime.utcnow() + timedelta(hours=1)

        conn = get_connection()
        conn.execute("""
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES (?, ?, ?)
        """, (user["id"], token, expires))
        conn.commit()
        conn.close()

        reset_link = f"http://localhost:5000/reset-password/{token}"

        # send email
        try:
            send_email(email, reset_link)
        except Exception as e:
            print("EMAIL ERROR:", e)
            raise

        return render_template(
            "forgot_password.html",
            message="Check your email"
        )

    return render_template("forgot_password.html")


def send_gmail_email(to_email, reset_link):

    msg = EmailMessage()
    msg["Subject"] = "Password Reset"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    msg.set_content(f"""
    Click the link to reset your password:

    {reset_link}

    This link expires in 1 hour.
    """)

    context = ssl.create_default_context()

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()

        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def send_email(to_email, reset_link):
    url = "https://api.resend.com/emails"

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": "onboarding@resend.dev",
        "to": [to_email],
        "subject": "Password Reset",
        "html": f"""
            <p>Click here:</p>
            <a href="{reset_link}">{reset_link}</a>
        """
    }

    response = requests.post(url, json=data, headers=headers)

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    if response.status_code >= 400:
        raise Exception(response.text)        


def claim_reset_token(token):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE password_reset_tokens
        SET used = 1
        WHERE token = ?
          AND used = 0
          AND expires_at > datetime('now')
    """, (token,))

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        return False  # invalid, expired or already used

    conn.close()
    return True

    
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token")

    if request.method == "POST":

        new_password = request.form["password"]
        hashed = generate_password_hash(new_password)

        if not claim_reset_token(token):
            return "Invalid or expired token"

        conn = get_connection()
        conn.execute("""
            UPDATE users
            SET password = ?
            WHERE id = (
                SELECT user_id
                FROM password_reset_tokens
                WHERE token = ?
            )
        """, (hashed, token))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("reset_password.html")

    
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
        """, (current_user.id,), one=True)

    # Latest blood sugar
    sugar = query("""
        SELECT glucose, unit, context, recorded_at
        FROM blood_sugar
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """, (current_user.id,), one=True)

    # 7-day BP average
    bp_avg = query("""
        SELECT
            AVG(systolic),
            AVG(diastolic)
        FROM blood_pressure
        WHERE user_id = ? AND recorded_at >= datetime('now', '-7 days')
        """, (current_user.id,), one=True)

    # 7-day sugar average
    sugar_avg = query("""
        SELECT AVG(glucose)
        FROM blood_sugar
        WHERE user_id = ? AND recorded_at >= datetime('now', '-7 days')
        """, (current_user.id,), one=True)

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
        """, (current_user.id, systolic, diastolic, pulse, datetime.now()))

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
        """, (current_user.id,), one=False)

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
            current_user.id,
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
        """, (current_user.id,), one=False)

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
        """, (current_user.id,), one=False)

    sugar = query("""
        SELECT recorded_at, glucose
        FROM blood_sugar
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 20
        """, (current_user.id,), one=False)

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
        """, (current_user.id,), one=False)

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
        """, (current_user.id,), one=False)

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
    
if __name__ == "__main__":
    app.run(debug=True)
