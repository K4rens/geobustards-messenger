from pydantic import BaseModel


class Peer(BaseModel):
    peer_id: str
    name: str
    address: str
    online: bool = True


class RelayInfo(BaseModel):
    peer_id: str
    name: str


class ChatMessage(BaseModel):
    id: str
    from_id: str
    to: str
    text: str
    timestamp: float
    encrypted: bool = True


class SendRequest(BaseModel):
    to: str = "broadcast"
    text: str


class WsEvent(BaseModel):
    type: str
    data: dict = {}
