"""Cache Money API server.

Run from the repository root:

    pip install -r backend/requirements.txt
    python backend/app.py

The API listens on http://localhost:8000. The Vite dev server forwards every
request that starts with /api to it (see frontend/vite.config.js), so the
browser only ever talks to one address.
"""

import os
import sys
from pathlib import Path

# Make the repository root importable so `database` and `backend` resolve
# when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify  # noqa: E402

from backend.auth import auth_bp  # noqa: E402
from backend.plaid_routes import plaid_bp  # noqa: E402
from database.db import init_db  # noqa: E402


def create_app():
    app = Flask(__name__)

    init_db()  # creates the database file and tables if they are missing

    app.register_blueprint(auth_bp)
    app.register_blueprint(plaid_bp, url_prefix="/api/plaid")

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Not found."), 404

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify(error="Something went wrong. Please try again."), 500

    return app


if __name__ == "__main__":
    create_app().run(
        port=8000,
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )