import uuid
import time

from fastapi import APIRouter
from models import Peer, RelayInfo, ChatMessage, SendRequest
from network.interface import NetworkClient
from ws.hub import WsHub


def create_router(network: NetworkClient, hub: WsHub) -> APIRouter:
    router = APIRouter()
    history: list[ChatMessage] = []

    @router.get("/peers", response_model=list[Peer])
    async def get_peers():
        return await network.get_peers()

    @router.get("/relay", response_model=RelayInfo)
    async def get_relay():
        return await network.get_relay()

    @router.get("/messages", response_model=list[ChatMessage])
    async def get_messages():
        return history

    @router.post("/message")
    async def send_message(body: SendRequest):
        msg = ChatMessage(
            id=str(uuid.uuid4())[:8],
            from_id="api-gateway",
            to=body.to,
            text=body.text,
            timestamp=time.time(),
            encrypted=True,
        )
        history.append(msg)
        if len(history) > 100:
            history.pop(0)

        await network.send_message(body.to, body.text)
        await hub.broadcast_raw("message:received", msg.model_dump())

        return {"message_id": msg.id, "status": "sent"}

    @router.get("/health")
    async def health():
        ok = await network.health_check()
        return {
            "status": "ok" if ok else "degraded",
            "ws_clients": hub.count(),
            "network": "mock" if not ok else "connected",
        }

    return router
