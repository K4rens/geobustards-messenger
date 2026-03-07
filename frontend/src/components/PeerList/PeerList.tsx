import { useStore } from '../../store/store'
import PeerCard from './PeerCard'

export default function PeerList() {
  const peers = useStore(s => s.peers)
  const relay = useStore(s => s.relay)
  const activePeerId = useStore(s => s.activePeerId)
  const setActivePeer = useStore(s => s.setActivePeer)

  const sorted = [...peers].sort((a, b) => Number(b.online) - Number(a.online))
  const onlineCount = peers.filter(p => p.online).length

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-gray-800">
        <span className="text-xs text-gray-400 font-bold tracking-widest">
          PEERS ({onlineCount} online)
        </span>
      </div>

      <div className="flex-1 overflow-y-auto py-1">
        <div
          onClick={() => setActivePeer(null)}
          className={`mx-2 my-1 p-3 rounded-lg cursor-pointer text-sm transition-colors ${
            activePeerId === null
              ? 'bg-blue-900/40 border border-blue-500/30 text-white'
              : 'text-gray-400 hover:bg-gray-800'
          }`}
        >
          # Broadcast
        </div>

        {sorted.length === 0 ? (
          <p className="text-center text-gray-600 text-sm mt-8 px-4">
            Connecting to mesh network...
          </p>
        ) : (
          sorted.map(peer => (
            <PeerCard
              key={peer.peer_id}
              peer={peer}
              isRelay={peer.peer_id === relay?.peer_id}
              isActive={peer.peer_id === activePeerId}
              onClick={() => setActivePeer(peer.peer_id)}
            />
          ))
        )}
      </div>
    </div>
  )
}