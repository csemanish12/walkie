# FastAPI hello world: `GET /health`

**Date started:** 2026-09-27
**Used in project:** `backend/app/main.py` (Phase 1, step 1)

## In one sentence
FastAPI turns a plain Python function into a web endpoint just by adding a decorator above
it; `uvicorn` is the actual program that listens on a port and calls that function whenever
a request comes in.

## Why I needed it
Everything else in Walkie's backend (adapters, the event store, the WebSocket) sits behind
this same FastAPI app. `/health` is the smallest possible thing that proves the server runs
at all, before adding anything real.

## How it works

**Two separate tools working together:**
```
my code (app/main.py)              the server program
------------------------           ------------------------
FastAPI: defines *what*      +     uvicorn: actually listens
happens for each URL/route         on a port, accepts
                                    connections, calls my code
```
FastAPI never runs by itself — it's just a set of Python objects describing routes.
`uvicorn` is what actually opens a network port and turns HTTP requests into calls into
that FastAPI app.

**The whole app, annotated:**
```python
from fastapi import FastAPI

app = FastAPI(title="Walkie backend")   # the "app" object every route attaches to

@app.get("/health")                     # decorator: "when someone GETs /health..."
def health() -> dict[str, str]:
    return {"status": "ok"}             # returned dict -> auto-converted to JSON
```
- `@app.get("/health")` is a **decorator**: it wraps the plain function below it and
  registers it as the handler for `GET /health`. I never call `health()` myself — uvicorn
  calls it whenever a matching request arrives.
- The **return type hint** (`dict[str, str]`) isn't just documentation — FastAPI reads it and
  uses it to validate/serialize the response, and to build the auto-generated docs.
- Returning a plain Python `dict` is enough. FastAPI converts it to a JSON HTTP response
  for me; I never touch JSON encoding by hand.

**Running it:**
```bash
uv run uvicorn app.main:app --reload
```
- `app.main:app` = "in the `app.main` module, use the object named `app`" (the `FastAPI()`
  instance). This exact string is how uvicorn finds my code.
- `--reload` restarts the server automatically whenever I save a file — essential while
  developing, never used in production.
- `uv run` runs the command **inside the project's virtual environment** (the `.venv` `uv
  init` created), without me having to activate it manually first.

**Testing it, two ways:**
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```
Or open `http://localhost:8000/docs` in a browser — FastAPI auto-generates a full
interactive page listing every route, for free, from the same type hints.

## Gotchas / mistakes I made
- `uv init` scaffolds its own placeholder `main.py` at the project root — had to delete it
  since I already have my own `app/` package with a `main.py` inside it. Two files with the
  same name in different folders, easy to run the wrong one by mistake.
- Needed `app/__init__.py` (even empty) so Python treats `app/` as an importable package —
  without it, `app.main:app` in the uvicorn command fails to resolve.

## Questions still open
- What does `--reload` actually watch — every file, or just `.py` files?
- When do I need `async def health()` instead of plain `def`? (Matters once routes call
  slow things like the AI service over HTTP.)

## Links
- https://fastapi.tiangolo.com/tutorial/first-steps/
- https://www.uvicorn.org/
