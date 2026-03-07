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