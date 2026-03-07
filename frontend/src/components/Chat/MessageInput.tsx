import { useState, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
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
    <div className="p-4 border-t border-white/5">
      <div className="flex items-center gap-2 px-4 py-3 rounded-2xl transition-all" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <FileTransfer activePeerId={activePeerId} />
        <input
          className="flex-1 bg-transparent text-slate-200 text-sm outline-none placeholder-slate-600"
          placeholder="Type a message..."
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="w-8 h-8 rounded-xl flex items-center justify-center transition-all disabled:opacity-30"
          style={text.trim() ? { background: 'linear-gradient(135deg, #7c3aed, #4f46e5)' } : { background: 'rgba(255,255,255,0.05)' }}
        >
          <Send size={14} className="text-white" />
        </button>
      </div>
    </div>
  )
}