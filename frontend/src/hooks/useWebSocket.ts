import { useEffect } from 'react'
import { useStore } from '../store/store'
import { createWs } from '../api'
import type { WsEvent, Peer, ChatMessage, RelayInfo } from '../types'

export function useWebSocket() {
  const store = useStore()

  useEffect(() => {
    const unsub = createWs((event: WsEvent) => {
      store.setConnected(true)

      switch (event.type) {
        case 'peer:joined': {
          const peer = event.data as unknown as Peer
          store.setPeers([...store.peers.filter(p => p.peer_id !== peer.peer_id), peer])
          break
        }
        case 'peer:left':
          store.setPeerOffline((event.data as { peer_id: string }).peer_id)
          break
        case 'peers:update': {
          const d = event.data as unknown as { peers: Peer[]; relay?: RelayInfo }
          store.setPeers(d.peers)
          if (d.relay) store.setRelay(d.relay)
          break
        }
        case 'message:received':
          store.addMessage(event.data as unknown as ChatMessage)
          break
        case 'relay:info':
          store.setRelay(event.data as unknown as RelayInfo)
          break
      }
    })
    return unsub
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}