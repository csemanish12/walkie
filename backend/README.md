# Backend

Python + FastAPI. Runs on http://localhost:8000

## Folders
```
app/
  watcher/   tail ~/.claude/projects/**/*.jsonl, parse lines into events
  store/     SQLite (sqlmodel): sessions + events
  mcp/       MCP server: check_inbox(), ask_human()
  api/       REST + WebSocket for the frontend
```

## Setup (not done yet)
```bash
uv init
uv add fastapi uvicorn watchdog sqlmodel mcp httpx
uv run uvicorn app.main:app --reload
```
