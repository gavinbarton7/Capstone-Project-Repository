"""Settings: language, date format, week start. Saved per user in `user_settings`.

Endpoints (need a signed-in user, otherwise 401)
    GET /api/settings    -> {settings: {...}, options: {...}}
    PUT /api/settings    (also PATCH) change one or more; send only what changed
                         {language, date_format, week_start}

What each setting does today
    language    saved only. Spanish and French can be chosen but nothing changes yet.
    date_format works now: every date the backend formats for display follows it
                (see format_date). Dates are always STORED as YYYY-MM-DD.
    week_start  saved only. Nothing changes yet.

Values are forgiving about how they are written, so the React form's own wording
works too: "English (US)" or "en-US", "dateFormat" or "date_format",
"weekStartsOn" or "week_start", "Monday" or "monday".

To offer a new choice, add it to LANGUAGES / DATE_FORMATS / WEEK_STARTS below.
The dropdowns on the settings page are built from these lists automatically.
"""

from datetime import datetime

from flask import Blueprint, g, jsonify

from auth import current_user, json_body, login_required
from db_connection import db
from validation import pick

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

LANGUAGES = {                      # value saved -> label shown
    "en-US": "English (US)",
    "es": "Spanish",               # can be chosen, does nothing yet
    "fr": "French",                # can be chosen, does nothing yet
}
DATE_FORMATS = {                   # value saved -> Python strftime pattern
    "MM/DD/YYYY": "%m/%d/%Y",
    "DD/MM/YYYY": "%d/%m/%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
}
WEEK_STARTS = [                    # saved only, does nothing yet
    "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
]
DEFAULTS = {"language": "en-US", "date_format": "MM/DD/YYYY", "week_start": "sunday"}

# Dropdown choices for the front end, as {value, label} pairs.
OPTIONS = {
    "languages": [{"value": k, "label": v} for k, v in LANGUAGES.items()],
    "date_formats": [{"value": k, "label": k} for k in DATE_FORMATS],
    "week_starts": [{"value": d, "label": d.capitalize()} for d in WEEK_STARTS],
}


def _lookup(pairs):
    """lowercase text -> the value we store, from [(stored_value, label), ...]."""
    table = {}
    for value, label in pairs:
        table[value.lower()] = value
        table[label.lower()] = value
    return table


# setting name -> (names it may be sent under, accepted values, error message)
SETTING_FIELDS = {
    "language": (("language",), _lookup(LANGUAGES.items()), "Unsupported language."),
    "date_format": (
        ("date_format", "dateFormat"),
        _lookup((k, k) for k in DATE_FORMATS),
        "Unsupported date format.",
    ),
    "week_start": (
        ("week_start", "weekStartsOn"),
        _lookup((d, d.capitalize()) for d in WEEK_STARTS),
        "Unsupported day for the start of the week.",
    ),
}


# =============================================================================
# Helpers other files use
# =============================================================================
def get_settings(conn, user_id):
    """The user's {language, date_format, week_start}; the defaults if never changed.
    `conn` is an open connection from `with db() as conn:`."""
    row = conn.execute(
        "SELECT language, date_format, week_start FROM user_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return {**DEFAULTS, **dict(row)} if row else dict(DEFAULTS)


def current_settings():
    """Settings of whoever is signed in (cached for this request).
    Signed out -> the defaults. Used by the HTML pages and by format_date()."""
    if "_settings" not in g:
        user = getattr(g, "user", None) or current_user()
        if user is None:
            g._settings = dict(DEFAULTS)
        else:
            with db() as conn:
                g._settings = get_settings(conn, user["user_id"])
    return g._settings


def format_date(value, date_format=None):
    """Show a stored date ('2026-11-20' or '2026-11-20 18:25:31') in the user's chosen
    format. Returns "" for an empty value.

    Dates are ALWAYS stored as YYYY-MM-DD; only the display changes.
      In a template:   {{ some_date | fmt_date }}
      In Python:       format_date(row["expense_date"], settings["date_format"])
    Any new endpoint that sends dates meant for display should use this so it
    follows the user's setting.
    """
    if not value:
        return ""
    date_format = date_format or current_settings()["date_format"]
    try:
        day = datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except ValueError:
        return str(value)
    return day.strftime(DATE_FORMATS.get(date_format, DATE_FORMATS[DEFAULTS["date_format"]]))


def settings_options_for_templates():
    """The dropdown choices (same as OPTIONS). The HTML pages use {{ settings.options }}."""
    return OPTIONS


def _settings_json(settings):
    return {
        **settings,
        "language_label": LANGUAGES[settings["language"]],
        "week_start_label": settings["week_start"].capitalize(),
    }


# =============================================================================
# Endpoints
# =============================================================================
@settings_bp.get("")
@login_required
def read_settings():
    with db() as conn:
        settings = get_settings(conn, g.user["user_id"])
    return jsonify(settings=_settings_json(settings), options=OPTIONS)


@settings_bp.route("", methods=["PUT", "PATCH"])
@login_required
def update_settings():
    data = json_body()
    changes = {}
    for setting, (names, accepted, message) in SETTING_FIELDS.items():
        value = pick(data, *names, default=None)
        if any(name in data for name in names):
            stored = accepted.get(value.strip().lower()) if isinstance(value, str) else None
            if stored is None:
                return jsonify(error=message), 400
            changes[setting] = stored
    if not changes:
        return jsonify(error="Nothing to update."), 400

    with db() as conn:
        new = {**get_settings(conn, g.user["user_id"]), **changes}
        # "Upsert": create the user's row the first time, update it afterwards.
        conn.execute(
            "INSERT INTO user_settings (user_id, language, date_format, week_start)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET language = excluded.language,"
            " date_format = excluded.date_format, week_start = excluded.week_start",
            (g.user["user_id"], new["language"], new["date_format"], new["week_start"]),
        )
    g.pop("_settings", None)   # forget the cached copy so the rest of this request sees the change
    return jsonify(settings=_settings_json(new), options=OPTIONS)
