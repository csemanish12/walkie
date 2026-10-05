"""End to end inside one process: append a line to a fake transcript, see it on /ws and in SQLite."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

SESSION = "11111111-2222-3333-4444-555555555555"


def append(path: Path, **fields) -> None:
    base = {"sessionId": SESSION, "timestamp": "2026-10-05T10:00:00.000Z", "cwd": "/tmp/demo"}
    with path.open("a") as f:
        f.write(json.dumps({**base, **fields}) + "\n")


def test_new_line_reaches_websocket_and_store(tmp_path: Path):
    transcripts = tmp_path / "projects"
    transcript = transcripts / "-tmp-demo" / f"{SESSION}.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("")

    app = create_app(transcripts_dir=transcripts, db_path=tmp_path / "test.db")
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}

        with client.websocket_connect("/ws") as ws:
            append(transcript, type="user", message={"role": "user", "content": "hello walkie"})
            msg = ws.receive_json()

        assert msg["kind"] == "prompt"
        assert msg["text"] == "hello walkie"
        assert msg["project"] == "demo"
        assert "raw" not in msg

        [session] = client.get("/sessions").json()
        assert session["session_id"] == SESSION
        assert session["event_count"] == 1

        [stored] = client.get(f"/sessions/{SESSION}/events").json()
        assert stored["id"] == msg["id"]
