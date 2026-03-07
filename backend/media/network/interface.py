from abc import ABC, abstractmethod
from typing import AsyncIterator

from models import Peer, RelayInfo


class NetworkClient(ABC):

    @abstractmethod
    async def get_peers(self) -> list[Peer]:
        """Список онлайн пиров"""

    @abstractmethod
    async def get_relay(self) -> RelayInfo:
        """Текущий relay узел"""

    @abstractmethod
    async def send_message(self, to: str, text: str) -> str:
        """Отправить сообщение, вернуть message_id"""

    @abstractmethod
    async def stream_events(self) -> AsyncIterator[dict]:
        """
        Поток событий от сети.
        Каждый элемент: {"type": "...", "data": {...}}
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Доступен ли Backend1"""
