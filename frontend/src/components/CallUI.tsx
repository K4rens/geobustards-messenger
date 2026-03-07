import { useEffect, useRef, useState } from 'react'
import { Phone, PhoneOff, Mic, MicOff } from 'lucide-react'
import { useStore } from '../store/store'
import { useWebRTC } from '../hooks/useWebRTC'

export default function CallUI() {
  const callState = useStore(s => s.callState)
  const callPeerId = useStore(s => s.callPeerId)
  const incomingCall = useStore(s => s.incomingCall)
  const peers = useStore(s => s.peers)
  const { hangup, startCall, remoteStream, audioRef } = useWebRTC()
  const [muted, setMuted] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const timerRef = useRef<number>(0)

  const callPeerName = peers.find(p => p.peer_id === callPeerId)?.name ?? callPeerId

  useEffect(() => {
    if (callState !== 'active') {
      window.clearInterval(timerRef.current)
      timerRef.current = 0
      return
    }
    let count = 0
    timerRef.current = window.setInterval(() => {
      count += 1
      setSeconds(count)
    }, 1000)
    return () => {
      window.clearInterval(timerRef.current)
    }
  }, [callState])

  useEffect(() => {
    if (audioRef.current && remoteStream) {
      audioRef.current.srcObject = remoteStream
    }
  }, [remoteStream, audioRef])

  const toggleMute = () => {
    const next = !muted
    setMuted(next)
    if (audioRef.current) audioRef.current.muted = next
  }

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  if (callState === 'idle') return null

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <audio ref={audioRef} autoPlay />
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 w-80 flex flex-col items-center gap-6">

        <div className="w-16 h-16 rounded-full bg-gray-700 flex items-center justify-center text-2xl">
          👤
        </div>

        <div className="text-center">
          <p className="text-white font-bold text-lg">{callPeerName}</p>
          {callState === 'calling' && (
            <p className="text-gray-400 text-sm mt-1">Calling...</p>
          )}
          {callState === 'ringing' && (
            <p className="text-gray-400 text-sm mt-1">Incoming call...</p>
          )}
          {callState === 'active' && (
            <p className="text-green-400 text-sm mt-1 font-mono">{formatTime(seconds)}</p>
          )}
        </div>

        {callState === 'ringing' && incomingCall && (
          <div className="flex gap-4">
            <button
              onClick={() => startCall(incomingCall.from_id)}
              className="w-14 h-14 rounded-full bg-green-500 hover:bg-green-400 flex items-center justify-center transition-colors"
            >
              <Phone size={22} className="text-white" />
            </button>
            <button
              onClick={hangup}
              className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-400 flex items-center justify-center transition-colors"
            >
              <PhoneOff size={22} className="text-white" />
            </button>
          </div>
        )}

        {(callState === 'calling' || callState === 'active') && (
          <div className="flex gap-4">
            {callState === 'active' && (
              <button
                onClick={toggleMute}
                className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${muted ? 'bg-gray-600 hover:bg-gray-500' : 'bg-gray-700 hover:bg-gray-600'}`}
              >
                {muted
                  ? <MicOff size={22} className="text-white" />
                  : <Mic size={22} className="text-white" />
                }
              </button>
            )}
            <button
              onClick={hangup}
              className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-400 flex items-center justify-center transition-colors"
            >
              <PhoneOff size={22} className="text-white" />
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
