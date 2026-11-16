import json
import os
import re
import sqlite3
#database example
from functools import wraps

from flask import (
    Flask, g, jsonify, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

# ====================================================

#HTML template filenames (inside the /templates folder)
# Edit to real frontname pages when time
SIGNUP_TEMPLATE = "signup.html"      
LOGIN_TEMPLATE = "login.html"        
DASHBOARD_TEMPLATE = "dashboard.html"
BUDGET_TEMPLATE = "budget.html"
PROFILE_TEMPLATE = "profile.html"
SETTING_TEMPLATE = "setting.html"
EXPENSES_TEMPLATE = "expenses.html"

#Form field names (the name="..." attribute on each <input>)
# Sign up form:  <input name="first_name"> <input name="last_name">
#                <input name="email">      <input name="password">

# Login form:    <input name="email">      <input name="password">
# change the strings on the right only if front end uses different name.
FIELD_FIRST_NAME = "first_name"
FIELD_LAST_NAME = "last_name"
FIELD_EMAIL = "email"
FIELD_PASSWORD = "password"
FIELD_NEW_PASSWORD = "new_password"   # used by the change-password endpoint

#Database
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")

MIN_PASSWORD_LENGTH = 8
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

#
# APP SETUP
#
app = Flask(__name__)

# Sessions are signed with this key. In production, set a real one:
#Windows (cmd):   set SECRET_KEY=some-long-random-string
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

#When front end edited anything in template or static pages, change shows
#up on refresh without restarting server.
# (debug=True at the bottom also auto-restarts when this .py file changes.)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0   # don't cache static css/js in dev


# =============
# DATABASE HELPERS
# =============
def get_db():
    """One SQLite connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't exist. Safe to run every startup."""
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name    TEXT NOT NULL,
            last_name     TEXT NOT NULL,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items   TEXT NOT NULL,   -- JSON list of {title, amount}
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    db.commit()
    db.close()


# ==============
# AUTH HELPERS
# =========
def get_payload():
    """Read data from JSON (fetch/AJAX) or a normal HTML form, same code path."""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


def current_user():
    """Return the logged-in user row, or None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return get_db().execute(
        "SELECT id, first_name, last_name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def login_required(view):
    """Protect a page: page routes redirect to login, /api routes return 401."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify(error="Not logged in"), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    """Makes `user` available in EVERY template, e.g. {{ user.first_name }}.
    Front-end devs get this for free, no backend change needed."""
    return {"user": current_user()}


def validate_name(value, label):
    value = (value or "").strip()
    if not value:
        return None, f"{label} is required."
    if len(value) > 50:
        return None, f"{label} is too long."
    return value, None


def validate_email(value):
    value = (value or "").strip().lower()
    if not EMAIL_REGEX.match(value):
        return None, "Please enter a valid email address."
    return value, None


def validate_password(value):
    value = value or ""
    if len(value) < MIN_PASSWORD_LENGTH:
        return None, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return value, None


# =======================================
# PUBLIC PAGES: SIGN UP / LOGIN / LOGOUT
# ======================================
@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template(SIGNUP_TEMPLATE)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Sign up page.
    HTML form should POST to /signup  ->  action="{{ url_for('signup') }}"
    Template receives (on error): `error` (string) and `form` (what they typed,
    minus the password) so you can refill the inputs:
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <input name="first_name" value="{{ form.first_name if form }}">
    """
    if request.method == "GET":
        return render_template(SIGNUP_TEMPLATE)

    data = get_payload()
    first, err1 = validate_name(data.get(FIELD_FIRST_NAME), "First name")
    last, err2 = validate_name(data.get(FIELD_LAST_NAME), "Last name")
    email, err3 = validate_email(data.get(FIELD_EMAIL))
    password, err4 = validate_password(data.get(FIELD_PASSWORD))

    error = err1 or err2 or err3 or err4
    # Echo back what they typed (never the password)
    form = {
        FIELD_FIRST_NAME: data.get(FIELD_FIRST_NAME, ""),
        FIELD_LAST_NAME: data.get(FIELD_LAST_NAME, ""),
        FIELD_EMAIL: data.get(FIELD_EMAIL, ""),
    }

    if error:
        return _signup_error(error, form)

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash) "
            "VALUES (?, ?, ?, ?)",
            (first, last, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        # UNIQUE constraint on email incase.
        return _signup_error("An account with that email already exists.", form)

    # Account is saved. They are NOT logged in yet. Are sent to login
    # page, where the email and password they just created must be entered.
    if request.is_json:
        return jsonify(ok=True), 201
    return redirect(url_for("login", created=1))


def _signup_error(message, form):
    if request.is_json:
        return jsonify(error=message), 400
    return render_template(SIGNUP_TEMPLATE, error=message, form=form), 400


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page.
    HTML form should POST to /login  ->  action="{{ url_for('login') }}"
    Template receives (on failure): `error` and `form` (the email they typed).
    """
    if request.method == "GET":
        if current_user():
            return redirect(url_for("dashboard"))
        # /login?created=1 is where signup sends people after "Create"
        message = "Account created! Please log in." if request.args.get("created") else None
        return render_template(LOGIN_TEMPLATE, message=message)

    data = get_payload()
    email = (data.get(FIELD_EMAIL) or "").strip().lower()
    password = data.get(FIELD_PASSWORD) or ""

    user = get_db().execute(
        "SELECT id, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()

    # Same message whether the email or the password is wrong, so hackers
    # can't use the form to discover which emails have accounts.
    if user is None or not check_password_hash(user["password_hash"], password):
        message = "Incorrect email or password."
        if request.is_json:
            return jsonify(error=message), 401
        return render_template(
            LOGIN_TEMPLATE, error=message, form={FIELD_EMAIL: email}
        ), 401

    session.clear()
    session["user_id"] = user["id"]
    if request.is_json:
        return jsonify(ok=True)
    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["POST", "GET"])
def logout():
    """Every page's 'Log out' link/button points here: {{ url_for('logout') }}"""
    session.clear()
    return redirect(url_for("home"))


# =============================================================================
# LOGGED-IN PAGES
#Dashboard, budget, profile, setting, expenses. Each page is protected by @login_required.
# =============================================================================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(DASHBOARD_TEMPLATE)


@app.route("/budget")
@login_required
def budget():
    return render_template(BUDGET_TEMPLATE)


@app.route("/profile")
@login_required
def profile():
    return render_template(PROFILE_TEMPLATE)


@app.route("/setting")
@login_required
def setting():
    return render_template(SETTING_TEMPLATE)


@app.route("/expenses")
@login_required
def expenses():
    return render_template(EXPENSES_TEMPLATE)


# =============================================================================
# PROFILE API  (front end calls these with fetch(); all return JSON)
# =============================================================================
@app.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    """Returns {id, first_name, last_name, email, created_at}"""
    return jsonify(dict(current_user()))


@app.route("/api/profile", methods=["PUT", "PATCH"])
@login_required
def update_profile():
    """
    Update name and/or email. Send only the fields being changed, e.g.
        fetch("/api/profile", {method: "PUT",
              headers: {"Content-Type": "application/json"},
              body: JSON.stringify({first_name: "Sam"})})
    """
    data = get_payload()
    user = current_user()
    updates = {}

    if FIELD_FIRST_NAME in data:
        value, err = validate_name(data[FIELD_FIRST_NAME], "First name")
        if err:
            return jsonify(error=err), 400
        updates["first_name"] = value

    if FIELD_LAST_NAME in data:
        value, err = validate_name(data[FIELD_LAST_NAME], "Last name")
        if err:
            return jsonify(error=err), 400
        updates["last_name"] = value

    if FIELD_EMAIL in data:
        value, err = validate_email(data[FIELD_EMAIL])
        if err:
            return jsonify(error=err), 400
        updates["email"] = value

    if not updates:
        return jsonify(error="Nothing to update."), 400

    # Column names come from the fixed set above, never from user input.
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    db = get_db()
    try:
        db.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?",
            (*updates.values(), user["id"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="That email is already in use."), 409

    return jsonify(dict(current_user()))


@app.route("/api/profile/password", methods=["POST"])
@login_required
def change_password():
    """Body: {password: <current>, new_password: <new>}"""
    data = get_payload()
    current = data.get(FIELD_PASSWORD) or ""
    new_password, err = validate_password(data.get(FIELD_NEW_PASSWORD))
    if err:
        return jsonify(error=err), 400

    db = get_db()
    row = db.execute(
        "SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not check_password_hash(row["password_hash"], current):
        return jsonify(error="Current password is incorrect."), 403

    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), session["user_id"]),
    )
    db.commit()
    return jsonify(ok=True)


