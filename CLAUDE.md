# CLAUDE.md — Expense Tracker MCP

This file tells Claude Code everything it needs to know about this project.
Read this before writing any code.

---

## What this project is

A conversational expense tracker built as an MCP (Model Context Protocol) server.
The user talks to it in plain English ("add ₹350 Zomato food") and it saves, queries,
and summarises their expenses using Claude as the brain.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| MCP framework | `fastmcp` | Simplest way to build MCP servers in Python |
| LLM | Claude via `anthropic` SDK | claude-sonnet-4-6 model |
| Storage (session 1–2) | JSON file (`expenses.json`) | Simple, no setup needed |
| Storage (session 3+) | SQLite | Proper persistence, easy to query |
| Interface | Terminal chat loop | Simple CLI, upgrades to Streamlit later |

---

## Project structure

```
expense-tracker/
├── CLAUDE.md          ← this file
├── phases.md          ← session-by-session build plan
├── requirements.txt
├── server.py          ← MCP server: all tools live here
├── client.py          ← agent loop: connects Claude to MCP
├── expenses.json      ← data store (session 1–2)
└── .gitignore
```

---

## server.py — rules and patterns

- Use `fastmcp` to create the server: `mcp = FastMCP("expense-tracker")`
- Every tool uses the `@mcp.tool()` decorator
- **Docstrings are critical** — Claude reads them to decide which tool to call.
  Make them clear and specific. Bad: `"""Add expense."""` Good: `"""Add a new expense entry. Use this when the user mentions spending money, paying for something, or logging a purchase."""`
- Type hints are required on all tool arguments — FastMCP uses them to generate the JSON schema Claude receives
- Each expense entry must have: `id` (auto-increment int), `date` (ISO format string), `amount` (float), `category` (lowercase string), `description` (string)
- Run the server at the bottom with: `if __name__ == "__main__": mcp.run()`

---

## client.py — rules and patterns

- Use the `anthropic` Python SDK
- Model: `claude-sonnet-4-6`
- The client must:
  1. Start the MCP server (use `fastmcp.Client` with stdio transport)
  2. Fetch the tool list from the server on startup
  3. Pass tools to every Claude API call
  4. Handle tool_use blocks in Claude's response — forward to MCP, get result, send back
  5. Loop until the user types `exit` or `quit`
- Keep `max_tokens=1024` for now
- API key comes from environment variable `ANTHROPIC_API_KEY` — never hardcode it
- Print Claude's reply clearly. Label it so it's easy to read in the terminal.

---

## MCP tool list (grows each session)

### Session 1
- `add_expense(amount: float, category: str, description: str) -> str`
  Appends one entry to expenses.json. Returns confirmation.

### Session 2 (coming next)
- `get_summary(month: str = None) -> str`
  Returns total spent per category. Month optional (e.g. "2026-06").
- `get_recent(n: int = 5) -> str`
  Returns the last N expenses as a readable list.
- `delete_expense(id: int) -> str`
  Removes the entry with the given ID.

### Session 3 (coming later)
- `check_budget(category: str) -> str`
  Returns how much is left in the budget for that category this month.
- `set_budget(category: str, limit: float) -> str`
  Sets a monthly spend limit for a category.

---

## Data format

### expenses.json (sessions 1–2)
```json
[
  {
    "id": 1,
    "date": "2026-06-08",
    "amount": 350.0,
    "category": "food",
    "description": "Zomato"
  }
]
```

### Categories (standard set — Claude should normalise user input to these)
`food`, `transport`, `shopping`, `health`, `entertainment`, `utilities`, `education`, `snacks`, `other`

---

## What NOT to do

- Don't use `asyncio` unless fastmcp requires it — keep client.py synchronous where possible
- Don't hardcode the API key anywhere
- Don't put business logic in client.py — all data operations belong in server.py tools
- Don't skip docstrings on tools — Claude's behaviour depends on them
- Don't use `print()` for debugging and leave it in — clean up before committing

---

## Testing a tool manually

You can test any tool directly without running the full client:

```python
# Quick test snippet — run in Python REPL
from server import mcp
# Then call the underlying function directly
```

Or use the FastMCP dev inspector:
```bash
fastmcp dev server.py
```
This opens a browser UI where you can call tools manually — very useful for debugging.

---

## Git commit style

```
session 1: add_expense tool + client loop
session 2: add get_summary, get_recent, delete_expense
session 3: migrate to sqlite, add budget tools
```

One commit per session minimum. Commit working code only — if it's broken, don't commit.

---

## Environment setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python client.py
```
