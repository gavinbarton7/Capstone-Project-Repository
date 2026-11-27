"""Tests for the whole backend: JSON API, HTML pages and the database.

Run from the folder that holds app.py (or from the repo root):
    pip install pytest
    python -m pytest
Each test uses its own temporary database, so your real cache_money.db is never touched.
"""

import os
import sqlite3
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from db_connection import get_connection, init_db  # noqa: E402

ALEX = {"first_name": "Alex", "last_name": "Lee", "email": "alex@example.com", "password": "correct-horse"}
SAM = {**ALEX, "first_name": "Sam", "email": "sam@example.com"}
HAS_TEMPLATES = (BACKEND_DIR / "templates").is_dir()


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_MONEY_DB", str(tmp_path / "test.db"))
    return create_app()


def sign_in(app, person=ALEX):
    """A test browser that is registered and signed in as `person`."""
    client = app.test_client()
    client.post("/api/auth/register", json=person)
    response = client.post("/api/auth/login", json={"email": person["email"], "password": person["password"]})
    assert response.status_code == 200
    return client


@pytest.fixture
def client(app):
    return sign_in(app)


# =============================================================================
# Sign up / log in / log out (JSON)
# =============================================================================
def test_register_stores_a_hashed_password(app):
    response = app.test_client().post("/api/auth/register", json=ALEX)
    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == "alex@example.com"
    assert "password" not in str(response.get_json())
    conn = get_connection()
    stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    conn.close()
    assert ALEX["password"] not in stored


def test_register_accepts_camel_case_names(app):
    body = {"firstName": "Ada", "lastName": "Lovelace", "email": "ada@example.com", "password": "password123"}
    assert app.test_client().post("/api/auth/register", json=body).status_code == 201


def test_register_rejects_duplicate_email_ignoring_case(app):
    client = app.test_client()
    client.post("/api/auth/register", json=ALEX)
    assert client.post("/api/auth/register", json={**ALEX, "email": "ALEX@example.com"}).status_code == 409


@pytest.mark.parametrize(
    "change",
    [{"password": "short"}, {"email": "not-an-email"}, {"first_name": "   "}, {"last_name": None}, {"first_name": "x" * 51}],
)
def test_register_rejects_bad_input(app, change):
    response = app.test_client().post("/api/auth/register", json={**ALEX, **change})
    assert response.status_code == 400
    assert response.get_json()["error"]


def test_login_then_me_then_logout(app):
    client = app.test_client()
    client.post("/api/auth/register", json=ALEX)
    assert client.get("/api/auth/me").status_code == 401

    response = client.post("/api/auth/login", json={"email": "Alex@Example.com", "password": ALEX["password"]})
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["Set-Cookie"]
    assert client.get("/api/auth/me").get_json()["user"]["first_name"] == "Alex"

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_wrong_password_and_unknown_email_look_the_same(app):
    client = app.test_client()
    client.post("/api/auth/register", json=ALEX)
    wrong = client.post("/api/auth/login", json={"email": ALEX["email"], "password": "wrong-password"})
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


def test_remember_me_sets_a_lasting_cookie(app):
    client = app.test_client()
    client.post("/api/auth/register", json=ALEX)
    creds = {"email": ALEX["email"], "password": ALEX["password"]}
    assert "Max-Age" not in client.post("/api/auth/login", json=creds).headers["Set-Cookie"]
    assert "Max-Age=2592000" in client.post("/api/auth/login", json={**creds, "remember_me": True}).headers["Set-Cookie"]


def test_expired_session_is_rejected(app):
    client = sign_in(app)
    conn = get_connection()
    conn.execute("UPDATE sessions SET expires_at = datetime('now', '-1 minute')")
    conn.commit()
    conn.close()
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/api/auth/me"), ("get", "/api/profile"), ("put", "/api/profile"),
        ("post", "/api/profile/password"), ("delete", "/api/profile"),
        ("get", "/api/settings"), ("put", "/api/settings"),
        ("get", "/api/budgets"), ("post", "/api/budgets"),
        ("put", "/api/budgets/1"), ("delete", "/api/budgets/1"),
    ],
)
def test_signed_out_requests_get_401(app, method, path):
    assert getattr(app.test_client(), method)(path, json={}).status_code == 401


