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
        
        # Start drivers boarding and GPS initialization
        await self._start_vehicle_operations()
        
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
    
    async def _start_vehicle_operations(self) -> None:
        """Start drivers boarding vehicles and initializing GPS devices."""
        try:
            logger.info("🚚 Starting vehicle operations...")
            
            # Get vehicle-driver assignments from dispatcher
            vehicle_assignments = await self.dispatcher.get_vehicle_assignments()
            driver_assignments = await self.dispatcher.get_driver_assignments()
            
            if not vehicle_assignments or not driver_assignments:
                logger.warning("No vehicle or driver assignments available")
                return
            
            # Start drivers for available assignments
            active_drivers = []
            for i in range(min(len(vehicle_assignments), len(driver_assignments))):
                vehicle_assignment = vehicle_assignments[i]
                driver_assignment = driver_assignments[i]
                
                logger.info(f"👤 Starting driver: {driver_assignment.driver_name} → {vehicle_assignment.vehicle_id} → {vehicle_assignment.route_id}")
                
                # Create and start vehicle driver
                driver = await self._create_and_start_driver(vehicle_assignment, driver_assignment)
                if driver:
                    active_drivers.append(driver)
            
            if active_drivers:
                logger.info(f"🎯 Started {len(active_drivers)} vehicle operations")
                self.active_drivers = active_drivers
            else:
                logger.warning("No drivers started successfully")
                
        except Exception as e:
            logger.error(f"Error starting vehicle operations: {e}")
            import traceback
            traceback.print_exc()
    
    async def _create_and_start_driver(self, vehicle_assignment, driver_assignment):
        """Create and start a vehicle driver with GPS device."""
        try:
            from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
            from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
            from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
            from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
            
            # Get route information
            route_info = await self.dispatcher.get_route_info(vehicle_assignment.route_id)
            if not route_info or not route_info.geometry:
                logger.error(f"No route geometry available for {vehicle_assignment.route_id}")
                return None
            
            # Create GPS device for this vehicle
            device_id = f"GPS-{vehicle_assignment.vehicle_id}"
            transmitter = WebSocketTransmitter(
                server_url="ws://localhost:5000",
                token=f"driver-{driver_assignment.driver_id}-token",
                device_id=device_id,
                codec=PacketCodec()
            )
            
            gps_device = GPSDevice(
                device_id=device_id,
                ws_transmitter=transmitter,
                plugin_config={
                    "plugin": "simulation",
                    "update_interval": 2.0,
                    "device_id": device_id
                }
            )
            
            # Create vehicle driver
            driver = VehicleDriver(
                driver_id=driver_assignment.driver_id,
                driver_name=driver_assignment.driver_name,
                vehicle_id=vehicle_assignment.vehicle_id,
                route_coordinates=route_info.geometry.get('coordinates', []),
                route_name=vehicle_assignment.route_id
            )
            
            # Set GPS device for this driver
            driver.set_vehicle_components(gps_device=gps_device)
            
            # Start driver (this should board vehicle and start GPS)
            logger.info(f"🔧 Driver {driver_assignment.driver_name} boarding vehicle {vehicle_assignment.vehicle_id}")
            await driver.start()
            
            logger.info(f"✅ Driver {driver_assignment.driver_name} started successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Error creating driver {driver_assignment.driver_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def shutdown(self) -> None:
        if self._running:
            self._running = False
        logger.info("Shutting down clean simulator...")
        try:
            # Stop active drivers first
            if hasattr(self, 'active_drivers') and self.active_drivers:
                logger.info(f"🛑 Stopping {len(self.active_drivers)} active drivers...")
                for driver in self.active_drivers:
                    try:
                        await driver.stop()
                    except Exception as e:
                        logger.warning(f"Error stopping driver: {e}")
                self.active_drivers = []
            
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
