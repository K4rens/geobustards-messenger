from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.router import create_router
from bridge import EventBridge
from config import settings
from errors import BadRequestError, ServiceNotReadyError
from ws.handler import ws_endpoint
from ws.hub import WsHub


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

    @app.exception_handler(BadRequestError)
    async def handle_bad_request(_: Request, exc: BadRequestError):
        return JSONResponse(status_code=400, content={"error": exc.message})

    @app.exception_handler(ServiceNotReadyError)
    async def handle_not_ready(_: Request, __: ServiceNotReadyError):
        return JSONResponse(status_code=503, content={"error": "not ready"})

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        first = exc.errors()[0]["msg"] if exc.errors() else "invalid request"
        return JSONResponse(status_code=400, content={"error": first})

    @app.exception_handler(Exception)
    async def handle_internal(_: Request, exc: Exception):
        print(f"[ERROR] {exc}")
        return JSONResponse(status_code=500, content={"error": "internal"})

    @app.websocket("/ws")
    async def ws_route(websocket: WebSocket):
        await ws_endpoint(websocket, hub)

    @app.get("/health")
    async def root_health():
        node_id = await network.get_node_id()
        return {"status": "ok", "node_id": node_id, "ws_clients": hub.count()}

    router = create_router(network, hub)
    app.include_router(router, prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.API_PORT)
