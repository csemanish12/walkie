# Vite + React: the live timeline

**Date started:** 2026-10-05
**Used in project:** `frontend/src/` (Phase 1, steps 7–8)

## In one sentence
Vite serves the React app on :5173. On load it fetches the session list and the selected session's
history over REST, then a custom hook keeps a WebSocket open and appends each new Event to state.

## Why I needed it
To see what Claude is doing in a browser tab, live, without reloading.

## How it works

```
App
 ├─ state: sessions, selectedId, events, now
 ├─ useEffect: fetch /sessions                 (once)
 ├─ useEffect: fetch /sessions/{id}/events     (whenever selectedId changes)
 ├─ useLiveEvents(onEvent)                     (WebSocket, reconnects every 2s)
 ├─ <SessionList>   grouped by app, green dot if active in last 2 min
 └─ <Timeline>      one row per event, <details> to expand full text
```

- **Scaffold**: `npm create vite@latest frontend -- --template react-ts --no-interactive`.
- **Props down, events up**: `SessionList` doesn't own the selection; it calls `onSelect(id)` and `App` holds the state.
- **useEffect cleanup**: the hook's cleanup closes the socket and cancels the reconnect timer.
  Without it, React's StrictMode (which mounts → unmounts → mounts in dev) would leave two sockets open.
- **Ref for the callback**: the socket is created once (`[]` deps), but `onEvent` changes every render.
  Keeping the latest one in a `useRef` lets the socket always call the current version without reconnecting.
- **Keys**: each timeline row uses `e.id` (our uuid), so React can tell rows apart when new ones arrive.
- **Functional state updates** (`setEvents(list => [...list, e])`): use the latest state, not a stale copy captured earlier.
- Tool calls show Claude's own `description` field as the headline, a free one-line summary before any AI.

## Gotchas / mistakes I made
- Deleting `App.css` before rewriting `App.tsx` made Vite's hot reload log a 404/500 for a moment. Harmless, but it's still in the console.
- Plain CSS for now. Tailwind/shadcn can wait until there's more UI (chat, voice).

## Questions still open
- TanStack Query for the REST calls (caching, loading/error states)?
- Very long sessions: only the latest 500 events load. Add "load older"?

## Links
- https://react.dev/learn/synchronizing-with-effects
- https://vite.dev/guide/
