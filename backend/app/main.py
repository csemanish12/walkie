"""Walkie backend — entry point.

Run with:  uv run uvicorn app.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="Walkie backend")


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check: is the server up and responding?"""
    return {"status": "ok"}
