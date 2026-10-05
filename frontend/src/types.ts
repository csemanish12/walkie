// Mirrors the backend's Common Event (docs/architecture.md), minus `raw`, which stays server-side.
export type Kind = 'prompt' | 'reply' | 'tool_call' | 'tool_result' | 'status'

export interface WalkieEvent {
  id: string
  app: string
  session_id: string
  project: string
  cwd: string
  timestamp: string
  kind: Kind
  tool_name: string | null
  tool_use_id: string | null
  text: string
  is_error: boolean
  summary_text: string | null
}

export interface SessionInfo {
  app: string
  session_id: string
  project: string
  first_seen: string
  last_seen: string
  event_count: number
}

export const BACKEND = 'http://localhost:8000'
export const BACKEND_WS = 'ws://localhost:8000/ws'
