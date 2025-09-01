#!/usr/bin/env python3
"""
Engine Block
------------

Threaded engine simulation loop.

- Loads a speed model via sim_speed_model.load_speed_model
- Runs in a background thread
- Each tick, updates speed, distance, and time
- Writes diagnostics into EngineBuffer
"""

import threading
import time
from typing import Any, Dict

from world.vehicle.engine.engine_buffer import EngineBuffer


class Engine:
    def __init__(self, vehicle_id: str, model: Any, buffer: EngineBuffer, tick_time: float = 0.1):
        """
        :param vehicle_id: Vehicle ID string (e.g., "ZR1101")
        :param model: Speed model instance (with .update())
        :param buffer: EngineBuffer instance for diagnostics
        :param tick_time: Tick duration in seconds
        """
        self.vehicle_id = vehicle_id
        self.model = model
        self.buffer = buffer
        self.tick_time = tick_time

        self._thread: threading.Thread = None
        self._stop_event = threading.Event()

        # cumulative stats
        self.total_distance = 0.0  # km
        self.total_time = 0.0      # s

    def on(self):
        """Start the engine simulation thread."""
        if self._thread and self._thread.is_alive():
            return  # already running
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        # print(f"[INFO] Engine for {self.vehicle_id} turned ON")

    def off(self):
        """Stop the engine simulation thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        # print(f"[INFO] Engine for {self.vehicle_id} turned OFF")

    def _run_loop(self):
        """Main loop: run until stopped."""
        while not self._stop_event.is_set():
            result = self.model.update()

            if isinstance(result, dict):
                velocity = result.get("velocity", 0.0)
            else:
                velocity = float(result)

            # accumulate distance (km) and time (s)
            self.total_distance += (velocity * self.tick_time) / 3600
            self.total_time += self.tick_time

            # write entry to buffer
            entry: Dict[str, Any] = {
                "device_id": self.vehicle_id,
                "timestamp": time.time(),
                "cruise_speed": velocity,
                "distance": self.total_distance,
                "time": self.total_time,
            }
            self.buffer.write(entry)

            time.sleep(self.tick_time)
