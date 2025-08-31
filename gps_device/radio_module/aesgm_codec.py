import base64
from dataclasses import asdict
import json
import os
from gps_device.base import TelemetryPacket
from gps_device.radio_module.packet_codec import PacketCodec


class AESGCMCodec(PacketCodec):
    """
    Optional AEAD codec (binary). Prefixes 12-byte nonce.
    Requires server support for binary frames + key management.
    """
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