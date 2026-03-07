import { create } from 'zustand'
import type { Peer, ChatMessage, RelayInfo, FileInfo, CallState } from '../types'

interface AppStore {
  peers: Peer[]
  messages: ChatMessage[]
  relay: RelayInfo | null
  activePeerId: string | null
  connected: boolean
  myId: string | null
  files: FileInfo[]
  callState: CallState
  callPeerId: string | null
  incomingCall: { from_id: string; name: string } | null

  setPeers(peers: Peer[]): void
  setPeerOffline(peer_id: string): void
  addMessage(msg: ChatMessage): void
  setMessages(msgs: ChatMessage[]): void
  setRelay(relay: RelayInfo): void
  setActivePeer(id: string | null): void
  setConnected(v: boolean): void
  setMyId(id: string): void
  addFile(file: FileInfo): void
  updateFileProgress(file_id: string, progress: number, complete?: boolean): void
  setCallState(state: CallState): void
  setCallPeerId(id: string | null): void
  setIncomingCall(call: { from_id: string; name: string } | null): void
}

export const useStore = create<AppStore>(set => ({
  peers: [],
  messages: [],
  relay: null,
  activePeerId: null,
  connected: false,
  myId: null,
  files: [],
  callState: 'idle',
  callPeerId: null,
  incomingCall: null,

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
  addFile: file => set(s => ({ files: [...s.files, file] })),
  updateFileProgress: (file_id, progress, complete = false) => set(s => ({
    files: s.files.map(f => f.file_id === file_id ? { ...f, progress, complete } : f),
  })),
  setCallState: callState => set({ callState }),
  setCallPeerId: callPeerId => set({ callPeerId }),
  setIncomingCall: incomingCall => set({ incomingCall }),
}))