#the agent loop (calls Claude + MCP)

import asyncio
import os

import anthropic
from fastmcp import Client

from server import mcp as expense_server

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


async def main():
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    async with Client(expense_server) as mcp:
        mcp_tools = await mcp.list_tools()
        tools = [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            for t in mcp_tools
        ]

        print("Expense Tracker ready. Type 'exit' to quit.\n")
        messages = []

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})

            # inner loop: keep going until Claude stops calling tools
            while True:
                response = claude.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages,
                )

                tool_uses = [b for b in response.content if b.type == "tool_use"]

                if not tool_uses:
                    messages.append({"role": "assistant", "content": response.content})
                    text = next((b.text for b in response.content if b.type == "text"), "")
                    print(f"\nClaude: {text}\n")
                    break

                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for tu in tool_uses:
                    result = await mcp.call_tool(tu.name, tu.input)
                    result_text = result.content[0].text if result.content else ""
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": result_text,
                    })

                messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    asyncio.run(main())
