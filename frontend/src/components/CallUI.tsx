import { useEffect, useState } from 'react'
import { Phone, PhoneOff, Mic, MicOff } from 'lucide-react'
import { useStore } from '../store/store'
import { useWebRTC } from '../hooks/useWebRTC'

export default function CallUI() {
  const callState = useStore(s => s.callState)
  const callPeerId = useStore(s => s.callPeerId)
  const incomingCall = useStore(s => s.incomingCall)
  const peers = useStore(s => s.peers)
  const { hangup, acceptCall, remoteStream, audioRef } = useWebRTC()
  const [muted, setMuted] = useState(false)
  const [seconds, setSeconds] = useState(0)

  const callPeerName = peers.find(p => p.peer_id === callPeerId)?.name ?? callPeerId
  const initials = callPeerName ? callPeerName.split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase() : '?'

  useEffect(() => {
    if (callState !== 'active') {
      setSeconds(0)
      return
    }
    let count = 0
    const timer = window.setInterval(() => { count += 1; setSeconds(count) }, 1000)
    return () => window.clearInterval(timer)
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
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)' }}>
      <audio ref={audioRef} autoPlay />
      <div className="animate-popIn rounded-3xl p-8 w-80 flex flex-col items-center gap-6" style={{ background: 'linear-gradient(135deg, #1a1a2e, #16162a)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 25px 60px rgba(0,0,0,0.5)' }}>

        <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-2xl font-bold text-purple-200" style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(79,70,229,0.3))', border: '1px solid rgba(139,92,246,0.3)' }}>
          {initials}
        </div>

        <div className="text-center">
          <p className="text-white font-semibold text-lg">{callPeerName}</p>
          {callState === 'calling' && (
            <p className="text-slate-400 text-sm mt-1 animate-pulse">Calling...</p>
          )}
          {callState === 'ringing' && (
            <p className="text-purple-300 text-sm mt-1 animate-pulse">Incoming call</p>
          )}
          {callState === 'active' && (
            <p className="text-emerald-400 text-sm mt-1 font-mono">{formatTime(seconds)}</p>
          )}
        </div>

        {callState === 'ringing' && incomingCall && (
          <div className="flex gap-4">
            <button
              onClick={acceptCall}
              className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 4px 20px rgba(16,185,129,0.4)' }}
            >
              <Phone size={22} className="text-white" />
            </button>
            <button
              onClick={hangup}
              className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
              style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)', boxShadow: '0 4px 20px rgba(239,68,68,0.4)' }}
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
                className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
                style={{ background: muted ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)' }}
              >
                {muted
                  ? <MicOff size={20} className="text-red-400" />
                  : <Mic size={20} className="text-slate-300" />
                }
              </button>
            )}
            <button
              onClick={hangup}
              className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all hover:scale-105 active:scale-95"
              style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)', boxShadow: '0 4px 20px rgba(239,68,68,0.4)' }}
            >
              <PhoneOff size={20} className="text-white" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
