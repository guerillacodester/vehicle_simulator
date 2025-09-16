import json
import os
import base64
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Dict


@dataclass
class TelemetryPacket:
    """
    Telemetry schema — must match what the server backend expects.
    """
    deviceId: str
    route: str
    vehicleReg: str
    driverId: str
    driverName: Dict[str, str]   # {"first": ..., "last": ...}
    timestamp: str               # ISO8601 UTC string
    lat: float
    lon: float
    speed: float
    heading: float

def make_packet(device_id: str,
                lat: float,
                lon: float,
                speed: float,
                heading: float,
                route: str = "0",
                vehicle_reg: Optional[str] = None,
                driver_id: Optional[str] = None,
                driver_name: Optional[Dict[str, str]] = None,
                ts: Optional[str] = None) -> TelemetryPacket:
    """
    Factory to build a TelemetryPacket in the correct format.
    Handles rounding + timestamp automatically.
    """
    return TelemetryPacket(
        deviceId=device_id,
        route=str(route),  # ensure string
        vehicleReg=vehicle_reg or device_id,
        driverId=driver_id or f"sim-{device_id}",
        driverName=driver_name or {"first": "Sim", "last": device_id},
        timestamp=ts or datetime.now(timezone.utc).isoformat(),
        lat=round(lat, 6),
        lon=round(lon, 6),
        speed=round(speed, 2),
        heading=round(heading, 1),
    )

class PacketCodec:
    """Default JSON/text codec (server-compatible today)."""
    name = "json"

    def encode_text(self, pkt: TelemetryPacket) -> str:
        return json.dumps(asdict(pkt), separators=(",", ":"))

    def encode_bytes(self, pkt: TelemetryPacket) -> bytes:
        return self.encode_text(pkt).encode("utf-8")
