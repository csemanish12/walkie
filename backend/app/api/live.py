"""Live fan-out: every connected WebSocket gets every new Event."""

from fastapi import WebSocket

from app.events import Event


class Hub:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def broadcast(self, event: Event) -> None:
        message = event.model_dump(mode="json", exclude={"raw"})  # raw stays server-side; it's big
        for ws in list(self.clients):
            try:
                await ws.send_json(message)
            except Exception:
                # Client vanished mid-send; forget it rather than crash the broadcaster.
                self.disconnect(ws)
