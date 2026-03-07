import { useState, type KeyboardEvent } from 'react'
import FileTransfer from './FileTransfer'

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
  activePeerId: string | null
}

export default function MessageInput({ onSend, disabled, activePeerId }: Props) {
  const [text, setText] = useState('')

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex gap-2 p-3 border-t border-gray-800 bg-gray-900 items-center">
      <FileTransfer activePeerId={activePeerId} />
      <input
        className="flex-1 bg-gray-800 text-gray-100 text-sm px-3 py-2 rounded-lg outline-none
          placeholder-gray-600 border border-gray-700 focus:border-blue-500 transition-colors"
        placeholder="Type a message..."
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={handleKey}
        disabled={disabled}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !text.trim()}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700
          disabled:text-gray-500 text-white text-sm rounded-lg transition-colors font-bold"
      >
        Send
      </button>
    </div>
  )
}
