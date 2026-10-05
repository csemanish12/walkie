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

## Run
```bash
uv run uvicorn app.main:app --reload
```
`uv run` installs everything from `pyproject.toml` / `uv.lock` into `.venv` automatically.
On startup it watches `~/.claude/projects/*/*.jsonl` and stores new events in `walkie.db`.

| Endpoint | What |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /sessions` | every session seen, most recently active first |
| `GET /sessions/{id}/events` | latest 500 events of one session |
| `WS /ws` | every new Event, as JSON, live |

Interactive docs: http://localhost:8000/docs

Watch events in the terminal only (no server): `uv run python -m app.sources.watcher`

## Test
```bash
uv run pytest
```
