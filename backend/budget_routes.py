"""Budgets: a user's budget plans.

Endpoints (all need a signed-in user, otherwise 401)
    GET    /api/budgets         -> {budgets: [...]}  oldest first
    POST   /api/budgets         {items: [{title, amount}]}  -> 201 {budget}
    PUT    /api/budgets/<id>    {items: [...]} replaces all the items  -> {budget}
    DELETE /api/budgets/<id>    -> {ok: true}

A budget is {id, items: [{title, amount}]}. A user only ever sees and changes
their own budgets (every query is filtered by user_id).

How it is stored (see schema.sql)
    budgets             one row per budget (name "Budget", this month, status "saved")
    categories          each item `title` is a category (created if new,
                        matched ignoring capitalization)
    budget_allocations  one row per item: budget + category + amount_cents
Amounts are whole cents in the database and dollars (e.g. 1200.5) in the API.
The database needs a title and an amount above 0, so other rows are skipped,
and the same title twice is added together.
"""

from datetime import datetime

from flask import Blueprint, g, jsonify

from auth import json_body, login_required
from db_connection import db

budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")

NO_ITEMS_ERROR = "A budget needs at least one item with a title and an amount."


def _clean_items(raw_items):
    """[{title, amount}] -> [(title, cents)], following the rules in the file header."""
    totals = {}
    for item in raw_items if isinstance(raw_items, list) else []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", item.get("name", ""))).strip()[:100]
        try:
            cents = round(float(item.get("amount", 0)) * 100)
        except (TypeError, ValueError, OverflowError):
            cents = 0
        if not title or cents <= 0:
            continue
        key = title.lower()
        if key in totals:
            totals[key][1] += cents
        else:
            totals[key] = [title, cents]
    return [(title, cents) for title, cents in totals.values()]


def _save_items(conn, budget_id, items):
    """Each title becomes a `categories` row (made if new), each amount a `budget_allocations` row."""
    for title, cents in items:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (title,))
        category = conn.execute(
            "SELECT category_id FROM categories WHERE name = ?", (title,)
        ).fetchone()
        conn.execute(
            "INSERT INTO budget_allocations (budget_id, category_id, amount_cents)"
            " VALUES (?, ?, ?)",
            (budget_id, category["category_id"], cents),
        )


def _budget_json(conn, budget_id):
    rows = conn.execute(
        "SELECT c.name AS title, a.amount_cents"
        "  FROM budget_allocations a JOIN categories c ON c.category_id = a.category_id"
        " WHERE a.budget_id = ? ORDER BY a.allocation_id",
        (budget_id,),
    ).fetchall()
    return {
        "id": budget_id,
        "items": [{"title": r["title"], "amount": r["amount_cents"] / 100} for r in rows],
    }


@budgets_bp.get("")
@login_required
def list_budgets():
    with db() as conn:
        ids = conn.execute(
            "SELECT budget_id FROM budgets WHERE user_id = ? ORDER BY budget_id",
            (g.user["user_id"],),
        ).fetchall()
        return jsonify(budgets=[_budget_json(conn, r["budget_id"]) for r in ids])


@budgets_bp.post("")
@login_required
def create_budget():
    items = _clean_items(json_body().get("items"))
    if not items:
        return jsonify(error=NO_ITEMS_ERROR), 400

    with db() as conn:
        cursor = conn.execute(
            "INSERT INTO budgets (user_id, name, month, status) VALUES (?, ?, ?, 'saved')",
            (g.user["user_id"], "Budget", datetime.now().strftime("%Y-%m")),
        )
        _save_items(conn, cursor.lastrowid, items)
        return jsonify(budget=_budget_json(conn, cursor.lastrowid)), 201


@budgets_bp.put("/<int:budget_id>")
@login_required
def update_budget(budget_id):
    items = _clean_items(json_body().get("items"))
    if not items:
        return jsonify(error=NO_ITEMS_ERROR), 400

    with db() as conn:
        # The user_id check means people can only edit their own budgets.
        mine = conn.execute(
            "SELECT 1 FROM budgets WHERE budget_id = ? AND user_id = ?",
            (budget_id, g.user["user_id"]),
        ).fetchone()
        if mine is None:
            return jsonify(error="Budget not found."), 404
        conn.execute("DELETE FROM budget_allocations WHERE budget_id = ?", (budget_id,))
        _save_items(conn, budget_id, items)
        return jsonify(budget=_budget_json(conn, budget_id))


@budgets_bp.delete("/<int:budget_id>")
@login_required
def delete_budget(budget_id):
    with db() as conn:
        deleted = conn.execute(
            "DELETE FROM budgets WHERE budget_id = ? AND user_id = ?",
            (budget_id, g.user["user_id"]),
        ).rowcount          # its budget_allocations rows go too (ON DELETE CASCADE)
    if deleted == 0:
        return jsonify(error="Budget not found."), 404
    return jsonify(ok=True)
