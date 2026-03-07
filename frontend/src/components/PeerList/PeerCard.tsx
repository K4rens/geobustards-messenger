import { Phone } from 'lucide-react'
import type { Peer } from '../../types'
import { useWebRTC } from '../../hooks/useWebRTC'
import { useStore } from '../../store/store'

interface Props {
  peer: Peer
  isRelay: boolean
  isActive: boolean
  onClick: () => void
}

export default function PeerCard({ peer, isRelay, isActive, onClick }: Props) {
  const { startCall } = useWebRTC()
  const callState = useStore(s => s.callState)

  const handleCall = (e: React.MouseEvent) => {
    e.stopPropagation()
    startCall(peer.peer_id)
  }

  const initials = peer.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer mb-1 transition-all duration-150 group ${
        !peer.online ? 'opacity-40' : ''
      } ${
        isActive
          ? 'text-white'
          : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
      }`}
      style={isActive ? { background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(79,70,229,0.2))', border: '1px solid rgba(139,92,246,0.3)' } : {}}
    >
      {/* Avatar */}
      <div className="relative shrink-0">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-semibold transition-all ${
          isActive ? 'bg-purple-500/30 text-purple-200' : 'bg-white/8 text-slate-400 group-hover:bg-white/10'
        }`}>
          {initials}
        </div>
        <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[#13131f] ${
          peer.online ? 'bg-emerald-400' : 'bg-slate-600'
        }`} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium truncate">{peer.name}</span>
          {isRelay && (
            <span className="text-yellow-400 text-xs shrink-0" title="Relay node">★</span>
          )}
        </div>
        <p className="text-xs text-slate-600 truncate">{peer.address}</p>
      </div>

      {peer.online && callState === 'idle' && (
        <button
          onClick={handleCall}
          className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-slate-500 hover:text-emerald-400 hover:bg-emerald-400/10 transition-all"
          title={`Call ${peer.name}`}
        >
          <Phone size={13} />
        </button>
      )}
    </div>
  )
}