"""The Common Event: the one shape every adapter produces (see docs/architecture.md)."""

import uuid
from typing import Any, Literal

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

Kind = Literal["prompt", "reply", "tool_call", "tool_result", "status"]


class Event(SQLModel, table=True):
    """One thing an AI app did. Also the SQLite table, so there's a single definition."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    app: str
    session_id: str = Field(index=True)
    project: str
    cwd: str
    timestamp: str = Field(index=True)
    kind: str  # one of Kind; plain str so SQLite stores it as text
    tool_name: str | None = None
    tool_use_id: str | None = None
    text: str
    is_error: bool = False
    summary_text: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
