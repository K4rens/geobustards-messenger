import { useRef, useEffect } from 'react'
import { useStore } from '../../store/store'
import { api } from '../../api'
import MessageBubble from './MessageBubble'
import MessageInput from './MessageInput'

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function ChatWindow() {
  const messages = useStore(s => s.messages)
  const peers = useStore(s => s.peers)
  const activePeerId = useStore(s => s.activePeerId)
  const addMessage = useStore(s => s.addMessage)
  const myId = useStore(s => s.myId)
  const files = useStore(s => s.files)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const activePeer = peers.find(p => p.peer_id === activePeerId)
  const title = activePeer ? activePeer.name : 'Broadcast'

  const visibleMessages = activePeerId
    ? messages.filter(m =>
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
          visibleMessages.map(msg => {
            const fileInfo = msg.file
              ? (files.find(f => f.file_id === msg.file!.file_id) ?? msg.file)
              : null

            return (
              <div key={msg.id}>
                <MessageBubble
                  msg={msg}
                  isOwn={msg.from_id === myId}
                  senderName={getSenderName(msg.from_id)}
                />
                {fileInfo && (
                  <div className={`flex mb-3 ${msg.from_id === myId ? 'justify-end' : 'justify-start'}`}>
                    <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 max-w-xs">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">📎</span>
                        <div className="min-w-0">
                          <p className="text-sm text-gray-200 truncate">{fileInfo.filename}</p>
                          <p className="text-xs text-gray-500">{formatSize(fileInfo.size)}</p>
                        </div>
                      </div>
                      {!fileInfo.complete && (
                        <div className="w-full bg-gray-700 rounded-full h-1.5 mb-2">
                          <div className="bg-blue-500 h-1.5 rounded-full transition-all" style={{ width: `${fileInfo.progress}%` }} />
                        </div>
                      )}
                      {fileInfo.complete && (
                        <a href={`/api/file/${fileInfo.file_id}`} download={fileInfo.filename} className="block text-center text-xs bg-blue-600 hover:bg-blue-500 text-white py-1 px-3 rounded-lg transition-colors">
                          Download
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
        <div ref={bottomRef} />
      </div>

      <MessageInput onSend={handleSend} disabled={!myId} activePeerId={activePeerId} />
    </div>
  )
}
