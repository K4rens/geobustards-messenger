import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


class MockNode:
    """Минимальный mock Node для тестирования FloodRouter."""
    def __init__(self):
        self.id = "test_node"
        self.name = "Test Node"
        self.peers = {}
        self.on_chat = None
        self.on_file = None
        self.on_signal = None
        self._broadcast_calls = []

    async def broadcast_message(self, msg: dict, exclude: str = ""):
        self._broadcast_calls.append({"msg": dict(msg), "exclude": exclude})


# Импортируем из правильного пути
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routing.flooding import FloodRouter


@pytest.mark.asyncio
async def test_flood_deduplication():
    """Одно и то же сообщение не должно форвардиться дважды."""
    node = MockNode()
    router = FloodRouter(node)

    msg = {"id": "test-uuid-001", "type": "CHAT", "from_id": "node2",
           "to": "broadcast", "text": "Hello", "ttl": 7, "timestamp": 1718000000.0}

    result1 = await router.process(dict(msg), "node2:9000")
    result2 = await router.process(dict(msg), "node2:9000")

    assert result1 is True, "Первый вызов должен вернуть True"
    assert result2 is False, "Дубликат должен вернуть False"
    assert len(node._broadcast_calls) == 1, "broadcast должен вызваться только один раз"


@pytest.mark.asyncio
async def test_flood_ttl_decrement():
    """TTL должен уменьшаться при каждом хопе."""
    node = MockNode()
    router = FloodRouter(node)

    msg = {"id": "test-uuid-002", "type": "CHAT", "from_id": "node2",
           "to": "broadcast", "text": "TTL test", "ttl": 3, "timestamp": 1718000001.0}

    await router.process(msg, "node2:9000")
    # После process TTL должен быть 3-1=2
    assert msg["ttl"] == 2, f"TTL должен быть 2, получили {msg['ttl']}"


@pytest.mark.asyncio
async def test_flood_ttl_zero_drops():
    """Сообщение с TTL=1 после декремента до 0 не должно форвардиться."""
    node = MockNode()
    router = FloodRouter(node)

    msg = {"id": "test-uuid-003", "type": "CHAT", "from_id": "node2",
           "to": "broadcast", "text": "TTL zero", "ttl": 1, "timestamp": 1718000002.0}

    result = await router.process(msg, "node2:9000")
    assert result is False, "Сообщение с TTL=1 после декремента до 0 должно быть дропнуто"
    assert len(node._broadcast_calls) == 0, "broadcast не должен вызываться при TTL=0"


@pytest.mark.asyncio
async def test_flood_calls_on_chat_for_incoming():
    """Входящее CHAT сообщение должно вызывать on_chat колбэк."""
    node = MockNode()
    received_msgs = []

    async def mock_on_chat(msg):
        received_msgs.append(msg)

    node.on_chat = mock_on_chat
    router = FloodRouter(node)

    msg = {"id": "test-uuid-004", "type": "CHAT", "from_id": "node3",
           "to": "broadcast", "text": "callback test", "ttl": 7, "timestamp": 1718000003.0}

    await router.process(msg, "node3:9000", is_local=False)
    assert len(received_msgs) == 1, "on_chat должен был вызваться один раз"
    assert received_msgs[0]["text"] == "callback test"


@pytest.mark.asyncio
async def test_flood_local_does_not_call_on_chat():
    """Локальное сообщение (is_local=True) НЕ должно вызывать on_chat."""
    node = MockNode()
    received_msgs = []

    async def mock_on_chat(msg):
        received_msgs.append(msg)

    node.on_chat = mock_on_chat
    router = FloodRouter(node)

    msg = {"id": "test-uuid-005", "type": "CHAT", "from_id": "node1",
           "to": "broadcast", "text": "local message", "ttl": 7, "timestamp": 1718000004.0}

    await router.process(msg, "", is_local=True)
    assert len(received_msgs) == 0, "on_chat НЕ должен вызываться для локальных сообщений"


@pytest.mark.asyncio
async def test_flood_exclude_sender():
    """При форварде должен передаваться exclude=from_addr."""
    node = MockNode()
    router = FloodRouter(node)

    msg = {"id": "test-uuid-006", "type": "CHAT", "from_id": "node2",
           "to": "broadcast", "text": "exclude test", "ttl": 7, "timestamp": 1718000005.0}

    await router.process(msg, "172.28.0.11:9000")
    assert len(node._broadcast_calls) == 1
    assert node._broadcast_calls[0]["exclude"] == "172.28.0.11:9000", \
        "broadcast должен быть вызван с exclude=адрес отправителя"
