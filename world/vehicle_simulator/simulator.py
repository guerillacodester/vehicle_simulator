"""Vehicle Simulator Core Module (Clean Architecture).

This replaces the previous `clean_simulator` module; name aligned with
user preference for clarity and conventional import path.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CleanVehicleSimulator:
    """Minimal orchestrator wrapper for depot + dispatcher lifecycle."""

    def __init__(self, api_url: str = "http://localhost:8000") -> None:
        self.api_url = api_url
        self.dispatcher = None
        self.depot = None
        self._running = False

    async def initialize(self) -> bool:
        try:
            from world.vehicle_simulator.core.depot_manager import DepotManager
            from world.vehicle_simulator.core.dispatcher import Dispatcher

            logger.info("Initializing clean simulator (depot + dispatcher)...")
            self.dispatcher = Dispatcher("FleetDispatcher", self.api_url)
            self.depot = DepotManager("MainDepot")
            self.depot.set_dispatcher(self.dispatcher)

            ok = await self.depot.initialize()
            if not ok:
                logger.error("Depot initialization failed")
                return False
            logger.info("Clean simulator initialized ✔")
            return True
        except Exception as e:  # pragma: no cover (defensive)
            logger.error(f"Initialization error: {e}")
            return False

    async def run(self, duration: Optional[float] = None) -> None:
        if not self.depot:
            logger.error("Simulator not initialized")
            return
        self._running = True
        if duration is None:
            logger.info("Running indefinitely (Ctrl+C to stop)...")
            try:
                while self._running:
                    await asyncio.sleep(1.0)
            except KeyboardInterrupt:
                logger.info("Interrupt received")
        else:
            logger.info(f"Running for {duration} seconds...")
            try:
                await asyncio.sleep(duration)
            except KeyboardInterrupt:
                logger.info("Interrupted before duration complete")
        await self.shutdown()

    async def shutdown(self) -> None:
        if self._running:
            self._running = False
        logger.info("Shutting down clean simulator...")
        try:
            if self.depot:
                await self.depot.shutdown()
            if self.dispatcher:
                await self.dispatcher.shutdown()
        finally:
            logger.info("Shutdown complete")

    async def get_vehicle_assignments(self):
        if not self.dispatcher:
            return []
        return await self.dispatcher.get_vehicle_assignments()

    async def get_route_info(self, route_id: str):
        if not self.dispatcher:
            return None
        return await self.dispatcher.get_route_info(route_id)
