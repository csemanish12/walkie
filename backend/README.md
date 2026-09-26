# Backend

Python + FastAPI. Runs on http://localhost:8000

## Folders
```
app/
  sources/   one adapter per AI app (first: Claude Code ~/.claude/projects/**/*.jsonl),
             each turns that app's activity into the common Event format
  store/     SQLite (sqlmodel): sessions + events
  mcp/       MCP server any MCP-capable app can call: check_inbox(), ask_human()
  api/       REST + WebSocket for the frontend
```

## Setup (not done yet)
```bash
uv init
uv add fastapi uvicorn watchdog sqlmodel mcp httpx
uv run uvicorn app.main:app --reload
```