def test_errors_are_json(app):
    assert app.test_client().get("/api/nope").get_json() == {"error": "Not found."}
    assert app.test_client().get("/api/auth/login").status_code == 405


# =============================================================================
# Profile (including changing the email)
# =============================================================================
def test_me_has_the_profile_fields(client):
    user = client.get("/api/auth/me").get_json()["user"]
    assert user["first_name"] == "Alex" and user["created_at"]
    for field in ("phone", "birthday", "street_address", "city", "state", "zip_code"):
        assert user[field] is None


def test_update_profile_saves_every_field(client):
    response = client.put("/api/profile", json={
        "phone": "(555) 123-4567", "birthday": "1999-03-07", "street_address": "12 Main St. #4",
        "city": "Kansas City", "state": "Missouri", "zip_code": "02134",
    })
    assert response.status_code == 200
    user = response.get_json()["user"]
    assert user["phone"] == "5551234567"      # formatting dropped
    assert user["zip_code"] == "02134"        # leading zero kept
    assert client.get("/api/auth/me").get_json()["user"]["city"] == "Kansas City"


def test_profile_accepts_the_react_form_names(client):
    form = {"firstName": "Alexandra", "lastName": "Lee", "email": "alex@example.com", "phone": "",
            "birthday": "", "street": "1 Elm St", "city": "KC", "state": "MO", "zip": "64108"}
    user = client.put("/api/profile", json=form).get_json()["user"]
    assert user["first_name"] == "Alexandra" and user["street_address"] == "1 Elm St"
    assert user["zip"] == "64108" and user["street"] == "1 Elm St"


@pytest.mark.parametrize(
    "body",
    [{"phone": "123"}, {"phone": "abc1234567"}, {"zip_code": "1234"}, {"zip_code": "12a45"},
     {"birthday": "2999-01-01"}, {"birthday": "03/07/1999"}, {"city": "<script>"}, {"state": "x" * 60},
     {"first_name": "  "}, {"email": "nope"}, {}],
)
def test_profile_rejects_bad_values(client, body):
    response = client.put("/api/profile", json=body)
    assert response.status_code == 400 and response.get_json()["error"]


def test_blank_optional_field_clears_it(client):
    client.put("/api/profile", json={"phone": "5551234567"})
    assert client.put("/api/profile", json={"phone": ""}).get_json()["user"]["phone"] is None


def test_one_bad_field_saves_nothing(client):
    assert client.put("/api/profile", json={"city": "Kansas City", "zip_code": "bad"}).status_code == 400
    assert client.get("/api/profile").get_json()["user"]["city"] is None


def test_changing_the_email_updates_the_database(app, client):
    response = client.put("/api/profile", json={"email": "New.Email@Example.com"})
    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "new.email@example.com"     # saved lowercase

    conn = get_connection()
    assert conn.execute("SELECT email FROM users").fetchone()[0] == "new.email@example.com"
    conn.close()
    assert client.get("/api/auth/me").get_json()["user"]["email"] == "new.email@example.com"   # still signed in

    fresh = app.test_client()
    old = fresh.post("/api/auth/login", json={"email": ALEX["email"], "password": ALEX["password"]})
    new = fresh.post("/api/auth/login", json={"email": "new.email@example.com", "password": ALEX["password"]})
    assert old.status_code == 401 and new.status_code == 200


def test_email_change_is_checked_for_duplicates_and_format(app, client):
    sign_in(app, SAM)
    assert client.put("/api/profile", json={"email": "SAM@example.com"}).status_code == 409
    assert client.put("/api/profile", json={"email": "not-an-email"}).status_code == 400
    assert client.get("/api/profile").get_json()["user"]["email"] == ALEX["email"]


