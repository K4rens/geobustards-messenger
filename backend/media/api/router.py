from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response

from models import ChatMessage, Peer, RelayInfo, SendRequest, SignalRequest
from network.interface import NetworkClient
from ws.hub import WsHub


def create_router(network: NetworkClient, hub: WsHub) -> APIRouter:
    router = APIRouter()

    @router.get("/peers", response_model=list[Peer])
    async def get_peers():
        return await network.get_peers()

    @router.get("/relay", response_model=RelayInfo)
    async def get_relay():
        return await network.get_relay()

    @router.get("/messages", response_model=list[ChatMessage])
    async def get_messages():
        return await network.get_messages()

    @router.post("/message")
    async def send_message(body: SendRequest):
        message_id = await network.send_message(body.to, body.text)
        return {"message_id": message_id}

    @router.post("/file")
    async def send_file(to: str = Form(...), file: UploadFile = File(...)):
        file_data = await file.read()
        filename = file.filename or "upload.bin"
        file_id = await network.send_file(to=to, file_data=file_data, filename=filename)
        return {"file_id": file_id}

    @router.get("/files")
    async def get_files():
        return await network.get_files()

    @router.get("/file/{file_id}")
    async def get_file(file_id: str):
        data = await network.get_file(file_id)
        return Response(content=data, media_type="application/octet-stream")

    @router.post("/signal")
    async def send_signal(body: SignalRequest):
        signal_id = await network.send_signal(body.to, body.signal_type, body.payload)
        return {"signal_id": signal_id}

    @router.get("/health")
    async def health():
        node_id = await network.get_node_id()
        return {"status": "ok", "node_id": node_id, "ws_clients": hub.count()}

    return router
