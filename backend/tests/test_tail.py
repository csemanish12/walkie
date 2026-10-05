from pathlib import Path

from app.sources.tail import Tailer
from app.sources.watcher import is_session_file


def test_reads_only_new_lines(tmp_path: Path):
    f = tmp_path / "s.jsonl"
    f.write_text('{"a": 1}\n')
    t = Tailer()
    assert t.read_new_lines(f) == ['{"a": 1}']
    assert t.read_new_lines(f) == []
    with f.open("a") as out:
        out.write('{"b": 2}\n')
    assert t.read_new_lines(f) == ['{"b": 2}']


def test_waits_for_half_written_line(tmp_path: Path):
    f = tmp_path / "s.jsonl"
    f.write_text('{"a": ')
    t = Tailer()
    assert t.read_new_lines(f) == []
    with f.open("a") as out:
        out.write('1}\n')
    assert t.read_new_lines(f) == ['{"a": 1}']


def test_skip_to_end_ignores_existing_lines(tmp_path: Path):
    f = tmp_path / "s.jsonl"
    f.write_text('{"old": 1}\n')
    t = Tailer()
    t.skip_to_end(f)
    with f.open("a") as out:
        out.write('{"new": 1}\n')
    assert t.read_new_lines(f) == ['{"new": 1}']


def test_only_top_level_session_files(tmp_path: Path):
    assert is_session_file(tmp_path / "proj" / "abc.jsonl", tmp_path)
    assert not is_session_file(tmp_path / "proj" / "abc" / "subagents" / "agent-1.jsonl", tmp_path)
    assert not is_session_file(tmp_path / "proj" / "notes.txt", tmp_path)
