# Walkie

Push-to-talk for your AI apps. A personal tool to see what desktop AI apps (Claude, Codex, Cursor, ChatGPT, ...)
are doing in each session, and talk to them by text or voice.
Runs fully locally on my Mac (M1, 16 GB).

Also a learning project for **AI** (local LLMs and voice models) and **frontend** (React).

## Layout

```
walkie/
  README.md         you are here
  PROGRESS.md       what's done, what's next, daily log
  docs/             architecture and decisions
  learning/         my notes: what I learned, for future me
  frontend/         React + Vite + TypeScript     (:5173)
  backend/          Python + FastAPI + adapters + MCP  (:8000)
  ai/               Python AI service + Ollama    (:8100)
```

## Where to look

- How it all fits together: [docs/architecture.md](docs/architecture.md)
- What I'm working on: [PROGRESS.md](PROGRESS.md)
- What I've learned: [learning/README.md](learning/README.md)
