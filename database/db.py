"""SQLite access for Cache Money.

Create (or update) the database file:

    python database/db.py

Use it from the API:

    from database.db import get_connection

    with get_connection() as conn:   # commits on success, rolls back on error
        conn.execute("INSERT INTO users (...) VALUES (?, ?, ?, ?)", (...))

Always pass values with `?` placeholders -- never build SQL with string
formatting.
"""

import os
import sqlite3
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
# Override with the CACHE_MONEY_DB environment variable (e.g. for tests).
DEFAULT_DB_PATH = DATABASE_DIR / "cache_money.db"


def get_connection(db_path=None):
    """Open a connection with foreign keys enforced and dict-like rows."""
    path = db_path or os.environ.get("CACHE_MONEY_DB") or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # off by default in SQLite
    return conn


def init_db(db_path=None):
    """Create any missing tables and seed the default categories.

    Safe to run repeatedly; existing data is left alone.
    """
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database ready: {os.environ.get('CACHE_MONEY_DB') or DEFAULT_DB_PATH}")
