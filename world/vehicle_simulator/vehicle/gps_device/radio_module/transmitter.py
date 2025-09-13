# world/vehicle/gps_device/radio_module/transmitter.py
import asyncio
from typing import Optional

import websockets

from .packet import TelemetryPacket, PacketCodec
from world.vehicle_simulator.utils.common.ws_utils import to_ws_url


class Transmitter:
    async def connect(self):  # pragma: no cover
        raise NotImplementedError

    async def send(self, pkt: TelemetryPacket):  # pragma: no cover
        raise NotImplementedError

    async def close(self):  # pragma: no cover
        raise NotImplementedError


class WebSocketTransmitter(Transmitter):
    """
    WebSocket transport. Uses text frames for JSON codec, binary otherwise.
    Also exposes request_close()/force_close() so other threads can nudge
    the socket shut to unblock the event loop during shutdown.
    """
    def __init__(self, server_url: str, token: str, device_id: str, codec: PacketCodec):
        self.server_url = server_url
        self.token = token
        self.device_id = device_id
        self.codec = codec

        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._closing: bool = False

    async def connect(self):
        # Build full WS URL with /device and query parameters.
        url = to_ws_url(self.server_url, self.token, self.device_id)
        self._loop = asyncio.get_running_loop()
        self._ws = await websockets.connect(url, open_timeout=10)
        return self._ws

    async def send(self, pkt: TelemetryPacket):
        if self._ws is None:
            raise RuntimeError("Transmitter not connected")
        
        # Hook for passenger integration (ultra-lightweight)
        try:
            from ....models.passenger_integration import hook_telemetry_packet
            hook_telemetry_packet(pkt)
        except ImportError:
            pass  # Passenger integration not available
        except Exception:
            pass  # Fail silently to avoid disrupting telemetry
        
        try:
            await self._ws.send(self.codec.encode_text(pkt))
        except Exception:
            await self._ws.send(self.codec.encode_bytes(pkt))

    async def close(self):
        ws = self._ws
        self._ws = None
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                # best-effort close
                pass

    # ---------- cooperative shutdown helpers ----------

    def request_close(self) -> None:
        """
        Schedule a graceful ws.close() on the owning event loop.
        Safe to call from another thread.
        """
        loop, ws = self._loop, self._ws
        if not loop or not ws:
            return

        def _do():
            try:
                if not ws.closed:
                    asyncio.create_task(ws.close(code=1000))
            except Exception:
                pass

        try:
            loop.call_soon_threadsafe(_do)
        except Exception:
            pass

    def force_close(self) -> None:
        """
        Best-effort immediate close to break blocking I/O.
        Safe to call from another thread.
        """
        ws = self._ws
        try:
            transport = getattr(ws, "transport", None) if ws else None
            if transport:
                transport.close()
        except Exception:
            pass
