# gps_device/device.py
import os
import time
import threading
import asyncio
from dotenv import load_dotenv

from .rxtx_buffer import RxTxBuffer
from .radio_module.transmitter import WebSocketTransmitter
from .radio_module.packet import TelemetryPacket, PacketCodec, make_packet

load_dotenv()


class GPSDevice:
    """
    Simulated GPS device.
      - Owns RxTx buffer
      - On .on(): instantiates transmitter and starts worker
      - Worker pulls telemetry dicts from buffer and calls make_packet(...)
      - Transmitter handles codec + sending (WebSocket only)
    """

    def __init__(self, device_id: str, server_url: str, auth_token: str,
                 method: str = "ws", interval: float = 0.1):
        self.device_id = device_id
        self.server_url = server_url
        self.auth_token = auth_token
        self.method = method
        self.interval = interval
        self.buffer = RxTxBuffer()
        self._stop = threading.Event()
        self.thread = None
        self.transmitter = None
        self.codec = PacketCodec()  # reuse one codec instance

    @classmethod
    def from_env(cls):
        """Factory: build GPSDevice from .env/.config"""
        device_id = os.getenv("DEVICE_ID", "sim-0000")
        server_url = os.getenv("SERVER_URL", "ws://localhost:5000")
        auth_token = os.getenv("AUTH_TOKEN", "")
        interval = float(os.getenv("UPDATE_INTERVAL", 1.0))
        return cls(device_id, server_url, auth_token, method="ws", interval=interval)

    # -------------------- Worker (single event loop) --------------------

    def _worker(self):
        """Own an asyncio loop in this thread."""
        asyncio.run(self._async_worker())

    async def _async_worker(self):
        """Async worker: connect once, then send packets on same loop."""
        if self.method != "ws":
            print(f"[ERROR] Unsupported method: {self.method}")
            return

        # Create transmitter once
        self.transmitter = WebSocketTransmitter(
            self.server_url,
            self.auth_token,
            self.device_id,
            codec=self.codec
        )

        try:
            # 1) Connect once on this loop
            await self.transmitter.connect()

            # 2) Pump buffer -> packet -> send
            while not self._stop.is_set():
                # Offload blocking buffer.read() so event loop stays responsive
                data = await asyncio.to_thread(self.buffer.read, self.interval)
                if data is None:
                    continue

                # data: {"lat","lon","speed","heading", optional route/vehicle_reg/driver_*/ts}
                pkt: TelemetryPacket = make_packet(
                    device_id=self.device_id,
                    lat=float(data["lat"]),
                    lon=float(data["lon"]),
                    speed=float(data["speed"]),
                    heading=float(data["heading"]),
                    route=str(data.get("route", "0")),
                    vehicle_reg=data.get("vehicle_reg", self.device_id),
                    driver_id=data.get("driver_id", f"sim-{self.device_id}"),
                    driver_name=data.get("driver_name", {"first": "Sim", "last": self.device_id}),
                    ts=data.get("ts") or data.get("timestamp"),
                )

                await self.transmitter.send(pkt)

        except Exception as e:
            print(f"[ERROR] GPSDevice worker failed: {e}")
        finally:
            try:
                await self.transmitter.close()
            except Exception:
                pass

    # -------------------- Lifecycle --------------------

    def on(self):
        """Turn on device (start worker thread)."""
        if not self.thread or not self.thread.is_alive():
            self._stop.clear()
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
            print("[INFO] GPSDevice ON")

    def off(self):
        """Turn off device (stop worker and close transmitter)."""
        self._stop.set()
        if self.thread:
            self.thread.join()
        print("[INFO] GPSDevice OFF")
