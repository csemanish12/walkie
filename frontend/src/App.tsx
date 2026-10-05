import { useEffect, useState } from 'react'
import { SessionList } from './components/SessionList'
import { Timeline } from './components/Timeline'
import { BACKEND, type SessionInfo, type WalkieEvent } from './types'
import { useLiveEvents } from './useLiveEvents'

export default function App() {
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [events, setEvents] = useState<WalkieEvent[]>([])
  const [now, setNow] = useState(() => Date.now())

  // Session list once on load; live events keep it up to date after that.
  useEffect(() => {
    fetch(`${BACKEND}/sessions`)
      .then((r) => r.json())
      .then((list: SessionInfo[]) => {
        setSessions(list)
        setSelectedId((id) => id ?? list[0]?.session_id ?? null)
      })
  }, [])

  // History for the selected session.
  useEffect(() => {
    if (!selectedId) return
    fetch(`${BACKEND}/sessions/${selectedId}/events`)
      .then((r) => r.json())
      .then(setEvents)
  }, [selectedId])

  // Re-render every 15s so active/idle dots age out.
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 15_000)
    return () => clearInterval(t)
  }, [])

  const connected = useLiveEvents((e) => {
    setNow(Date.now())
    setSessions((list) => {
      const existing = list.find((s) => s.session_id === e.session_id)
      const updated: SessionInfo = existing
        ? { ...existing, last_seen: e.timestamp, event_count: existing.event_count + 1 }
        : { app: e.app, session_id: e.session_id, project: e.project, first_seen: e.timestamp, last_seen: e.timestamp, event_count: 1 }
      // Most recently active session moves to the top.
      return [updated, ...list.filter((s) => s.session_id !== e.session_id)]
    })
    setSelectedId((id) => id ?? e.session_id)
    if (e.session_id === selectedId) setEvents((list) => [...list, e])
  })

  const selected = sessions.find((s) => s.session_id === selectedId)

  return (
    <div className="app">
      <aside>
        <header>
          <h1>Walkie</h1>
          <span className={`status ${connected ? 'on' : 'off'}`}>{connected ? 'live' : 'offline'}</span>
        </header>
        <SessionList sessions={sessions} selectedId={selectedId} onSelect={setSelectedId} now={now} />
      </aside>
      <main>
        {selected ? (
          <>
            <header className="session-header">
              <h2>{selected.project}</h2>
              <code>{selected.session_id}</code>
            </header>
            <Timeline events={events} />
          </>
        ) : (
          <p className="empty">Pick a session.</p>
        )}
      </main>
    </div>
  )
}
