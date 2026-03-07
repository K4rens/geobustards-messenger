from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from ws.hub import WsHub
from ws.handler import ws_endpoint
from api.router import create_router
from bridge import EventBridge


def create_app() -> FastAPI:
    hub = WsHub()

    if settings.USE_MOCK:
        from network.mock import MockClient
        network = MockClient()
        print("[BOOT] Using MOCK network client")
    else:
        from network.client import RealClient
        network = RealClient(settings.NETWORK_HOST, settings.NETWORK_PORT)
        print(f"[BOOT] Using REAL client -> {settings.NETWORK_HOST}:{settings.NETWORK_PORT}")

    bridge = EventBridge(network, hub)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await bridge.start()
        print(f"[BOOT] API ready on :{settings.API_PORT}")
        yield

    app = FastAPI(title="Mesh API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.websocket("/ws")
    async def ws_route(websocket: WebSocket):
        await ws_endpoint(websocket, hub)

    router = create_router(network, hub)
    app.include_router(router, prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.API_PORT)
