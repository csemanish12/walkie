# Frontend

React + Vite + TypeScript. Runs on http://localhost:5173

Not scaffolded yet. That's my first frontend learning step:

```bash
npm create vite@latest . -- --template react-ts
npm install
npm run dev
```

## Planned pieces
- `SessionList`: all sessions, active/idle badge
- `Timeline`: live events + AI summaries
- `Chat`: send to inbox, answer Claude's questions
- `VoiceControls`: mic + playback

Talks **only** to the backend (REST + WebSocket on :8000).
