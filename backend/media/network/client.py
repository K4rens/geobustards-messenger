import httpx

from errors import BadRequestError, ServiceNotReadyError
from models import ChatMessage, Peer, RelayInfo
from network.interface import NetworkClient


class RealClient(NetworkClient):
    def __init__(self, host: str, port: int):
        self.base = f"http://{host}:{port}"
        self.http = httpx.AsyncClient(timeout=15.0)

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base}{path}"
        try:
            response = await self.http.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 400:
                raise BadRequestError(self._error_message(exc.response, "invalid request")) from exc
            if status_code == 503:
                raise ServiceNotReadyError() from exc
            if status_code >= 500:
                raise ServiceNotReadyError() from exc
            raise RuntimeError(f"Unexpected upstream status code: {status_code}") from exc
        except httpx.RequestError as exc:
            raise ServiceNotReadyError() from exc

    @staticmethod
    def _error_message(response: httpx.Response, fallback: str) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                error_value = data.get("error")
                if isinstance(error_value, str) and error_value:
                    return error_value
        except ValueError:
            pass
        return fallback

    async def get_peers(self) -> list[Peer]:
        response = await self._request("GET", "/peers")
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Invalid peers payload")
        return [Peer(**item) for item in payload]

    async def get_relay(self) -> RelayInfo:
        response = await self._request("GET", "/relay")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid relay payload")
        return RelayInfo(**payload)

    async def get_messages(self) -> list[ChatMessage]:
        response = await self._request("GET", "/messages")
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Invalid messages payload")
        return [ChatMessage(**item) for item in payload]

    async def send_message(self, to: str, text: str) -> str:
        response = await self._request("POST", "/send", json={"to": to, "text": text})
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid send payload")
        message_id = payload.get("message_id")
        if not isinstance(message_id, str) or not message_id:
            raise RuntimeError("Missing message_id in send response")
        return message_id

    async def send_file(self, to: str, file_data: bytes, filename: str) -> str:
        files = {"file": (filename, file_data, "application/octet-stream")}
        data = {"to": to}
        response = await self._request("POST", "/send_file", data=data, files=files)
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid send_file payload")
        file_id = payload.get("file_id") or payload.get("message_id")
        if not isinstance(file_id, str) or not file_id:
            raise RuntimeError("Missing file_id in send_file response")
        return file_id

    async def get_files(self) -> list[dict]:
        response = await self._request("GET", "/files")
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Invalid files payload")
        return [item for item in payload if isinstance(item, dict)]

    async def get_file(self, file_id: str) -> bytes:
        response = await self._request("GET", f"/file/{file_id}")
        return response.content

    async def send_signal(self, to: str, signal_type: str, payload: dict) -> str:
        response = await self._request(
            "POST",
            "/signal",
            json={"to": to, "signal_type": signal_type, "payload": payload},
        )
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Invalid signal payload")
        signal_id = data.get("signal_id") or data.get("message_id") or data.get("id")
        if not isinstance(signal_id, str) or not signal_id:
            raise RuntimeError("Missing signal_id in signal response")
        return signal_id

    async def get_events(self) -> list[dict]:
        response = await self._request("GET", "/events")
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Invalid events payload")
        return [event for event in payload if isinstance(event, dict)]

    async def get_node_id(self) -> str:
        response = await self._request("GET", "/health")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid health payload")
        node_id = payload.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            raise RuntimeError("Missing node_id in health response")
        return node_id
