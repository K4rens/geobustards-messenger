import { create } from 'zustand'
import type { Peer, ChatMessage, RelayInfo } from '../types'

interface AppStore {
  peers: Peer[]
  messages: ChatMessage[]
  relay: RelayInfo | null
  activePeerId: string | null
  connected: boolean
  myId: string | null

  setPeers(peers: Peer[]): void
  setPeerOffline(peer_id: string): void
  addMessage(msg: ChatMessage): void
  setMessages(msgs: ChatMessage[]): void
  setRelay(relay: RelayInfo): void
  setActivePeer(id: string | null): void
  setConnected(v: boolean): void
  setMyId(id: string): void
}

export const useStore = create<AppStore>(set => ({
  peers: [],
  messages: [],
  relay: null,
  activePeerId: null,
  connected: false,
  myId: null,

  setPeers: peers => set({ peers }),
  setPeerOffline: id => set(s => ({
    peers: s.peers.map(p => p.peer_id === id ? { ...p, online: false } : p),
  })),
  addMessage: msg => set(s => ({ messages: [...s.messages.slice(-99), msg] })),
  setMessages: messages => set({ messages }),
  setRelay: relay => set({ relay }),
  setActivePeer: activePeerId => set({ activePeerId }),
  setConnected: connected => set({ connected }),
  setMyId: myId => set({ myId }),
}))