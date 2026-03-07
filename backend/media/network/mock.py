import time
import uuid

from errors import BadRequestError
from models import ChatMessage, Peer, RelayInfo
from network.interface import NetworkClient


class MockClient(NetworkClient):
    def __init__(self):
        self._node_id = "node1"
        self._peers = [
            Peer(peer_id="node2", name="Node 2", address="192.168.1.2:9000", online=True),
            Peer(peer_id="node3", name="Node 3", address="192.168.1.3:9000", online=True),
            Peer(peer_id="node4", name="Node 4", address="192.168.1.4:9000", online=False),
        ]
        self._messages: list[ChatMessage] = [
            ChatMessage(
                id=str(uuid.uuid4()),
                from_id="node2",
                to="broadcast",
                text="Mesh network is up!",
                timestamp=time.time() - 60,
                encrypted=True,
            )
        ]
        self._files: dict[str, dict] = {}
        self._events: list[dict] = []
        self._tick = 0

    async def get_peers(self) -> list[Peer]:
        return list(self._peers)

    async def get_relay(self) -> RelayInfo:
        online = [peer for peer in self._peers if peer.online]
        if not online:
            return RelayInfo(peer_id=self._node_id, name="Node 1")
        first = online[0]
        return RelayInfo(peer_id=first.peer_id, name=first.name)

    async def get_messages(self) -> list[ChatMessage]:
        return list(self._messages[-100:])

    async def send_message(self, to: str, text: str) -> str:
        message_id = str(uuid.uuid4())
        self._messages.append(
            ChatMessage(
                id=message_id,
                from_id=self._node_id,
                to=to,
                text=text,
                timestamp=time.time(),
                encrypted=True,
            )
        )
        self._messages = self._messages[-100:]
        return message_id

    async def send_file(self, to: str, file_data: bytes, filename: str) -> str:
        file_id = str(uuid.uuid4())
        metadata = {
            "file_id": file_id,
            "from_id": self._node_id,
            "to": to,
            "filename": filename,
            "size": len(file_data),
            "timestamp": time.time(),
        }
        self._files[file_id] = {"meta": metadata, "content": file_data}
        self._events.append(
            {
                "type": "file:progress",
                "data": {"file_id": file_id, "to": to, "filename": filename, "progress": 100},
            }
        )
        self._events.append({"type": "file:received", "data": metadata})
        return file_id

    async def get_files(self) -> list[dict]:
        ordered = sorted(
            (item["meta"] for item in self._files.values()),
            key=lambda x: x.get("timestamp", 0),
        )
        return ordered[-100:]

    async def get_file(self, file_id: str) -> bytes:
        item = self._files.get(file_id)
        if not item:
            raise BadRequestError("file not found")
        return item["content"]

    async def send_signal(self, to: str, signal_type: str, payload: dict) -> str:
        signal_id = str(uuid.uuid4())
        self._events.append(
            {
                "type": "signal:received",
                "data": {
                    "id": signal_id,
                    "from_id": self._node_id,
                    "to": to,
                    "signal_type": signal_type,
                    "payload": payload,
                    "timestamp": time.time(),
                },
            }
        )
        return signal_id

    async def get_events(self) -> list[dict]:
        self._tick += 1

        if self._tick == 2:
            incoming = ChatMessage(
                id=str(uuid.uuid4()),
                from_id="node3",
                to="broadcast",
                text="hi",
                timestamp=time.time(),
                encrypted=True,
            )
            self._messages.append(incoming)
            self._messages = self._messages[-100:]
            self._events.append({"type": "message:received", "data": incoming.model_dump()})

        if self._tick == 4:
            self._peers[0].online = False
            self._events.append({"type": "peer:left", "data": {"peer_id": "node2"}})
            self._events.append({"type": "relay:info", "data": {"peer_id": "node3", "name": "Node 3"}})

        if self._tick == 6:
            self._peers[0].online = True
            self._events.append({"type": "peer:joined", "data": self._peers[0].model_dump()})
            self._events.append({"type": "relay:info", "data": {"peer_id": "node2", "name": "Node 2"}})
            self._tick = 0

        events = list(self._events)
        self._events.clear()
        return events

    async def get_node_id(self) -> str:
        return self._node_id
