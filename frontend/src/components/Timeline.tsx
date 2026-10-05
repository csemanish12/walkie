import { useEffect, useRef } from 'react'
import type { WalkieEvent } from '../types'

const LABEL: Record<WalkieEvent['kind'], string> = {
  prompt: 'You',
  reply: 'Claude',
  tool_call: 'Tool',
  tool_result: 'Result',
  status: 'Status',
}

/** One line to show for an event. Tool calls use Claude's own `description` when it gave one. */
function headline(e: WalkieEvent): string {
  if (e.kind === 'tool_call') {
    try {
      const input = JSON.parse(e.text)
      return input.description ?? input.command ?? input.file_path ?? input.pattern ?? e.text
    } catch {
      return e.text
    }
  }
  return e.text
}

export function Timeline({ events }: { events: WalkieEvent[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Follow new events, like a terminal.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  if (events.length === 0) return <p className="empty">No events in this session yet.</p>

  return (
    <ol className="timeline">
      {events.map((e) => {
        const line = headline(e)
        const time = new Date(e.timestamp).toLocaleTimeString()
        return (
          <li key={e.id} className={`event ${e.kind} ${e.is_error ? 'error' : ''}`}>
            <time>{time}</time>
            <span className="kind">
              {LABEL[e.kind]}
              {e.tool_name ? ` · ${e.tool_name}` : ''}
              {e.is_error ? ' · failed' : ''}
            </span>
            <details>
              <summary>{line.split('\n')[0].slice(0, 200) || '(empty)'}</summary>
              <pre>{e.text}</pre>
            </details>
          </li>
        )
      })}
      <div ref={bottomRef} />
    </ol>
  )
}
