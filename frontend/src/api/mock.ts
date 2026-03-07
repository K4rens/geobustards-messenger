import type { Peer, RelayInfo, ChatMessage, WsEvent } from '../types'

const PEERS: Peer[] = [
  { peer_id: 'node1', name: 'Node 1', address: '192.168.1.1:9000', online: true },
  { peer_id: 'node2', name: 'Node 2', address: '192.168.1.2:9000', online: true },
  { peer_id: 'node3', name: 'Node 3', address: '192.168.1.3:9000', online: true },
  { peer_id: 'node4', name: 'Node 4', address: '192.168.1.4:9000', online: false },
]

const MESSAGES: ChatMessage[] = [
  { id: '1', from_id: 'node2', to: 'broadcast', text: 'Mesh network is up!', timestamp: Date.now() / 1000 - 120, encrypted: true },
  { id: '2', from_id: 'node3', to: 'broadcast', text: 'All nodes connected', timestamp: Date.now() / 1000 - 60, encrypted: true },
]

export const mockApi = {
  getHealth: async (): Promise<{ node_id: string }> => { await sleep(100); return { node_id: 'node1' } },
  getPeers: async (): Promise<Peer[]> => { await sleep(200); return PEERS },
  getMessages: async (): Promise<ChatMessage[]> => { await sleep(150); return MESSAGES },
  getRelay: async (): Promise<RelayInfo> => { await sleep(100); return { peer_id: 'node2', name: 'Node 2' } },
  sendMessage: async (_to: string, _text: string): Promise<{ message_id: string }> => {
    await sleep(100)
    return { message_id: Math.random().toString(36).slice(2, 10) }
  },
}

export function createMockWs(onEvent: (e: WsEvent) => void): () => void {
  let iteration = 0
  const interval = setInterval(() => {
    iteration++
    if (iteration % 2 === 0) {
      onEvent({ type: 'peers:update', data: { peers: PEERS, relay: { peer_id: 'node2', name: 'Node 2' } } })
    }
    if (iteration === 5) {
      onEvent({ type: 'peer:left', data: { peer_id: 'node2' } })
      setTimeout(() => {
        onEvent({ type: 'relay:info', data: { peer_id: 'node3', name: 'Node 3' } })
      }, 2000)
    }
    if (iteration === 3) {
      onEvent({ type: 'message:received', data: { id: 'mock-incoming', from_id: 'node3', to: 'broadcast', text: 'Anyone there?', timestamp: Date.now() / 1000, encrypted: true } })
    }
  }, 3000)
  return () => clearInterval(interval)
}

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}