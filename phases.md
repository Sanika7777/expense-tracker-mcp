# Expense Tracker MCP — Session 1 Phases

## What we're building today
A working agent that:
- Understands natural language ("add ₹200 Zomato food")
- Saves that expense to a real JSON file on your machine
- You can talk to it from your terminal

---

## Phase 1 — Project setup (10 min)

**Goal:** Get the folder and dependencies ready.

```
expense-tracker/
├── server.py        ← the MCP server (your tools live here)
├── client.py        ← the agent loop (calls Claude + MCP)
├── expenses.json    ← where data gets saved
└── requirements.txt
```

**Steps:**
1. Create a new folder called `expense-tracker`
2. Open it in your terminal
3. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Mac/Linux
   venv\Scripts\activate           # Windows
   ```
4. Create `requirements.txt` with these contents:
   ```
   fastmcp
   anthropic
   ```
5. Install them:
   ```bash
   pip install -r requirements.txt
   ```
6. Create an empty `expenses.json` file with just `[]` inside it

**You're done when:** `python -c "import fastmcp, anthropic; print('ok')"` prints `ok`

---

## Phase 2 — Build the MCP server (20 min)

**Goal:** Write `server.py` with one tool: `add_expense`.

This file is the "tool provider." Claude will discover these tools and decide when to call them.

**What `server.py` needs to do:**
- Create a FastMCP server instance
- Define an `add_expense(amount, category, description)` tool that:
  - Takes those 3 arguments
  - Reads `expenses.json`
  - Appends a new entry with today's date + a unique ID
  - Saves the file back
  - Returns a confirmation string like `"Saved ₹200 under Food"`
- Start the server when the file is run

**Ask Claude Code:** *"Write server.py for a FastMCP expense tracker. One tool: add_expense(amount: float, category: str, description: str). It should read/write a local expenses.json file. Each entry needs: id, date (today), amount, category, description."*

**You're done when:** `python server.py` runs without errors and you see a server startup message.

---

## Phase 3 — Build the client / agent loop (20 min)

**Goal:** Write `client.py` — the thing that connects Claude to your MCP server.

This file is the "brain connector." It starts your MCP server, tells Claude what tools are available, and loops so you can keep chatting.

**What `client.py` needs to do:**
- Import `anthropic` and `fastmcp`
- Start the MCP server as a subprocess
- Ask the server: "what tools do you have?" and get back the tool list
- Run a loop:
  - Take your input
  - Send it to Claude (via Anthropic API) along with the available tools
  - If Claude wants to call a tool → run it via MCP → send the result back to Claude
  - Print Claude's final reply
  - Repeat

**Ask Claude Code:** *"Write client.py that connects to a local FastMCP server (server.py), gets its tools, then runs a chat loop with Claude using claude-sonnet-4-6. Handle tool calls — when Claude calls a tool, forward it to the MCP server and return the result."*

**Important:** You need an Anthropic API key. Set it as an environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**You're done when:** `python client.py` starts and shows a prompt like `You:`.

---

## Phase 4 — End-to-end test (10 min)

**Goal:** Make the whole thing actually work.

Run the client and try these exact phrases:
```
You: add ₹350 Zomato food
You: log 120 rupees auto rickshaw transport
You: spent 80 on chai snacks
```

After each one, open `expenses.json` and check that the entry was actually saved.

**What success looks like:**
```json
[
  {"id": 1, "date": "2026-06-08", "amount": 350, "category": "food", "description": "Zomato"},
  {"id": 2, "date": "2026-06-08", "amount": 120, "category": "transport", "description": "auto rickshaw"},
  {"id": 3, "date": "2026-06-08", "amount": 80, "category": "snacks", "description": "chai"}
]
```

**Common issues:**
- `API key not found` → check your export command, or add it directly in client.py temporarily
- `ModuleNotFoundError` → make sure your venv is activated
- Tool not being called → the `add_expense` docstring in server.py is what Claude reads — make it clear

---

## Phase 5 — Push to GitHub (10 min)

**Goal:** Get it on GitHub before you close your laptop.

```bash
git init
git add .
git commit -m "session 1: working add_expense tool via MCP"
```

Then create a new repo on GitHub (call it `expense-tracker-mcp`) and push.

Add a `.gitignore` first:
```
venv/
__pycache__/
.env
*.pyc
```

**You're done when:** Your repo is live on GitHub with at least one commit.

---

## Session 1 done — what you built

- A real MCP server with a working tool
- A Claude agent that understands natural language and calls that tool
- Real data saved to disk
- Project on GitHub

**Next session:** Add `get_summary()`, `get_recent()`, and `delete_expense()` tools so you can query and manage what you've saved.
