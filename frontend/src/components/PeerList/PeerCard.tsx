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

  return (
    <div
      onClick={onClick}
      className={`mx-2 my-1 p-3 rounded-lg cursor-pointer flex items-center justify-between transition-colors ${
        isActive ? 'bg-blue-900/40 border border-blue-500/30' : 'hover:bg-gray-800'
      } ${!peer.online ? 'opacity-40' : ''}`}
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className={`w-2 h-2 rounded-full shrink-0 ${peer.online ? 'bg-green-400' : 'bg-gray-600'}`} />
        <span className={`text-sm truncate ${peer.online ? 'text-gray-200' : 'text-gray-500'}`}>
          {peer.name}
        </span>
      </div>
      <div className="flex items-center gap-1 ml-2 shrink-0">
        {isRelay && <span className="text-yellow-400 text-xs">★</span>}
        {peer.online && callState === 'idle' && (
          <button
            onClick={handleCall}
            className="p-1 text-gray-600 hover:text-green-400 transition-colors"
            title={`Call ${peer.name}`}
          >
            <Phone size={13} />
          </button>
        )}
      </div>
    </div>
  )
}
