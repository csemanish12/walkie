# Reading a real Claude Code transcript

**Date started:** 2026-09-27
**Used in project:** `backend/app/sources/` (the Claude Code adapter), `docs/architecture.md` (Common Event format)

## In one sentence
Claude Code writes every session as a **JSON Lines** file (one JSON object per line) under
`~/.claude/projects/<encoded-project-path>/<session-id>.jsonl`, appended to live as the
session runs, and the whole design of Walkie's Common Event format came from reading a
real one.

## Why I needed it
Before designing the shared event format every adapter must produce, I wanted to see the
actual shape of the data instead of guessing field names.

## How it works

**Where the files live:** one folder per project, path characters swapped for dashes:
```
~/.claude/projects/-Users-devandbeyond-playground-projects-walkie/
  9de1c110-....jsonl        <- the transcript, one JSON object per line
  9de1c110-.../             <- a folder with the same session id (extra data, e.g. history snapshots)
```
The session id (a UUID) is both the filename and the `sessionId` field inside each line.

**Line count grows live.** Our own session was already at 816 lines mid-conversation — every
prompt, reply, tool call and tool result adds a line as it happens. `wc -l` on the file
during a live session is basically a heartbeat.

**Top-level `type` values I found**, and what they're for:
| type | What it is | Walkie cares? |
|---|---|---|
| `user` | either your prompt, or a tool result (see below) | yes |
| `assistant` | either a reply, or a tool call (see below) | yes |
| `queue-operation` | messages queued while a turn was running | not yet |
| `system`, `custom-title`, `agent-name`, `last-prompt`, `atis-latch` | Claude Code's own bookkeeping | no |
| `file-history-snapshot` / `file-history-delta` | undo history for edited files | no |
| `relocated`, `attachment` | internal | no |

**The four events Walkie's adapter actually extracts**, with real examples:

1. **Prompt** — `type: "user"`, `message.content` is a plain **string**.
   ```json
   { "type": "user", "message": { "role": "user", "content": "i want to build a plugin..." },
     "timestamp": "2026-09-26T09:09:52.654Z", "sessionId": "9de1c110-...",
     "cwd": "/Users/devandbeyond/playground/projects/newProject" }
   ```

2. **Reply** — `type: "assistant"`, `message.content` is a **list**, and the item with
   `"type": "text"` holds what Claude said.

3. **Tool call** — `type: "assistant"`, a content item with `"type": "tool_use"`:
   ```json
   { "type": "tool_use", "id": "toolu_01BVmMaTj4Tr2tonQNuydYcD", "name": "Bash",
     "input": { "command": "sysctl -n machdep.cpu.brand_string...",
                "description": "Show Mac hardware specs" } }
   ```
   `description` is already a short human label — a free summary for the timeline, no LLM needed.

4. **Tool result** — `type: "user"` (yes, user role — a bit surprising), content item
   `"type": "tool_result"`, linked back to its call by `tool_use_id`:
   ```json
   { "type": "tool_result", "content": "Exit code 1\nApple M1...",
     "is_error": true, "tool_use_id": "toolu_01BVmMaTj4Tr2tonQNuydYcD" }
   ```

## Gotchas / mistakes I made
- Assumed `user` role always meant "something I typed." It doesn't — a **tool result** also
  arrives as a `type: "user"` line. Have to look at `message.content`'s shape (string vs list,
  and the list item's `type`) to know what a line actually is, not just the top-level `type`.
- Nearly missed `is_error: true` on the tool_result — the command exited 1 but still printed
  useful text, so it's easy to only look at the text and miss that it technically failed.
  This became the `is_error` field in the Common Event format.

## Questions still open
- How do `queue-operation` lines relate to messages sent mid-turn (like the ones during this
  session)? Might matter later for showing "queued, not yet seen" state in the UI.
- Do other apps (Codex, Cursor) use anything like JSON Lines, or something totally different
  (e.g. a SQLite database)? Need to check before writing their adapters.

## Links
- The Common Event format this fed into: `docs/architecture.md` → "Common Event format"
