"""Watch Claude Code's transcript folder and hand every new Event to a callback.

Run on its own to see events print in the terminal:  uv run python -m app.sources.watcher
"""

import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.events import Event
from app.sources.claude_code import TRANSCRIPTS_DIR, parse_line
from app.sources.tail import Tailer


def is_session_file(path: Path, root: Path) -> bool:
    """Only <root>/<project>/<session>.jsonl — not the nested subagents/*.jsonl files."""
    return path.suffix == ".jsonl" and path.parent.parent == root


class _Handler(FileSystemEventHandler):
    def __init__(self, root: Path, tailer: Tailer, on_event: Callable[[Event], None]) -> None:
        self.root = root
        self.tailer = tailer
        self.on_event = on_event

    def on_created(self, event: FileSystemEvent) -> None:
        self._read(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._read(event)

    def _read(self, event: FileSystemEvent) -> None:
        path = Path(str(event.src_path))
        if event.is_directory or not is_session_file(path, self.root):
            return
        for line in self.tailer.read_new_lines(path):
            for e in parse_line(line):
                self.on_event(e)


def start_watching(on_event: Callable[[Event], None], root: Path = TRANSCRIPTS_DIR) -> Observer:
    """Start a background thread that calls on_event(e) for every new Event.

    Files that already exist are tailed from their current end, so only new activity shows
    up (history from before the backend started isn't replayed). on_event runs on the
    watchdog thread, not the asyncio loop.
    """
    tailer = Tailer()
    for path in root.glob("*/*.jsonl"):
        tailer.skip_to_end(path)

    observer = Observer()
    observer.schedule(_Handler(root, tailer, on_event), str(root), recursive=True)
    observer.start()
    return observer


if __name__ == "__main__":
    def show(e: Event) -> None:
        print(f"{e.timestamp}  {e.project:<20} {e.kind:<12} {e.tool_name or '':<8} {e.text[:60]!r}")

    observer = start_watching(show)
    print(f"Watching {TRANSCRIPTS_DIR} ... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
