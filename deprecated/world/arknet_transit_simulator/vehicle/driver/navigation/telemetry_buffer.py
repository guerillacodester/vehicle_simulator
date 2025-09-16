#!/usr/bin/env python3
"""
TelemetryBuffer
---------------
Thread-safe circular buffer for navigator-produced telemetry.

Each entry is a dict like:
{
  "deviceId": str,
  "timestamp": float,      # epoch time
  "lon": float,
  "lat": float,
  "bearing": float,        # degrees
  "speed": float,          # km/h
  "time": float,           # s (elapsed)
  "distance": float        # km (cumulative)
}
"""
import threading
from typing import Any, Dict, Optional

class TelemetryBuffer:
    def __init__(self, size: int = 1000):
        self.size = size
        self.buffer = [None] * size
        self.start = 0
        self.count = 0
        self.lock = threading.Lock()

    def write(self, entry: Dict[str, Any]) -> None:
        with self.lock:
            idx = (self.start + self.count) % self.size
            self.buffer[idx] = entry
            if self.count == self.size:
                self.start = (self.start + 1) % self.size
            else:
                self.count += 1

    def read(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            if self.count == 0:
                return None
            entry = self.buffer[self.start]
            self.buffer[self.start] = None
            self.start = (self.start + 1) % self.size
            self.count -= 1
            return entry

    def peek(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            if self.count == 0:
                return None
            return self.buffer[self.start]

    def __len__(self) -> int:
        with self.lock:
            return self.count

    def __repr__(self) -> str:
        return f"<TelemetryBuffer size={self.size} count={self.count}>"
