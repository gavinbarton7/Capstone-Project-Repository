"""Profile: personal details, address, email, password, delete account.

Endpoints (all need a signed-in user, otherwise 401)
    GET    /api/profile             -> {user: {...}}
    PUT    /api/profile             (also PATCH) change any of the fields below;
                                    send only what changed -> {user: {...}}
    POST   /api/profile/password    {password, new_password}   (also PUT)
    DELETE /api/profile             {password}   deletes the account

Fields (JSON key -> rule). The rules themselves live in validation.py.
    first_name, last_name  required, max 50 characters
    email                  required, valid email, must not belong to someone else.
                           THIS is how a user changes their email: it is updated
                           in the database right away and they sign in with the
                           new one from then on.
    phone                  optional, numbers only (10 digits)
    birthday               optional, YYYY-MM-DD (what a date picker sends)
    street_address         optional, letters/numbers, max 100
    city, state            optional, letters/numbers, max 50
    zip_code               optional, numbers only (5 digits), kept as text
Optional fields: send "" (or null) to clear the saved value.

The React form's own key names work too: firstName, lastName, street, zip,
so a React page can send its whole form state as it is.

Dates are stored as YYYY-MM-DD. The response also has created_at_display and
birthday_display in the user's chosen date format (Settings).
"""

import sqlite3

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from auth import SESSION_COOKIE, end_session, hash_token, json_body, login_required
from db_connection import db
from settings_routes import format_date, get_settings
from validation import (
    MIN_PASSWORD_LENGTH,
    pick,
    validate_birthday,
    validate_email,
    validate_name,
    validate_phone,
    validate_text,
    validate_zip,
)

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

# database column -> (names the value may be sent under, validator)
# To add a profile field: add the column to schema.sql and to USER_PROFILE_COLUMNS
# (db_connection.py), add it to auth.public_user() and current_user(), then add one line here.
PROFILE_FIELDS = {
    "first_name": (("first_name", "firstName"), lambda v: validate_name(v, "First name")),
    "last_name": (("last_name", "lastName"), lambda v: validate_name(v, "Last name")),
    "email": (("email",), validate_email),
    "phone": (("phone",), validate_phone),
    "birthday": (("birthday",), validate_birthday),
    "street_address": (("street_address", "street"), lambda v: validate_text(v, "Street address", 100)),
    "city": (("city",), lambda v: validate_text(v, "City", 50)),
    "state": (("state",), lambda v: validate_text(v, "State", 50)),
    "zip_code": (("zip_code", "zip"), validate_zip),
}

PROFILE_COLUMNS = (
    "user_id, email, first_name, last_name, created_at, phone, birthday, "
    "street_address, city, state, zip_code"
)


def _profile_json(row, date_format):
    """User row -> JSON-ready dict, plus display copies of the dates in the user's format."""
    profile = {key: row[key] for key in row.keys()}
    profile["created_at_display"] = format_date(row["created_at"], date_format)
    profile["birthday_display"] = format_date(row["birthday"], date_format)
    # The same values under the names the React Profile form uses.
    profile["firstName"] = row["first_name"]
    profile["lastName"] = row["last_name"]
    profile["street"] = row["street_address"]
    profile["zip"] = row["zip_code"]
    return profile


def _load_profile(conn, user_id):
    row = conn.execute(
        f"SELECT {PROFILE_COLUMNS} FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return _profile_json(row, get_settings(conn, user_id)["date_format"])


@profile_bp.get("")
@login_required
def read_profile():
    with db() as conn:
        return jsonify(user=_load_profile(conn, g.user["user_id"]))


@profile_bp.route("", methods=["PUT", "PATCH"])
@login_required
def update_profile():
    data = json_body()

    # 1) Check every field that was sent. Nothing is saved unless ALL are valid.
    changes = {}
    for column, (names, validate) in PROFILE_FIELDS.items():
        if any(name in data for name in names):
            value, error = validate(pick(data, *names))
            if error:
                return jsonify(error=error), 400
            changes[column] = value
    if not changes:
        return jsonify(error="Nothing to update."), 400

    # 2) Save them in one UPDATE. Column names come from the fixed PROFILE_FIELDS
    #    keys above, never from user input.
    set_clause = ", ".join(f"{column} = ?" for column in changes)
    try:
        with db() as conn:
            conn.execute(
                f"UPDATE users SET {set_clause} WHERE user_id = ?",
                (*changes.values(), g.user["user_id"]),
            )
            user = _load_profile(conn, g.user["user_id"])
    except sqlite3.IntegrityError:     # the email column is UNIQUE
        return jsonify(error="An account with that email already exists."), 409
    return jsonify(user=user)


def _first_text(data, *names):
    for name in names:
        if isinstance(data.get(name), str):
            return data[name]
    return ""


@profile_bp.route("/password", methods=["POST", "PUT"])
@login_required
def change_password():
    """Body: {password: <current>, new_password: <new>}"""
    data = json_body()
    current = _first_text(data, "password", "current_password", "currentPassword")
    new_password = _first_text(data, "new_password", "newPassword")
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify(error=f"Password must be at least {MIN_PASSWORD_LENGTH} characters."), 400

    with db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE user_id = ?", (g.user["user_id"],)
        ).fetchone()
        if not check_password_hash(row["password_hash"], current):
            return jsonify(error="Current password is incorrect."), 403

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?",
            (generate_password_hash(new_password), g.user["user_id"]),
        )
        # Sign out every OTHER device; this one stays signed in.
        conn.execute(
            "DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
            (g.user["user_id"], hash_token(request.cookies.get(SESSION_COOKIE, ""))),
        )
    return jsonify(ok=True)


@profile_bp.delete("")
@login_required
def delete_account():
    """Body: {password: <current>}. Deletes the user and everything they own."""
    password = _first_text(json_body(), "password", "current_password", "currentPassword")
    with db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE user_id = ?", (g.user["user_id"],)
        ).fetchone()
        if not check_password_hash(row["password_hash"], password):
            return jsonify(error="Password is incorrect."), 403
        # Cascades: sessions, settings, budgets, expenses, bank items... all go too.
        conn.execute("DELETE FROM users WHERE user_id = ?", (g.user["user_id"],))
    return end_session(jsonify(ok=True))
