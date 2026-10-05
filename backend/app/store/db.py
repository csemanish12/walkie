"""Event store: SQLite via SQLModel. One table, `event`, shaped exactly like the Common Event."""

from pathlib import Path

from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from app.events import Event

DEFAULT_DB = Path(__file__).resolve().parents[2] / "walkie.db"  # backend/walkie.db


def make_engine(path: Path | str = DEFAULT_DB) -> Engine:
    # check_same_thread=False: events are saved from the asyncio loop, read from request threads.
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def save_event(engine: Engine, event: Event) -> None:
    with Session(engine) as db:
        db.add(event)
        db.commit()
        db.refresh(event)  # reload fields so the object is still usable after the session closes


def list_sessions(engine: Engine) -> list[dict]:
    """One row per session, most recently active first."""
    with Session(engine) as db:
        rows = db.exec(
            select(
                Event.app,
                Event.session_id,
                func.min(Event.timestamp),
                func.max(Event.timestamp),
                func.count(),
            )
            .group_by(Event.app, Event.session_id)
            .order_by(func.max(Event.timestamp).desc())
        ).all()
        sessions = []
        for app, session_id, first_seen, last_seen, count in rows:
            # A session's cwd can change mid-way (e.g. `cd backend`); name it after where it started.
            first = db.exec(
                select(Event.project).where(Event.session_id == session_id).order_by(Event.timestamp).limit(1)
            ).one()
            sessions.append(
                {
                    "app": app,
                    "session_id": session_id,
                    "project": first,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "event_count": count,
                }
            )
        return sessions


def list_events(engine: Engine, session_id: str, limit: int = 500) -> list[Event]:
    """The latest `limit` events of one session, oldest first."""
    with Session(engine) as db:
        newest = db.exec(
            select(Event).where(Event.session_id == session_id).order_by(Event.timestamp.desc()).limit(limit)
        ).all()
        return list(reversed(newest))
