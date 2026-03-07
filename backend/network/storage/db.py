import sqlite3
import os
import json
from cryptography.fernet import Fernet

# Ключ генерируется один раз при старте ноды
# В продакшене — из ENV или key exchange
_key = os.getenv("STORAGE_KEY", "").encode()
if not _key:
    _key = Fernet.generate_key()
    print(f"[CRYPTO] WARNING: no STORAGE_KEY in ENV, generated random key.")
    print(f"[CRYPTO] Nodes won't read each other's DB — это нормально для демо.")
_fernet = Fernet(_key)


def init_db(db_path: str = None):
    if db_path is None:
        db_path = os.getenv("DB_PATH", "messages.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            from_id TEXT,
            to_field TEXT,
            text_enc BLOB,
            timestamp REAL,
            encrypted INTEGER
        )
    """)
    conn.commit()
    return conn


def save_message(conn, msg: dict):
    try:
        text_enc = _fernet.encrypt(msg["text"].encode())
        conn.execute(
            "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?)",
            (msg["id"], msg["from_id"], msg.get("to", "broadcast"),
             text_enc, msg["timestamp"], 1)
        )
        conn.commit()
    except Exception as e:
        print(f"[DB] save_message error: {e}")


def load_messages(conn, limit: int = 100) -> list[dict]:
    try:
        rows = conn.execute(
            "SELECT id, from_id, to_field, text_enc, timestamp "
            "FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        result = []
        for row in reversed(rows):
            try:
                text = _fernet.decrypt(row[3]).decode()
            except Exception:
                text = "[encrypted]"
            result.append({
                "id": row[0],
                "from_id": row[1],
                "to": row[2],
                "text": text,
                "timestamp": row[4],
                "encrypted": True
            })
        return result
    except Exception as e:
        print(f"[DB] load_messages error: {e}")
        return []
