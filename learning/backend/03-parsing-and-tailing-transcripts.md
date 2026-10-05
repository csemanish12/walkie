# Parsing and tailing transcripts (the Claude Code adapter)

**Date started:** 2026-10-05
**Used in project:** `backend/app/sources/claude_code.py`, `tail.py`, `watcher.py` (Phase 1, steps 2–4)

## In one sentence
The adapter is two small jobs: **parse** one transcript line into 0+ Events (a pure function, easy
to test), and **tail** each `.jsonl` file so only newly appended lines get parsed (watchdog says
*that* a file changed; I have to work out *what* is new).

## Why I needed it
Step 2 of Phase 1: turn Claude Code's raw log into the Common Event, live, without re-reading
whole 1000+ line files on every change.

## How it works

**Parsing (step 2–3).** Parsing two real transcripts with `json.loads` and counting the shapes found
three things the Sep 27 note didn't:
- `assistant` lines can contain `"type": "thinking"` items → skipped.
- `user` lines with `isMeta: true` are Claude Code's injected system reminders, not my prompts → skipped.
- A prompt with an image attached is a **list** (`image` + `text`), not a plain string → each `text` item is a prompt.
- tool_result `content` can be a string **or** a list of `{"type": "text"}` → joined.

One line can produce **several** Events (a reply text *and* a tool call in the same message), so
`parse_line()` returns a list. Sanity check on a real 1,226-line transcript: 142 tool calls, 142
results (they match), 87 replies, 50 prompts (49 strings + 1 image prompt).

**Tailing (step 4).**
```
file on disk:  [ already read ......... | new bytes  | half line ]
                                        ^ offset     ^ wait for "\n"
```
- `Tailer` remembers a byte **offset** per file; on change, `seek(offset)`, read the rest.
- The last chunk may be a **half-written line** (Claude Code mid-write) → kept in a buffer until its `\n` arrives.
- Files that exist at startup are skipped to their end (`skip_to_end`) → only live activity, no replay.
- Only `<project>/<session>.jsonl` counts: there are 533 `…/subagents/agent-*.jsonl` files nested deeper that would flood the timeline.

**Threads.** watchdog runs its own background thread and calls my handler there. The FastAPI
side is asyncio, so the handler doesn't touch the loop directly — see note 04.

## Minimal example
```bash
cd backend && uv run python -m app.sources.watcher
# 2026-10-05T02:02:25Z  backend   tool_call   Bash   '{"command": "echo \"ping from step 4\"...'
```

## Gotchas / mistakes I made
- `timeout` isn't a macOS command (it's GNU coreutils), so `timeout 25 uv run ...` just failed.
- `project` comes from each line's `cwd`, so a session that does `cd backend` switches project
  name from `walkie` to `backend` mid-way. The session list names a session after its **first** project.
- Read in **bytes**, not text: offsets are byte counts, and a multi-byte UTF-8 char can be split across two reads.

## Questions still open
- History from before the backend started isn't replayed; offsets live in memory. Persist them, or backfill on startup?
- Should subagent transcripts show up nested under their parent session?
- Use the encoded folder name (`-Users-...-walkie`) for project instead of `cwd`?

## Links
- https://python-watchdog.readthedocs.io/en/stable/quickstart.html
