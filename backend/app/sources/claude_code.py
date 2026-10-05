"""Claude Code adapter: one transcript line (JSON) -> zero or more Common Events.

Transcripts live at ~/.claude/projects/<encoded-path>/<session-id>.jsonl.
See learning/backend/01-claude-code-transcript.md for the line shapes.
"""

import json
from pathlib import Path
from typing import Any

from app.events import Event

APP = "claude-code"
TRANSCRIPTS_DIR = Path.home() / ".claude" / "projects"


def parse_line(line: str) -> list[Event]:
    """Turn one raw .jsonl line into Events. Lines we don't care about give []."""
    try:
        raw = json.loads(line)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, dict):
        return []

    kind_of_line = raw.get("type")
    # isMeta lines are Claude Code's own injected notes (system reminders), not my prompts.
    if kind_of_line not in ("user", "assistant") or raw.get("isMeta"):
        return []

    content = (raw.get("message") or {}).get("content")

    # A plain-string user message is a prompt I typed.
    if isinstance(content, str):
        return [_event(raw, "prompt", text=content)]
    if not isinstance(content, list):
        return []

    # Otherwise content is a list; one line can hold several items (e.g. text + tool_use).
    events = []
    for item in content:
        item_type = item.get("type")
        if item_type == "text":
            kind = "prompt" if kind_of_line == "user" else "reply"
            events.append(_event(raw, kind, text=item.get("text", "")))
        elif item_type == "tool_use":
            events.append(
                _event(
                    raw,
                    "tool_call",
                    text=json.dumps(item.get("input", {})),
                    tool_name=item.get("name"),
                    tool_use_id=item.get("id"),
                )
            )
        elif item_type == "tool_result":
            events.append(
                _event(
                    raw,
                    "tool_result",
                    text=_result_text(item.get("content")),
                    tool_use_id=item.get("tool_use_id"),
                    is_error=bool(item.get("is_error")),
                )
            )
        # "thinking", "image", ... are skipped for now.
    return events


def _event(raw: dict[str, Any], kind: str, **fields: Any) -> Event:
    cwd = raw.get("cwd", "")
    return Event(
        app=APP,
        session_id=raw.get("sessionId", ""),
        project=Path(cwd).name if cwd else "",
        cwd=cwd,
        timestamp=raw.get("timestamp", ""),
        kind=kind,
        raw=raw,
        **fields,
    )


def _result_text(content: Any) -> str:
    """tool_result content is either a string or a list of {"type": "text", "text": ...}."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
    return ""
