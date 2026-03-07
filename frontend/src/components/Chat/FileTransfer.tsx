import { useRef, useState } from 'react'
import { Paperclip } from 'lucide-react'
import { useStore } from '../../store/store'
import { BASE } from '../../api/client'

const MAX_SIZE = 200 * 1024 * 1024 // 200MB

interface Props {
  activePeerId: string | null
}

export default function FileTransfer({ activePeerId }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const addFile = useStore(s => s.addFile)
  const updateFileProgress = useStore(s => s.updateFileProgress)

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.size > MAX_SIZE) {
      alert('Max file size is 200MB')
      return
    }

    const file_id = Math.random().toString(36).slice(2, 10)

    addFile({
      file_id,
      filename: file.name,
      size: file.size,
      complete: false,
      progress: 0,
    })

    setUploading(true)
    setProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('to', activePeerId ?? 'broadcast')
    formData.append('file_id', file_id)

    const xhr = new XMLHttpRequest()
    xhr.upload.onprogress = ev => {
      if (ev.lengthComputable) {
        const pct = Math.round((ev.loaded / ev.total) * 100)
        setProgress(pct)
        updateFileProgress(file_id, pct)
      }
    }
    xhr.onload = () => {
      updateFileProgress(file_id, 100, true)
      setUploading(false)
      setProgress(0)
    }
    xhr.onerror = () => {
      setUploading(false)
      setProgress(0)
    }
    xhr.open('POST', `${BASE}/api/file`)
    xhr.send(formData)

    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="flex items-center">
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={handleFile}
        accept="*"
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="p-2 text-gray-500 hover:text-gray-300 disabled:text-gray-700 transition-colors"
        title="Attach file"
      >
        {uploading ? (
          <div className="flex items-center gap-1 text-xs text-blue-400">
            <Paperclip size={16} />
            <span>{progress}%</span>
          </div>
        ) : (
          <Paperclip size={16} />
        )}
      </button>
    </div>
  )
}
