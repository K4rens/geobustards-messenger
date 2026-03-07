import asyncio
import time

from core.node import Node


class FloodRouter:
    def __init__(self, node: Node):
        self.node = node
        self.seen: dict[str, float] = {}
        asyncio.create_task(self._cleanup_loop())

    async def process(self, msg: dict, from_addr: str, is_local: bool = False) -> bool:
        msg_id = msg.get("id", "")

        if msg_id and msg_id in self.seen:
            return False

        if msg_id:
            self.seen[msg_id] = time.time()

        msg["ttl"] = msg.get("ttl", 7) - 1
        if msg["ttl"] <= 0:
            return False

        if not is_local:
            msg_type = msg.get("type")
            if msg_type == "FILE_CHUNK" and self.node.on_file:
                await self.node.on_file(msg)
            elif msg_type == "SIGNAL" and self.node.on_signal:
                await self.node.on_signal(msg)
            elif msg_type == "CHAT" and self.node.on_chat:
                await self.node.on_chat(msg)

        await self.node.broadcast_message(msg, exclude=from_addr)
        print(f"[FLOOD] Forwarded {msg_id[:8] if msg_id else '?'} TTL={msg['ttl']}")
        return True

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(30)
            cutoff = time.time() - 300
            self.seen = {k: v for k, v in self.seen.items() if v > cutoff}
