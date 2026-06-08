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


if __name__ == "__main__":
    mcp.run()
