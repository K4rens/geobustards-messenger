from abc import ABC, abstractmethod

from models import ChatMessage, Peer, RelayInfo


class NetworkClient(ABC):
    @abstractmethod
    async def get_peers(self) -> list[Peer]:
        """Return all peers from network backend."""

    @abstractmethod
    async def get_relay(self) -> RelayInfo:
        """Return current relay node info."""

    @abstractmethod
    async def get_messages(self) -> list[ChatMessage]:
        """Return latest chat messages."""

    @abstractmethod
    async def send_message(self, to: str, text: str) -> str:
        """Send chat message and return message_id."""

    @abstractmethod
    async def send_file(self, to: str, file_data: bytes, filename: str) -> str:
        """Send file and return file_id."""

    @abstractmethod
    async def get_files(self) -> list[dict]:
        """Return file metadata list."""

    @abstractmethod
    async def get_file(self, file_id: str) -> bytes:
        """Return file bytes by file_id."""

    @abstractmethod
    async def send_signal(self, to: str, signal_type: str, payload: dict) -> str:
        """Send signaling payload and return signal_id."""

    @abstractmethod
    async def get_events(self) -> list[dict]:
        """Return queued events since previous call."""

    @abstractmethod
    async def get_node_id(self) -> str:
        """Return current node_id from network backend."""
