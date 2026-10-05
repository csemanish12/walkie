# Frontend

React + Vite + TypeScript. Runs on http://localhost:5173

```bash
npm install
npm run dev
```
Needs the backend running on :8000 (the badge says **live** when the WebSocket is connected).

## Planned pieces
- [x] `SessionList`: sessions from every connected AI app, grouped by app, active/idle badge
- [x] `Timeline`: live events (AI summaries in Phase 2)
- [ ] `Chat`: send to inbox, answer the AI app's questions
- [ ] `VoiceControls`: mic + playback

Talks **only** to the backend (REST + WebSocket on :8000).
