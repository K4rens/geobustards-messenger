import asyncio
import time
import uuid
import hashlib
import base64
from typing import Any

from fastapi import FastAPI, UploadFile, File
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from core.node import Node

node = None
chat_history: list[dict[str, Any]] = []
_event_queue: list[dict[str, Any]] = []
_CHAT_FIELDS = {"id", "from_id", "to", "text", "timestamp", "encrypted"}
file_assembler = None
_db_conn = None


class FileAssembler:
    def __init__(self, push_event_fn):
        self._received_files: dict[str, dict] = {}
        self._file_data: dict[str, bytes] = {}
        self._push_event = push_event_fn
        asyncio.create_task(self._cleanup_loop())

    async def add_chunk(self, msg: dict):
        file_id = msg.get("file_id", "")

        # Не больше 10 незавершённых передач
        incomplete = [fid for fid, f in self._received_files.items()
                      if isinstance(f.get("chunks"), dict)]
        if len(incomplete) >= 10 and file_id not in self._received_files:
            oldest = min(incomplete, key=lambda fid: self._received_files[fid].get("started", 0))
            del self._received_files[oldest]
            self._file_data.pop(oldest, None)

        chunk_index = msg.get("chunk_index", 0)
        chunk_data = msg.get("data", "")

        if file_id not in self._received_files:
            self._received_files[file_id] = {
                "chunks": {},
                "metadata": {"filename": msg.get("filename", ""), "sha256": msg.get("sha256", "")},
                "total_chunks": msg.get("total_chunks", 0),
                "received": 0,
                "started": time.time(),
            }

        file = self._received_files[file_id]
        if not isinstance(file.get("chunks"), dict):
            return

        if chunk_index not in file["chunks"]:
            file["chunks"][chunk_index] = chunk_data
            file["received"] += 1
            await self._push_event({"type": "file:progress", "data": {
                "file_id": file_id,
                "filename": file["metadata"]["filename"],
                "received": file["received"],
                "total": file["total_chunks"],
            }})
            if file["received"] == file["total_chunks"]:
                await self._assemble_file(file_id)

    async def _assemble_file(self, file_id: str):
        file = self._received_files.get(file_id)
        if not file:
            return
        chunks = file.get("chunks", {})
        total = file.get("total_chunks", 0)
        chunk_data = []
        for i in range(total):
            if i not in chunks:
                return
            chunk_data.append(base64.b64decode(chunks[i]))
        full_data = b"".join(chunk_data)
        expected_sha256 = file["metadata"]["sha256"]
        actual_sha256 = hashlib.sha256(full_data).hexdigest()
        if expected_sha256 != actual_sha256:
            del self._received_files[file_id]
            return
        self._file_data[file_id] = full_data
        self._received_files[file_id] = {
            "file_id": file_id,
            "filename": file["metadata"]["filename"],
            "size": len(full_data),
            "sha256": actual_sha256,
            "complete": True,
            "chunks": total,
        }
        await self._push_event({"type": "file:received", "data": self._received_files[file_id]})

    def get_status(self, file_id: str) -> dict:
        file = self._received_files.get(file_id)
        if not file:
            return {"error": "not found"}
        if not isinstance(file.get("chunks"), dict):
            # уже собран
            return {**file, "missing_chunks": [], "received_chunks": file.get("chunks", 0)}
        total = file["total_chunks"]
        received_idxs = set(file["chunks"].keys())
        missing = [i for i in range(total) if i not in received_idxs]
        return {
            "file_id": file_id,
            "filename": file["metadata"]["filename"],
            "total_chunks": total,
            "received_chunks": file["received"],
            "missing_chunks": missing,
            "complete": False,
            "sha256": file["metadata"]["sha256"],
        }

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(30)
            now = time.time()
            cutoff = now - 600
            to_remove = [
                fid for fid, f in self._received_files.items()
                if f.get("started", 0) < cutoff or (f.get("complete") and f.get("started", now) < now - 300)
            ]
            for fid in to_remove:
                del self._received_files[fid]
                self._file_data.pop(fid, None)


def _clean_message(msg: dict) -> dict:
    return {k: v for k, v in msg.items() if k in _CHAT_FIELDS}


