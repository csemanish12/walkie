"""Walkie backend — entry point.

Run with:  uv run uvicorn app.main:app --reload

Flow:  watchdog thread -> queue -> pump task -> SQLite + every WebSocket client
"""

import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.live import Hub
from app.events import Event
from app.sources.claude_code import TRANSCRIPTS_DIR
from app.sources.watcher import start_watching
from app.store import db


def create_app(transcripts_dir: Path = TRANSCRIPTS_DIR, db_path: Path | str = db.DEFAULT_DB) -> FastAPI:
    """Build the app. Tests pass a temp transcripts folder and DB instead of the real ones."""
    engine = db.make_engine(db_path)
    hub = Hub()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Event] = asyncio.Queue()

        # Watchdog calls this on its own thread; hop the Event over to the asyncio loop.
        def on_event(e: Event) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, e)

        async def pump() -> None:
            while True:
                e = await queue.get()
                db.save_event(engine, e)
                await hub.broadcast(e)

        observer = start_watching(on_event, transcripts_dir)
        pump_task = asyncio.create_task(pump())
        yield
        observer.stop()
        observer.join()
        pump_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await pump_task

    app = FastAPI(title="Walkie backend", lifespan=lifespan)
    # The Vite dev server (:5173) is a different origin, so the browser needs permission to call us.
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"])

    @app.get("/health")
    def health() -> dict[str, str]:
        """Simple liveness check: is the server up and responding?"""
        return {"status": "ok"}

    @app.get("/sessions")
    def sessions() -> list[dict]:
        """Every session seen so far, most recently active first."""
        return db.list_sessions(engine)

    @app.get("/sessions/{session_id}/events")
    def session_events(session_id: str) -> list[dict]:
        """History for one session, so the UI isn't empty before the next live event."""
        return [e.model_dump(mode="json", exclude={"raw"}) for e in db.list_events(engine, session_id)]

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        """Pushes every new Event, from every session, as one JSON message each."""
        await hub.connect(websocket)
        try:
            while True:
                await websocket.receive_text()  # we don't expect messages; this just waits for close
        except WebSocketDisconnect:
            hub.disconnect(websocket)

    return app


app = create_app()
