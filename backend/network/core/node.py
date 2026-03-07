import asyncio
import time
import uuid
import os
import json
from typing import Callable, Optional

from .transport import Transport

# Lazy import to avoid circular dependency
def _get_push_peer_event():
    from api.server import push_peer_event
    return push_peer_event


class Node:
    def __init__(self, node_id: str, name: str, port: int):
        self.id = node_id
        self.name = name
        self.port = port
        self.transport = Transport(port)

        self.peers: dict[str, dict] = {}
        self.last_seen: dict[str, float] = {}
        self._reconnect_cooldown: dict[str, float] = {}

        self.on_chat: Optional[Callable[[dict], None]] = None
        self.on_file: Optional[Callable[[dict], None]] = None
        self.on_signal: Optional[Callable[[dict], None]] = None
        self.flood_router = None

    async def start(self):
        self.transport.set_handler(self._handle_message)
        await self.transport.start()
        asyncio.create_task(self._heartbeat_loop())

    async def connect_to_peers(self, addresses: list[str]):
        my_address = f"{self.id}:{self.port}"
        for addr in addresses:
            success = await self.transport.connect(addr)
            if success:
                await self.transport.send(addr, {
                    "type": "HELLO",
                    "from_id": self.id,
                    "name": self.name,
                    "address": my_address,
                })
                print(f"[NODE] Sent HELLO to {addr}")

    async def _handle_message(self, msg: dict, from_addr: str):
        from_id = msg.get("from_id", "")

        if from_id:
            self.last_seen[from_id] = time.time()

        msg_type = msg.get("type", "")

        if msg_type == "HELLO":
            peer = {
                "peer_id": msg["from_id"],
                "name": msg.get("name", msg["from_id"]),
                "address": msg.get("address", from_addr),
                "online": True,
            }
            self.peers[msg["from_id"]] = peer
            print(f"[NODE] 👋 Peer joined: {peer['name']}")
            try:
                push_fn = _get_push_peer_event()
                asyncio.create_task(push_fn("peer:joined", peer))
            except Exception:
                pass

        elif msg_type == "HEARTBEAT":
            ts = msg.get("ts")
            if ts and from_id:
                rtt = (time.time() - ts) * 1000
                if not hasattr(self, '_rtt_samples'):
                    self._rtt_samples: dict[str, list[float]] = {}
                samples = self._rtt_samples.setdefault(from_id, [])
                samples.append(rtt)
                if len(samples) > 10:
                    samples.pop(0)

        elif msg_type == "CHAT":
            if self.flood_router:
                await self.flood_router.process(msg, from_addr)

        elif msg_type == "FILE_CHUNK":
            if self.on_file:
                await self.on_file(msg)
            if self.flood_router:
                await self.flood_router.process(msg, from_addr)

        elif msg_type == "SIGNAL":
            if self.flood_router:
                await self.flood_router.process(msg, from_addr)

    async def _heartbeat_loop(self):
        while True:
            await asyncio.sleep(1)
            now = time.time()

            for peer_id, peer in self.peers.items():
                last = self.last_seen.get(peer_id, 0)
                was_online = peer["online"]
                is_online = (now - last) < 4.0

                if was_online and not is_online:
                    peer["online"] = False
                    print(f"[NODE] 💀 Peer offline: {peer['name']}")
                    try:
                        push_fn = _get_push_peer_event()
                        asyncio.create_task(push_fn("peer:left", {"peer_id": peer["peer_id"]}))
                    except Exception:
                        pass
                elif not was_online and is_online:
                    peer["online"] = True
                    print(f"[NODE] 🔄 Peer back: {peer['name']}")
                    try:
                        push_fn = _get_push_peer_event()
                        asyncio.create_task(push_fn("peer:joined", peer))
                    except Exception:
                        pass
                elif not was_online and not is_online:
                    addr = peer.get("address", "")
                    now_ts = time.time()
                    last_attempt = self._reconnect_cooldown.get(peer_id, 0)
                    if addr and addr not in self.transport.connections and (now_ts - last_attempt) > 10:
                        self._reconnect_cooldown[peer_id] = now_ts
                        asyncio.create_task(self._try_reconnect(peer_id, addr))

            await self.transport.broadcast({
                "type": "HEARTBEAT",
                "from_id": self.id,
                "ts": time.time(),
            })

    async def _try_reconnect(self, peer_id: str, addr: str):
        my_address = f"{self.id}:{self.port}"
        success = await self.transport.connect(addr)
        if success:
            await self.transport.send(addr, {
                "type": "HELLO",
                "from_id": self.id,
                "name": self.name,
                "address": my_address,
            })
            print(f"[NODE] 🔁 Reconnected to {addr}")

    def get_rtt_ms(self, peer_id: str) -> float:
        """Возвращает среднее RTT в мс для пира, или -1 если нет данных."""
        samples = getattr(self, '_rtt_samples', {}).get(peer_id, [])
        if not samples:
            return -1.0
        return round(sum(samples) / len(samples), 1)

    def get_peers(self) -> list[dict]:
        return list(self.peers.values())

    def get_relay(self) -> Optional[dict]:
        online = [p for p in self.peers.values() if p["online"]]
        return online[0] if online else None

    async def broadcast_message(self, msg: dict, exclude: str = ""):
        await self.transport.broadcast(msg, exclude)
