import type { Peer } from '../../types'

interface Props {
  peer: Peer
  isRelay: boolean
  isActive: boolean
  onClick: () => void
}

export default function PeerCard({ peer, isRelay, isActive, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className={`mx-2 my-1 p-3 rounded-lg cursor-pointer flex items-center justify-between transition-colors ${
        isActive
          ? 'bg-blue-900/40 border border-blue-500/30'
          : 'hover:bg-gray-800'
      } ${!peer.online ? 'opacity-40' : ''}`}
    >
      <div className="flex items-center gap-2 min-w-0">
        <span className={`w-2 h-2 rounded-full shrink-0 ${peer.online ? 'bg-green-400' : 'bg-gray-600'}`} />
        <span className={`text-sm truncate ${peer.online ? 'text-gray-200' : 'text-gray-500'}`}>
          {peer.name}
        </span>
      </div>
      {isRelay && (
        <span className="text-yellow-400 text-xs ml-2 shrink-0">★</span>
      )}
    </div>
  )
}