def test_change_password(app, client):
    other_device = app.test_client()
    other_device.post("/api/auth/login", json={"email": ALEX["email"], "password": ALEX["password"]})

    assert client.post("/api/profile/password", json={"password": "bad", "new_password": "new-password-1"}).status_code == 403
    assert client.post("/api/profile/password", json={"password": ALEX["password"], "new_password": "x"}).status_code == 400
    ok = client.post("/api/profile/password", json={"currentPassword": ALEX["password"], "newPassword": "new-password-1"})
    assert ok.status_code == 200
    assert client.get("/api/auth/me").status_code == 200            # this device stays signed in
    assert other_device.get("/api/auth/me").status_code == 401      # other devices are signed out

    fresh = app.test_client()
    assert fresh.post("/api/auth/login", json={"email": ALEX["email"], "password": ALEX["password"]}).status_code == 401
    assert fresh.post("/api/auth/login", json={"email": ALEX["email"], "password": "new-password-1"}).status_code == 200


def test_delete_account_removes_everything(client):
    client.put("/api/settings", json={"language": "fr"})
    client.post("/api/budgets", json={"items": [{"title": "Rent", "amount": 5}]})
    assert client.delete("/api/profile", json={"password": "wrong"}).status_code == 403
    assert client.delete("/api/profile", json={"password": ALEX["password"]}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    conn = sqlite3.connect(os.environ["CACHE_MONEY_DB"])
    for table in ("users", "user_settings", "budgets", "budget_allocations", "sessions"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    conn.close()


# =============================================================================
# Settings
# =============================================================================
def test_settings_defaults_and_options(client):
    body = client.get("/api/settings").get_json()
    assert body["settings"]["language"] == "en-US"
    assert body["settings"]["date_format"] == "MM/DD/YYYY"
    assert body["settings"]["week_start"] == "sunday"
    assert [o["value"] for o in body["options"]["languages"]] == ["en-US", "es", "fr"]
    assert len(body["options"]["week_starts"]) == 7


def test_settings_save_and_accept_react_wording(client):
    client.put("/api/settings", json={"language": "Spanish", "weekStartsOn": "Friday"})
    body = client.put("/api/settings", json={"dateFormat": "DD/MM/YYYY"}).get_json()["settings"]
    assert (body["language"], body["week_start"], body["date_format"]) == ("es", "friday", "DD/MM/YYYY")
    assert client.get("/api/settings").get_json()["settings"]["language"] == "es"


@pytest.mark.parametrize("body", [{"language": "de"}, {"date_format": "x"}, {"week_start": "funday"}, {"language": 5}, {"language": None}, {}])
def test_settings_reject_bad_values(client, body):
    assert client.put("/api/settings", json=body).status_code == 400


def test_settings_belong_to_one_user(app, client):
    client.put("/api/settings", json={"language": "fr"})
    assert sign_in(app, SAM).get("/api/settings").get_json()["settings"]["language"] == "en-US"


def test_date_format_changes_displayed_dates(client):
    client.put("/api/profile", json={"birthday": "1999-03-07"})
    assert client.get("/api/profile").get_json()["user"]["birthday_display"] == "03/07/1999"
    client.put("/api/settings", json={"date_format": "DD/MM/YYYY"})
    assert client.get("/api/profile").get_json()["user"]["birthday_display"] == "07/03/1999"
    client.put("/api/settings", json={"date_format": "YYYY-MM-DD"})
    user = client.get("/api/profile").get_json()["user"]
    assert user["birthday_display"] == "1999-03-07" and user["birthday"] == "1999-03-07"
    assert user["created_at_display"] == user["created_at"][:10]


# =============================================================================
# Budgets
# =============================================================================
def test_budget_create_update_list_delete(client):
    assert client.get("/api/budgets").get_json() == {"budgets": []}
    created = client.post("/api/budgets", json={"items": [
        {"title": "Rent", "amount": "1200.50"}, {"title": "car", "amount": 300},
        {"title": "", "amount": 0}, {"title": "Rent", "amount": 10}]})
    assert created.status_code == 201
    budget = created.get_json()["budget"]
    assert budget["items"] == [{"title": "Rent", "amount": 1210.5}, {"title": "Car", "amount": 300.0}]

    updated = client.put(f"/api/budgets/{budget['id']}", json={"items": [{"title": "Food", "amount": 250}]})
    assert updated.get_json()["budget"]["items"] == [{"title": "Food", "amount": 250.0}]
    assert len(client.get("/api/budgets").get_json()["budgets"]) == 1
    assert client.delete(f"/api/budgets/{budget['id']}").status_code == 200
    assert client.delete(f"/api/budgets/{budget['id']}").status_code == 404


def test_budget_needs_a_valid_item(client):
    for items in ([], [{"title": "x", "amount": 0}], [{"title": "", "amount": 5}], "nope"):
        assert client.post("/api/budgets", json={"items": items}).status_code == 400


def test_users_cannot_touch_each_others_budgets(app, client):
    mine = client.post("/api/budgets", json={"items": [{"title": "Rent", "amount": 5}]}).get_json()["budget"]
    other = sign_in(app, SAM)
    assert other.get("/api/budgets").get_json() == {"budgets": []}
    assert other.put(f"/api/budgets/{mine['id']}", json={"items": [{"title": "x", "amount": 1}]}).status_code == 404
    assert other.delete(f"/api/budgets/{mine['id']}").status_code == 404
    assert len(client.get("/api/budgets").get_json()["budgets"]) == 1


# =============================================================================
# Database creation / upgrade
# =============================================================================
def test_a_missing_database_file_is_created(tmp_path, monkeypatch):
    path = tmp_path / "brand_new.db"
    monkeypatch.setenv("CACHE_MONEY_DB", str(path))
    assert not path.exists()
    create_app()
    conn = sqlite3.connect(path)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "sessions", "user_settings", "budgets", "categories"} <= tables
    conn.close()


def test_an_older_database_file_is_upgraded(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    monkeypatch.setenv("CACHE_MONEY_DB", str(path))
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE users (user_id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,"
        " password_hash TEXT NOT NULL, first_name TEXT NOT NULL, last_name TEXT NOT NULL,"
        " created_at TEXT NOT NULL DEFAULT (datetime('now'))) STRICT"
    )
    conn.execute("INSERT INTO users (email, password_hash, first_name, last_name) VALUES ('a@b.co', 'x', 'A', 'B')")
    conn.commit()
    conn.close()

    init_db()
    init_db()   # safe to run twice
    conn = sqlite3.connect(path)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    assert {"phone", "birthday", "street_address", "city", "state", "zip_code"} <= columns
    assert conn.execute("SELECT first_name FROM users").fetchone()[0] == "A"     # data kept
    conn.close()


# =============================================================================
# HTML pages (only when the /templates folder is there)
# =============================================================================
pages = pytest.mark.skipif(not HAS_TEMPLATES, reason="no templates folder")


def form_sign_up(client, person=ALEX):
    return client.post("/signup", data={k: person[k] for k in ("first_name", "last_name", "email", "password")})


def form_log_in(client, email=ALEX["email"], password=ALEX["password"], **extra):
    return client.post("/login", data={"email": email, "password": password, **extra})


@pages
def test_pages_are_on_by_default(app):
    assert app.config["PAGES_ENABLED"] is True
    assert b"Sign Up" in app.test_client().get("/").data
    assert app.test_client().get("/login").status_code == 200


@pages
def test_signup_form_sends_you_to_login_and_does_not_sign_you_in(app):
    client = app.test_client()
    response = form_sign_up(client)
    assert response.status_code == 302 and response.headers["Location"].endswith("/login?created=1")
    assert b"Account created" in client.get("/login?created=1").data
    assert client.get("/api/auth/me").status_code == 401
    conn = get_connection()
    assert conn.execute("SELECT first_name, last_name, email FROM users").fetchone()[:] == ("Alex", "Lee", "alex@example.com")
    conn.close()


@pages
def test_signup_form_errors_show_on_the_page_and_keep_what_was_typed(app):
    client = app.test_client()
    bad = client.post("/signup", data={"first_name": "Alex", "last_name": "Lee", "email": "nope", "password": "x" * 9})
    assert bad.status_code == 400 and b"valid email" in bad.data and b'value="Alex"' in bad.data
    form_sign_up(client)
    dup = form_sign_up(client)
    assert dup.status_code == 409 and b"already exists" in dup.data


@pages
def test_login_form_wrong_password_shows_one_message(app):
    client = app.test_client()
    form_sign_up(client)
    wrong_pw = form_log_in(client, password="wrong-password")
    wrong_email = form_log_in(client, email="nobody@example.com")
    assert wrong_pw.status_code == wrong_email.status_code == 401
    assert b"Incorrect email or password." in wrong_pw.data and b"Incorrect email or password." in wrong_email.data
    assert b'value="alex@example.com"' in wrong_pw.data


@pages
def test_login_form_then_pages_then_logout(app):
    client = app.test_client()
    form_sign_up(client)
    assert client.get("/dashboard").headers["Location"].endswith("/login")      # signed out -> login page

    response = form_log_in(client)
    assert response.status_code == 302 and response.headers["Location"].endswith("/dashboard")
    assert "Max-Age" not in response.headers["Set-Cookie"]
    assert b"Welcome, Alex Lee!" in client.get("/dashboard").data
    for path in ("/budget", "/profile", "/setting", "/expenses"):
        assert client.get(path).status_code == 200
    assert client.get("/").headers["Location"].endswith("/dashboard")           # signed in -> skip sign up page

    assert client.get("/logout").status_code == 302
    assert client.get("/dashboard").status_code == 302
    assert client.get("/api/auth/me").status_code == 401


@pages
def test_login_form_remember_me(app):
    client = app.test_client()
    form_sign_up(client)
    assert "Max-Age=2592000" in form_log_in(client, remember_me="on").headers["Set-Cookie"]


@pages
def test_a_page_login_also_works_for_the_api(app):
    client = app.test_client()
    form_sign_up(client)
    form_log_in(client)
    assert client.get("/api/auth/me").get_json()["user"]["email"] == "alex@example.com"


@pages
def test_json_still_works_on_the_page_urls(app):
    client = app.test_client()
    assert client.post("/signup", json=ALEX).status_code == 201
    assert client.post("/login", json={"email": ALEX["email"], "password": ALEX["password"]}).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


@pages
def test_profile_and_settings_pages_use_the_saved_values(app):
    client = sign_in(app)
    client.put("/api/profile", json={"city": "Kansas City", "birthday": "1999-03-07"})
    client.put("/api/settings", json={"date_format": "DD/MM/YYYY", "language": "fr", "week_start": "friday"})
    user = client.get("/api/profile").get_json()["user"]
    year, month, day = user["created_at"][:10].split("-")
    created = f"{day}/{month}/{year}"                 # DD/MM/YYYY, the format chosen above
    assert user["created_at_display"] == created

    profile = client.get("/profile").data.decode()
    assert 'value="Kansas City"' in profile and 'value="1999-03-07"' in profile
    assert f"Member since {created}" in profile
    setting = client.get("/setting").data.decode()
    assert 'value="DD/MM/YYYY" selected' in setting and 'value="fr" selected' in setting and 'value="friday" selected' in setting


@pages
def test_email_can_be_changed_from_the_settings_page_form(app):
    client = sign_in(app)
    assert 'name="email"' in client.get("/setting").data.decode()          # the Account email box is there
    assert client.put("/api/profile", json={"email": "changed@example.com"}).status_code == 200   # what its button calls
    assert 'value="changed@example.com"' in client.get("/setting").data.decode()
    assert 'value="changed@example.com"' in client.get("/profile").data.decode()
    assert form_log_in(app.test_client(), email="changed@example.com").status_code == 302


@pages
def test_pages_can_be_switched_off(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_MONEY_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("SERVE_HTML_PAGES", "0")
    app = create_app()
    client = app.test_client()
    assert app.config["PAGES_ENABLED"] is False
    assert client.get("/dashboard").status_code == 404 and client.get("/login").status_code == 404
    assert client.post("/api/auth/register", json=ALEX).status_code == 201      # the API is untouched
