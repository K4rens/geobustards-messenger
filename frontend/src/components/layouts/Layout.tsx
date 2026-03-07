import { useStore } from '../../store/store'
import PeerList from '../PeerList/PeerList.tsx'
import ChatWindow from '../Chat/ChatWindow.tsx'
import RelayBadge from '../RelayBadge.tsx'

export default function Layout() {
  const connected = useStore(s => s.connected)

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white font-mono overflow-hidden">
      <header className="h-12 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-sm font-bold tracking-widest text-white">MESH MESSENGER</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-500">🔒 E2E Encrypted</span>
          <span className={`ml-4 flex items-center gap-1 ${connected ? 'text-green-400' : 'text-gray-500'}`}>
            <span>{connected ? '●' : '○'}</span>
            <span>{connected ? 'Connected' : 'Connecting...'}</span>
          </span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-60 border-r border-gray-800 flex flex-col overflow-hidden shrink-0">
          <PeerList />
        </aside>
        <main className="flex-1 flex flex-col overflow-hidden">
          <ChatWindow />
        </main>
        <aside className="w-52 border-l border-gray-800 flex flex-col overflow-hidden shrink-0">
          <RelayBadge />
        </aside>
      </div>
    </div>
  )
}
