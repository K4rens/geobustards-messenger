import asyncio
import json

import httpx

from network.interface import NetworkClient
from models import Peer, RelayInfo


class RealClient(NetworkClient):
    def __init__(self, host: str, port: int):
        self.base = f"http://{host}:{port}"
        self.http = httpx.AsyncClient(timeout=5.0)

    async def get_peers(self) -> list[Peer]:
        try:
            r = await self.http.get(f"{self.base}/peers")
            r.raise_for_status()
            return [Peer(**p) for p in r.json()]
        except Exception as e:
            print(f"[CLIENT] get_peers error: {e}")
            return []

    async def get_relay(self) -> RelayInfo:
        try:
            r = await self.http.get(f"{self.base}/relay")
            r.raise_for_status()
            data = r.json()
            return RelayInfo(
                peer_id=data["peer_id"],
                name=data.get("name", data["peer_id"]),
            )
        except Exception as e:
            print(f"[CLIENT] get_relay error: {e}")
            return RelayInfo(peer_id="unknown", name="unknown")

    async def send_message(self, to: str, text: str) -> str:
        try:
            r = await self.http.post(
                f"{self.base}/send",
                json={"to": to, "text": text},
            )
            return r.json().get("message_id", "")
        except Exception as e:
            print(f"[CLIENT] send error: {e}")
            return ""

    async def stream_events(self):
        """
        Читать SSE поток от Backend1.
        Формат строк: data: {"type": "peer:joined", "data": {...}}
        """
        url = f"{self.base}/stream"
        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", url) as response:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                try:
                                    event = json.loads(line[6:])
                                    if event.get("type") != "ping":
                                        yield event
                                except json.JSONDecodeError:
                                    continue
            except Exception as e:
                print(f"[CLIENT] Stream disconnected: {e}")
                await asyncio.sleep(2)

    async def health_check(self) -> bool:
        try:
            r = await self.http.get(f"{self.base}/health")
            return r.status_code == 200
        except Exception:
            return False
