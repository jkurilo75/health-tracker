from functools import wraps
from flask import session, redirect

# -----------------------------
# Current user helpers
# -----------------------------

def current_user_id():
    return session.get("user_id")


def current_username():
    return session.get("username")


def is_authenticated():
    return "user_id" in session


# -----------------------------
# Login required decorator
# -----------------------------

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return redirect("/login")
        return view_func(*args, **kwargs)
    return wrapper


# -----------------------------
# Login / logout helpers
# -----------------------------

def login_user(user):
    """
    user = (id, username)
    """
    session["user_id"] = user[0]
    session["username"] = user[1]


def logout_user():
    session.clear()