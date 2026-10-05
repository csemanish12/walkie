import { useEffect, useRef, useState } from 'react'
import { BACKEND_WS, type WalkieEvent } from './types'

/**
 * Keeps one WebSocket open to the backend and calls `onEvent` for every new Event.
 * Reconnects every 2s if the backend restarts. Returns whether we're connected right now.
 */
export function useLiveEvents(onEvent: (e: WalkieEvent) => void): boolean {
  const [connected, setConnected] = useState(false)
  // A ref so the socket always calls the latest onEvent without reconnecting each render.
  const onEventRef = useRef(onEvent)
  useEffect(() => {
    onEventRef.current = onEvent
  })

  useEffect(() => {
    let ws: WebSocket
    let retry: ReturnType<typeof setTimeout>
    let stopped = false

    const connect = () => {
      ws = new WebSocket(BACKEND_WS)
      ws.onopen = () => setConnected(true)
      ws.onmessage = (msg) => onEventRef.current(JSON.parse(msg.data))
      ws.onclose = () => {
        setConnected(false)
        if (!stopped) retry = setTimeout(connect, 2000)
      }
    }
    connect()

    return () => {
      stopped = true
      clearTimeout(retry)
      ws.close()
    }
  }, [])

  return connected
}
