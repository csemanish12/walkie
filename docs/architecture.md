# Walkie — Architecture

Personal tool to see what my **desktop AI apps** are doing in each session (Claude, Codex,
Cursor, ChatGPT, ...) and talk to them by text or voice.
Everything runs locally on the Mac (M1, 16 GB).

Three parts:

| Part         | Stack                              | Port  | Job                                                  |
|--------------|------------------------------------|-------|------------------------------------------------------|
| **Frontend** | React + Vite + TypeScript          | 5173  | Show sessions, timeline, chat, mic/speaker           |
| **Backend**  | Python + FastAPI                   | 8000  | Read app activity, store events, MCP server, API     |
| **AI**       | Python service + Ollama            | 8100  | Speech-to-text, text-to-speech, summarize            |

---

## Key idea: one adapter per AI app

Each AI app records its activity differently. Walkie handles this with **adapters**:
small plug-ins that each know how to read **one** app and turn its activity into the
**same common event format**. Everything after the adapter (store, UI, voice) is app-agnostic.

```
  AI app A logs --> [ adapter A ] --\
  AI app B logs --> [ adapter B ] ----> common Event --> store --> UI / voice
  AI app C logs --> [ adapter C ] --/
```

Adding support for a new app = writing one new adapter. Nothing else changes.

Two ways Walkie connects to an app:

| Channel | Direction | Works with | Used for |
|---|---|---|---|
| **Activity source** (adapter) | app → Walkie | Only apps that keep readable local logs/history | Watching: timeline, summaries |
| **MCP server** | both ways | Any app that supports MCP (an open standard many AI apps use) | Talking: `check_inbox`, `ask_human` |

An app can support both, only one, or neither. Walkie shows whatever each app allows.

---

## Big picture

```
+--------------------------------------------------------------+
|                 Desktop AI apps (any number)                 |
|                                                              |
|   [ Local logs / history ]             [ MCP client ]        |
+--------------|----------------------------------^------------+
               | read by adapters                 | check_inbox / ask_human
               v                                  v
+--------------------------------------------------------------+
|                      BACKEND  (FastAPI :8000)                |
|                                                              |
|   [ Source adapters ] --> [ Event store (SQLite) ]           |
|                                                              |
|   [ MCP server ] <---------> [ Inbox queue ]                 |
|                                                              |
|   [ API: REST + WebSocket ]                                  |
+-------------|-------------------------------------|----------+
              | WebSocket / REST                    | HTTP
              v                                     v
+---------------------------+       +---------------------------------+
|  FRONTEND (React :5173)   |       |       AI SERVICE (:8100)        |
|                           |       |                                 |
|  [ Session list ]         |       |  [ Silero VAD ]  detect speech  |
|  [ Timeline ]             |       |  [ Moonshine ]   speech -> text |
|  [ Chat ]                 |       |  [ Kokoro ]      text -> speech |
|  [ Voice controls ]       |       |  [ Qwen 3.5 4B ] summarize,     |
|                           |       |     (Ollama :11434) clean up    |
+---------------------------+       +---------------------------------+
```

The frontend only talks to the backend. The backend is the only thing that calls the AI service.

---

## Supported apps (to research)

Each row is a candidate adapter. Status stays "to verify" until I've looked at the app's real files.

| App | Activity source (where it keeps history) | MCP support | Status |
|---|---|---|---|
| Claude Code (desktop / CLI) | `~/.claude/projects/**/*.jsonl` | Yes | Verified; first adapter |
| OpenAI Codex (CLI / app) | Session `.jsonl` files under `~/.codex/` | Yes | To verify |
| Cursor | Local SQLite database in app data | Yes | To verify |
| ChatGPT desktop | No documented local history | Check | To verify (may be MCP-only) |
| Others (Windsurf, VS Code Copilot, ...) | ? | ? | Later |

---

## Frontend

```
+-------------------------------------------------------+
|  Sessions         |  Timeline (selected session)      |
|                   |                                   |
|  Claude Code      |  10:02  Read src/auth.ts          |
|   > project-a     |  10:03  Edit src/auth.ts          |
|  Codex            |  10:03  "Refactoring login flow"  |
|     project-b     |                                   |
|                   |-----------------------------------|
|                   |  Chat: [ type or hold mic ] (mic) |
+-------------------------------------------------------+
```

- **Session list**: sessions from every connected app, grouped by app, with an active or idle badge.
- **Timeline**: live events plus one-line AI summaries.
- **Chat**: my messages go to the inbox, and the AI app's `ask_human` questions appear here.
- **Voice controls**: the browser records the mic (Web Audio) and streams it to the backend, then plays back the TTS audio.

Libraries: React, Vite, TypeScript, Tailwind, shadcn/ui, TanStack Query.

---

## Backend

```
   app A logs     app B logs     app C logs
        |              |              |
        v              v              v
   [ adapter A ]  [ adapter B ]  [ adapter C ]     (sources/)
        \              |              /
         \-------------+-------------/
                       |  common Event
                       v
               [ Event store ]  (SQLite)
                       |
                       +------> [ AI service ] summarize ----+
                       |                                     |
                       v                                     v
               [ WebSocket push to frontend ] <--------------+


   any MCP app --calls--> [ MCP server ] <--> [ Inbox queue ] <-- frontend chat / voice
```

- **Source adapters** (`sources/`): one per app. Each watches that app's files and emits common Events.
- **Common Event**: the contract, see [Common Event format](#common-event-format) below.
- **Event store** keeps history across restarts.
- **MCP server** (FastMCP, mounted in FastAPI at `/mcp`) provides:
  - `check_inbox()`: returns queued messages from me.
  - `ask_human(question)`: waits until I answer in the UI or by voice.
- **API** exposes REST for history and a WebSocket for live events and audio.

Libraries: FastAPI, uvicorn, watchdog, sqlmodel, mcp (Python SDK), httpx, and uv as the package manager.

### Connecting an app over MCP
Every MCP app has its own settings for adding a server. The address is always the same:
`http://localhost:8000/mcp`. Example for Claude Code:
`claude mcp add --transport http walkie http://localhost:8000/mcp`

Apps only read the inbox when they call `check_inbox`, so each app needs one line in its
own instructions file (e.g. `CLAUDE.md`, `AGENTS.md`, Cursor rules):
"Call `check_inbox` between major steps and before finishing."

---

## Common Event format

The contract every adapter must produce, and the only shape the store/API/frontend/AI
service ever deal with. Designed by looking at a real Claude Code transcript line
(`~/.claude/projects/**/*.jsonl`) — see `learning/backend/` for that walkthrough.

```
Event
  id            string    our own id (uuid4), stable even if the source's id format changes
  app           string    which adapter produced this, e.g. "claude-code"
  session_id    string    the source app's session/conversation id
  project       string    short project name, derived from cwd (last path segment)
  cwd           string    full working directory, as the source app reported it
  timestamp     string    ISO 8601, from the source app (not our own clock)
  kind          string    one of: prompt | reply | tool_call | tool_result | status
  tool_name     string?   e.g. "Bash", "Read", "Edit" — only set for tool_call / tool_result
  tool_use_id   string?   correlates a tool_call with its later tool_result
  text          string    the content: prompt text, reply text, tool input, or tool output
  is_error      bool      true if a tool_result represents a failure
  summary_text  string?   one-line AI summary, filled in later by the AI service (null at first)
  raw           object    the original parsed source line, kept for debugging and future fields
```

**Why these fields, from what the real transcript showed:**
- Claude Code's file already separates events exactly this way: a plain-string user message
  (`prompt`), assistant message content of type `text` (`reply`), assistant content of type
  `tool_use` (`tool_call`), and a later user-role message with content type `tool_result`
  (`tool_result`) that references the call via `tool_use_id`. That mapping is 1:1, so the
  adapter's job is mostly renaming fields, not restructuring data.
- `is_error` exists because a real tool call in this project's own transcript exited 1 (a
  failed command) but still returned useful text — the UI needs to flag that distinctly from
  a normal result, not just show the same box.
- `cwd` doubles as the "which project" signal; other apps may or may not expose this the
  same way, so `project` is a derived, adapter-agnostic field the frontend can always rely on.
- `raw` exists because every source app will have extra fields (`usage` token counts,
  `permissionMode`, `gitBranch`, ...) that aren't part of the contract yet, but that are
  cheap to keep around instead of throwing away.
- `summary_text` starts empty and gets filled in by Phase 2 (the AI service) — the format
  doesn't wait on that being built.

**What an adapter does, concretely:** tail the source file for new lines, parse each line,
and if it matches one of the four `kind`s above, emit one Event. Everything else (queue
operations, file-history snapshots, etc.) is ignored for now.

---

## AI service

```
            audio in                              text in
               |                                     |
               v                                     v
        [ Silero VAD ]                        [ Qwen 3.5 4B ]  (Ollama)
               |                              - summarize event
               v                              - clean up spoken request
        [ Moonshine STT ] --> text            - decide "worth speaking?"
                                                     |
                                                     v
                                              [ Kokoro TTS ] --> audio out
```

| Model        | Role                   | Approx. memory |
|--------------|------------------------|----------------|
| Silero VAD   | Detect start/stop talk | tiny           |
| Moonshine    | Speech -> text         | ~0.5 GB        |
| Kokoro-82M   | Text -> speech         | ~0.3 GB        |
| Qwen 3.5 4B  | Summarize / clean up   | ~3 GB          |

Alternates: Gemma 4 E4B instead of Qwen, or Parakeet v3 instead of Moonshine.

Endpoints (draft):
- `POST /stt`: audio in, text out
- `POST /tts`: text in, audio out
- `POST /summarize`: event in, one-line summary out
- `POST /clean`: raw spoken text in, clear instruction out

This runs as a separate process so heavy models can load slowly or restart without taking the backend down.

---

## Main flows

**1. Watch a session**
```
AI app writes its log -> adapter -> common Event -> store -> AI summarize -> WebSocket -> Timeline
                                                                        \-> (optional) TTS -> speaker
```

**2. I talk to an AI app**
```
mic -> frontend -> backend -> AI (VAD -> STT -> clean up) -> Inbox queue (for a chosen app/session)
AI app calls check_inbox() -> gets my message
```

**3. An AI app asks me**
```
AI app calls ask_human("...") -> backend -> frontend Chat (+ TTS spoken)
I answer (text or voice) -> backend -> returns the answer to the app
```

---

## Folder layout

```
walkie/
  frontend/     React + Vite app
  docs/         architecture + decisions
  learning/     my notes (ai, frontend, backend)
  PROGRESS.md   what is done / next / log
  backend/      FastAPI: sources/, store/, mcp/, api/
  ai/           AI service: vad/, stt/, tts/, llm/
```

## Build order

1. Common Event format + first adapter (Claude Code) + store + API, plus a frontend Timeline (read-only live view).
2. AI summarizer (Qwen via Ollama).
3. MCP server with inbox and `ask_human`, plus frontend Chat.
4. Voice: STT, TTS, and frontend mic/playback.
5. More adapters (Codex, Cursor, ...).

## Open questions

- Which apps keep readable local history? (fill in the Supported apps table)
- How does the inbox know **which** app/session a message is for?
- Voice v1: spoken updates only, or two-way conversation?
