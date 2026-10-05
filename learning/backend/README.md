# Backend notes

## Topics I've written up

| Topic | File | Date |
|---|---|---|
| Reading a real Claude Code transcript | [01-claude-code-transcript.md](01-claude-code-transcript.md) | 2026-09-27 |
| FastAPI hello world (`GET /health`) | [02-fastapi-hello-world.md](02-fastapi-hello-world.md) | 2026-09-27 |
| Parsing and tailing transcripts (the adapter) | [03-parsing-and-tailing-transcripts.md](03-parsing-and-tailing-transcripts.md) | 2026-10-05 |
| SQLite store + WebSocket push | [04-sqlite-and-websockets.md](04-sqlite-and-websockets.md) | 2026-10-05 |

## Things to learn

- [x] uv: Python projects and virtual envs ([note](02-fastapi-hello-world.md))
- [x] FastAPI basics: routes, request/response models ([note](02-fastapi-hello-world.md))
- [ ] async / await in Python
- [x] Watching files (watchdog) and tailing new lines ([note](03-parsing-and-tailing-transcripts.md))
- [x] SQLite + sqlmodel ([note](04-sqlite-and-websockets.md))
- [x] WebSockets in FastAPI ([note](04-sqlite-and-websockets.md))
- [ ] Adapter pattern: one interface, many implementations
- [ ] MCP: what a tool is, FastMCP, registering with different AI apps
- [x] How Claude Code stores history ([note](01-claude-code-transcript.md)); Codex/Cursor still to check
