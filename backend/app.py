"""Cache Money backend: starts the server and plugs the other files together.

HOW THE BACKEND IS SPLIT (one job per file)
    app.py              this file: creates the app, registers the pieces, runs it
    db_connection.py    finds/creates the SQLite database; `with db() as conn:`
    validation.py       the rules for names, email, password, phone, ZIP, birthday
    auth.py             sign up / log in / log out / "who am I?" + @login_required
    profile_routes.py   profile details, email change, password, delete account
    settings_routes.py  language, date format, week start (+ format_date helper)
    budget_routes.py    budget plans
    pages.py            the plain HTML pages in /templates (optional, see below)
    plaid_routes.py     bank connection through Plaid (optional, only in the team repo)
    schema.sql          the database tables

TWO WAYS TO RUN IT (same code, nothing to switch by hand)
    With the React frontend:   python backend/app.py      (API on port 8000;
                               the Vite dev server forwards /api/... to it)
    Backend only:              python app.py     then open http://127.0.0.1:8000
                               (serves the HTML pages from /templates)
    To run with the pages turned off:  set SERVE_HTML_PAGES=0

SETTINGS (environment variables, all optional)
    PORT=8000              port to listen on (the frontend's vite.config.js expects 8000)
    FLASK_DEBUG=0          turn off auto-restart / debug mode (default is on)
    SERVE_HTML_PAGES=0|1   force the HTML pages off/on (default: on if /templates exists)
    CACHE_MONEY_DB=path    use a different database file
    COOKIE_SECURE=1        mark the sign-in cookie HTTPS-only (use when deployed)
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The files in this folder import each other by plain name (`from auth import ...`).
# Putting the folder on the path makes that work however the app is started
# (python app.py, python backend/app.py, flask run, or the tests).
sys.path.insert(0, str(HERE))

from flask import Flask, jsonify  # noqa: E402

from auth import auth_bp  # noqa: E402
from budget_routes import budgets_bp  # noqa: E402
from db_connection import database_path, init_db  # noqa: E402
from profile_routes import profile_bp  # noqa: E402
from settings_routes import settings_bp  # noqa: E402


def pages_enabled():
    """Serve the HTML pages? An explicit SERVE_HTML_PAGES wins, otherwise yes if /templates exists."""
    setting = os.environ.get("SERVE_HTML_PAGES")
    if setting is not None:
        return setting == "1"
    return (HERE / "templates").is_dir()


def create_app():
    app = Flask(__name__)

    # When someone edits a file in /templates or /static the change shows up on the
    # next refresh, with no restart and no caching.
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    init_db()   # creates the database file / missing tables / missing columns

    # ---- the JSON API (always on) ----
    app.register_blueprint(auth_bp)       # /api/auth/...
    app.register_blueprint(profile_bp)    # /api/profile...
    app.register_blueprint(settings_bp)   # /api/settings
    app.register_blueprint(budgets_bp)    # /api/budgets...

    # ---- Plaid (only if its file and packages are there) ----
    # The team repo has plaid_routes.py and needs `pip install plaid-python python-dotenv`.
    # A stand-alone folder without them simply skips it.
    app.config["PLAID_ENABLED"] = False
    try:
        from plaid_routes import plaid_bp
        app.register_blueprint(plaid_bp, url_prefix="/api/plaid")   # /api/plaid/...
        app.config["PLAID_ENABLED"] = True
    except ImportError as reason:
        app.config["PLAID_NOTE"] = str(reason)

    # ---- the HTML pages (optional) ----
    app.config["PAGES_ENABLED"] = pages_enabled()
    if app.config["PAGES_ENABLED"]:
        from pages import pages_bp
        app.register_blueprint(pages_bp)

    @app.get("/api/health")
    def health():
        """Quick check that the server is running."""
        return jsonify(status="ok", service="cache-money-api")

    # Errors are always JSON so the frontend can read the message.
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Not found."), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(error="Method not allowed."), 405

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify(error="Something went wrong. Please try again."), 500

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app = create_app()
    # With the auto-restart on, Flask runs this file twice; only print the summary once.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print(f"Database:   {database_path()}")
        print(f"API:        http://127.0.0.1:{port}/api/health")
        if app.config["PAGES_ENABLED"]:
            print(f"HTML pages: http://127.0.0.1:{port}/   (sign up, log in, dashboard, ...)")
        else:
            print("HTML pages: off (API only)")
        if not app.config["PLAID_ENABLED"]:
            print(f"Plaid:      off ({app.config.get('PLAID_NOTE', 'plaid_routes.py not found')})")
    app.run(port=port, debug=os.environ.get("FLASK_DEBUG", "1") == "1")
