# Frontend notes

## Topics I've written up

| Topic | File | Date |
|---|---|---|
| Vite + React: the live timeline | [01-vite-react-live-timeline.md](01-vite-react-live-timeline.md) | 2026-10-05 |

## Things to learn (roughly in build order)

Tick a box once I've written the note.

**Foundations**
- [ ] Node, npm, and what `package.json` is
- [ ] Vite: what a dev server / bundler does
- [ ] TypeScript basics: types, interfaces, why bother

**React**
- [x] Components and props ([note](01-vite-react-live-timeline.md))
- [x] State with `useState` ([note](01-vite-react-live-timeline.md))
- [x] Side effects with `useEffect` (and cleanup!) ([note](01-vite-react-live-timeline.md))
- [x] Lists and keys (the timeline) ([note](01-vite-react-live-timeline.md))
- [ ] Lifting state up / sharing state between components
- [x] Custom hooks (`useLiveEvents`) ([note](01-vite-react-live-timeline.md))

**Styling**
- [ ] Tailwind: utility classes
- [ ] shadcn/ui: using prebuilt components

**Talking to the backend**
- [ ] `fetch` + REST
- [ ] TanStack Query: caching and loading states
- [x] WebSocket in the browser: connect, reconnect, messages ([note](01-vite-react-live-timeline.md))

**Audio in the browser**
- [ ] Mic permission + `getUserMedia`
- [ ] Web Audio API + AudioWorklet (recording PCM)
- [ ] Playing audio from the backend
