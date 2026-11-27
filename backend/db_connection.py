"""Database access shared by every backend file.

Everything that talks to SQLite goes through this one file, so there is only
one place that knows WHERE the database is and HOW it gets created.

Where is the database?  (nothing to configure, it is picked by folder layout)
  1. Team repo:   repo/backend/  (these files)  sits next to  repo/database/
                  -> uses repo/database/cache_money.db and repo/database/schema.sql
  2. Stand-alone: one folder holding these files + schema.sql (+ cache_money.db)
                  -> uses cache_money.db in that same folder
  You can always override the file with the CACHE_MONEY_DB environment variable
  (the tests do this so they never touch the real database).

How is it created?
  init_db() runs schema.sql (every table is CREATE TABLE IF NOT EXISTS, so it is
  safe to run on every start and never touches existing data) and then adds
  any profile columns an older database file is missing.

Always pass values with `?` placeholders. Never build SQL with string formatting.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent          # the folder these files are in
REPO_DATABASE_DIR = HERE.parent / "database"    # exists only in the team repo layout

# Profile columns that were added to `users` after the first release.
# CREATE TABLE IF NOT EXISTS leaves an existing table alone, so a database file
# made before these existed gets them added by _add_missing_user_columns().
USER_PROFILE_COLUMNS = ["phone", "birthday", "street_address", "city", "state", "zip_code"]


def find_schema():
    """Path of schema.sql: the repo's database/ copy first, else the one next to this file."""
    for candidate in (REPO_DATABASE_DIR / "schema.sql", HERE / "schema.sql"):
        if candidate.exists():
            return candidate
    raise RuntimeError("schema.sql not found (looked in database/ and next to db_connection.py).")


def database_path():
    """The SQLite file in use (see the top of this file)."""
    override = os.environ.get("CACHE_MONEY_DB")
    if override:
        return Path(override)
    if (REPO_DATABASE_DIR / "schema.sql").exists():
        return REPO_DATABASE_DIR / "cache_money.db"
    return HERE / "cache_money.db"


def get_connection():
    """Open a connection. Rows act like dicts (row["email"]); foreign keys are enforced
    (SQLite has them OFF by default, and ON DELETE CASCADE needs them ON)."""
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    """Use it like this:

        with db() as conn:
            conn.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id))

    The changes are saved when the block ends normally, undone if an error is
    raised inside it, and the connection is always closed.
    """
    conn = get_connection()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _add_missing_user_columns(conn):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    for column in USER_PROFILE_COLUMNS:       # a fixed list, never user input
        if column not in existing:
            conn.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")


def init_db():
    """Create the database file and any missing tables/columns. Safe to run every start."""
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript(find_schema().read_text(encoding="utf-8"))
        _add_missing_user_columns(conn)
        conn.commit()
    finally:
        conn.close()
