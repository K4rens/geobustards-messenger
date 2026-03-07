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
  const initials = activePeer ? activePeer.name.split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase() : '#'

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
      {/* Chat header */}
      <div className="h-14 border-b border-white/5 flex items-center px-5 gap-3 shrink-0" style={{ background: 'rgba(255,255,255,0.02)' }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-semibold text-purple-200" style={{ background: 'rgba(124,58,237,0.2)' }}>
          {initials}
        </div>
        <div>
          <p className="text-sm font-semibold text-white">{title}</p>
          {activePeer && (
            <p className={`text-xs ${activePeer.online ? 'text-emerald-400' : 'text-slate-600'}`}>
              {activePeer.online ? 'Online' : 'Offline'}
            </p>
          )}
          {!activePeer && (
            <p className="text-xs text-slate-600">All nodes</p>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {visibleMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 opacity-40">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl" style={{ background: 'rgba(124,58,237,0.1)' }}>
              💬
            </div>
            <p className="text-slate-500 text-sm">No messages yet</p>
          </div>
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
                  <div className={`flex mb-4 ${msg.from_id === myId ? 'justify-end' : 'justify-start'}`}>
                    <div className="rounded-2xl px-4 py-3 max-w-xs" style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg" style={{ background: 'rgba(124,58,237,0.15)' }}>
                          📎
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm text-slate-200 truncate font-medium">{fileInfo.filename}</p>
                          <p className="text-xs text-slate-500">{formatSize(fileInfo.size)}</p>
                        </div>
                      </div>
                      {!fileInfo.complete && (
                        <div className="w-full rounded-full h-1 mb-2" style={{ background: 'rgba(255,255,255,0.1)' }}>
                          <div className="h-1 rounded-full transition-all" style={{ width: `${fileInfo.progress}%`, background: 'linear-gradient(90deg, #7c3aed, #4f46e5)' }} />
                        </div>
                      )}
                      {fileInfo.complete && (
                        <a href={`/api/file/${fileInfo.file_id}`} download={fileInfo.filename} className="block text-center text-xs text-purple-300 py-1.5 px-3 rounded-xl transition-all hover:text-white" style={{ background: 'rgba(124,58,237,0.2)', border: '1px solid rgba(139,92,246,0.3)' }}>
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