"""Vehicle Simulator Core Module (Clean Architecture).

Rebuilt to remove corruption and provide a clean, deterministic orchestrator:
 - Initialize depot + dispatcher
 - Create drivers (active vs idle based on vehicle status)
 - Create an Engine for ALL active drivers (was previously Jane-only)
 - Always create a GPS device
 - Provide a single consolidated status report (no duplicate/garbled blocks)
 - Use DeviceState / DriverState enums via .current_state
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CleanVehicleSimulator:
    """Minimal orchestrator wrapper for depot + dispatcher lifecycle."""

    def __init__(self, api_url: str = "http://localhost:8000", *, status_interim: bool = False) -> None:
        self.api_url = api_url
        self.dispatcher = None
        self.depot = None
        self._running = False
        self.active_drivers = []
        self.idle_drivers = []
        # When True, prints status after each idle-driver addition (verbose). Default False for cleaner output.
        self.status_interim = status_interim

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
            
            # Process drivers based on vehicle availability status
            active_drivers = []
            idle_drivers = []
            
            for i in range(min(len(vehicle_assignments), len(driver_assignments))):
                vehicle_assignment = vehicle_assignments[i]
                driver_assignment = driver_assignments[i]
                
                # Check vehicle status to determine driver state
                vehicle_status = getattr(vehicle_assignment, 'vehicle_status', 'available')
                
                if vehicle_status in ['available', 'in_service']:
                    # Vehicle is operational - driver boards and starts GPS
                    logger.info(f"👤 Starting driver: {driver_assignment.driver_name} → {vehicle_assignment.vehicle_id} ({vehicle_status}) → {vehicle_assignment.route_id}")
                    
                    driver = await self._create_and_start_driver(vehicle_assignment, driver_assignment)
                    if driver:
                        active_drivers.append(driver)
                else:
                    # Vehicle is not available (maintenance/retired) - driver stays IDLE
                    logger.info(f"🚶 Driver present but IDLE: {driver_assignment.driver_name} → {vehicle_assignment.vehicle_id} ({vehicle_status}) - vehicle not operational")
                    
                    # Create idle driver (present in depot but not boarding vehicle)
                    idle_driver = await self._create_idle_driver(driver_assignment, vehicle_assignment)
                    if idle_driver:
                        idle_drivers.append(idle_driver)
                        if self.status_interim:
                            # Optional verbose interim status
                            self._report_status(active_drivers, idle_drivers)

            
            logger.info("")
            
            # Now distribute routes to operational vehicles (drivers onboard with GPS running)
            if active_drivers:
                logger.info(f"🗺️ Distributing routes to {len(active_drivers)} operational vehicles...")
                await self.depot.distribute_routes_to_operational_vehicles(active_drivers)
            else:
                logger.info("🗺️ No active drivers found for route distribution")
            
            self.active_drivers = active_drivers
            self.idle_drivers = idle_drivers
            
            if not active_drivers and not idle_drivers:
                logger.warning("No drivers started successfully")
            else:
                # Final consolidated status after all drivers (active + idle) established
                self._report_status(self.active_drivers, self.idle_drivers)
                
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
            from world.vehicle_simulator.vehicle.engine.engine_block import Engine
            from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
            from world.vehicle_simulator.vehicle.engine.sim_speed_model import load_speed_model
            from world.vehicle_simulator.core.states import DeviceState
            
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
            
            # Engine creation for ALL active drivers (uniform fixed speed for now)
            engine = None
            try:
                speed_model = load_speed_model("fixed", speed=25.0)
                engine_buffer = EngineBuffer()
                engine = Engine(vehicle_id=vehicle_assignment.vehicle_id, model=speed_model, buffer=engine_buffer, tick_time=0.5)
                logger.info(f"🔧 Engine created for driver {driver_assignment.driver_name} on vehicle {vehicle_assignment.vehicle_id} (25 km/h fixed)")
            except Exception as e:
                logger.warning(f"Failed to create engine for {driver_assignment.driver_name}: {e}")
            
            # Set components for this driver (engine may be None)
            driver.engine_buffer = engine.buffer if engine else None
            driver.set_vehicle_components(engine=engine, gps_device=gps_device)
            
            # Start driver (this should board vehicle and start GPS)
            logger.info(f"🔧 Driver {driver_assignment.driver_name} boarding vehicle {vehicle_assignment.vehicle_id}")
            await driver.start()
            
            # Check driver status after starting
            driver_state = driver.current_state.value if hasattr(driver, 'current_state') else 'UNKNOWN'
            if driver_state == "ONBOARD":
                logger.info(f"✅ Driver {driver_assignment.driver_name} is ONBOARD vehicle {vehicle_assignment.vehicle_id}")
            elif driver_state == "DISEMBARKED":
                logger.info(f"⏸️ Driver {driver_assignment.driver_name} is IDLE (disembarked) in depot")
            elif driver_state == "IDLE":
                logger.info(f"⏸️ Driver {driver_assignment.driver_name} is IDLE in vehicle {vehicle_assignment.vehicle_id}")
            else:
                logger.info(f"📋 Driver {driver_assignment.driver_name} status: {driver_state}")
            return driver
            
        except Exception as e:
            logger.error(f"Error creating driver {driver_assignment.driver_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _create_idle_driver(self, driver_assignment, vehicle_assignment):
        """Create an idle driver who is present in depot but cannot board non-operational vehicle."""
        try:
            from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
            
            # Create driver instance with minimal parameters (no route coordinates since not boarding)
            # Use empty coordinates since the driver won't actually navigate
            empty_coordinates = [(0.0, 0.0)]  # Placeholder coordinates
            
            driver = VehicleDriver(
                driver_id=driver_assignment.driver_id,
                driver_name=driver_assignment.driver_name,
                vehicle_id=vehicle_assignment.vehicle_id,
                route_coordinates=empty_coordinates,
                route_name=vehicle_assignment.route_id
            )
            
            logger.info(f"🚶 Idle driver {driver_assignment.driver_name} present in depot (assigned to non-operational {vehicle_assignment.vehicle_id})")
            return driver
            
        except Exception as e:
            logger.error(f"Error creating idle driver {driver_assignment.driver_name}: {e}")
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
            
            # Stop idle drivers (just transition them to OFFSITE)
            if hasattr(self, 'idle_drivers') and self.idle_drivers:
                logger.info(f"🚶 Dismissing {len(self.idle_drivers)} idle drivers...")
                for driver in self.idle_drivers:
                    try:
                        await driver.stop()
                    except Exception as e:
                        logger.warning(f"Error stopping idle driver: {e}")
                self.idle_drivers = []
            
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _report_status(self, active_drivers, idle_drivers):
        """Unified status reporting (replaces corrupted/duplicate blocks)."""
        try:
            logger.info("")
            logger.info("═══════════════════════════════════════════════════════════════")
            logger.info("🚌 VEHICLE STATUS REPORT - OPERATIONAL OVERVIEW")
            logger.info("═══════════════════════════════════════════════════════════════")

            # Active vehicles
            if active_drivers:
                logger.info("🟢 ACTIVE VEHICLES:")
                for i, d in enumerate(active_drivers, 1):
                    d_name = getattr(d, 'driver_name', 'Unknown Driver')
                    v_id = getattr(d, 'vehicle_id', 'Unknown Vehicle')
                    d_state = getattr(getattr(d, 'current_state', None), 'value', 'UNKNOWN')

                    logger.info("")
                    logger.info(f"  🚌 VEHICLE #{i}: {v_id}")
                    logger.info(f"  ├─ 👨‍💼 Driver: {d_name}")

                    status_map = {
                        'ONBOARD': '🚌 ONBOARD - Currently driving vehicle',
                        'DISEMBARKED': '⏸️ DISEMBARKED - In depot',
                        'BOARDING': '🚪 BOARDING - Getting on vehicle',
                        'DISEMBARKING': '🚪 DISEMBARKING - Getting off vehicle',
                    }
                    status_detail = status_map.get(d_state, f"❓ Status: {d_state}")
                    logger.info(f"  ├─ 📋 Status: {status_detail}")

                    # Engine state (using DeviceState via current_state)
                    if getattr(d, 'vehicle_engine', None):
                        eng_state = getattr(getattr(d.vehicle_engine, 'current_state', None), 'value', 'UNKNOWN')
                        if eng_state == 'ON':
                            eng_detail = '⚡ RUNNING - Engine operational'
                        elif eng_state == 'OFF':
                            eng_detail = '🛑 STOPPED - Engine off'
                        elif eng_state == 'STARTING':
                            eng_detail = '⚙️ STARTING - Engine warming up'
                        elif eng_state == 'STOPPING':
                            eng_detail = '⏳ STOPPING - Shutting down'
                        elif eng_state == 'ERROR':
                            eng_detail = '❗ ERROR - Engine fault'
                        else:
                            eng_detail = '❓ UNKNOWN - Engine status unclear'
                        logger.info(f"  ├─ 🔧 Engine: {eng_detail}")
                    else:
                        logger.info("  ├─ 🔧 Engine: 🔴 NO ENGINE (GPS-only mode)")

                    # GPS state
                    if getattr(d, 'vehicle_gps', None):
                        gps_state = getattr(getattr(d.vehicle_gps, 'current_state', None), 'value', 'UNKNOWN')
                        icon = '🟢' if gps_state == 'ON' else '🔴' if gps_state == 'OFF' else '🟡'
                        device_id = getattr(d.vehicle_gps, 'device_id', None) or getattr(d.vehicle_gps, 'component_id', f'GPS-{v_id}')
                        logger.info(f"  └─ 📡 GPS: {icon} {gps_state} ({device_id})")
                    else:
                        logger.info("  └─ 📡 GPS: 🔴 NO DEVICE")

            # Idle vehicles
            if idle_drivers:
                logger.info("")
                logger.info("🔴 INACTIVE VEHICLES:")
                for d in idle_drivers:
                    d_name = getattr(d, 'driver_name', 'Unknown Driver')
                    v_id = getattr(d, 'vehicle_id', 'Unknown Vehicle')
                    d_state = getattr(getattr(d, 'current_state', None), 'value', 'IDLE')
                    logger.info("")
                    logger.info(f"  ⏸️ VEHICLE: {v_id}")
                    logger.info(f"    👤 Driver: {d_name} ({d_state}) - vehicle not operational")
                    logger.info("    🔧 Engine: DISABLED (vehicle maintenance/retired)")
                    logger.info("    📡 GPS: DISABLED (vehicle not operational)")

            # Summary
            total = len(active_drivers) + len(idle_drivers)
            logger.info("")
            logger.info("📊 FLEET SUMMARY:")
            logger.info(f"  🟢 Operational: {len(active_drivers)} vehicles")
            logger.info(f"  🔴 Non-operational: {len(idle_drivers)} vehicles")
            logger.info(f"  📋 Total drivers: {total}")
            logger.info("")
        except Exception as e:  # pragma: no cover
            logger.warning(f"Status report error: {e}")
