"""parse_line against the real line shapes from learning/backend/01-claude-code-transcript.md."""

import json

from app.sources.claude_code import parse_line

BASE = {
    "sessionId": "9de1c110-dc6b-402b-adb9-ecf8a060580b",
    "timestamp": "2026-09-26T09:09:52.654Z",
    "cwd": "/Users/devandbeyond/playground/projects/walkie",
}


def line(**fields) -> str:
    return json.dumps({**BASE, **fields})


def test_prompt():
    [e] = parse_line(line(type="user", message={"role": "user", "content": "i want to build a plugin"}))
    assert e.kind == "prompt"
    assert e.text == "i want to build a plugin"
    assert e.app == "claude-code"
    assert e.session_id == BASE["sessionId"]
    assert e.project == "walkie"
    assert e.timestamp == BASE["timestamp"]


def test_reply():
    content = [{"type": "text", "text": "Sure, here's the plan."}]
    [e] = parse_line(line(type="assistant", message={"role": "assistant", "content": content}))
    assert e.kind == "reply"
    assert e.text == "Sure, here's the plan."


def test_tool_call():
    content = [
        {
            "type": "tool_use",
            "id": "toolu_01BVmMaTj4Tr2tonQNuydYcD",
            "name": "Bash",
            "input": {"command": "sysctl -n machdep.cpu.brand_string", "description": "Show Mac hardware specs"},
        }
    ]
    [e] = parse_line(line(type="assistant", message={"role": "assistant", "content": content}))
    assert e.kind == "tool_call"
    assert e.tool_name == "Bash"
    assert e.tool_use_id == "toolu_01BVmMaTj4Tr2tonQNuydYcD"
    assert json.loads(e.text)["description"] == "Show Mac hardware specs"


def test_tool_result_error():
    content = [
        {
            "type": "tool_result",
            "content": "Exit code 1\nApple M1",
            "is_error": True,
            "tool_use_id": "toolu_01BVmMaTj4Tr2tonQNuydYcD",
        }
    ]
    [e] = parse_line(line(type="user", message={"role": "user", "content": content}))
    assert e.kind == "tool_result"
    assert e.is_error is True
    assert e.tool_use_id == "toolu_01BVmMaTj4Tr2tonQNuydYcD"
    assert e.text == "Exit code 1\nApple M1"


def test_tool_result_list_content():
    content = [{"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "ok"}]}]
    [e] = parse_line(line(type="user", message={"role": "user", "content": content}))
    assert e.text == "ok"
    assert e.is_error is False


def test_prompt_with_image_is_list_of_text():
    content = [{"type": "image", "source": {}}, {"type": "text", "text": "how can i format it better?"}]
    [e] = parse_line(line(type="user", message={"role": "user", "content": content}))
    assert e.kind == "prompt"
    assert e.text == "how can i format it better?"


def test_skipped_lines():
    assert parse_line(line(type="queue-operation", operation="enqueue")) == []
    assert parse_line(line(type="user", isMeta=True, message={"role": "user", "content": "<system-reminder>"})) == []
    thinking = [{"type": "thinking", "thinking": "hmm"}]
    assert parse_line(line(type="assistant", message={"role": "assistant", "content": thinking})) == []
    assert parse_line("not json{") == []
    assert parse_line("") == []
