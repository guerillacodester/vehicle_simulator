#!/usr/bin/env python3
"""
EngineBuffer
------------

Thread-safe circular buffer for engine diagnostics.

Each entry is a dict with:
    {
        "device_id": str,
        "timestamp": float,        # epoch time
        "cruise_speed": float,     # legacy alias (now m/s)
        "cruise_speed_mps": float, # primary velocity in m/s
        "distance": float,         # km traveled so far
        "time": float              # seconds elapsed
    }
"""

import threading
import time
from typing import Any, Dict, Optional


class EngineBuffer:
    def __init__(self, size: int = 100):
        """
        Initialize a circular buffer.

        :param size: maximum number of entries to hold before overwriting oldest
        """
        self.size = size
        self.buffer = [None] * size
        self.start = 0
        self.count = 0
        self.lock = threading.Lock()

    def write(self, entry: Dict[str, Any]) -> None:
        """
        Write a new entry into the buffer. If the buffer is full,
        the oldest entry is overwritten.

        :param entry: dictionary with engine diagnostics
        """
        with self.lock:
            idx = (self.start + self.count) % self.size
            self.buffer[idx] = entry
            if self.count == self.size:
                # overwrite oldest
                self.start = (self.start + 1) % self.size
            else:
                self.count += 1

    def read(self) -> Optional[Dict[str, Any]]:
        """
        Read and remove the oldest entry.

        :return: oldest entry dict, or None if empty
        """
        with self.lock:
            if self.count == 0:
                return None
            entry = self.buffer[self.start]
            self.buffer[self.start] = None
            self.start = (self.start + 1) % self.size
            self.count -= 1
            return entry

    def peek(self) -> Optional[Dict[str, Any]]:
        """
        Peek at the oldest entry without removing it.

        :return: oldest entry dict, or None if empty
        """
        with self.lock:
            if self.count == 0:
                return None
            return self.buffer[self.start]
    
    def read_latest(self) -> Optional[Dict[str, Any]]:
        """
        Read the most recent entry without removing it.

        :return: newest entry dict, or None if empty
        """
        with self.lock:
            if self.count == 0:
                return None
            # Most recent entry is at (start + count - 1) % size
            latest_idx = (self.start + self.count - 1) % self.size
            return self.buffer[latest_idx]

    def __len__(self) -> int:
        """Return number of entries currently in buffer."""
        with self.lock:
            return self.count

    def __repr__(self) -> str:
        return f"<EngineBuffer size={self.size} count={self.count}>"

# ---------------------------
# Manual smoke test
# ---------------------------
if __name__ == "__main__":
    buf = EngineBuffer(size=3)
    for i in range(5):
        buf.write({
            "tick": i,
            "device_id": "TEST",
            "timestamp": time.time(),
            "cruise_speed": 50.0,
            "distance": i * 0.1,
            "time": i * 0.1
        })
    print("Peek oldest:", buf.peek())
    while len(buf) > 0:
        print("Read:", buf.read())
