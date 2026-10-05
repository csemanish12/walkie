import type { SessionInfo } from '../types'

const ACTIVE_MS = 2 * 60 * 1000 // a session counts as "active" if it did something in the last 2 min

interface Props {
  sessions: SessionInfo[]
  selectedId: string | null
  onSelect: (id: string) => void
  now: number
}

export function SessionList({ sessions, selectedId, onSelect, now }: Props) {
  // Group by app ("claude-code", later "codex", ...). Sessions arrive newest-first already.
  const byApp = new Map<string, SessionInfo[]>()
  for (const s of sessions) byApp.set(s.app, [...(byApp.get(s.app) ?? []), s])

  if (sessions.length === 0) {
    return <p className="empty">No sessions yet. Do something in an AI app.</p>
  }

  return (
    <nav className="sessions">
      {[...byApp].map(([app, list]) => (
        <section key={app}>
          <h2>{app}</h2>
          <ul>
            {list.map((s) => {
              const active = now - Date.parse(s.last_seen) < ACTIVE_MS
              return (
                <li key={s.session_id}>
                  <button
                    className={s.session_id === selectedId ? 'selected' : ''}
                    onClick={() => onSelect(s.session_id)}
                  >
                    <span className={`dot ${active ? 'active' : ''}`} title={active ? 'active' : 'idle'} />
                    <span className="project">{s.project || '(no project)'}</span>
                    <span className="meta">
                      {s.session_id.slice(0, 8)} · {s.event_count}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </section>
      ))}
    </nav>
  )
}
