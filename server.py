#the MCP server (all tools live here)

import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from fastmcp import FastMCP

DB_FILE = Path(__file__).parent / "expenses.db"
EXPENSES_JSON = Path(__file__).parent / "expenses.json"

mcp = FastMCP("expense-tracker")


def _init_db() -> None:
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY,
                date        TEXT NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
        """)
    _migrate_json()


def _migrate_json() -> None:
    if not EXPENSES_JSON.exists():
        return
    text = EXPENSES_JSON.read_text().strip()
    if not text:
        return
    entries = json.loads(text)
    if not entries:
        return
    with _db() as conn:
        existing_ids = {row[0] for row in conn.execute("SELECT id FROM expenses")}
        to_insert = [e for e in entries if e["id"] not in existing_ids]
        if to_insert:
            conn.executemany(
                "INSERT INTO expenses (id, date, amount, category, description) VALUES (?, ?, ?, ?, ?)",
                [(e["id"], e["date"], e["amount"], e["category"], e["description"]) for e in to_insert],
            )
    EXPENSES_JSON.rename(EXPENSES_JSON.with_suffix(".json.migrated"))


@contextmanager
def _db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@mcp.tool()
def add_expense(amount: float, category: str, description: str) -> str:
    """Add a new expense entry. Use this when the user mentions spending money, paying for
    something, logging a purchase, or any transaction. category must be one of: food,
    transport, shopping, health, entertainment, utilities, education, snacks, other —
    normalise the user's words to the closest match."""
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (date, amount, category, description) VALUES (?, ?, ?, ?)",
            (date.today().isoformat(), amount, category.lower(), description),
        )
        new_id = cur.lastrowid
    return f"Saved ₹{amount} under {category.capitalize()} (id={new_id})"


@mcp.tool()
def get_summary(month: str = None) -> str:
    """Return total spending per category. Use this when the user asks how much they spent,
    wants a breakdown by category, or asks for a summary of their expenses. Optionally filter
    by month in 'YYYY-MM' format (e.g. '2026-06'). If no month given, summarises all time."""
    with _db() as conn:
        if month:
            rows = conn.execute(
                "SELECT category, SUM(amount) as total FROM expenses WHERE date LIKE ? GROUP BY category ORDER BY category",
                (f"{month}%",),
            ).fetchall()
            label = f" ({month})"
        else:
            rows = conn.execute(
                "SELECT category, SUM(amount) as total FROM expenses GROUP BY category ORDER BY category"
            ).fetchall()
            label = " (all time)"
    if not rows:
        return f"No expenses found{label.strip()}."
    parts = [f"{row['category'].capitalize()}: ₹{row['total']:.0f}" for row in rows]
    grand_total = sum(row["total"] for row in rows)
    return f"Spending{label} — " + " | ".join(parts) + f" | Total: ₹{grand_total:.0f}"


@mcp.tool()
def get_recent(n: int = 5) -> str:
    """Return the last N expenses as a readable list, most recent first. Use this when the user
    asks to see recent expenses, their last few purchases, or what they spent money on lately.
    Defaults to 5 entries if no number is given."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, date, amount, category, description FROM expenses ORDER BY date DESC, id DESC LIMIT ?",
            (n,),
        ).fetchall()
    if not rows:
        return "No expenses recorded yet."
    lines = [
        f"#{row['id']} {row['date']} — ₹{row['amount']:.0f} [{row['category']}] {row['description']}"
        for row in rows
    ]
    return f"Last {len(lines)} expense(s):\n" + "\n".join(lines)


@mcp.tool()
def delete_expense(id: int) -> str:
    """Delete an expense by its ID number. Use this when the user wants to remove, delete,
    or undo a specific expense. The user will typically mention the ID number (e.g. 'delete
    expense 3' or 'remove #5')."""
    with _db() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    if cur.rowcount == 0:
        return f"No expense found with id={id}."
    return f"Deleted expense #{id}."


@mcp.tool()
def set_budget(category: str, limit: float) -> str:
    """Set a monthly spending limit for a category. Use this when the user says things like
    'set my food budget to ₹3000', 'I want to spend at most ₹500 on transport', or
    'limit my shopping to ₹2000 a month'. category must be one of: food, transport,
    shopping, health, entertainment, utilities, education, snacks, other."""
    cat = category.lower()
    with _db() as conn:
        conn.execute(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (cat, limit),
        )
    return f"Budget set: ₹{limit:.0f}/month for {cat.capitalize()}."


@mcp.tool()
def check_budget(category: str) -> str:
    """Check how much of the monthly budget remains for a category. Use this when the user asks
    'how much budget is left for food?', 'am I over my transport limit?', 'how much can I still
    spend on shopping?', or similar. Reports spent vs limit for the current month."""
    cat = category.lower()
    current_month = date.today().strftime("%Y-%m")
    with _db() as conn:
        budget_row = conn.execute(
            "SELECT monthly_limit FROM budgets WHERE category = ?", (cat,)
        ).fetchone()
        spent_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as spent FROM expenses WHERE category = ? AND date LIKE ?",
            (cat, f"{current_month}%"),
        ).fetchone()
    if not budget_row:
        return f"No budget set for {cat.capitalize()}. Use set_budget to add one."
    limit = budget_row["monthly_limit"]
    spent = spent_row["spent"]
    remaining = limit - spent
    status = "over budget" if remaining < 0 else f"₹{remaining:.0f} remaining"
    return f"{cat.capitalize()} ({current_month}): spent ₹{spent:.0f} of ₹{limit:.0f} limit — {status}."


_init_db()

if __name__ == "__main__":
    mcp.run()
