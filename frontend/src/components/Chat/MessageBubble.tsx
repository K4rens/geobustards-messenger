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
    <div className={`flex mb-3 ${isOwn ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md ${isOwn ? 'items-end' : 'items-start'} flex flex-col`}>
        {!isOwn && senderName && (
          <span className="text-xs text-gray-500 mb-1 ml-1">{senderName}</span>
        )}
        <div className={`px-3 py-2 rounded-2xl text-sm ${
          isOwn
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-gray-700 text-gray-100 rounded-bl-sm'
        }`}>
          {msg.text}
        </div>
        <span className="text-xs text-gray-600 mt-1 mx-1">
          {time} {msg.encrypted && '🔒'}
        </span>
      </div>
    </div>
  )
}