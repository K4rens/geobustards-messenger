import asyncio
import os
import struct
import time
import uuid
from typing import Optional

VOICE_PORT = 9002
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
CHUNK_SAMPLES = 960       # 60ms @ 16kHz
CHUNK_BYTES = CHUNK_SAMPLES * 2   # int16 = 2 bytes
PACKET_HEADER_SIZE = 8   # 4 bytes call_id prefix + 4 bytes seq

try:
    import numpy as np
    import sounddevice as sd
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False
    print("[VOICE] sounddevice not available, running in stub mode")


class VoiceCall:
    def __init__(self):
        self._active_calls: dict[str, dict] = {}
        self._jitter_buffers: dict[str, dict] = {}   # call_id -> {seq: pcm_bytes}
        self._play_seq: dict[str, int] = {}           # call_id -> next_seq to play
        self._send_seq: dict[str, int] = {}           # call_id -> next_seq to send
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start_listener(self):
        self._loop = asyncio.get_event_loop()
        try:
            transport, protocol = await self._loop.create_datagram_endpoint(
                lambda: _VoiceProtocol(self),
                local_addr=("0.0.0.0", VOICE_PORT)
            )
            self._transport = transport
            print(f"[VOICE] UDP listener on :{VOICE_PORT}")
        except Exception as e:
            print(f"[VOICE] Failed to start UDP listener: {e}")

    async def start_call(self, peer_addr: str, peer_voice_port: int = VOICE_PORT) -> str:
        call_id = str(uuid.uuid4())
        call_info = {
            "call_id": call_id,
            "peer": peer_addr,
            "peer_addr": peer_addr,
            "peer_voice_port": peer_voice_port,
            "started": time.time(),
            "packets_sent": 0,
            "packets_received": 0,
            "packets_lost": 0,
        }
        self._active_calls[call_id] = call_info
        self._jitter_buffers[call_id] = {}
        self._play_seq[call_id] = 0
        self._send_seq[call_id] = 0

        if _AUDIO_AVAILABLE:
            asyncio.create_task(self._capture_loop(call_id, peer_addr, peer_voice_port))
            asyncio.create_task(self._playback_loop(call_id))

        return call_id

    async def end_call(self, call_id: str):
        call = self._active_calls.pop(call_id, None)
        self._jitter_buffers.pop(call_id, None)
        self._play_seq.pop(call_id, None)
        self._send_seq.pop(call_id, None)

    def get_stats(self, call_id: str) -> dict:
        call = self._active_calls.get(call_id)
        if not call:
            return {"error": "call not found"}
        sent = call["packets_sent"]
        received = call["packets_received"]
        lost = call["packets_lost"]
        elapsed = time.time() - call["started"]
        loss_rate = (lost / max(sent, 1)) * 100
        latency_estimate_ms = 60 + (30 if loss_rate > 5 else 0)
        return {
            "packets_sent": sent,
            "packets_received": received,
            "packets_lost": lost,
            "loss_rate_pct": round(loss_rate, 1),
            "duration_sec": round(elapsed, 1),
            "latency_estimate_ms": latency_estimate_ms,
            "note": "latency estimated from frame duration; use /peers rtt_ms for network RTT"
        }

    def get_active_calls(self) -> list[dict]:
        return [
            {
                "call_id": c["call_id"],
                "peer": c["peer"],
                "started": c["started"],
            }
            for c in self._active_calls.values()
        ]

    def _receive_packet(self, data: bytes, addr):
        """Called by UDP protocol when a packet arrives."""
        if len(data) < PACKET_HEADER_SIZE:
            return
        call_id_prefix = data[:4]
        seq = struct.unpack(">I", data[4:8])[0]
        pcm = data[8:]

        # Match call by prefix
        matched_call_id = None
        for cid in self._active_calls:
            if cid[:4].encode("ascii", errors="replace")[:4] == call_id_prefix[:4]:
                matched_call_id = cid
                break
            # also try matching hex prefix
            try:
                if bytes.fromhex(cid[:8])[:4] == call_id_prefix:
                    matched_call_id = cid
                    break
            except Exception:
                pass

        if matched_call_id is None:
            # Try to find any active call from this peer
            addr_str = addr[0] if addr else ""
            for cid, call in self._active_calls.items():
                if call.get("peer_addr") == addr_str or call.get("peer") == addr_str:
                    matched_call_id = cid
                    break

        if matched_call_id is None:
            return

        call = self._active_calls[matched_call_id]
        call["packets_received"] += 1

        # Jitter buffer: store up to 10 frames ahead
        buf = self._jitter_buffers.get(matched_call_id, {})
        next_play = self._play_seq.get(matched_call_id, 0)
        if seq >= next_play and len(buf) < 10:
            buf[seq] = pcm
            self._jitter_buffers[matched_call_id] = buf

        # Count lost packets (gaps)
        if seq > next_play + 1:
            call["packets_lost"] += seq - next_play - 1

    async def _capture_loop(self, call_id: str, peer_addr: str, peer_voice_port: int):
        """Capture mic audio and send UDP packets."""
        if not _AUDIO_AVAILABLE or self._transport is None:
            return
        try:
            loop = asyncio.get_event_loop()
            q: asyncio.Queue = asyncio.Queue()

            def callback(indata, frames, time_info, status):
                loop.call_soon_threadsafe(q.put_nowait, bytes(indata))

            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SAMPLES,
                callback=callback,
            )
            stream.start()

            while call_id in self._active_calls:
                try:
                    pcm = await asyncio.wait_for(q.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                seq = self._send_seq.get(call_id, 0)
                self._send_seq[call_id] = seq + 1

                call_prefix = bytes.fromhex(call_id[:8])[:4]
                header = call_prefix + struct.pack(">I", seq)
                packet = header + pcm[:CHUNK_BYTES]

                try:
                    self._transport.sendto(packet, (peer_addr, peer_voice_port))
                    self._active_calls[call_id]["packets_sent"] += 1
                except Exception:
                    pass

            stream.stop()
            stream.close()
        except Exception as e:
            print(f"[VOICE] Capture error for {call_id}: {e}")

    async def _playback_loop(self, call_id: str):
        """Read from jitter buffer and play audio every 60ms."""
        if not _AUDIO_AVAILABLE:
            return
        try:
            stream = sd.OutputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SAMPLES,
            )
            stream.start()

            while call_id in self._active_calls:
                await asyncio.sleep(0.060)
                seq = self._play_seq.get(call_id, 0)
                buf = self._jitter_buffers.get(call_id, {})
                pcm = buf.pop(seq, None)
                if pcm is None:
                    pcm = b"\x00" * CHUNK_BYTES
                self._play_seq[call_id] = seq + 1

                try:
                    import numpy as np
                    arr = np.frombuffer(pcm, dtype=np.int16)
                    if len(arr) < CHUNK_SAMPLES:
                        arr = np.pad(arr, (0, CHUNK_SAMPLES - len(arr)))
                    stream.write(arr)
                except Exception:
                    pass

            stream.stop()
            stream.close()
        except Exception as e:
            print(f"[VOICE] Playback error for {call_id}: {e}")


class _VoiceProtocol(asyncio.DatagramProtocol):
    def __init__(self, voice: VoiceCall):
        self._voice = voice

    def datagram_received(self, data: bytes, addr):
        self._voice._receive_packet(data, addr)

    def error_received(self, exc):
        print(f"[VOICE] UDP error: {exc}")
