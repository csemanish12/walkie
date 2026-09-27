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

## Setup
```bash
uv run uvicorn app.main:app --reload
```
Dependencies (`fastapi`, `uvicorn`, more added as each Phase 1 step needs them) are already
tracked in `pyproject.toml` / `uv.lock` — `uv run` installs them into `.venv` automatically.

Check it's up: `curl http://localhost:8000/health` -> `{"status":"ok"}`, or open
`http://localhost:8000/docs` for the interactive API explorer.
