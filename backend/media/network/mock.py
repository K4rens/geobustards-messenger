import asyncio
import uuid

from network.interface import NetworkClient
from models import Peer, RelayInfo

PEERS = [
    Peer(peer_id="node1", name="Node 1", address="192.168.1.1:9000", online=True),
    Peer(peer_id="node2", name="Node 2", address="192.168.1.2:9000", online=True),
    Peer(peer_id="node3", name="Node 3", address="192.168.1.3:9000", online=True),
    Peer(peer_id="node4", name="Node 4", address="192.168.1.4:9000", online=False),
]


class MockClient(NetworkClient):

    async def get_peers(self) -> list[Peer]:
        return PEERS

    async def get_relay(self) -> RelayInfo:
        online = [p for p in PEERS if p.online]
        first = online[0] if online else PEERS[0]
        return RelayInfo(peer_id=first.peer_id, name=first.name)

    async def send_message(self, to: str, text: str) -> str:
        return str(uuid.uuid4())[:8]

    async def stream_events(self):
        """
        Генерирует тестовые события каждые несколько секунд.
        Имитирует поведение реальной сети.
        """
        iteration = 0
        while True:
            await asyncio.sleep(3)
            iteration += 1

            if iteration % 2 == 0:
                yield {
                    "type": "peers:update",
                    "data": {
                        "peers": [p.model_dump() for p in PEERS],
                        "relay": {"peer_id": "node2", "name": "Node 2"},
                    },
                }

            if iteration == 5:
                yield {
                    "type": "peer:left",
                    "data": {"peer_id": "node2"},
                }
                await asyncio.sleep(1)
                yield {
                    "type": "relay:info",
                    "data": {"peer_id": "node3", "name": "Node 3"},
                }

    async def health_check(self) -> bool:
        return True
