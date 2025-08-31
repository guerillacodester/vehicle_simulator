import time
from typing import Dict, Any
from dataclasses import dataclass, asdict

class BaseCodec:
    def encode(self, packet: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    def decode(self, raw: bytes) -> Dict[str, Any]:
        raise NotImplementedError

@dataclass
class TelemetryPacket:
    """
    Core telemetry packet contract.
    Encapsulates metadata + telemetry before transmission.
    """
    device_id: str
    timestamp: float
    telemetry: dict

    def to_dict(self) -> dict:
        """Convert to dict for encoding/transmission."""
        return asdict(self)

    @classmethod
    def build(cls, device_id: str, telemetry: dict):
        """Helper to quickly create a packet with current timestamp."""
        return cls(
            device_id=device_id,
            timestamp=time.time(),
            telemetry=telemetry
        )