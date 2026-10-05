# SQLite store + WebSocket push

**Date started:** 2026-10-05
**Used in project:** `backend/app/store/db.py`, `app/api/live.py`, `app/main.py` (Phase 1, steps 5–6)

## In one sentence
Every new Event goes through one async "pump": save to SQLite, then send to every connected
WebSocket client; REST endpoints read the same SQLite for history.

## Why I needed it
The live view needs both **history** (open the page and see what already happened) and **push**
(new events appear without refreshing).

## How it works

```
watchdog thread                 asyncio loop (uvicorn)
---------------                 --------------------------------------------
on_event(e) --call_soon_threadsafe--> queue --> pump(): save_event() -> hub.broadcast()
                                                                          |
GET /sessions, /sessions/{id}/events  <-- SQLite <--                  every /ws client
```

- **SQLModel**: one class `Event(SQLModel, table=True)` is both the Pydantic model *and* the
  SQLite table, so the Common Event is defined once. `raw` is a dict, so it needs an explicit
  `Column(JSON)`.
- **Thread → asyncio hop**: asyncio objects aren't thread-safe, so the watchdog thread can't call
  `queue.put_nowait()` directly. `loop.call_soon_threadsafe(queue.put_nowait, e)` asks the loop to
  do it on its own thread.
- **lifespan**: FastAPI's startup/shutdown hook. Starts the watcher + pump on startup, stops them on shutdown.
- **Hub**: a `set` of open WebSockets. Broadcast loops over a *copy* (`list(...)`) so a client
  dropping out mid-loop can be removed safely.
- `raw` is excluded from what goes to the browser; it's large and only for debugging.
- **CORS**: the Vite page (`:5173`) and backend (`:8000`) are different origins, so the backend
  has to say "5173 may call me", or the browser blocks `fetch`. (WebSockets aren't covered by CORS.)
- `create_app(transcripts_dir, db_path)` instead of a bare global, so the test can point at a temp
  folder and DB and run the full flow: append a line → receive it on `/ws` → see it in `/sessions`.

## Minimal example
```bash
cd backend && uv run uvicorn app.main:app --reload
curl localhost:8000/sessions
```

## Gotchas / mistakes I made
- `uvicorn` alone has no WebSocket support; needs `uvicorn[standard]` (pulls in `websockets`).
- `check_same_thread=False` on the SQLite engine, since saves and reads happen on different threads.
- Starlette's TestClient now wants `httpx2`; plain `httpx` gives a deprecation warning.

## Questions still open
- When to switch to async SQLite (`aiosqlite`)? Sync saves are fine at this volume.
- Send history over the WebSocket too, instead of a separate REST call?

## Links
- https://fastapi.tiangolo.com/advanced/websockets/
- https://sqlmodel.tiangolo.com/