@app.route("/api/profile", methods=["DELETE"])
@login_required
def delete_account():
    """Body: {password: <current>}. Deletes the user and their budgets."""
    data = get_payload()
    db = get_db()
    row = db.execute(
        "SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    if not check_password_hash(row["password_hash"], data.get(FIELD_PASSWORD) or ""):
        return jsonify(error="Password is incorrect."), 403

    db.execute("DELETE FROM users WHERE id = ?", (session["user_id"],))
    db.commit()
    session.clear()
    return jsonify(ok=True)


# TODO for Profile: profile picture, phone number, currency preference,
# monthly income. Add a column in init_db() (or ALTER TABLE on an existing
# app.db), then add the field to update_profile() above.


# =============================================================================
# BUDGET API (now saved in SQLite and tied to the logged-in user)
# =============================================================================
def clean_items(raw_items):
    """Keep only valid {title, amount} rows."""
    items = []
    for item in raw_items or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        try:
            amount = round(float(item.get("amount", 0)), 2)
        except (TypeError, ValueError):
            amount = 0.0
        if title or amount:
            items.append({"title": title, "amount": amount})
    return items


def budget_to_dict(row):
    return {"id": row["id"], "items": json.loads(row["items"])}


@app.route("/api/budgets", methods=["GET"])
@login_required
def list_budgets():
    rows = get_db().execute(
        "SELECT id, items FROM budgets WHERE user_id = ? ORDER BY id",
        (session["user_id"],),
    ).fetchall()
    return jsonify([budget_to_dict(r) for r in rows])


@app.route("/api/budgets", methods=["POST"])
@login_required
def create_budget():
    data = request.get_json(silent=True) or {}
    items = clean_items(data.get("items"))
    if not items:
        return jsonify(error="A budget needs at least one item"), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO budgets (user_id, items) VALUES (?, ?)",
        (session["user_id"], json.dumps(items)),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "items": items}), 201


@app.route("/api/budgets/<int:budget_id>", methods=["PUT"])
@login_required
def update_budget(budget_id):
    data = request.get_json(silent=True) or {}
    items = clean_items(data.get("items"))
    if not items:
        return jsonify(error="A budget needs at least one item"), 400

    db = get_db()
    # user_id check means users can only edit their own budgets
    cur = db.execute(
        "UPDATE budgets SET items = ? WHERE id = ? AND user_id = ?",
        (json.dumps(items), budget_id, session["user_id"]),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Budget not found"), 404
    return jsonify({"id": budget_id, "items": items})


@app.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
@login_required
def delete_budget(budget_id):
    db = get_db()
    cur = db.execute(
        "DELETE FROM budgets WHERE id = ? AND user_id = ?",
        (budget_id, session["user_id"]),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Budget not found"), 404
    return jsonify(ok=True)


# =============================================================================
# RUN
# Run these one at a time in the terminal:
#   python -m venv venv
#   venv\Scripts\activate
#   pip install flask
#   python app.py
# Then open: http://127.0.0.1:5000
# =============================================================================
init_db()   # runs on import too, so it also works under `flask run`

if __name__ == "__main__":
    app.run(debug=True)   # debug=True: auto-reload on .py/template changes