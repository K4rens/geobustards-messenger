import { mockApi, createMockWs } from './mock'
import { realApi, createRealWs } from './client'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export const api = USE_MOCK ? mockApi : realApi
export const createWs = USE_MOCK ? createMockWs : createRealWs