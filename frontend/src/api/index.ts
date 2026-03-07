import { mockApi, createMockWs } from './mock'
import { realApi, createRealWs } from './client'
import type { WsEvent } from '../types'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export const api = USE_MOCK ? mockApi : realApi
export const createWs = USE_MOCK
  ? (onEvent: (e: WsEvent) => void, _onDisconnect?: () => void) => createMockWs(onEvent)
  : createRealWs
