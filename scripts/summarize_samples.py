import json
import uuid
from pathlib import Path

import httpx

from ollama_chat import ChatRequest, chat

FILE_PATH = Path(__file__).parent / "samples.json"
OLLAMA_URL = "http://localhost:11434"
think_mode = False
num_predict = 60

# Fixed instructions: identical on every call, so Ollama can reuse (cache) them.
# Nothing agent-specific here; which agent it was comes from each event's "app" field.
system_prompt = """You summarize events from an AI coding assistant's session in one short line.
In these events, "the user" is the human developer and "the assistant" is the AI coding agent
named in the event.

Rules:
- Reply with only the summary: start with a verb, no subject, under 8 words.
- If Status is FAILED, say what failed and why, e.g. "X failed: reason".

Examples:

<event>
Actor: the assistant (Claude Code)
Kind: tool_call
Tool: Bash
Input: {"command": "npm test", "description": "Run the test suite"}
</event>
<event>
Actor: the assistant (Claude Code)
Kind: tool_result
Status: OK
Output: Test Suites: 6 passed, 6 total
Tests: 48 passed, 48 total
</event>
Summary: Ran tests: 48 passed

<event>
Actor: the assistant (Codex)
Kind: tool_call
Tool: shell
Input: {"command": ["git", "push", "origin", "main"]}
</event>
<event>
Actor: the assistant (Codex)
Kind: tool_result
Status: FAILED
Output: ! [rejected] main -> main (fetch first)
error: failed to push some refs
</event>
Summary: git push failed: remote has newer commits

<event>
Actor: the assistant (Claude Code)
Kind: tool_call
Tool: Write
Input: {"file_path": "/repo/src/api/client.ts", "content": "export async function getUser(id: string) {\n  const res = await fetch(`/api/users/${id}`)\n  ..."}
</event>
<event>
Actor: the assistant (Claude Code)
Kind: tool_result
Status: OK
Output: File created successfully at: /repo/src/api/client.ts
</event>
Summary: Created src/api/client.ts (getUser API call)

<event>
Actor: the assistant (Claude Code)
Kind: tool_call
Tool: mcp__browser__navigate
Input: {"url": "http://localhost:3000/login"}
</event>
<event>
Actor: the assistant (Claude Code)
Kind: tool_result
Status: OK
Output: Navigated to http://localhost:3000/login. Page title: "Sign in"
</event>
Summary: Opened the login page in the browser

<event>
Actor: the assistant (Claude Code)
Kind: tool_call
Tool: Bash
Input: {"command": "mkdir -p logs", "description": "Create logs directory"}
</event>
<event>
Actor: the assistant (Claude Code)
Kind: tool_result
Status: OK
Output: ok
</event>
Summary: Created logs directory

<event>
Actor: the user
Kind: prompt
Message: the dashboard is slow when there are lots of rows, can you look into it and fix it?
</event>
Summary: Asked to fix the slow dashboard with many rows

<event>
Actor: the assistant (Codex)
Kind: reply
Message: I found the cause: the table re-renders every row on each keystroke in the search box. I memoized the row component and debounced the search input by 200 ms. With 5,000 rows, typing is now smooth. I didn't touch the API...
</event>
Summary: Explained the fix: memoized rows, debounced search

<event>
Actor: the assistant (Claude Code)
Kind: tool_call
Tool: Bash
Input: {"command": "cd /repo/api && uv run pytest tests/test_orders.py", "description": "Run order tests"}
</event>
<event>
Actor: the assistant (Claude Code)
Kind: tool_result
Status: FAILED
Output: Exit code 2
ImportError while importing test module tests/test_orders.py
ModuleNotFoundError: No module named 'stripe'
</event>
Summary: Order tests failed: missing stripe module"""

# Display names for the "app" field each adapter sets. Unknown apps fall back to the raw id.
APP_NAME = {"claude-code": "Claude Code", "codex": "Codex", "cursor": "Cursor"}
# What the text is, by event kind.
TEXT_LABEL = {"prompt": "Message", "reply": "Message", "tool_call": "Input", "tool_result": "Output"}


def format_event(event):
    kind = event["kind"]
    agent = APP_NAME.get(event["app"], event["app"])
    # Who did it: the human wrote prompts; the agent did everything else (a tool result is the
    # output of a tool the agent ran).
    actor = "the user" if kind == "prompt" else f"the assistant ({agent})"
    tool_line = f"Tool: {event['tool_name']}\n" if event["tool_name"] else ""
    status_line = f"Status: {'FAILED' if event['is_error'] else 'OK'}\n" if kind == "tool_result" else ""
    return f"""
        <event>
        Actor: {actor}
        Kind: {kind}
        {tool_line}{status_line}{TEXT_LABEL[kind]}: {event['text']}
        </event>
      """


with open(FILE_PATH) as file:
    contents = file.read()

events = json.loads(contents)
with httpx.Client(base_url=OLLAMA_URL, timeout=300) as client:
    grouped_events = {}
    for event in events:
        tool_use_id = event.get("tool_use_id")
        if tool_use_id:
            if grouped_events.get(tool_use_id):
                grouped_events[tool_use_id].append(event)
            else:
                grouped_events[tool_use_id] = [event]
        else:
            grouped_events[uuid.uuid4()] = [event]

    for group in grouped_events.values():
        main_prompt_str = "Summarize this event:\n"
        for event in group:
            main_prompt_str += format_event(event)

        request = ChatRequest(
            system=system_prompt,
            prompt=main_prompt_str,
            think=think_mode,
            num_predict=num_predict,
            temperature=0
        )
        result = chat(client, request)
        kinds = " + ".join(event["kind"] for event in group)
        print(
            f"{kinds} | summary: {result.content} | tokens {result.tokens}"
            f" | seconds {result.seconds('eval_duration'):.2f}"
        )
