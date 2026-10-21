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
- [x] Install tools: `uv` (0.8.15), Node (v24.4.1, via nvm), Ollama (0.34.4)
- [x] Look at a real Claude Code transcript `.jsonl` ([notes](learning/backend/01-claude-code-transcript.md))
- [x] Draft the common Event format ([docs/architecture.md](docs/architecture.md#common-event-format))

## Phase 1: Read-only live view

Goal: watch this session's own tool calls appear live in a browser tab. No AI, no voice yet.

- [x] 1. Backend skeleton: `uv init`, FastAPI + uvicorn, `GET /health` returns `{"status": "ok"}` ([note](learning/backend/02-fastapi-hello-world.md))
- [x] 2. Read one transcript line by hand: open the `.jsonl`, parse a few lines with `json.loads`
- [x] 3. Turn a line into a Common Event: one function, raw line -> Event dict (see docs/architecture.md#common-event-format), test against the 4 real examples from learning/backend/01
- [x] 4. Watch the file live: watchdog tails new lines, print each new Event to the terminal
- [x] 5. Save to SQLite: one table matching the Event shape, insert on every new event
- [x] 6. WebSocket: `/ws` endpoint pushes each new Event to connected clients, test before any frontend
- [x] 7. Frontend scaffold: `npm create vite@latest` in frontend/, confirm default page runs
- [x] 8. Session list + Timeline: connect to `/ws`, render events live, group by session/project

## Phase 2: AI summaries

Goal: every timeline row gets a one-line summary from a local model. **I write the code;
Claude coaches** (hints, reviews), see the approach in the 2026-10-11 log.

- [x] Install Ollama, pull `qwen3.5:4b`, try it in the terminal ([results](learning/ai/01-ollama-first-llm.md))
- [x] Try Gemma 4 E4B and compare speed and quality ([results](learning/ai/01-ollama-first-llm.md))
- [x] 1. Talk to Ollama with `curl`: `POST /api/chat`, read the JSON, try `"stream": false` and `"think": false` ([note](learning/ai/03-ollama-api.md))
- [x] 2. Same request from a Python script with `httpx` (`scripts/ollama_chat.py`)
- [x] 3. Prompt design: pull ~10 real events from `backend/walkie.db`, iterate until summaries are good, time each call ([note](learning/ai/04-prompting-summaries.md))
- [ ] 4. `ai/` service skeleton: `uv init`, FastAPI on :8100, `GET /health` (from memory, no peeking at backend/)
- [ ] 5. `POST /summarize`: Pydantic request/response models, `async def`, `httpx.AsyncClient` with a timeout
- [ ] 6. Backend calls AI service without blocking the live stream, stores `summary_text`, pushes the update over `/ws` (design it with Claude first: which events, bursts, AI service down)
- [ ] 7. Frontend shows summaries: replace the row by `id` when an updated event arrives

## Phase 3: Talk to AI apps (text)
- [ ] Backend: MCP server with `check_inbox()` and `ask_human()`
- [ ] Register MCP server with the first app (Claude Code)
- [ ] Frontend: chat box, which sends to the inbox and shows the app's questions
- [ ] Add "call check_inbox" instruction to the app's instructions file (`CLAUDE.md` / `AGENTS.md` / ...)
- [ ] Inbox: route messages to the right app + session

## Phase 4: Voice
- [ ] AI service: `POST /tts` with Kokoro
- [ ] AI service: `POST /stt` with Moonshine (+ Silero VAD)
- [ ] Frontend: mic recording (Web Audio) + playback
- [ ] Spoken updates for important events
- [ ] Push-to-talk → inbox

## Phase 5: More apps
- [ ] Research which apps keep readable local history (fill table in docs/architecture.md)
- [ ] Adapter: Codex
- [ ] Adapter: Cursor
- [ ] Connect MCP to each app that supports it

## Ideas / later
- Phone access on local network
- macOS menu-bar app
- Bring back hooks (blocking / approvals)

---

## Log

### 2026-10-21
- Step 3 done: `scripts/summarize_samples.py` summarizes 17 real events (`scripts/samples.json`,
  gitignored) with gemma4:e4b. Baseline failures were all missing context: the model answered
  events instead of summarizing them, missed a failure (never saw `is_error`), and got the actor wrong.
- Fixes: delimited `<event>` block, explicit Kind/Tool/Status fields, tool call + result paired
  by `tool_use_id` and summarized once, actors stated in the event, fixed rules in the system
  message (cacheable), agent-agnostic (agent name from `app`), few-shot examples, temperature 0.
- Result: 7–13 tokens per summary (was 9–42), ~0.5 s each, 3.6× less writing time for the
  same events. Wrote learning/ai/04-prompting-summaries.md. Post idea L: "LLMs are stateless".
- Next: step 4, the `ai/` service skeleton on :8100.

### 2026-10-19
- Step 2 done: `scripts/ollama_chat.py` calls `/api/chat` with httpx (`uv run --with httpx`, no
  project needed) and prints answer | tokens | total s | prompt s | tok/s.
- Long answers measure 17.5–17.75 tok/s, matching step 1's hand calculation. 2-token answers
  read ~30 tok/s: too few tokens to measure (eval_duration covers ~1 token gap).
- First call hit `httpx.ReadTimeout`: httpx's default is 5 s, and the model had been unloaded
  (keep_alive) so loading alone took ~5 s. `think: true` gave eval_count 747 for a visibly
  shorter answer: the rest was hidden thinking tokens.
- Skipped the failure-mode drills (familiar from backend work). LLM-specific differences worth
  remembering: latency depends on output length (bound it with `options.num_predict`), cold
  start after keep_alive, read timeout = whole generation when not streaming, and requests
  queue on one GPU.
- Next: step 3, prompt design on ~10 real events from walkie.db.

### 2026-10-11
- Phase 1 merged to main (one commit per step).
- New way of working from Phase 2: I implement, Claude coaches. Per step: goal, what to learn,
  "done when" check. I ask for "hint", "stuck", "review", "why...?" or "check my note".
- Split Phase 2 into 7 small steps (above).
- Step 1 done: called Ollama's `/api/chat` with curl. gemma4:e4b runs at ~17 tok/s on the M1.
  Same question went from 755 tokens / 44.6 s (defaults) to 157 / 14.1 s (`think: false`) to
  2 / 0.51 s (+ system prompt "one short plain-text line"). Speed is fixed; only fewer tokens
  make it faster. `keep_alive` default 5 min, so ~4.4 s reload after quiet spells.
  Wrote learning/ai/03-ollama-api.md.
- Noticed `qwen3.5:4b` is no longer installed; only `gemma4:e4b`.
- Next: step 2, the same request from Python with `httpx`.

### 2026-10-05
- **Phase 1 done**: this session's own tool calls show up live in the browser at :5173.
- Steps 2–3: `parse_line()` in `backend/app/sources/claude_code.py`. Real transcripts also have
  `thinking` items, `isMeta` system-reminder lines, and image prompts as lists; all handled.
  Full 1,226-line transcript → 142 tool calls / 142 results / 87 replies / 50 prompts.
- Step 4: `Tailer` (byte offsets + half-line buffer) + watchdog. Skips nested `subagents/*.jsonl`.
- Steps 5–6: SQLite via SQLModel (`backend/walkie.db`), `/sessions`, `/sessions/{id}/events`, `/ws`.
  Watchdog thread → `call_soon_threadsafe` → asyncio queue → save + broadcast.
- Steps 7–8: Vite + React + TS, `SessionList` + `Timeline` + `useLiveEvents` hook. Plain CSS for now.
- 12 backend tests (pytest), incl. one end-to-end: append a line → arrives on `/ws` → stored.
- Notes: learning/backend/03, 04 and learning/frontend/01.
- Open: history before backend start isn't replayed; `project` changes if a session `cd`s.
- Next: Phase 2. AI service `POST /summarize`.

### 2026-09-26
- Explored what can be built: hooks, transcripts, MCP, Agent SDK.
- Checked the Mac (M1, 16 GB) and picked current small models: Qwen 3.5 4B, Moonshine, Kokoro.
- Dropped hooks / policy engine for v1; split into frontend, backend, ai.
- Created project structure and notes system.
- Named the project **Walkie** (push-to-talk with AI apps); renamed folder from newProject.
- Made the design app-agnostic: one adapter per AI app + a common Event format; MCP for talking back.

### 2026-09-27
- Ran qwen3.5:4b and gemma4:e4b side by side on the M1: near-identical speed (~19 tok/s).
- Learned why Gemma's 9.6 GB file only uses 3.2 GB memory: Per-Layer Embeddings keep big
  embedding tables on disk instead of GPU memory ("effective parameters"). Wrote it up in
  learning/ai/01-ollama-first-llm.md.
- Wrote learning/ai/02-precision-fp16-bf16.md: why LLMs train in 16-bit, FP16 vs BF16 with
  worked examples, and how 4-bit quantization works (integer + scale, not floating point).
- Confirmed uv, Node/nvm, Ollama all installed.
- Opened this session's own live transcript (~/.claude/projects/.../*.jsonl) to see the real
  shape of Claude Code events: prompt, reply, tool_call, tool_result, with is_error on
  results. Wrote it up in learning/backend/01-claude-code-transcript.md.
- Drafted the Common Event format from that data (docs/architecture.md). **Phase 0 done.**
- Fixed SSH: origin was pointed at plain `github.com` instead of the `github-personal` host
  alias in `~/.ssh/config`, so the wrong key kept getting used for push.
- Planned Phase 1 as 8 small steps in PROGRESS.md, backend first then frontend.
- Step 1 done: `backend/` is a real uv project, FastAPI + uvicorn installed, `GET /health`
  works end to end (curl + `/docs`). Wrote up FastAPI/uv basics in
  learning/backend/02-fastapi-hello-world.md.
- Next: Step 2 — read one transcript line by hand with `json.loads`.
