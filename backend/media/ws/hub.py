import asyncio

from fastapi import WebSocket
from models import WsEvent


class WsHub:
    def __init__(self):
        self._conns: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._conns.add(ws)
        print(f"[WS] Client connected. Total: {len(self._conns)}")

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._conns.discard(ws)
        print(f"[WS] Client disconnected. Total: {len(self._conns)}")

    async def broadcast(self, event: WsEvent):
        if not self._conns:
            return
        payload = event.model_dump_json()
        dead = set()
        for ws in list(self._conns):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                self._conns -= dead

    async def broadcast_raw(self, event_type: str, data: dict):
        await self.broadcast(WsEvent(type=event_type, data=data))

    def count(self) -> int:
        return len(self._conns)
