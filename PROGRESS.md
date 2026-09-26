# Progress

How to use this file:
- Tick boxes as things get done.
- Add a **Log** entry each session: newest on top, a few lines is enough.
- Anything learned in depth goes in `learning/`; the log just links to it.

---

## Phase 0: Setup
- [x] Decide architecture (frontend / backend / ai), see [docs/architecture.md](docs/architecture.md)
- [x] Create project structure
- [x] `git init` + first commit
- [ ] Install tools: `uv` (Python), Node.js (LTS), Ollama
- [ ] Look at a real transcript `.jsonl` and write down the event format

## Phase 1: Read-only live view
- [ ] Backend: FastAPI hello world (`GET /health`)
- [ ] Backend: transcript watcher prints new lines
- [ ] Backend: parse lines into events + save to SQLite
- [ ] Backend: WebSocket pushes new events
- [ ] Frontend: scaffold with Vite (React + TS)
- [ ] Frontend: session list
- [ ] Frontend: timeline that updates live over WebSocket

## Phase 2: AI summaries
- [ ] Install Ollama, pull `qwen3.5:4b`, try it in the terminal
- [ ] AI service: `POST /summarize`
- [ ] Try Gemma 4 E4B and compare speed and quality (write results in learning/ai)
- [ ] Backend calls AI service, timeline shows summaries

## Phase 3: Talk to Claude (text)
- [ ] Backend: MCP server with `check_inbox()` and `ask_human()`
- [ ] Register MCP server with Claude Code
- [ ] Frontend: chat box, which sends to the inbox and shows Claude's questions
- [ ] Add "call check_inbox" instruction to `~/.claude/CLAUDE.md`

## Phase 4: Voice
- [ ] AI service: `POST /tts` with Kokoro
- [ ] AI service: `POST /stt` with Moonshine (+ Silero VAD)
- [ ] Frontend: mic recording (Web Audio) + playback
- [ ] Spoken updates for important events
- [ ] Push-to-talk → inbox

## Ideas / later
- Phone access on local network
- macOS menu-bar app
- Bring back hooks (blocking / approvals)

---

## Log

### 2026-09-26
- Explored what can be built: hooks, transcripts, MCP, Agent SDK.
- Checked the Mac (M1, 16 GB) and picked current small models: Qwen 3.5 4B, Moonshine, Kokoro.
- Dropped hooks / policy engine for v1; split into frontend, backend, ai.
- Created project structure and notes system.
- Named the project **Walkie** (push-to-talk with Claude); renamed folder from newProject.
- Next: git init, install tools, study a transcript file.
