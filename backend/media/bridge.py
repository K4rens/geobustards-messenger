import asyncio

from network.interface import NetworkClient
from ws.hub import WsHub


class EventBridge:
    def __init__(self, network: NetworkClient, hub: WsHub):
        self.network = network
        self.hub = hub

    async def start(self):
        asyncio.create_task(self._poll_loop())
        print("[BRIDGE] Started")

    async def _poll_loop(self):
        while True:
            try:
                events = await self.network.get_events()
                for event in events:
                    event_type = event.get("type", "")
                    data = event.get("data", {})
                    if not isinstance(event_type, str) or not event_type:
                        continue
                    if not isinstance(data, dict):
                        data = {}
                    await self.hub.broadcast_raw(event_type, data)

                peers = await self.network.get_peers()
                relay = await self.network.get_relay()
                await self.hub.broadcast_raw(
                    "peers:update",
                    {
                        "peers": [peer.model_dump() for peer in peers],
                        "relay": relay.model_dump(),
                    },
                )
            except Exception as exc:
                print(f"[BRIDGE] Poll error: {exc}")

            await asyncio.sleep(2)
