# transmitter.py
import websockets
from .packet import TelemetryPacket, PacketCodec
from common.ws_utils import to_ws_url  # import the helper

class Transmitter:
    async def connect(self): ...
    async def send(self, pkt: TelemetryPacket): ...
    async def close(self): ...

class WebSocketTransmitter(Transmitter):
    """
    WebSocket transport. Uses text frames for JSON codec, binary otherwise.
    """
    def __init__(self, server_url: str, token: str, device_id: str, codec: PacketCodec):
        self.server_url = server_url
        self.token = token
        self.device_id = device_id
        self.codec = codec
        self._ws = None

    async def connect(self):
        # Build the full WS URL with /device and query parameters.
        url = to_ws_url(self.server_url, self.token, self.device_id)
        self._ws = await websockets.connect(url, open_timeout=10)
        return self._ws

    async def send(self, pkt: TelemetryPacket):
        if self._ws is None:
            raise RuntimeError("Transmitter not connected")
        try:
            await self._ws.send(self.codec.encode_text(pkt))
        except Exception:
            await self._ws.send(self.codec.encode_bytes(pkt))

    async def close(self):
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
