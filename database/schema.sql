-- Cache Money: database schema (SQLite)
--
-- Conventions
--   * Money is stored as INTEGER cents (never floating point).
--   * Timestamps are ISO-8601 UTC text, e.g. '2026-11-12 18:30:00'.
--   * Foreign keys only work when the connection runs `PRAGMA foreign_keys = ON`
--     (database/db.py does this for you).
--   * Deleting a user removes everything they own (ON DELETE CASCADE).

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- users  (DATA-USER, UC-AUTH-01/02)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,              -- salted hash, never plain text
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
) STRICT;

-- ---------------------------------------------------------------------------
-- sessions  (stretch goal: remember me, US-03)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash TEXT    NOT NULL UNIQUE,          -- hash of the session token
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT    NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- ---------------------------------------------------------------------------
-- plaid_items  (INT-005, Plaid Sandbox link)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plaid_items (
    item_id          INTEGER PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    plaid_item_id    TEXT    NOT NULL UNIQUE,    -- id assigned by Plaid
    access_token     TEXT    NOT NULL,           -- store encrypted, never plain text
    institution_name TEXT    NOT NULL,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_plaid_items_user ON plaid_items(user_id);

-- ---------------------------------------------------------------------------
-- bank_accounts  (DATA-ACCT, UC-BANK-01)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id       INTEGER PRIMARY KEY,
    item_id          INTEGER NOT NULL REFERENCES plaid_items(item_id) ON DELETE CASCADE,
    plaid_account_id TEXT    NOT NULL UNIQUE,    -- id assigned by Plaid
    name             TEXT    NOT NULL,
    type             TEXT    NOT NULL CHECK (type IN ('checking', 'savings', 'credit')),
    account_number   TEXT    NOT NULL,           -- fake data only
    balance_cents    INTEGER NOT NULL DEFAULT 0 CHECK (balance_cents >= 0)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_bank_accounts_item ON bank_accounts(item_id);

-- ---------------------------------------------------------------------------
-- transfers  (UC-BUD-02, FR-BUD-002)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transfers (
    transfer_id     INTEGER PRIMARY KEY,
    from_account_id INTEGER NOT NULL REFERENCES bank_accounts(account_id) ON DELETE CASCADE,
    to_account_id   INTEGER NOT NULL REFERENCES bank_accounts(account_id) ON DELETE CASCADE,
    amount_cents    INTEGER NOT NULL CHECK (amount_cents > 0),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (from_account_id <> to_account_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_transfers_from ON transfers(from_account_id);
CREATE INDEX IF NOT EXISTS idx_transfers_to   ON transfers(to_account_id);

-- A transfer may not exceed the source account's balance. A CHECK constraint
-- cannot look at another table, so this is enforced with a trigger.
-- NOTE: this only validates. The API must still debit/credit the two
-- bank_accounts rows in the same transaction as the INSERT.
CREATE TRIGGER IF NOT EXISTS trg_transfers_sufficient_balance
BEFORE INSERT ON transfers
FOR EACH ROW
WHEN NEW.amount_cents > (SELECT balance_cents
                           FROM bank_accounts
                          WHERE account_id = NEW.from_account_id)
BEGIN
    SELECT RAISE(ABORT, 'transfer amount exceeds source account balance');
END;

-- ---------------------------------------------------------------------------
-- investments  (DATA-INV, UC-INV-01)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investments (
    investment_id INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id       INTEGER REFERENCES plaid_items(item_id) ON DELETE SET NULL,  -- NULL = entered manually
    type          TEXT    NOT NULL CHECK (type IN ('stock', 'bond', 'mutual fund')),
    ticker        TEXT    NOT NULL,
    value_cents   INTEGER NOT NULL CHECK (value_cents >= 0),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_investments_user ON investments(user_id);
CREATE INDEX IF NOT EXISTS idx_investments_item ON investments(item_id);

-- ---------------------------------------------------------------------------
-- categories  (shared by expenses and budgets)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL UNIQUE COLLATE NOCASE
) STRICT;

INSERT OR IGNORE INTO categories (name) VALUES
    ('Rent/Mortgage'),
    ('Car'),
    ('Utilities'),
    ('Credit Cards');

-- ---------------------------------------------------------------------------
-- budgets  (UC-BUD-01, UC-BUD-03)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budgets (
    budget_id  INTEGER PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    month      TEXT    NOT NULL                  -- 'YYYY-MM'
               CHECK (month GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'
                      AND substr(month, 6, 2) BETWEEN '01' AND '12'),
    status     TEXT    NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'saved')),
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_budgets_user_month ON budgets(user_id, month);

-- ---------------------------------------------------------------------------
-- budget_allocations  (FR-BUD-001/003, one row per category per budget)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budget_allocations (
    allocation_id INTEGER PRIMARY KEY,
    budget_id     INTEGER NOT NULL REFERENCES budgets(budget_id) ON DELETE CASCADE,
    category_id   INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    amount_cents  INTEGER NOT NULL CHECK (amount_cents > 0),
    UNIQUE (budget_id, category_id)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_budget_allocations_category ON budget_allocations(category_id);

-- ---------------------------------------------------------------------------
-- expenses  (DATA-EXP, UC-BUD-04/05)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenses (
    expense_id   INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    description  TEXT,
    expense_date TEXT    NOT NULL                -- 'YYYY-MM-DD'
                 CHECK (expense_date IS date(expense_date)),
    source       TEXT    NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'plaid'))
) STRICT;

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category  ON expenses(category_id);
