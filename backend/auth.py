"""Account creation, sign in, sign out (UC-AUTH-01/02, remember me US-03).

Endpoints
    POST /api/auth/register   {first_name, last_name, email, password}
    POST /api/auth/login      {email, password, remember_me}
    POST /api/auth/logout
    GET  /api/auth/me         -> the signed-in user, or 401

How sign-in works
    On login the server makes a random token, sends it to the browser in an
    HttpOnly cookie (JavaScript cannot read it), and stores only a SHA-256
    hash of it in the `sessions` table. Each later request sends the cookie
    back and the server looks the hash up.
"""

import hashlib
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_connection

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SESSION_COOKIE = "session_token"
REMEMBER_ME_DAYS = 30      # "Keep me signed in" ticked
DEFAULT_SESSION_HOURS = 12  # not ticked (cookie also vanishes when the browser closes)
MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Checked when the email is unknown, so a wrong email takes as long to reject
# as a wrong password and cannot be told apart by timing.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


@contextmanager
def db():
    """Open a connection; commit on success, roll back on error, always close."""
    conn = get_connection()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _public_user(row):
    """The user fields that are safe to send to the browser."""
    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
    }


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _text(data, key):
    value = data.get(key)
    return value.strip() if isinstance(value, str) else ""


def current_user():
    """Return the signed-in user's row, or None. Other routes can reuse this."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    with db() as conn:
        return conn.execute(
            """
            SELECT u.user_id, u.email, u.first_name, u.last_name
              FROM sessions s
              JOIN users u ON u.user_id = s.user_id
             WHERE s.token_hash = ? AND s.expires_at > datetime('now')
            """,
            (_hash_token(token),),
        ).fetchone()


@auth_bp.post("/register")
def register():
    data = _json_body()
    first_name = _text(data, "first_name")
    last_name = _text(data, "last_name")
    email = _text(data, "email").lower()
    password = data.get("password") if isinstance(data.get("password"), str) else ""

    if not first_name or not last_name:
        return jsonify(error="First name and last name are required."), 400
    if not EMAIL_PATTERN.match(email):
        return jsonify(error="Enter a valid email address."), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify(
            error=f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        ), 400

    try:
        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, first_name, last_name)"
                " VALUES (?, ?, ?, ?)",
                (email, generate_password_hash(password), first_name, last_name),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify(error="An account with that email already exists."), 409

    return jsonify(
        user={
            "user_id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
    ), 201


@auth_bp.post("/login")
def login():
    data = _json_body()
    email = _text(data, "email").lower()
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    remember_me = data.get("remember_me") is True

    with db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        password_ok = check_password_hash(
            user["password_hash"] if user else _DUMMY_HASH, password
        )
        if not user or not password_ok:
            # Same message either way, so it does not reveal which emails exist.
            return jsonify(error="Incorrect email or password."), 401

        token = secrets.token_urlsafe(32)
        lifetime = (
            f"+{REMEMBER_ME_DAYS} days" if remember_me
            else f"+{DEFAULT_SESSION_HOURS} hours"
        )
        conn.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
        conn.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at)"
            " VALUES (?, ?, datetime('now', ?))",
            (user["user_id"], _hash_token(token), lifetime),
        )

    response = jsonify(user=_public_user(user))
    response.set_cookie(
        SESSION_COOKIE,
        token,
        # No max_age = the browser forgets the cookie when it closes.
        max_age=REMEMBER_ME_DAYS * 24 * 60 * 60 if remember_me else None,
        httponly=True,
        samesite="Lax",
        # Set COOKIE_SECURE=1 when the site is served over HTTPS.
        secure=os.environ.get("COOKIE_SECURE") == "1",
    )
    return response


@auth_bp.post("/logout")
def logout():
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with db() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),)
            )
    response = jsonify(ok=True)
    response.delete_cookie(SESSION_COOKIE)
    return response


@auth_bp.get("/me")
def me():
    user = current_user()
    if user is None:
        return jsonify(error="Not signed in."), 401
    return jsonify(user=_public_user(user))
