export interface Peer {
  peer_id: string
  name: string
  address: string
  online: boolean
}

export interface RelayInfo {
  peer_id: string
  name: string
}

export interface ChatMessage {
  id: string
  from_id: string
  to: string
  text: string
  timestamp: number
  encrypted: boolean
  file?: FileInfo
}

export interface FileInfo {
  file_id: string
  filename: string
  size: number
  complete: boolean
  progress: number
}

export interface WsEvent {
  type: WsEventType
  data: Record<string, unknown>
}

export type WsEventType =
  | 'peer:joined'
  | 'peer:left'
  | 'peers:update'
  | 'message:received'
  | 'relay:info'
  | 'file:progress'
  | 'file:received'
  | 'signal:received'

export type CallState = 'idle' | 'calling' | 'ringing' | 'active'

export interface SignalData {
  from_id: string
  signal_type: 'offer' | 'answer' | 'ice-candidate' | 'hangup'
  payload: Record<string, unknown>
}