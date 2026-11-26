"""Rules for the values users type in, shared by auth.py and profile_routes.py

Every validate_* function returns a pair:  (clean_value, error_message)
  - on success  -> (value ready to save, None)
  - on a problem -> (None, "text the user will see")
Optional fields (phone, birthday, address...) treat a blank value as "clear it"
and return (None, None)

To change a rule (for example allow 11-digit phone numbers), change it here once
"""

import re
from datetime import date, datetime

# ---- limits you may want to change --------
MIN_PASSWORD_LENGTH = 8
PHONE_DIGITS = 10   # US number basically
ZIP_DIGITS = 5

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
# Street / city / state: letters (accents are fine), numbers, spaces and  . , # ' / -
TEXT_PATTERN = re.compile(r"^[\w\s.,#'\u2019/\-]+$")


def pick(data, *names, default=None):
    """Value of the first key in `names` found in `data` (a dict).

    Lets the front end use either style of name, e.g. pick(data, "first_name", "firstName").
    """
    for name in names:
        if name in data:
            return data[name]
    return default


# ---- required fields ------
def validate_name(value, label):
    value = value.strip() if isinstance(value, str) else ""
    if not value:
        return None, f"{label} is required."
    if len(value) > 50:
        return None, f"{label} is too long."
    return value, None


def validate_email(value):
    value = value.strip().lower() if isinstance(value, str) else ""   # saved lowercase
    if not EMAIL_PATTERN.match(value):
        return None, "Please enter a valid email address."
    return value, None


def validate_password(value):
    value = value if isinstance(value, str) else ""
    if len(value) < MIN_PASSWORD_LENGTH:
        return None, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return value, None


# ---- optional profile fields --------
def validate_text(value, label, max_len):
    """Street address / city / state: letters and numbers (plus basic punctuation)."""
    value = str(value).strip() if value is not None else ""
    if not value:
        return None, None
    if len(value) > max_len:
        return None, f"{label} is too long."
    if not TEXT_PATTERN.match(value):
        return None, f"{label} can only use letters, numbers and basic punctuation."
    return value, None


def validate_phone(value):
    """Numbers only. Spaces, dashes, dots and brackets the user typed are dropped,
    so '(555) 123-4567' is saved as '5555551234'."""
    raw = str(value).strip() if value is not None else ""
    if not raw:
        return None, None
    digits = re.sub(r"[\s().+\-]", "", raw)
    if not re.fullmatch(r"[0-9]+", digits) or len(digits) != PHONE_DIGITS:
        return None, f"Phone number must be {PHONE_DIGITS} digits."
    return digits, None


def validate_zip(value):
    """Numbers only. Kept as text so a ZIP like 02134 keeps its leading 0."""
    raw = str(value).strip() if value is not None else ""
    if not raw:
        return None, None
    if not re.fullmatch(rf"[0-9]{{{ZIP_DIGITS}}}", raw):
        return None, f"ZIP code must be {ZIP_DIGITS} digits."
    return raw, None


def validate_birthday(value):
    """Expects YYYY-MM-DD (what a date picker sends). Must be a real date, not in the future."""
    raw = str(value).strip() if value is not None else ""
    if not raw:
        return None, None
    try:
        day = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None, "Birthday must be a valid date (YYYY-MM-DD)."
    if day > date.today() or day.year < 1900:
        return None, "Birthday is not a valid date."
    return day.isoformat(), None
