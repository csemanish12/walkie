"""Tail .jsonl files: remember how far we've read each file, return only new full lines.

Watchdog tells us *that* a file changed, not *what* changed — this class works that out.
"""

from pathlib import Path


class Tailer:
    def __init__(self) -> None:
        self._offsets: dict[Path, int] = {}  # bytes already read, per file
        self._partial: dict[Path, bytes] = {}  # half-written last line, waiting for its "\n"

    def skip_to_end(self, path: Path) -> None:
        """Start a file from its current end: only lines written from now on count."""
        self._offsets[path] = path.stat().st_size

    def read_new_lines(self, path: Path) -> list[str]:
        """Lines appended since the last call. A file we've never seen is read from the start."""
        offset = self._offsets.get(path, 0)
        try:
            with path.open("rb") as f:
                f.seek(offset)
                chunk = f.read()
        except FileNotFoundError:
            return []
        self._offsets[path] = offset + len(chunk)

        data = self._partial.pop(path, b"") + chunk
        *complete, rest = data.split(b"\n")
        if rest:
            self._partial[path] = rest
        return [line.decode("utf-8", errors="replace") for line in complete if line.strip()]
