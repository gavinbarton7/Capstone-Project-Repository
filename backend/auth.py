"""Accounts and sign-in: sign up, log in, log out, "who am I?".

This file has two parts:

  1. Shared helpers (create_account, check_credentials, start_session,
     end_session, current_user, login_required). Both the JSON API below and
     the HTML pages (pages.py) call them, so there is ONE sign-in system.
  2. The JSON endpoints under /api/auth  (this is what the React frontend uses).

JSON endpoints
    POST /api/auth/register   {first_name, last_name, email, password}
    POST /api/auth/login      {email, password, remember_me}
    POST /api/auth/logout
    GET  /api/auth/me         -> the signed-in user, or 401

How sign-in works
    On login the server makes a random token and sends it to the browser in an
    HttpOnly cookie (JavaScript cannot read it). Only a SHA-256 hash of the token
    is stored, in the `sessions` table. Each later request sends the cookie back
    and the server looks the hash up. Logging out deletes that row.
    Passwords are never stored: only a salted hash (werkzeug generate_password_hash).
"""

import hashlib
import os
import secrets
import sqlite3
from functools import wraps

from flask import Blueprint, g, jsonify, redirect, request
from werkzeug.security import check_password_hash, generate_password_hash

from db_connection import db
from validation import (
    pick,
    validate_email,
    validate_name,
    validate_password,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SESSION_COOKIE = "session_token"   # name of the cookie in the browser
REMEMBER_ME_DAYS = 30              # "Keep me signed in" ticked
DEFAULT_SESSION_HOURS = 12         # not ticked (the cookie also vanishes when the browser closes)

# Checked when the email is unknown, so a wrong email takes as long to reject as
# a wrong password and the two cannot be told apart by timing.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


# =============================================================================
# Small helpers
# =============================================================================
def json_body():
    """The request's JSON body as a dict ({} if it is missing or not a JSON object)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def public_user(row):
    """The user fields that are safe to send to the browser (never the password hash).

    `row` must come from a query that selects these columns (see current_user()).
    Profile fields are None until the user fills them in.
    """
    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "created_at": row["created_at"],
        "phone": row["phone"],
        "birthday": row["birthday"],
        "street_address": row["street_address"],
        "city": row["city"],
        "state": row["state"],
        "zip_code": row["zip_code"],
    }


# =============================================================================
# Who is signed in?
# =============================================================================
def current_user():
    """The signed-in user's row, or None. Reads the cookie and looks the session up."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    with db() as conn:
        return conn.execute(
            """
            SELECT u.user_id, u.email, u.first_name, u.last_name, u.created_at,
                   u.phone, u.birthday, u.street_address, u.city, u.state, u.zip_code
              FROM sessions s
              JOIN users u ON u.user_id = s.user_id
             WHERE s.token_hash = ? AND s.expires_at > datetime('now')
            """,
            (hash_token(token),),
        ).fetchone()


def login_required(view):
    """Protect an endpoint: put it UNDER the @route line.

        @profile_bp.get("")
        @login_required
        def read_profile():
            user_id = g.user["user_id"]     # the signed-in user's row is in g.user

    Not signed in:
      - /api/... routes answer 401 {"error": "Not signed in."}
      - page routes redirect to the login page
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            if request.path.startswith("/api/"):
                return jsonify(error="Not signed in."), 401
            return redirect("/login")
        g.user = user
        return view(*args, **kwargs)
    return wrapped


# =============================================================================
# Create an account / check a password / start and end a session
# (shared by the JSON endpoints below and by the HTML pages in pages.py)
# =============================================================================
def create_account(data):
    """Validate sign-up data and save the new user.

    `data` is a dict with first_name, last_name, email, password (the camelCase
    names firstName / lastName also work).
    Returns (user_dict, None, 201) on success, or (None, "error text", status).
    The user is NOT signed in by this; the caller decides what happens next.
    """
    first, error1 = validate_name(pick(data, "first_name", "firstName"), "First name")
    last, error2 = validate_name(pick(data, "last_name", "lastName"), "Last name")
    email, error3 = validate_email(pick(data, "email"))
    password, error4 = validate_password(pick(data, "password"))

    error = error1 or error2 or error3 or error4
    if error:
        return None, error, 400

    try:
        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, first_name, last_name)"
                " VALUES (?, ?, ?, ?)",
                (email, generate_password_hash(password), first, last),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:        # the email column is UNIQUE
        return None, "An account with that email already exists.", 409

    user = {"user_id": user_id, "email": email, "first_name": first, "last_name": last}
    return user, None, 201


def check_credentials(email, password):
    """The user's row if the email + password are right, otherwise None."""
    email = email.strip().lower() if isinstance(email, str) else ""
    password = password if isinstance(password, str) else ""
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    # Always check a hash (a fake one if the email is unknown) so timing does not leak.
    password_ok = check_password_hash(user["password_hash"] if user else _DUMMY_HASH, password)
    return user if (user and password_ok) else None


def start_session(user_id, remember_me=False):
    """Save a new session for the user and return the random token for the cookie."""
    token = secrets.token_urlsafe(32)
    lifetime = f"+{REMEMBER_ME_DAYS} days" if remember_me else f"+{DEFAULT_SESSION_HOURS} hours"
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")  # tidy up
        conn.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at)"
            " VALUES (?, ?, datetime('now', ?))",
            (user_id, hash_token(token), lifetime),
        )
    return token


def set_session_cookie(response, token, remember_me=False):
    """Put the sign-in cookie on `response` (any Flask response)."""
    response.set_cookie(
        SESSION_COOKIE,
        token,
        # No max_age = the browser forgets the cookie when it closes.
        max_age=REMEMBER_ME_DAYS * 24 * 60 * 60 if remember_me else None,
        httponly=True,      # JavaScript cannot read it
        samesite="Lax",
        # Set COOKIE_SECURE=1 when the site is served over HTTPS.
        secure=os.environ.get("COOKIE_SECURE") == "1",
    )
    return response


def end_session(response):
    """Sign out: delete this browser's session row and its cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))
    response.delete_cookie(SESSION_COOKIE)
    return response


# =============================================================================
# JSON endpoints  (/api/auth/...)
# =============================================================================
@auth_bp.post("/register")
def register():
    user, error, status = create_account(json_body())
    if error:
        return jsonify(error=error), status
    # Not signed in yet: the frontend sends the new user to the login page.
    return jsonify(user=user), 201


@auth_bp.post("/login")
def login():
    data = json_body()
    user = check_credentials(pick(data, "email"), pick(data, "password"))
    if user is None:
        # Same message either way, so it does not reveal which emails exist.
        return jsonify(error="Incorrect email or password."), 401

    remember_me = pick(data, "remember_me", "rememberMe") is True
    token = start_session(user["user_id"], remember_me)
    response = jsonify(user=public_user(user))
    return set_session_cookie(response, token, remember_me)


@auth_bp.post("/logout")
def logout():
    return end_session(jsonify(ok=True))


@auth_bp.get("/me")
@login_required
def me():
    """200 + the user if signed in, 401 if not. The frontend calls this on page load."""
    return jsonify(user=public_user(g.user))
