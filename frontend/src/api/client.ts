import type { WsEvent } from '../types'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'
const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8080/ws'

export const realApi = {
  getHealth: () => fetch(`${BASE}/api/health`).then(r => r.json()),
  getPeers: () => fetch(`${BASE}/api/peers`).then(r => r.json()),
  getMessages: () => fetch(`${BASE}/api/messages`).then(r => r.json()),
  getRelay: () => fetch(`${BASE}/api/relay`).then(r => r.json()),
  sendMessage: (to: string, text: string) =>
    fetch(`${BASE}/api/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to, text }),
    }).then(r => r.json()),
}

export function createRealWs(onEvent: (e: WsEvent) => void): () => void {
  let ws: WebSocket

  const connect = () => {
    ws = new WebSocket(WS_URL)
    ws.onmessage = e => {
      try { onEvent(JSON.parse(e.data)) } catch { /* ignore */ }
    }
    ws.onclose = () => setTimeout(connect, 3000)
  }

  connect()
  return () => ws?.close()
}