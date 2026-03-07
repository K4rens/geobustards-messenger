import type { ChatMessage } from '../../types'

interface Props {
  msg: ChatMessage
  isOwn: boolean
  senderName?: string
}

export default function MessageBubble({ msg, isOwn, senderName }: Props) {
  const time = new Date(msg.timestamp * 1000).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div className={`flex mb-4 animate-fadeIn ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex flex-col max-w-xs lg:max-w-sm ${isOwn ? 'items-end' : 'items-start'}`}>
        {!isOwn && senderName && (
          <span className="text-xs text-slate-500 mb-1.5 ml-1 font-medium">{senderName}</span>
        )}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed transition-all ${
            isOwn
              ? 'text-white rounded-br-sm'
              : 'text-slate-200 rounded-bl-sm'
          }`}
          style={isOwn
            ? { background: 'linear-gradient(135deg, #7c3aed, #4f46e5)', boxShadow: '0 4px 15px rgba(124,58,237,0.3)' }
            : { background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.08)' }
          }
        >
          {msg.text}
        </div>
        <span className="text-xs text-slate-600 mt-1 mx-1 flex items-center gap-1">
          {time}
          {msg.encrypted && <span className="text-slate-600">🔒</span>}
        </span>
      </div>
    </div>
  )
}