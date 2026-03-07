import asyncio
import os
import uvicorn

from core.node import Node
from core.voice import VoiceCall
from routing.flooding import FloodRouter
from api.server import create_app, chat_history, _push_event
from storage.db import init_db, save_message, load_messages


def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def get_peers_from_env() -> list[str]:
    raw = get_env("PEERS", "")
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


async def main():
    node_id = get_env("NODE_ID", "node1")
    node_name = get_env("NODE_NAME", node_id)
    port = int(get_env("PORT", "9000"))
    api_port = int(get_env("API_PORT", "9001"))

    node = Node(node_id, node_name, port)
    flood = FloodRouter(node)
    node.flood_router = flood

    db_conn = init_db()

    # Загружаем историю при старте — история переживает перезапуск контейнера
    for msg in load_messages(db_conn):
        chat_history.append(msg)
    print(f"[BOOT] Loaded {len(chat_history)} messages from DB")

    async def on_chat(msg: dict):
        chat_history.append(msg)
        if len(chat_history) > 100:
            chat_history.pop(0)
        save_message(db_conn, msg)
        await _push_event({"type": "message:received", "data": msg})

    node.on_chat = on_chat

    async def on_file(msg: dict):
        from api.server import file_assembler
        if file_assembler is not None:
            await file_assembler.add_chunk(msg)

    node.on_file = on_file

    async def on_signal(msg: dict):
        # Handle call:invite signals
        if msg.get("signal_type") == "call:invite":
            await _push_event({
                "type": "call:incoming",
                "data": {
                    "from_id": msg.get("from_id"),
                    "call_id": msg.get("payload", {}).get("call_id"),
                    "peer_addr": msg.get("payload", {}).get("peer_addr"),
                    "peer_voice_port": msg.get("payload", {}).get("peer_voice_port"),
                }
            })
        await _push_event({
            "type": "signal:received",
            "data": {
                "from_id": msg.get("from_id"),
                "to": msg.get("to"),
                "signal_type": msg.get("signal_type"),
                "payload": msg.get("payload", {}),
            }
        })

    node.on_signal = on_signal

    await node.start()
    print(f"[BOOT] Node {node_id} started on :{port}")

    voice = VoiceCall()
    await voice.start_listener()
    print(f"[BOOT] Voice UDP on :9002")

    app = create_app(node, voice, db_conn=db_conn)
    config = uvicorn.Config(app, host="0.0.0.0", port=api_port, log_level="warning")

    await asyncio.sleep(2)
    peers = get_peers_from_env()
    if peers:
        print(f"[BOOT] Connecting to: {peers}")
        await node.connect_to_peers(peers)
    server = uvicorn.Server(config)
    print(f"[BOOT] API on :{api_port}")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