def create_app(node_instance: "Node", voice_instance=None, db_conn=None) -> FastAPI:
    global node, file_assembler, _db_conn
    node = node_instance
    _db_conn = db_conn
    _voice = voice_instance
    file_assembler = FileAssembler(_push_event)
    app = FastAPI(title="Mesh Network API")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content={"error": exc.errors()[0]["msg"] if exc.errors() else "invalid request"}
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request, exc):
        print(f"[API] Unhandled error: {exc}")
        return JSONResponse(status_code=500, content={"error": "internal"})

    @app.get("/health")
    async def health():
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        return {"status": "ok", "node_id": node.id, "peers_count": len(node.get_peers())}

    @app.get("/peers")
    async def get_peers():
        if node is None:
            return []
        peers = node.get_peers()
        result = []
        for p in peers:
            peer_data = dict(p)
            peer_data["rtt_ms"] = node.get_rtt_ms(p["peer_id"])
            result.append(peer_data)
        return result

    @app.get("/relay")
    async def get_relay():
        if node is None:
            return {"peer_id": "unknown", "name": "unknown"}
        relay = node.get_relay()
        if relay:
            return {"peer_id": relay["peer_id"], "name": relay["name"]}
        return {"peer_id": node.id, "name": node.name}

    @app.get("/messages")
    async def get_messages():
        if node is None:
            return []
        return [_clean_message(m) for m in chat_history]

    @app.post("/send")
    async def send_message(body: dict):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        if not body.get("text", "").strip():
            return JSONResponse(status_code=400, content={"error": "text is required"})
        msg = {
            "id": str(uuid.uuid4()),
            "type": "CHAT",
            "from_id": node.id,
            "to": body.get("to", "broadcast"),
            "text": body.get("text", ""),
            "timestamp": time.time(),
            "ttl": 7,
            "encrypted": True,
        }
        chat_history.append(msg)
        if len(chat_history) > 100:
            chat_history.pop(0)
        if _db_conn is not None:
            from storage.db import save_message as _save_message
            try:
                _save_message(_db_conn, msg)
            except Exception as _e:
                print(f"[API] DB save error: {_e}")
        if node.flood_router:
            await node.flood_router.process(msg, "", is_local=True)
        else:
            await node.broadcast_message(msg)
        return {"message_id": msg["id"]}

    @app.post("/send_file")
    async def send_file(file: UploadFile = File(...)):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            return JSONResponse(status_code=400, content={"error": "file size exceeds 50MB limit"})
        file_id = str(uuid.uuid4())
        filename = file.filename or "unnamed"
        sha256 = hashlib.sha256(content).hexdigest()
        CHUNK_SIZE = 32 * 1024
        total_chunks = (len(content) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for i in range(total_chunks):
            chunk = content[i * CHUNK_SIZE: (i + 1) * CHUNK_SIZE]
            chunk_msg = {
                "id": str(uuid.uuid4()),
                "type": "FILE_CHUNK",
                "from_id": node.id,
                "to": "broadcast",
                "file_id": file_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "data": base64.b64encode(chunk).decode(),
                "sha256": sha256,
                "timestamp": time.time(),
                "ttl": 7,
            }
            if node.flood_router:
                await node.flood_router.process(chunk_msg, "", is_local=True)
                await asyncio.sleep(0.05)
            else:
                await node.broadcast_message(chunk_msg)
        return {"file_id": file_id, "chunks": total_chunks}

    @app.get("/files")
    async def get_files():
        if node is None:
            return []
        return list(file_assembler._received_files.values())

    @app.get("/file/{file_id}/status")
    async def get_file_status(file_id: str):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        return file_assembler.get_status(file_id)

    @app.post("/file/{file_id}/request_retry")
    async def request_file_retry(file_id: str, body: dict):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        status = file_assembler.get_status(file_id)
        if "error" in status:
            return JSONResponse(status_code=404, content={"error": "file not found"})
        missing = status.get("missing_chunks", [])
        from_node = body.get("from_node", "")
        if not from_node:
            return JSONResponse(status_code=400, content={"error": "from_node is required"})
        signal_msg = {
            "id": str(uuid.uuid4()),
            "type": "SIGNAL",
            "from_id": node.id,
            "to": from_node,
            "signal_type": "file:retry_request",
            "payload": {"file_id": file_id, "missing_chunks": missing},
            "ttl": 7,
            "timestamp": time.time(),
        }
        if node.flood_router:
            await node.flood_router.process(signal_msg, "", is_local=True)
        else:
            await node.broadcast_message(signal_msg)
        return {"requested": missing}

    @app.get("/file/{file_id}")
    async def get_file(file_id: str):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        if file_id not in file_assembler._received_files:
            return JSONResponse(status_code=404, content={"error": "file not found"})
        data = file_assembler._file_data.get(file_id)
        if data is None:
            return JSONResponse(status_code=404, content={"error": "file not assembled yet"})
        filename = file_assembler._received_files[file_id].get("filename", "file")
        return Response(content=data, media_type="application/octet-stream",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    @app.post("/signal")
    async def send_signal(body: dict):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        if not body.get("to") or not body.get("signal_type"):
            return JSONResponse(status_code=400, content={"error": "to and signal_type are required"})
        msg = {
            "id": str(uuid.uuid4()),
            "type": "SIGNAL",
            "from_id": node.id,
            "to": body["to"],
            "signal_type": body["signal_type"],
            "payload": body.get("payload", {}),
            "ttl": 7,
            "timestamp": time.time(),
        }
        if node.flood_router:
            await node.flood_router.process(msg, "", is_local=True)
        else:
            await node.broadcast_message(msg)
        return {"message_id": msg["id"]}

    # ── Voice call endpoints ──────────────────────────────────────────────────

    @app.post("/call/start")
    async def call_start(body: dict):
        if node is None:
            return JSONResponse(status_code=503, content={"error": "not ready"})
        to = body.get("to", "")
        peer_addr = body.get("peer_addr", "")
        peer_voice_port = int(body.get("peer_voice_port", 9002))
        if not to or not peer_addr:
            return JSONResponse(status_code=400, content={"error": "to and peer_addr are required"})

        call_id = await _voice.start_call(peer_addr, peer_voice_port) if _voice else str(uuid.uuid4())

        # Send call:invite signal
        invite_msg = {
            "id": str(uuid.uuid4()),
            "type": "SIGNAL",
            "from_id": node.id,
            "to": to,
            "signal_type": "call:invite",
            "payload": {
                "call_id": call_id,
                "peer_addr": peer_addr,
                "peer_voice_port": peer_voice_port,
            },
            "ttl": 7,
            "timestamp": time.time(),
        }
        if node.flood_router:
            await node.flood_router.process(invite_msg, "", is_local=True)
        else:
            await node.broadcast_message(invite_msg)

        return {"call_id": call_id, "status": "calling"}

    @app.post("/call/end")
    async def call_end(body: dict):
        call_id = body.get("call_id", "")
        if not call_id:
            return JSONResponse(status_code=400, content={"error": "call_id is required"})
        if _voice:
            await _voice.end_call(call_id)
        return {"status": "ended"}

    @app.get("/call/stats/{call_id}")
    async def call_stats(call_id: str):
        if _voice is None:
            return JSONResponse(status_code=503, content={"error": "voice not available"})
        stats = _voice.get_stats(call_id)
        if "error" in stats:
            return JSONResponse(status_code=404, content=stats)
        return stats

    @app.get("/call/active")
    async def call_active():
        if _voice is None:
            return []
        return _voice.get_active_calls()

    # ── Events ────────────────────────────────────────────────────────────────

    @app.get("/events")
    async def get_events():
        if node is None:
            return []
        raw = list(_event_queue)
        _event_queue[:] = []
        result = []
        for event in raw:
            if event.get("type") == "message:received":
                result.append({"type": event["type"], "data": _clean_message(event["data"])})
            else:
                result.append(event)
        return result

    return app


async def push_peer_event(event_type: str, peer: dict):
    if node is None:
        return
    await _push_event({"type": event_type, "data": peer})


async def _push_event(event: dict):
    if node is None:
        return
    _event_queue.append(event)
    if len(_event_queue) > 500:
        _event_queue.pop(0)
