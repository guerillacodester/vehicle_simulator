import base64, json, os
from dataclasses import asdict
from .packet import TelemetryPacket, PacketCodec

class AESGCMCodec(PacketCodec):
    name = "aesgcm"

    def __init__(self, key_b64: str):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        self.key = base64.b64decode(key_b64)
        if len(self.key) not in (16, 24, 32):
            raise ValueError("AES-GCM key must be 128/192/256-bit (base64).")
        self.aesgcm = AESGCM(self.key)

    def encode_text(self, pkt: TelemetryPacket) -> str:
        raise TypeError("AESGCMCodec produces binary; use encode_bytes().")

    def encode_bytes(self, pkt: TelemetryPacket) -> bytes:
        nonce = os.urandom(12)
        plaintext = json.dumps(asdict(pkt), separators=(",", ":")).encode("utf-8")
        ct = self.aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct
