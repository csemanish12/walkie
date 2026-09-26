# Walkie — Architecture

Personal tool to see what Claude (desktop app) is doing in each session, and talk to it by text or voice.
Everything runs locally on the Mac (M1, 16 GB).

Three parts:

| Part         | Stack                              | Port  | Job                                             |
|--------------|------------------------------------|-------|-------------------------------------------------|
| **Frontend** | React + Vite + TypeScript          | 5173  | Show sessions, timeline, chat, mic/speaker      |
| **Backend**  | Python + FastAPI                   | 8000  | Read transcripts, store events, MCP server, API |
| **AI**       | Python service + Ollama            | 8100  | Speech-to-text, text-to-speech, summarize       |

---

## Big picture

```
+--------------------------------------------------------------+
|                  Claude desktop app sessions                 |
|                                                              |
|   [ Transcripts (.jsonl) ]            [ MCP client ]         |
+--------------|----------------------------------^------------+
               | file watch                       | check_inbox / ask_human
               v                                  v
+--------------------------------------------------------------+
|                      BACKEND  (FastAPI :8000)                |
|                                                              |
|   [ Transcript watcher ] --> [ Event store (SQLite) ]        |
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

## Frontend

```
+------------------------------------------------------+
|  Session list   |  Timeline (selected session)        |
|                 |                                     |
|  > project-a    |  10:02  Read src/auth.ts            |
|    project-b    |  10:03  Edit src/auth.ts            |
|                 |  10:03  "Refactoring login flow"    |
|                 |                                     |
|                 |-------------------------------------|
|                 |  Chat:  [ type or hold mic ]  (mic) |
+------------------------------------------------------+
```

- **Session list**: all sessions across projects, with an active or idle badge.
- **Timeline**: live events plus one-line AI summaries.
- **Chat**: your messages go to the inbox, and Claude's `ask_human` questions appear here.
- **Voice controls**: the browser records the mic (Web Audio) and streams it to the backend, then plays back the TTS audio.

Libraries: React, Vite, TypeScript, Tailwind, shadcn/ui, TanStack Query.

---

## Backend

```
~/.claude/projects/**/*.jsonl
            |
            v
   [ Transcript watcher ]  (watchdog, tail new lines)
            |
            v  parsed event
   [ Event store ]  (SQLite)
            |
            +------> [ AI service ] summarize ----+
            |                                     |
            v                                     v
   [ WebSocket push to frontend ] <---------------+


   Claude --calls--> [ MCP server ] <--> [ Inbox queue ] <-- frontend chat / voice
```

- **Transcript watcher** parses each new line into an event: prompt, tool call, tool result, or reply.
- **Event store** keeps history across restarts.
- **MCP server** (FastMCP, mounted in FastAPI at `/mcp`) provides:
  - `check_inbox()`: returns queued messages from you.
  - `ask_human(question)`: waits until you answer in the UI or by voice.
- **API** exposes REST for history and a WebSocket for live events and audio.

Libraries: FastAPI, uvicorn, watchdog, sqlmodel, mcp (Python SDK), httpx, and uv as the package manager.

Register the MCP server with Claude once:
`claude mcp add --transport http dashboard http://localhost:8000/mcp`

Claude only reads the inbox when it calls `check_inbox`, so add this to `~/.claude/CLAUDE.md`:
"Call `check_inbox` between major steps and before finishing."

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
Claude writes transcript -> watcher -> store -> AI summarize -> WebSocket -> Timeline
                                                            \-> (optional) TTS -> speaker
```

**2. You talk to Claude**
```
mic -> frontend -> backend -> AI (VAD -> STT -> clean up) -> Inbox queue
Claude calls check_inbox() -> gets your message
```

**3. Claude asks you**
```
Claude calls ask_human("...") -> backend -> frontend Chat (+ TTS spoken)
you answer (text or voice) -> backend -> returns answer to Claude
```

---

## Folder layout

```
walkie/
  frontend/     React + Vite app
  docs/         architecture + decisions
  learning/     my notes (ai, frontend, backend)
  PROGRESS.md   what is done / next / log
  backend/      FastAPI: watcher/, store/, mcp/, api/
  ai/           AI service: vad/, stt/, tts/, llm/
```

## Build order

1. Backend watcher, store, and API, plus a frontend Timeline (read-only live view).
2. AI summarizer (Qwen via Ollama).
3. MCP server with inbox and `ask_human`, plus frontend Chat.
4. Voice: STT, TTS, and frontend mic/playback.

## Open questions

- Event format: which fields to pull from each transcript line. This is the contract between backend and frontend.
- Show all sessions, or only the active project?
- Voice v1: spoken updates only, or two-way conversation?
