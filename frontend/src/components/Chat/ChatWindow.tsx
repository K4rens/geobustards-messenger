import { useRef, useEffect } from 'react'
import { useStore } from '../../store/store'
import { api } from '../../api'
import MessageBubble from './MessageBubble'
import MessageInput from './MessageInput'

export default function ChatWindow() {
  const messages = useStore(s => s.messages)
  const peers = useStore(s => s.peers)
  const activePeerId = useStore(s => s.activePeerId)
  const addMessage = useStore(s => s.addMessage)
  const myId = useStore(s => s.myId)

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const activePeer = peers.find(p => p.peer_id === activePeerId)
  const title = activePeer ? activePeer.name : 'Broadcast'

  const visibleMessages = activePeerId
    ? messages.filter(
        m =>
          (m.from_id === activePeerId && m.to === myId) ||
          (m.from_id === myId && m.to === activePeerId)
      )
    : messages.filter(m => m.to === 'broadcast')

  const handleSend = async (text: string) => {
    const to = activePeerId ?? 'broadcast'
    await api.sendMessage(to, text)
    if (myId) {
      addMessage({
        id: Math.random().toString(36).slice(2, 10),
        from_id: myId,
        to,
        text,
        timestamp: Date.now() / 1000,
        encrypted: true,
      })
    }
  }

  const getSenderName = (from_id: string) =>
    peers.find(p => p.peer_id === from_id)?.name ?? from_id

  return (
    <div className="flex flex-col h-full">
      <div className="h-12 border-b border-gray-800 flex items-center px-4 bg-gray-900 shrink-0">
        <span className="text-sm font-bold text-gray-200 tracking-wide">{title}</span>
        {activePeer && (
          <span className={`ml-2 w-2 h-2 rounded-full ${activePeer.online ? 'bg-green-400' : 'bg-gray-600'}`} />
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        {visibleMessages.length === 0 ? (
          <p className="text-center text-gray-600 text-sm mt-12">No messages yet</p>
        ) : (
          visibleMessages.map(msg => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              isOwn={msg.from_id === myId}
              senderName={getSenderName(msg.from_id)}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <MessageInput onSend={handleSend} disabled={!myId} />
    </div>
  )
}