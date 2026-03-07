import { useEffect } from 'react'
import { useStore } from '../store/store'
import { createWs } from '../api'
import type { WsEvent, Peer, ChatMessage, RelayInfo, FileInfo, SignalData } from '../types'
import { useWebRTC } from './useWebRTC'

export function useWebSocket() {
  const store = useStore()
  const { handleSignal } = useWebRTC()

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
        case 'file:progress': {
          const d = event.data as unknown as { file_id: string; progress: number }
          store.updateFileProgress(d.file_id, d.progress)
          break
        }
        case 'file:received': {
          const file = event.data as unknown as FileInfo
          store.addFile({ ...file, complete: true, progress: 100 })
          break
        }
        case 'signal:received': {
          const d = event.data as unknown as SignalData
          handleSignal(d.from_id, d.signal_type, d.payload)
          break
        }
      }
    })
    return unsub
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
