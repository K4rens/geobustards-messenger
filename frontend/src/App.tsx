import { useEffect } from 'react'
import { useStore } from './store/store'
import { api } from './api'
import { useWebSocket } from './hooks/useWebSocket'
import Layout from './components/layout/Layout'
import CallUI from './components/CallUI'

export default function App() {
  const { setPeers, setMessages, setRelay, setMyId } = useStore()

  useWebSocket()

  useEffect(() => {
    async function init() {
      const [health, peers, messages, relay] = await Promise.all([
        api.getHealth(),
        api.getPeers(),
        api.getMessages(),
        api.getRelay(),
      ])
      setMyId(health.node_id)
      setPeers(peers)
      setMessages(messages)
      setRelay(relay)
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
