import { useEffect } from 'react'
import { useStore } from './store/store'
import { api } from './api'
import { useWebSocket } from './hooks/useWebSocket'
import Layout from './components/layouts/Layout.tsx'
import CallUI from './components/CallUI'

export default function App() {
  const { setPeers, setMessages, setRelay, setMyId } = useStore()

  useWebSocket()

  useEffect(() => {
    async function init() {
      try {
        const [health, peers, messages, relay] = await Promise.all([
          api.getHealth(),
          api.getPeers(),
          api.getMessages(),
          api.getRelay(),
        ])
        setMyId(health.node_id)
        setPeers(peers ?? [])
        setMessages(messages ?? [])
        if (relay?.peer_id) setRelay(relay)
      } catch (e) {
        console.warn('Backend not ready, waiting for WS events', e)
      }
    }
    init()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Layout />
      <CallUI />
    </>
  )
}
