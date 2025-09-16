#!/usr/bin/env python3
"""
Engine Block
------------

Threaded engine simulation loop with state management.

- Loads a speed model via sim_speed_model.load_speed_model
- Runs in a background thread
- Each tick, updates speed, distance, and time
- Writes diagnostics into EngineBuffer
- Uses DeviceState for proper lifecycle management
"""

import threading
import time
from typing import Any, Dict

from arknet_transit_simulator.vehicle.engine.engine_buffer import EngineBuffer
from arknet_transit_simulator.vehicle.base_component import BaseComponent
from arknet_transit_simulator.core.states import DeviceState


class Engine(BaseComponent):
    def __init__(self, vehicle_id: str, model: Any, buffer: EngineBuffer, tick_time: float = 0.1):
        """
        :param vehicle_id: Vehicle ID string (e.g., "ZR1101")
        :param model: Speed model instance (with .update())
        :param buffer: EngineBuffer instance for diagnostics
        :param tick_time: Tick duration in seconds
        """
        # Initialize BaseComponent with DeviceState
        super().__init__(vehicle_id, "Engine", DeviceState.OFF)
        
        self.model = model
        self.buffer = buffer
        self.tick_time = tick_time

        self._thread: threading.Thread = None
        self._stop_event = threading.Event()

        # cumulative stats
        self.total_distance = 0.0  # km
        self.total_time = 0.0      # s

    async def _start_implementation(self) -> bool:
        """Start the engine simulation thread."""
        try:
            if self._thread and self._thread.is_alive():
                return True  # already running
            
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            self.logger.info(f"Engine for {self.component_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start engine for {self.component_id}: {e}")
            return False

    async def _stop_implementation(self) -> bool:
        """Stop the engine simulation thread."""
        try:
            self._stop_event.set()
            if self._thread:
                self._thread.join(timeout=2.0)
                if self._thread.is_alive():
                    self.logger.warning(f"Engine thread for {self.component_id} did not stop cleanly")
                    return False
            
            self.logger.info(f"Engine for {self.component_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping engine for {self.component_id}: {e}")
            return False
    
    # Keep backward compatibility with existing on/off methods
    def on(self):
        """Start the engine simulation thread (legacy sync method)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                task = loop.create_task(self.start())
                return True  # Return immediately, don't wait
            else:
                return loop.run_until_complete(self.start())
        except RuntimeError:
            # No event loop running, create one
            return asyncio.run(self.start())

    def off(self):
        """Stop the engine simulation thread (legacy sync method)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                task = loop.create_task(self.stop())
                return True  # Return immediately, don't wait
            else:
                return loop.run_until_complete(self.stop())
        except RuntimeError:
            # No event loop running, create one
            return asyncio.run(self.stop())

    def _run_loop(self):
        """Main loop: run until stopped."""
        while not self._stop_event.is_set():
            result = self.model.update()

            # Prefer explicit velocity_mps if provided (physics); fallback to legacy 'velocity'
            if isinstance(result, dict):
                velocity_mps = result.get("velocity_mps", result.get("velocity", 0.0))
            else:
                velocity_mps = float(result)

            # accumulate distance (km) and time (s) using m/s -> km: divide by 1000
            self.total_distance += (velocity_mps * self.tick_time) / 1000.0
            self.total_time += self.tick_time

            # write entry to buffer (explicit m/s; keep legacy compatibility key cruise_speed for now but clarify units)
            entry: Dict[str, Any] = {
                "device_id": self.component_id,
                "timestamp": time.time(),
                "cruise_speed_mps": velocity_mps,
                "cruise_speed": velocity_mps,  # legacy; now m/s
                "distance": self.total_distance,  # km
                "time": self.total_time,
            }
            # If physics model provided extended diagnostics, include them under namespaced key
            if isinstance(result, dict) and any(k in result for k in ("acceleration", "phase", "progress", "segment_index")):
                physics_block = {
                    "accel": result.get("acceleration"),
                    "phase": result.get("phase"),
                    "progress": result.get("progress"),
                    "segment_index": result.get("segment_index"),
                }
                entry["physics"] = physics_block
            self.buffer.write(entry)

            time.sleep(self.tick_time)
