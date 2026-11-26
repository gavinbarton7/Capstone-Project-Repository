# Cache Money Backend

A Flask + SQLite backend that works **two ways from the same files**:

| Mode | What you get | How |
|---|---|---|
| **Backend only** | The plain HTML pages in `templates/` (sign up, login, dashboard, profile, settings, ...) plus the JSON API. No React needed. | `python app.py`, then open http://127.0.0.1:8000 |
| **With the React frontend** | The JSON API only. The Vite dev server forwards every `/api/...` request to port 8000. | `python backend/app.py` in the repo, plus `npm run dev` in `frontend` |

Nothing has to be switched by hand. The HTML pages are served only when a `templates/` folder exists next to `app.py` (or `SERVE_HTML_PAGES=1`), and Plaid is loaded only when `plaid_routes.py` and its packages are there.

## What each file does

| File | Job |
|---|---|
| `app.py` | Starts the server. Creates the app, plugs in all the other files, makes errors JSON. Start here. |
| `db_connection.py` | Finds or creates the SQLite database. Gives every file `with db() as conn:`. Adds any missing profile columns to an older database. |
| `validation.py` | The rules for names, email, password, phone, ZIP, birthday. Change a rule here once and it applies everywhere. |
| `auth.py` | Sign up, log in, log out, "who am I?", and `@login_required`. Used by both the JSON API and the HTML pages, so there is one sign-in system. |
| `profile_routes.py` | Profile details, address, **changing the email**, password, delete account. |
| `settings_routes.py` | Language, date format, week start. Also the `format_date` helper for showing dates. |
| `budget_routes.py` | Budget plans. |
| `pages.py` | The HTML pages. The only file that serves web pages, and it can be turned off. |
| `plaid_routes.py` | Bank connection through Plaid. Lives in the team repo only (not part of this folder). |
| `schema.sql` | The database tables. |
| `templates/` | The plain HTML pages. |
| `tests/test_backend.py` | Automatic tests (70 of them). |

Every `.py` file starts with a comment block explaining what it does, and each function has a short description.

## Run it

**Backend only** (in the `Back_end` folder, one command at a time):
```
python -m venv venv
venv\Scripts\activate
pip install flask
python app.py
```
Open http://127.0.0.1:8000. The terminal prints which database, pages and Plaid mode is in use. Edits to anything in `templates/` show up on refresh. Python edits restart the server by themselves.

**With the React frontend** (repo root, two terminals):
```
pip install -r backend/requirements.txt
python backend/app.py                 # API on http://localhost:8000
cd frontend && npm install && npm run dev
```

**Settings** (environment variables, all optional; on Windows: `set NAME=value` before `python app.py`):

