import asyncio

from network.interface import NetworkClient
from ws.hub import WsHub


class EventBridge:
    def __init__(self, network: NetworkClient, hub: WsHub):
        self.network = network
        self.hub = hub

    async def start(self):
        asyncio.create_task(self._stream_loop())
        asyncio.create_task(self._poll_loop())
        print("[BRIDGE] Started")

    async def _stream_loop(self):
        """
        Читать события из network.stream_events()
        и пробрасывать в WebSocket.
        При разрыве — реконнект через 2 сек.
        """
        while True:
            try:
                async for event in self.network.stream_events():
                    event_type = event.get("type", "")
                    data = event.get("data", {})
                    print(f"[BRIDGE] Event: {event_type}")
                    await self.hub.broadcast_raw(event_type, data)
            except Exception as e:
                print(f"[BRIDGE] Stream error: {e}, reconnecting...")
                await asyncio.sleep(2)

    async def _poll_loop(self):
        """
        Каждые 5 сек запрашивать актуальных пиров и relay,
        пушить в WS чтобы UI всегда был актуален.
        """
        while True:
            await asyncio.sleep(5)
            try:
                peers = await self.network.get_peers()
                relay = await self.network.get_relay()
                await self.hub.broadcast_raw("peers:update", {
                    "peers": [p.model_dump() for p in peers],
                    "relay": relay.model_dump(),
                })
            except Exception as e:
                print(f"[BRIDGE] Poll error: {e}")
