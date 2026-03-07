import { useStore } from '../store/store'

export default function RelayBadge() {
  const peers = useStore(s => s.peers)
  const relay = useStore(s => s.relay)

  const onlineCount = peers.filter(p => p.online).length

  return (
    <div className="flex flex-col gap-3 p-3 overflow-y-auto h-full">
      <div className={`rounded-lg p-3 border ${
        relay ? 'border-green-500/40 bg-green-500/5' : 'border-gray-700 bg-gray-800'
      }`}>
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-2 h-2 rounded-full shrink-0 ${
            relay ? 'bg-green-400 animate-pulse' : 'bg-gray-600'
          }`} />
          <span className="text-xs text-gray-400 font-bold tracking-wider">RELAY NODE</span>
        </div>
        {relay ? (
          <>
            <p className="text-white font-semibold text-sm">{relay.name}</p>
            <p className="text-gray-500 text-xs mt-0.5">{relay.peer_id}</p>
          </>
        ) : (
          <p className="text-gray-500 text-sm">Detecting...</p>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg p-3">
        <p className="text-xs text-gray-400 font-bold tracking-wider mb-2">STATUS</p>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Online</span>
          <span className="text-green-400 font-mono">{onlineCount}</span>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="text-gray-400">Total</span>
          <span className="text-gray-300 font-mono">{peers.length}</span>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-3">
        <p className="text-xs text-gray-400 font-bold tracking-wider mb-2">NODES</p>
        {peers.map(peer => (
          <div key={peer.peer_id} className="flex items-center justify-between py-1">
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${
                peer.online ? 'bg-green-400' : 'bg-gray-600'
              }`} />
              <span className={`text-xs ${peer.online ? 'text-gray-300' : 'text-gray-600'}`}>
                {peer.name}
              </span>
            </div>
            {peer.peer_id === relay?.peer_id && (
              <span className="text-yellow-400 text-xs">★</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}