#the MCP server (all tools live here)

import json
from datetime import date
from pathlib import Path

from fastmcp import FastMCP

EXPENSES_FILE = Path(__file__).parent / "expenses.json"

mcp = FastMCP("expense-tracker")


def _load() -> list[dict]:
    text = EXPENSES_FILE.read_text().strip()
    if not text:
        return []
    return json.loads(text)


def _save(expenses: list[dict]) -> None:
    EXPENSES_FILE.write_text(json.dumps(expenses, indent=2))


@mcp.tool()
def add_expense(amount: float, category: str, description: str) -> str:
    """Add a new expense entry. Use this when the user mentions spending money, paying for
    something, logging a purchase, or any transaction. category must be one of: food,
    transport, shopping, health, entertainment, utilities, education, snacks, other —
    normalise the user's words to the closest match."""
    expenses = _load()
    new_id = (expenses[-1]["id"] + 1) if expenses else 1
    entry = {
        "id": new_id,
        "date": date.today().isoformat(),
        "amount": amount,
        "category": category.lower(),
        "description": description,
    }
    expenses.append(entry)
    _save(expenses)
    return f"Saved ₹{amount} under {category.capitalize()} (id={new_id})"


@mcp.tool()
def get_summary(month: str = None) -> str:
    """Return total spending per category. Use this when the user asks how much they spent,
    wants a breakdown by category, or asks for a summary of their expenses. Optionally filter
    by month in 'YYYY-MM' format (e.g. '2026-06'). If no month given, summarises all time."""
    expenses = _load()
    if month:
        expenses = [e for e in expenses if e["date"].startswith(month)]
    if not expenses:
        label = f" in {month}" if month else ""
        return f"No expenses found{label}."
    totals: dict[str, float] = {}
    for e in expenses:
        totals[e["category"]] = totals.get(e["category"], 0.0) + e["amount"]
    parts = [f"{cat.capitalize()}: ₹{total:.0f}" for cat, total in sorted(totals.items())]
    grand_total = sum(totals.values())
    label = f" ({month})" if month else " (all time)"
    return f"Spending{label} — " + " | ".join(parts) + f" | Total: ₹{grand_total:.0f}"


@mcp.tool()
def get_recent(n: int = 5) -> str:
    """Return the last N expenses as a readable list, most recent first. Use this when the user
    asks to see recent expenses, their last few purchases, or what they spent money on lately.
    Defaults to 5 entries if no number is given."""
    expenses = _load()
    if not expenses:
        return "No expenses recorded yet."
    recent = sorted(expenses, key=lambda e: e["date"], reverse=True)[:n]
    lines = [
        f"#{e['id']} {e['date']} — ₹{e['amount']:.0f} [{e['category']}] {e['description']}"
        for e in recent
    ]
    return f"Last {len(lines)} expense(s):\n" + "\n".join(lines)


@mcp.tool()
def delete_expense(id: int) -> str:
    """Delete an expense by its ID number. Use this when the user wants to remove, delete,
    or undo a specific expense. The user will typically mention the ID number (e.g. 'delete
    expense 3' or 'remove #5')."""
    expenses = _load()
    original_len = len(expenses)
    expenses = [e for e in expenses if e["id"] != id]
    if len(expenses) == original_len:
        return f"No expense found with id={id}."
    _save(expenses)
    return f"Deleted expense #{id}."


if __name__ == "__main__":
    mcp.run()