| Variable | Meaning |
|---|---|
| `PORT` | Port to listen on. Default `8000` (the frontend's `vite.config.js` expects 8000). |
| `FLASK_DEBUG` | `0` turns off the auto-restart / debug mode. Default is on. |
| `SERVE_HTML_PAGES` | `0` = API only, `1` = force the pages on. Default: on if `templates/` exists. |
| `CACHE_MONEY_DB` | Use a different database file. |
| `COOKIE_SECURE` | `1` marks the sign-in cookie HTTPS-only (use when deployed). |
| `PLAID_CLIENT_ID`, `PLAID_SECRET` | Plaid keys (repo only), usually in a `.env` file. |

No `SECRET_KEY` is needed any more: sign-in uses a random token stored in the database, not a signed cookie.

## Where the database is

- **Team repo** (`backend/` next to `database/`): `database/cache_money.db`, built from `database/schema.sql`.
- **Stand-alone folder**: `cache_money.db` in the same folder as `app.py`, built from the `schema.sql` next to it. If the file does not exist it is created on start.
- On every start the app runs `schema.sql` (only creates what is missing, existing data is untouched) and adds any missing profile columns. Keep **one** copy of `schema.sql` per project: in the repo it is `database/schema.sql`.
- The profile fields live on `users` (`phone`, `birthday`, `street_address`, `city`, `state`, `zip_code`, all optional). Settings live in `user_settings` (`user_id`, `language`, `date_format`, `week_start`), one row per user, created the first time they change a setting.
- Dates are always stored as `YYYY-MM-DD`. Money is stored as whole cents.

## How requests and responses work

- **JSON API**: send `Content-Type: application/json`. Successful answers wrap the data under a name: `{ "user": {...} }`, `{ "settings": {...} }`, `{ "budget": {...} }`, `{ "ok": true }`.
- **Errors** are always `{ "error": "message" }` with a status code: `400` bad input, `401` not signed in / wrong login, `403` wrong password, `404` not found, `405` wrong method, `409` email already used.
- **Signed in** means a `session_token` cookie (HttpOnly). Only a hash of it is stored, in the `sessions` table. It lasts 12 hours, or 30 days with "keep me signed in" (`remember_me`). Signing in on an HTML page or through `/api/auth/login` gives the same cookie, so both work together.
- **Needs sign-in** endpoints answer `401 {"error": "Not signed in."}` when nobody is signed in. HTML pages redirect to `/login` instead.
- **Names**: either style works for these keys: `first_name` / `firstName`, `last_name` / `lastName`, `street_address` / `street`, `zip_code` / `zip`, `date_format` / `dateFormat`, `week_start` / `weekStartsOn`, `remember_me` / `rememberMe`.
- **Every HTML page** can use: `{{ user.first_name }}`, `{{ user.last_name }}`, `{{ user.email }}`, `{{ user.phone }}`, `{{ user.birthday }}`, `{{ user.street_address }}`, `{{ user.city }}`, `{{ user.state }}`, `{{ user.zip_code }}`, `{{ user.created_at }}` (empty on the login and sign up pages); `{{ settings.language }}`, `{{ settings.date_format }}`, `{{ settings.week_start }}`, `{{ settings.options }}`; and the filter `{{ some_date | fmt_date }}` to show a date in the user's chosen format.

## HTML pages (`pages.py`, only when pages are on)

| Method | Path | Sign-in needed | What it does |
|---|---|---|---|
| GET | `/` | No | Sign up page. Signed in already: redirects to `/dashboard`. |
| GET | `/signup` | No | Sign up page. |
| POST | `/signup` | No | Form: `first_name`, `last_name`, `email`, `password`. Creates the account (password hashed), then redirects to `/login?created=1`. The user is **not** signed in yet. On a problem (bad email, short password, missing name, email taken) the page is shown again with `error` and `form` (what they typed, no password) and status `400` (`409` for a taken email). Sending JSON instead works like `POST /api/auth/register`. |
| GET | `/login` | No | Login page. With `?created=1` the template gets `message` ("Account created! Please log in."). Signed in already: redirects to `/dashboard`. |
| POST | `/login` | No | Form: `email`, `password`, optional `remember_me` checkbox. Success: sets the cookie and redirects to `/dashboard`. Wrong email **or** password: the page is shown again with `error` = "Incorrect email or password." and `form.email`, status `401` (same message for both on purpose). Sending JSON works like `POST /api/auth/login`. |
| GET or POST | `/logout` | No | Ends the session, redirects to `/`. |
| GET | `/dashboard` | Yes | `dashboard.html`: greeting with the user's name, budgets. |
| GET | `/budget` | Yes | `budget.html` |
| GET | `/profile` | Yes | `profile.html`: name, email, phone, birthday, address. Saves through `PUT /api/profile`. |
| GET | `/setting` | Yes | `setting.html`: language, date format, week start (each dropdown saves by itself), **Account email** box, log out. |
| GET | `/expenses` | Yes | `expenses.html`. No data endpoint yet. |

Template and field names are the constants at the top of `pages.py`, so renaming a page or an input is a one-line change.

## Auth API (`auth.py`)

| Method | Path | Sign-in needed | What it does |
|---|---|---|---|
| POST | `/api/auth/register` | No | Body: `first_name`, `last_name`, `email`, `password`. Creates the account. Returns `201 { user: { user_id, email, first_name, last_name } }`. Does **not** sign in. `400` missing name / bad email / password under 8 characters, `409` email taken. |
| POST | `/api/auth/login` | No | Body: `email`, `password`, optional `remember_me`. Sets the cookie, returns `{ user }`. `401 "Incorrect email or password."` |
| POST | `/api/auth/logout` | No | Deletes the session and the cookie. Returns `{ ok: true }`. |
| GET | `/api/auth/me` | Yes | `{ user: { user_id, email, first_name, last_name, created_at, phone, birthday, street_address, city, state, zip_code } }`. Profile fields are `null` until filled in. |

Rules: first and last name required (max 50 characters), valid email (saved in lowercase), password at least 8 characters. Passwords are stored only as a salted hash.

## Profile API (`profile_routes.py`)

| Field | Rule |
|---|---|
| `first_name`, `last_name` | Required, max 50 characters. |
| `email` | Required, valid email, not used by someone else. Saved lowercase. |
| `phone` | Optional. **Numbers only, 10 digits.** Brackets, spaces, dots and dashes are dropped: `(555) 123-4567` is saved as `5555551234`. |
| `birthday` | Optional. A real date as `YYYY-MM-DD` (what a date picker sends). Not in the future, not before 1900. |
| `street_address` | Optional, max 100. Letters, numbers, spaces and `. , # ' / -`. |
| `city`, `state` | Optional, max 50. Same characters. |
| `zip_code` | Optional. **Numbers only, 5 digits.** Saved as text so `02134` keeps its 0. |

Optional fields: send `""` or `null` to clear the saved value.

| Method | Path | Sign-in needed | What it does |
|---|---|---|---|
| GET | `/api/profile` | Yes | `{ user }` with all fields above, plus `created_at_display` and `birthday_display` (dates in the user's chosen format), and the form-style names `firstName`, `lastName`, `street`, `zip`. |
| PUT or PATCH | `/api/profile` | Yes | Updates any of the fields. Send only what changed. Nothing is saved unless every field sent is valid. Returns `{ user }`. `400` with a message for an invalid value or nothing sent, `409` if the email belongs to someone else. |
| POST or PUT | `/api/profile/password` | Yes | Body: `password` (current) and `new_password`. `400` if the new one is under 8 characters, `403` if the current one is wrong. Signs out every **other** device. Returns `{ ok: true }`. |
| DELETE | `/api/profile` | Yes | Body: `{ "password": "..." }`. `403` if wrong. Deletes the account and everything it owns (sessions, settings, budgets, expenses, bank items), signs out, returns `{ ok: true }`. |

**Changing the email**: `PUT /api/profile` with `{ "email": "new@example.com" }`. It is written to the database straight away (lowercase), the user stays signed in, and from then on they log in with the new email and the old one stops working. Both the Profile page (Email field) and the Settings page (Account email box) use this.

## Settings API (`settings_routes.py`)

| Setting | Allowed values | Default | Effect today |
|---|---|---|---|
| `language` | `en-US` (English (US)), `es` (Spanish), `fr` (French) | `en-US` | **Saved only.** Spanish and French can be chosen, nothing changes yet. |
| `date_format` | `MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD` | `MM/DD/YYYY` | **Works now** (see below). |
| `week_start` | `sunday` ... `saturday` (7 options) | `sunday` | **Saved only.** Nothing changes yet. |

Values may be written the way the React form writes them: `"English (US)"` or `en-US`, `"Monday"` or `monday`.

| Method | Path | Sign-in needed | What it does |
|---|---|---|---|
| GET | `/api/settings` | Yes | `{ settings: { language, language_label, date_format, week_start, week_start_label }, options: { languages, date_formats, week_starts } }`. Each option is `{ value, label }`, so dropdowns can be built from it. |
| PUT or PATCH | `/api/settings` | Yes | Change one or more, e.g. `{ "date_format": "DD/MM/YYYY" }`. Returns the same shape as GET. `400` for a value that is not allowed, or nothing sent. |

**Date format.** Dates are stored as `YYYY-MM-DD`; the setting only changes how they are *shown*. HTML pages use `{{ date | fmt_date }}`. The API sends ready-made `created_at_display` and `birthday_display`. Any new endpoint that sends dates for display should do the same:
```python
from settings_routes import format_date, get_settings
with db() as conn:
    fmt = get_settings(conn, g.user["user_id"])["date_format"]
display = format_date(row["expense_date"], fmt)
```
To offer another format or language, add it to `DATE_FORMATS` / `LANGUAGES` at the top of `settings_routes.py`.

## Budget API (`budget_routes.py`)

A budget is `{ "id": 1, "items": [ { "title": "Rent", "amount": 1200.5 } ] }`. Amounts are dollars in the API and cents in the database. Each `title` becomes a row in `categories` (created if new, matched ignoring capitalization) and each amount a row in `budget_allocations`. The database needs a title and an amount above 0, so other rows are skipped, and the same title twice is added together. Users only see and change their own budgets.

| Method | Path | Sign-in needed | What it does |
|---|---|---|---|
| GET | `/api/budgets` | Yes | `{ budgets: [...] }`, oldest first. |
| POST | `/api/budgets` | Yes | Body: `{ "items": [ { "title": "...", "amount": 100 } ] }`. Returns `201 { budget }`. `400` if no valid item. |
| PUT | `/api/budgets/<id>` | Yes | Replaces all items. Returns `{ budget }`. `400` if no valid item, `404` if it is not yours. |
| DELETE | `/api/budgets/<id>` | Yes | Deletes the budget and its items. `{ ok: true }` or `404`. |

## Plaid (team repo only, `plaid_routes.py`, unchanged)

| Method | Path | What it does |
|---|---|---|
| POST | `/api/plaid/link-token` | Creates a Plaid Link token. Returns `{ link_token }`. |
| POST | `/api/plaid/exchange-token` | Body `{ "public_token": "..." }`. Returns `{ item_id, accounts: [...] }`. |

Needs `pip install plaid-python python-dotenv` and the Plaid keys. These two routes do not require sign-in yet, use one fixed user id, and do not save the accounts to the database.

## Utility

| Method | Path | What it does |
|---|---|---|
| GET | `/api/health` | `{ status: "ok" }`. Use it to check the server is running. |

## What changed from the previous single-file `app.py`

- The code is split into the files above. All the features are kept: sign up, login, profile fields, email change, settings, date format, budgets.
- **One sign-in system.** The old version kept the login in a Flask cookie signed with `SECRET_KEY`. Now both the HTML pages and the JSON API use the database-backed session cookie (the team's `/api/auth/...` system), including "keep me signed in". Anyone signed in before the update will be asked to sign in once.
- **JSON answers are wrapped** (`{ user }`, `{ settings }`, `{ budget }`, `{ budgets }`) instead of flat, to match the team's `/api/auth/...` routes. The HTML pages' scripts were updated to match.
- **Port 8000** by default (was 5000) so the React frontend's proxy finds it.
- Log out links on the budget, dashboard and expenses pages now point to `/logout` (the old `/` and `logout` links did not reliably sign anyone out).
- The login page has a "keep me signed in" checkbox, and the Settings page has an **Account email** box.

## Tests

```
pip install pytest
python -m pytest
```
Each test uses a temporary database, so the real `cache_money.db` is never touched. They cover sign up and login (JSON and forms), wrong passwords, remember me, expired sessions, every profile field and its rules, changing the email, password change and delete account, settings, date formats, budgets (and that users cannot touch each other's), the HTML pages, creating a new database, and upgrading an older one.

## Adding a new endpoint (recipe)

1. Make `something_routes.py` with `bp = Blueprint("something", __name__, url_prefix="/api/something")`.
2. Under each `@bp.get(...)` / `@bp.post(...)` line put `@login_required` (from `auth`). The signed-in user is `g.user["user_id"]`.
3. Read the body with `json_body()` (from `auth`), check it with the functions in `validation.py`, use `with db() as conn:` and `?` placeholders, and always filter by `g.user["user_id"]`.
4. Answer with `jsonify(name=...)`; errors as `jsonify(error="...")` with a status code.
5. Add two lines to `create_app()` in `app.py`: the import and `app.register_blueprint(bp)`.
