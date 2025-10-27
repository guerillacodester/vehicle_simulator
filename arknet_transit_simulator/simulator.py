"""Vehicle Simulator Core Module (Clean Architecture).

This replaces the previous `clean_simulator` module; name aligne                logger.info("")
                       # GPS sta                    # Engine status for this vehicle
                    if hasattr(driver, 'vehicle_engine') and driver.vehicle_engine:
                        # Engine uses DeviceState enum, check current_state
                        engine_state = getattr(driver.vehicle_engine, 'current_state', None)
                        if engine_state and hasattr(engine_state, 'value'):
                            state_value = engine_state.value
                            if state_value == "ON":
                                engine_detail = "🟢 ⚡ RUNNING - Engine operational"
                            elif state_value == "OFF":
                                engine_detail = "🔴 🛑 STOPPED - Engine shut down"
                            elif state_value == "STARTING":
                                engine_detail = "🟡 🚀 STARTING - Engine starting up"
                            elif state_value == "STOPPING":
                                engine_detail = "🟡 ⏹️ STOPPING - Engine shutting down"
                            elif state_value == "ERROR":
                                engine_detail = "🔴 ⚠️ ERROR - Engine malfunction"
                            else:
                                engine_detail = f"🟡 ❓ {state_value} - Engine status unclear"
                        else:
                            engine_detail = "🟡 ❓ UNKNOWN - Engine status unclear"
                        logger.info(f"  ├─ 🔧 Engine: {engine_detail}")     # ═══ SECTION 2: INACTIVE VEHICLES ═══
            if idle_drivers:
                logger.info("")
                logger.info("")
                logger.info("┌─────────────────────────────────────────────────────────────")
                logger.info("│ 🔴 INACTIVE VEHICLES - NON-OPERATIONAL FLEET")
                logger.info("└─────────────────────────────────────────────────────────────")
                
                for i, driver in enumerate(idle_drivers, 1):
                    driver_name = getattr(driver, 'person_name', 'Unknown Driver')
                    vehicle_id = getattr(driver, 'vehicle_id', 'Unknown Vehicle')
                    driver_state = driver.current_state.value if hasattr(driver, 'current_state') else 'IDLE'
                    
                    logger.info("")
                    logger.info(f"  ⏸️ VEHICLE #{i}: {vehicle_id}")
                    logger.info(f"  ├─ 👨‍💼 Driver: {driver_name}")
                    logger.info(f"  ├─ 📋 Status: 🚶 Waiting in depot - vehicle not operational")
                    logger.info(f"  ├─ 🔧 Engine: 🔴 ❌ DISABLED (vehicle under maintenance/retired)")
                    logger.info(f"  └─ 📡 GPS: 🔴 ❌ DISABLED (vehicle not operational)")cle
                    if hasattr(driver, 'vehicle_gps') and driver.vehicle_gps:
                        try:
                            # GPS uses DeviceState enum, check current_state
                            gps_state = getattr(driver.vehicle_gps, 'current_state', None)
                            device_id = getattr(driver.vehicle_gps, 'device_id', None) or \
                                       getattr(driver.vehicle_gps, 'component_id', None) or \
                                       f"GPS-{driver.vehicle_id}"
                            
                            if gps_state and hasattr(gps_state, 'value'):
                                state_value = gps_state.value
                                if state_value == "ON":
                                    gps_detail = f"🟢 📡 ACTIVE - Transmitting location ({device_id})"
                                elif state_value == "OFF":
                                    gps_detail = f"🔴 📴 OFFLINE - No GPS signal ({device_id})"
                                elif state_value == "STARTING":
                                    gps_detail = f"🟡 🚀 STARTING - GPS starting up ({device_id})"
                                elif state_value == "STOPPING":
                                    gps_detail = f"🟡 ⏹️ STOPPING - GPS shutting down ({device_id})"
                                elif state_value == "ERROR":
                                    gps_detail = f"🔴 ⚠️ ERROR - GPS malfunction ({device_id})"
                                else:
                                    gps_detail = f"🟡 📡 {state_value} - GPS status unclear ({device_id})"
                            else:
                                gps_detail = f"🟡 📡 UNKNOWN - GPS status unclear ({device_id})"
                            logger.info(f"  └─ 📡 GPS: {gps_detail}")
                        except Exception as e:
                            logger.info(f"  └─ 📡 GPS: 🟡 ⚠️ ERROR - {str(e)}")
                    else:
                        logger.info(f"  └─ 📡 GPS: 🔴 ❌ NO DEVICE - GPS not installed")logger.info("┌─────────────────────────────────────────────────────────────")
                logger.info("│ 🟢 ACTIVE VEHICLES - OPERATIONAL FLEET")
                logger.info("└─────────────────────────────────────────────────────────────") with
user preference for clarity and            #leet Summary
            total_drivers = len(active_drivers) + len(idle_drivers)
            logger.info("")
            logger.info("📊 FLEET SUMMARY:")
            logger.info(f"  🟢 Operational: {len(active_drivers)} vehicles")
            logger.info(f"  🔴 Non-operational: {len(idle_drivers)} vehicles") 
            logger.info(f"  📋 Total drivers: {total_drivers}")ntional import path.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CleanVehicleSimulator:
    """Minimal orchestrator wrapper for depot + dispatcher lifecycle."""

    def __init__(self, api_url: str = "http://localhost:1337", enable_boarding_after: float = None) -> None:
        self.api_url = api_url
        self.enable_boarding_after = enable_boarding_after  # Delay in seconds before auto-enabling boarding
        self.dispatcher = None
        self.depot = None
        self._running = False
        self.active_drivers = []
        self.idle_drivers = []

    async def initialize(self) -> bool:
        try:
            from arknet_transit_simulator.core.depot_manager import DepotManager
            from arknet_transit_simulator.core.dispatcher import Dispatcher

            logger.info("Initializing clean simulator (depot + dispatcher)...")
            self.dispatcher = Dispatcher("FleetDispatcher", api_base_url=self.api_url)
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
                
                if vehicle_status in ['available', 'in_service', 'active']:
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
            
            # Organized Component Status Display
            logger.info("")
            logger.info("═══════════════════════════════════════════════════════════════")
            logger.info("🚌 VEHICLE STATUS REPORT - OPERATIONAL OVERVIEW")
            logger.info("═══════════════════════════════════════════════════════════════")
            
            # Active Vehicles - Complete Status Per Vehicle
            if active_drivers:
                logger.info("� ACTIVE VEHICLES:")
                for i, driver in enumerate(active_drivers, 1):
                    driver_name = getattr(driver, 'person_name', 'Unknown Driver')
                    vehicle_id = getattr(driver, 'vehicle_id', 'Unknown Vehicle')
                    driver_state = driver.current_state.value if hasattr(driver, 'current_state') else 'UNKNOWN'
                    
                    logger.info("")
                    logger.info(f"  🚌 VEHICLE #{i}: {vehicle_id}")
                    logger.info(f"  ├─ �‍💼 Driver: {driver_name}")
                    
                    # Driver status with more detailed icons
                    status_detail = ""
                    if driver_state == "ONBOARD":
                        status_detail = "🚌 ONBOARD - Currently driving vehicle"
                    elif driver_state == "WAITING":
                        status_detail = "⏸️ WAITING - Boarded, engine off, waiting for start trigger"
                    elif driver_state == "DISEMBARKED":
                        status_detail = "⏸️ IDLE - Standing by in depot"
                    elif driver_state == "IDLE":
                        status_detail = "⏸️ IDLE - Standing by in vehicle"
                    elif driver_state == "BOARDING":
                        status_detail = "🚪 BOARDING - Getting on vehicle"
                    elif driver_state == "DISEMBARKING":
                        status_detail = "🚪 DISEMBARKING - Getting off vehicle"
                    else:
                        status_detail = f"❓ Status: {driver_state}"
                    logger.info(f"  ├─ 📋 Status: {status_detail}")
                    
                    # Engine status for this vehicle
                    if hasattr(driver, 'vehicle_engine') and driver.vehicle_engine:
                        # Engine uses DeviceState enum, check current_state
                        engine_state = getattr(driver.vehicle_engine, 'current_state', None)
                        if engine_state and hasattr(engine_state, 'value'):
                            state_value = engine_state.value
                            if state_value == "ON":
                                engine_detail = "🟢 ⚡ RUNNING - Engine operational"
                            elif state_value == "OFF":
                                engine_detail = "🔴 🛑 STOPPED - Engine shut down"
                            elif state_value == "STARTING":
                                engine_detail = "🟡 🚀 STARTING - Engine starting up"
                            elif state_value == "STOPPING":
                                engine_detail = "� ⏹️ STOPPING - Engine shutting down"
                            elif state_value == "ERROR":
                                engine_detail = "🔴 ⚠️ ERROR - Engine malfunction"
                            else:
                                engine_detail = f"🟡 ❓ {state_value} - Engine status unclear"
                        else:
                            engine_detail = "🟡 ❓ UNKNOWN - Engine status unclear"
                        logger.info(f"  ├─ 🔧 Engine: {engine_detail}")
                    else:
                        logger.info(f"  ├─ 🔧 Engine: 🔴 ❌ NO ENGINE (GPS-only mode)")
                    
                    # GPS status for this vehicle
                    if hasattr(driver, 'vehicle_gps') and driver.vehicle_gps:
                        try:
                            # GPS uses DeviceState enum, check current_state
                            gps_state = getattr(driver.vehicle_gps, 'current_state', None)
                            if gps_state and hasattr(gps_state, 'value'):
                                state_value = gps_state.value
                                icon = "🟢" if state_value == "ON" else "🔴" if state_value == "OFF" else "🟡"
                                gps_state = state_value  # Use string value for display
                            else:
                                gps_state = 'UNKNOWN'
                                icon = "🟡"
                            device_id = getattr(driver.vehicle_gps, 'device_id', None) or \
                                       getattr(driver.vehicle_gps, 'component_id', None) or \
                                       f"GPS-{driver.vehicle_id}"
                            logger.info(f"    � GPS: {icon} {gps_state} ({device_id})")
                        except Exception as e:
                            logger.info(f"    📡 GPS: 🟡 ERROR - {str(e)}")
                    else:
                        logger.info(f"    📡 GPS: 🔴 NO DEVICE")
            
            # Inactive Vehicles - Complete Status Per Vehicle  
            if idle_drivers:
                logger.info("")
                logger.info("🔴 INACTIVE VEHICLES:")
                for driver in idle_drivers:
                    driver_name = getattr(driver, 'person_name', 'Unknown Driver')
                    vehicle_id = getattr(driver, 'vehicle_id', 'Unknown Vehicle')
                    driver_state = driver.current_state.value if hasattr(driver, 'current_state') else 'IDLE'
                    
                    logger.info(f"")
                    logger.info(f"  ⏸️ VEHICLE: {vehicle_id}")
                    logger.info(f"    👤 Driver: {driver_name} ({driver_state}) - vehicle not operational")
                    logger.info(f"    🔧 Engine: � DISABLED (vehicle under maintenance/retired)")
                    logger.info(f"    � GPS: 🔴 DISABLED (vehicle not operational)")
            
            # Driver Status Section
            logger.info("👤 DRIVER STATUS:")
            total_drivers = len(active_drivers) + len(idle_drivers)
            logger.info(f"  � Active: {len(active_drivers)} drivers operating vehicles")
            logger.info(f"  🔴 Idle: {len(idle_drivers)} drivers (vehicles not operational)")
            logger.info(f"  📊 Total: {total_drivers} drivers in depot")
            
            # Vehicle-Driver Assignment Details
            logger.info("� VEHICLE-DRIVER ASSIGNMENTS:")
            


            
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
                
        except Exception as e:
            logger.error(f"Error starting vehicle operations: {e}")
            import traceback
            traceback.print_exc()
    
    async def _create_and_start_driver(self, vehicle_assignment, driver_assignment):
        """Create and start a vehicle driver with GPS device."""
        try:
            from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
            from arknet_transit_simulator.vehicle.gps_device.device import GPSDevice
            from arknet_transit_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
            from arknet_transit_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
            
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
            
            # Create engine for all active vehicles (not just ZR400)
            engine = None
            engine_buffer = None
            logger.info(f"🚗 Creating engine for vehicle: vehicle_id='{vehicle_assignment.vehicle_id}'")
            
            from arknet_transit_simulator.vehicle.engine.engine_block import Engine
            from arknet_transit_simulator.vehicle.engine.engine_buffer import EngineBuffer
            from arknet_transit_simulator.vehicle.engine import sim_speed_model
            import os
            
            # Create engine buffer
            engine_buffer = EngineBuffer()
            
            # Check if physics kernel should be used
            vehicle_id = vehicle_assignment.vehicle_id
            physics_env = os.getenv("PHYSICS_KERNEL", "0")
            use_physics = physics_env == "1" and vehicle_id == "ZR400"
            logger.info(f"🧮 Physics check: PHYSICS_KERNEL='{physics_env}', vehicle_id='{vehicle_id}', use_physics={use_physics}")
            
            if use_physics:
                # Physics kernel with database-driven performance characteristics
                coords = route_info.geometry.get('coordinates', [])
                
                # Get vehicle performance from database to set appropriate target speed
                from arknet_transit_simulator.services.vehicle_performance import VehiclePerformanceService
                try:
                    logger.info(f"🔍 Looking up performance characteristics for {vehicle_id}")
                    performance = VehiclePerformanceService.get_performance_by_reg_code(vehicle_id)
                    target_speed_mps = performance.max_speed_kmh / 3.6  # Convert km/h to m/s
                    logger.info(f"🎯 Setting target speed to {performance.max_speed_kmh} km/h ({target_speed_mps:.2f} m/s) for {vehicle_id}")
                except Exception as e:
                    logger.warning(f"Failed to get performance for {vehicle_id}, using default: {e}")
                    target_speed_mps = 25.0/3.6  # Fallback to 25 km/h
                    logger.info(f"🎯 Using fallback target speed: 25.0 km/h ({target_speed_mps:.2f} m/s)")
                
                speed_model = sim_speed_model.load_speed_model(
                    "physics", 
                    route_coords=coords, 
                    target_speed_mps=target_speed_mps, 
                    dt=0.5,
                    vehicle_reg_code=vehicle_id
                )
                logger.info(f"🧪 Physics kernel enabled for vehicle {vehicle_id} with database-driven performance")
            else:
                # Standard fixed speed model
                speed_model = sim_speed_model.load_speed_model("fixed", speed=25.0)  # 25 km/h for testing
            
            # Create engine
            engine = Engine(
                vehicle_id=vehicle_assignment.vehicle_id,
                model=speed_model,
                buffer=engine_buffer,
                tick_time=0.5  # Update every 0.5 seconds for testing
            )
            
            if use_physics:
                logger.info(f"🔧 Engine (physics) created for {driver_assignment.driver_name} - ready for advanced telemetry")
            else:
                logger.info(f"🔧 Engine (standard) created for {driver_assignment.driver_name} - ready for telemetry testing")
            
            # Create vehicle driver WITH engine_buffer so it can detect engine state
            driver = VehicleDriver(
                driver_id=driver_assignment.driver_id,
                driver_name=driver_assignment.driver_name,
                vehicle_id=vehicle_assignment.vehicle_id,
                route_coordinates=route_info.geometry.get('coordinates', []),
                route_name=vehicle_assignment.route_id,
                engine_buffer=engine_buffer  # Pass engine buffer so driver can read engine state
            )
            
            # Set vehicle components for this driver
            driver.set_vehicle_components(engine=engine, gps_device=gps_device)
            
            # Create Conductor for passenger management
            try:
                from arknet_transit_simulator.vehicle.conductor import Conductor
                from arknet_transit_simulator.services.vehicle_performance import VehiclePerformanceService
                from arknet_transit_simulator.services.strapi_passenger_service import StrapiPassengerService
                from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository
                
                # Get vehicle capacity from database
                try:
                    performance = await VehiclePerformanceService.get_performance_async(vehicle_assignment.vehicle_id)
                    vehicle_capacity = performance.capacity
                    logger.info(f"[CONDUCTOR] Retrieved vehicle capacity from database: {vehicle_capacity} passengers")
                except Exception as perf_error:
                    logger.warning(f"[CONDUCTOR] Failed to get capacity from database: {perf_error}, using default 40")
                    vehicle_capacity = 40  # Fallback to standard minibus capacity
                
                # Create passenger service using new commuter_simulator infrastructure
                # This breaks the tight coupling to deprecated commuter_service module
                passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
                passenger_service = StrapiPassengerService(passenger_repo)
                await passenger_service.connect()
                logger.info(f"[CONDUCTOR] Connected to PassengerService via commuter_simulator infrastructure")
                
                conductor = Conductor(
                    conductor_id=f"COND-{driver_assignment.driver_id}",
                    conductor_name=f"Conductor-{driver_assignment.driver_name}",
                    vehicle_id=vehicle_assignment.vehicle_id,
                    assigned_route_id=vehicle_assignment.route_id,
                    capacity=vehicle_capacity,
                    passenger_db=passenger_service  # Inject new passenger service (via dependency injection)
                )
                
                # Attach conductor to driver for future integration
                driver.conductor = conductor
                
                # Attach driver to conductor for direct communication (fallback when Socket.IO unavailable)
                conductor.driver = driver
                logger.info(f"[CONDUCTOR] ✅ Linked conductor ↔ driver for direct communication")
                logger.info(f"[CONDUCTOR] conductor.driver = {conductor.driver}")
                logger.info(f"[CONDUCTOR] hasattr(conductor, 'driver') = {hasattr(conductor, 'driver')}")
                logger.info(f"[CONDUCTOR] Driver ID: {driver.component_id}, Name: {driver.person_name}")
                
                # Start conductor's Socket.IO connection
                await conductor.start()
            except Exception as e:
                logger.error(f"[CONDUCTOR] Failed to initialize: {e}")
                import traceback
                traceback.print_exc()
                # Continue without conductor for now
                driver.conductor = None
            
            # Start driver (this should board vehicle and start GPS)
            logger.info(f"🔧 Driver {driver_assignment.driver_name} boarding vehicle {vehicle_assignment.vehicle_id}")
            
            # Log conductor status
            if hasattr(driver, 'conductor') and driver.conductor:
                logger.info(f"[Conductor] {driver.conductor.person_name} ready for vehicle {vehicle_assignment.vehicle_id} - Capacity: {driver.conductor.capacity} passengers")
            
            try:
                await driver.start()
                logger.info(f"⚡ Driver state after boarding: {driver.current_state.value}")
            except Exception as e:
                logger.error(f"❌ Exception during driver.start(): {e}")
                import traceback
                traceback.print_exc()
                raise
            
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

            # By default do NOT enable automatic boarding here. Boarding must be
            # explicitly enabled to avoid vehicles starting already full when the
            # PassengerDatabase contains pre-existing waiting commuters.
            if hasattr(driver, 'conductor') and driver.conductor:
                logger.info(
                    f"[Simulator] Conductor for vehicle {vehicle_assignment.vehicle_id} created; boarding is DISABLED by default."
                )
                
                # If --enable-boarding-after N was specified, auto-enable after delay
                if self.enable_boarding_after is not None:
                    async def enable_boarding_after_delay():
                        await asyncio.sleep(self.enable_boarding_after)
                        driver.conductor.start_boarding()
                        logger.info(
                            f"[Simulator] Boarding ENABLED for {vehicle_assignment.vehicle_id} "
                            f"after {self.enable_boarding_after:.1f} second delay"
                        )
                    
                    asyncio.create_task(enable_boarding_after_delay())
                    logger.info(
                        f"[Simulator] Boarding will auto-enable in {self.enable_boarding_after:.1f} seconds"
                    )
                else:
                    logger.info(
                        "[Simulator] To enable boarding: call driver.conductor.start_boarding() "
                        "or restart with --enable-boarding-after N"
                    )
            return driver
            
        except Exception as e:
            logger.error(f"Error creating driver {driver_assignment.driver_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _create_idle_driver(self, driver_assignment, vehicle_assignment):
        """Create an idle driver who is present in depot but cannot board non-operational vehicle."""
        try:
            from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
            
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
