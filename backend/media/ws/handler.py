from fastapi import WebSocket, WebSocketDisconnect
from ws.hub import WsHub


async def ws_endpoint(websocket: WebSocket, hub: WsHub):
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
