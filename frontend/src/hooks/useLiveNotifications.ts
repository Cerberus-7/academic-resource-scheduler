import { useEffect, useRef, useState } from 'react'

export interface WsMessage {
  event: string
  data: any
}

export function useLiveNotifications(onMessage?: (msg: WsMessage) => void) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws?token=${token}`)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (evt) => {
      try {
        const parsed: WsMessage = JSON.parse(evt.data)
        onMessage?.(parsed)
      } catch {
        // ignore malformed payloads
      }
    }
    return () => ws.close()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { connected }
}
