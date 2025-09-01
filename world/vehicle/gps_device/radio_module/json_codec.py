import json
from .base_codec import BaseCodec
from .packet import TelemetryPacket

class JsonCodec(BaseCodec):
    def encode(self, packet: TelemetryPacket) -> bytes:
        return json.dumps(packet.__dict__).encode("utf-8")

    def decode(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8"))
