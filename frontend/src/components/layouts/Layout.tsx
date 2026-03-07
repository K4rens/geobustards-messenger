import { useStore } from '../../store/store'
import PeerList from '../PeerList/PeerList'
import ChatWindow from '../Chat/ChatWindow'
import RelayBadge from '../RelayBadge'

export default function Layout() {
  const connected = useStore(s => s.connected)

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: 'linear-gradient(135deg, #0f0f17 0%, #13131f 50%, #0f0f17 100%)' }}>
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-6 shrink-0 glass border-x-0 border-t-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #7c3aed, #4f46e5)' }}>
            <span className="text-white text-sm">⬡</span>
          </div>
          <span className="font-semibold text-white tracking-tight">MeshChat</span>
          <span className="text-xs px-2 py-0.5 rounded-full text-purple-300 border border-purple-500/30" style={{ background: 'rgba(139,92,246,0.1)' }}>
            🔒 E2E
          </span>
        </div>
        <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full transition-all ${
          connected
            ? 'text-emerald-400 border border-emerald-500/30'
            : 'text-slate-500 border border-slate-700'
        }`} style={{ background: connected ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)' }}>
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
          {connected ? 'Connected' : 'Connecting...'}
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden gap-0">
        <aside className="w-64 flex flex-col overflow-hidden shrink-0 border-r border-white/5">
          <PeerList />
        </aside>
        <main className="flex-1 flex flex-col overflow-hidden">
          <ChatWindow />
        </main>
        <aside className="w-56 flex flex-col overflow-hidden shrink-0 border-l border-white/5">
          <RelayBadge />
        </aside>
      </div>
    </div>
  )
}