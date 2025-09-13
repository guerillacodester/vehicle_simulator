#!/usr/bin/env python3
"""
Depot-Based Vehicle Simulation Test

This test demonstrates the proper integration flow:
1. Initialize depot system (connects to Fleet Manager API)
2. Dispatcher fetches vehicle/driver/route assignments 
3. Routes are distributed to drivers with GPS coordinates
4. Drivers board vehicles and activate GPS devices
5. Engines turn on and vehicles move along real route coordinates
6. GPS telemetry is transmitted to telemetry server

This uses the proper depot workflow instead of manually creating drivers.
"""
import asyncio
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.vehicle_simulator.simulator import CleanVehicleSimulator
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.core.states import DeviceState, PersonState
from world.vehicle_simulator.vehicle.base_person import BasePerson
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer


class DepotVehicleDriver(BasePerson):
    """Vehicle driver that integrates with depot system for proper route assignment."""
    
    def __init__(self, assignment_data: dict, route_coordinates: list, gps_device: GPSDevice):
        # Extract driver info from depot assignment
        driver_id = assignment_data.get('driver_id', 'UNKNOWN_DRIVER')
        driver_name = assignment_data.get('driver_name', 'Unknown Driver')
        
        super().__init__(driver_id, "DepotVehicleDriver", driver_name)
        
        self.assignment = assignment_data
        self.vehicle_id = assignment_data.get('vehicle_id', 'UNKNOWN_VEHICLE')
        self.route_id = assignment_data.get('route_id', 'UNKNOWN_ROUTE')
        self.route_name = assignment_data.get('route_name', 'Unknown Route')
        self.vehicle_reg = assignment_data.get('vehicle_reg_code', 'Unknown Vehicle')
        
        self.route_coordinates = route_coordinates
        self.gps_device = gps_device
        
        # Create VehicleDriver with proper route assignment
        self.vehicle_driver = VehicleDriver(
            driver_id=driver_id,
            driver_name=driver_name,
            vehicle_id=self.vehicle_id,
            route_coordinates=route_coordinates,
            engine_buffer=None,  # Start with engine OFF
            tick_time=1.0,
            mode="geodesic",
            direction="outbound"
        )
        
        # Engine simulation state
        self._simulation_active = False
        self._engine_running = False
        self._engine_buffer = None
        self._engine_task = None
        
    async def _start_implementation(self) -> bool:
        """Driver boards vehicle and starts GPS device."""
        try:
            # Turn on GPS device
            gps_success = await self.gps_device.start()
            if not gps_success:
                return False
            
            # Start vehicle driver simulation
            vehicle_success = await self.vehicle_driver.start()
            if not vehicle_success:
                await self.gps_device.stop()
                return False
            
            # Connect telemetry bridge
            self._start_telemetry_bridge()
            self._simulation_active = True
            
            return True
        except Exception as e:
            print(f"   ❌ Failed to start depot driver: {e}")
            return False
    
    async def _stop_implementation(self) -> bool:
        """Driver stops engine, GPS, and leaves vehicle."""
        try:
            # Stop engine if running
            if self._engine_running:
                await self.stop_engine()
            
            self._simulation_active = False
            
            # Stop vehicle simulation
            if hasattr(self.vehicle_driver, 'stop'):
                await self.vehicle_driver.stop()
            
            # Stop GPS device
            return await self.gps_device.stop()
        except Exception as e:
            print(f"   ❌ Failed to stop depot driver: {e}")
            return False
    
    def _start_telemetry_bridge(self):
        """Bridge vehicle simulation telemetry to GPS device."""
        if hasattr(self.gps_device, 'plugin_manager') and self.gps_device.plugin_manager.active_plugin:
            plugin = self.gps_device.plugin_manager.active_plugin
            if hasattr(plugin, 'set_vehicle_state'):
                self._telemetry_bridge_active = True
                asyncio.create_task(self._telemetry_bridge_worker())
                print(f"   🔗 Connected vehicle simulation to GPS plugin for {self.route_name}")
    
    async def _telemetry_bridge_worker(self):
        """Worker that feeds real vehicle simulation data to GPS plugin."""
        print(f"   🔄 Starting telemetry bridge for Route {self.route_name}...")
        
        while self._simulation_active and hasattr(self, '_telemetry_bridge_active') and self._telemetry_bridge_active:
            try:
                # Get real telemetry from VehicleDriver
                telemetry_data = self.vehicle_driver.step()
                
                if telemetry_data:
                    # DEBUG: Show telemetry data with route context
                    engine_status = "ON" if self._engine_running else "OFF"
                    print(f"   🔍 [{self.route_name}] lat={telemetry_data.get('lat'):.6f}, lon={telemetry_data.get('lon'):.6f}, speed={telemetry_data.get('speed', 0.0):.1f}, engine={engine_status}")
                    
                    # Convert to GPS plugin format with proper route information
                    vehicle_state = {
                        "lat": telemetry_data.get("lat"),
                        "lon": telemetry_data.get("lon"),
                        "speed": telemetry_data.get("speed", 0.0),
                        "heading": telemetry_data.get("bearing", 0.0),
                        "route_id": self.route_id,  # Real route ID from depot assignment
                        "route_name": self.route_name,  # Real route name
                        "vehicle_reg": self.vehicle_reg,
                        "driver_id": self.component_id,
                        "driver_name": {"first": self.person_name.split()[0], "last": self.person_name.split()[-1]},
                        "device_id": self.gps_device.component_id,
                        "timestamp": telemetry_data.get("timestamp")
                    }
                    
                    # Feed to GPS plugin
                    plugin = self.gps_device.plugin_manager.active_plugin
                    if hasattr(plugin, 'set_vehicle_state'):
                        plugin.set_vehicle_state(vehicle_state)
                
                # Update interval
                await asyncio.sleep(self.vehicle_driver.tick_time)
                
            except Exception as e:
                print(f"   ⚠️  Telemetry bridge error for {self.route_name}: {e}")
                await asyncio.sleep(1.0)
        
        print(f"   🛑 Telemetry bridge stopped for Route {self.route_name}")
    
    async def start_engine(self):
        """Start engine and begin moving along assigned route."""
        if self._engine_running:
            print(f"   ⚠️  Engine already running for Route {self.route_name}")
            return
        
        print(f"🔥 {self.person_name} starting engine for Route {self.route_name}")
        
        # Set engine state BEFORE creating buffer and task
        self._engine_running = True
        
        # Create engine buffer
        self._engine_buffer = EngineBuffer()
        
        # Connect to VehicleDriver
        self.vehicle_driver.engine_buffer = self._engine_buffer
        
        # Start engine simulation
        self._engine_task = asyncio.create_task(self._engine_simulation_worker())
        
        # Give task time to start
        await asyncio.sleep(0.1)
        
        print(f"   ✅ Engine started - moving along Route {self.route_name}")
    
    async def stop_engine(self):
        """Stop engine - vehicle becomes stationary."""
        if not self._engine_running:
            print(f"   ⚠️  Engine already stopped for Route {self.route_name}")
            return
        
        print(f"🛑 {self.person_name} stopping engine for Route {self.route_name}")
        
        # Stop engine simulation
        self._engine_running = False
        
        # Wait for task to finish
        if hasattr(self, '_engine_task') and self._engine_task:
            try:
                await asyncio.wait_for(self._engine_task, timeout=2.0)
            except asyncio.TimeoutError:
                print(f"   ⚠️  Engine task timeout for Route {self.route_name}")
        
        # Disconnect engine buffer
        self.vehicle_driver.engine_buffer = None
        self._engine_buffer = None
        
        print(f"   ✅ Engine stopped - Route {self.route_name} vehicle stationary")
    
    async def _engine_simulation_worker(self):
        """Engine simulation for route movement."""
        print(f"   🔄 Engine simulation started for Route {self.route_name}")
        print(f"   📊 Engine state check: running={self._engine_running}, buffer={'exists' if self._engine_buffer else 'None'}")
        
        total_distance = 0.0
        cruise_speed = 25.0  # km/h
        tick_interval = 1.0
        start_time = time.time()
        tick_count = 0
        
        while self._engine_running and self._engine_buffer:
            try:
                # Calculate movement
                distance_per_tick = cruise_speed * (tick_interval / 3600.0)
                total_distance += distance_per_tick
                tick_count += 1
                
                current_time = time.time()
                engine_time = current_time - start_time
                
                # DEBUG: Show engine progress
                print(f"   🚗 [Route {self.route_name}] Tick {tick_count}: distance={total_distance:.4f}km, speed={cruise_speed}km/h")
                
                # Create engine data
                engine_data = {
                    "timestamp": current_time,
                    "time": engine_time,
                    "distance": total_distance,
                    "cruise_speed": cruise_speed,
                    "acceleration": 0.0,
                    "fuel_consumption": 0.1 * distance_per_tick
                }
                
                # Write to buffer for VehicleDriver
                self._engine_buffer.write(engine_data)
                
                await asyncio.sleep(tick_interval)
                
            except Exception as e:
                print(f"   ⚠️  Engine simulation error for Route {self.route_name}: {e}")
                break
        
        engine_time = time.time() - start_time
        print(f"   🛑 Engine simulation stopped for Route {self.route_name}")
        print(f"   📊 Total distance: {total_distance:.4f} km in {engine_time:.1f} seconds ({tick_count} ticks)")


async def test_depot_vehicle_simulation():
    """Test vehicle simulation using proper depot system initialization."""
    print("🏭 Depot-Based Vehicle Simulation Test")
    print("=" * 60)
    print("📋 This test demonstrates proper depot workflow:")
    print("   • Initialize depot system (connects to Fleet Manager API)")
    print("   • Fetch real vehicle/driver/route assignments")
    print("   • Distribute routes with GPS coordinates to drivers")
    print("   • Drivers board vehicles and activate GPS devices")
    print("   • Engines start and vehicles move along real routes")
    print("   • GPS telemetry transmitted to telemetry server")
    
    simulator = None
    depot_drivers = {}
    
    try:
        # Phase 1: Initialize depot system (connects to Fleet Manager API)
        print(f"\n🔌 Phase 1: Initializing depot system...")
        simulator = CleanVehicleSimulator(api_url="http://localhost:8000")
        
        success = await simulator.initialize()
        if not success:
            print(f"❌ Depot system initialization failed")
            print(f"   💡 Make sure Fleet Manager API is running on localhost:8000")
            return False
        
        print(f"   ✅ Depot system initialized - dispatcher connected to API")
        
        # Phase 2: Get vehicle assignments from depot
        print(f"\n📋 Phase 2: Fetching vehicle assignments from depot...")
        vehicle_assignments = await simulator.get_vehicle_assignments()
        
        if not vehicle_assignments:
            print(f"   ❌ No vehicle assignments found")
            print(f"   💡 Make sure vehicles, drivers, and routes are configured in Fleet Manager")
            return False
        
        print(f"   ✅ Found {len(vehicle_assignments)} vehicle assignments:")
        for assignment in vehicle_assignments:
            driver_name = assignment.driver_name or "Unknown Driver"
            vehicle_reg = assignment.vehicle_reg_code or assignment.vehicle_id
            route_name = assignment.route_name or assignment.route_id
            print(f"   📋 {driver_name} → {vehicle_reg} → Route {route_name}")
        
        # Phase 3: Get route coordinates for assigned routes
        print(f"\n🗺️  Phase 3: Fetching route GPS coordinates...")
        route_coordinates = {}
        
        for assignment in vehicle_assignments:
            if assignment.route_id:
                route_info = await simulator.get_route_info(assignment.route_id)
                if route_info:
                    route_name = route_info.route_name or assignment.route_id
                    if route_info.geometry and route_info.geometry.get('coordinates'):
                        coords = route_info.geometry.get('coordinates', [])
                        # Convert to (lon, lat) tuples for VehicleDriver
                        route_coords = [(coord[0], coord[1]) for coord in coords]
                        route_coordinates[assignment.route_id] = route_coords
                        print(f"   ✅ Route {route_name}: {len(route_coords)} GPS coordinates")
                    else:
                        # No geometry data - use default depot coordinates for stationary simulation
                        # This represents vehicles parked at depot without route geometry
                        depot_coords = [(-59.61, 13.10), (-59.61, 13.10)]  # Static depot position
                        route_coordinates[assignment.route_id] = depot_coords
                        print(f"   ⚠️  Route {route_name}: No GPS coordinates in database - using depot position")
                else:
                    print(f"   ❌ Route {assignment.route_id}: Route info not found")
        
        if not route_coordinates:
            print(f"   ❌ No route assignments could be processed")
            return False
        
        # Phase 4: Create depot drivers with proper route assignments
        print(f"\n🚌 Phase 4: Creating depot drivers with route assignments...")
        
        for assignment in vehicle_assignments:
            if assignment.route_id in route_coordinates:
                # Create GPS device for this driver
                device_id = f"GPS-{assignment.vehicle_id}"
                
                # Import required components
                from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
                
                # Create WebSocket transmitter with proper parameters
                transmitter = WebSocketTransmitter(
                    server_url="ws://localhost:5000",
                    token="depot-test-token",
                    device_id=device_id,
                    codec=PacketCodec()
                )
                
                # Configure simulation plugin for GPS device
                plugin_config = {
                    "plugin": "simulation",
                    "update_interval": 1.0,
                    "device_id": device_id
                }
                
                # Create GPS device with proper plugin infrastructure
                gps_device = GPSDevice(
                    device_id=device_id,
                    ws_transmitter=transmitter,
                    plugin_config=plugin_config
                )
                
                # Create depot driver with proper assignment data
                assignment_data = {
                    'driver_id': assignment.driver_id,
                    'driver_name': assignment.driver_name,
                    'vehicle_id': assignment.vehicle_id,
                    'vehicle_reg_code': assignment.vehicle_reg_code,
                    'route_id': assignment.route_id,
                    'route_name': assignment.route_name
                }
                
                depot_driver = DepotVehicleDriver(
                    assignment_data=assignment_data,
                    route_coordinates=route_coordinates[assignment.route_id],
                    gps_device=gps_device
                )
                
                depot_drivers[assignment.driver_id] = depot_driver
                
                driver_name = assignment.driver_name or "Unknown Driver"
                route_name = assignment.route_name or assignment.route_id
                coord_count = len(route_coordinates[assignment.route_id])
                print(f"   ✅ Created {driver_name} for Route {route_name} ({coord_count} GPS points)")
        
        if not depot_drivers:
            print(f"   ❌ No drivers created")
            return False
        
        # Phase 5: Drivers board vehicles and activate GPS
        print(f"\n🚪 Phase 5: Drivers boarding vehicles...")
        boarding_success = []
        
        for driver_id, driver in depot_drivers.items():
            success = await driver.arrive()  # Driver boards vehicle
            boarding_success.append(success)
            
            if success:
                route_name = driver.route_name
                vehicle_reg = driver.vehicle_reg
                print(f"   ✅ {driver.person_name} boarded {vehicle_reg} for Route {route_name}")
                print(f"   📡 GPS device {driver.gps_device.component_id} activated")
            else:
                print(f"   ❌ {driver.person_name} boarding failed")
        
        if not any(boarding_success):
            print(f"   ❌ No drivers successfully boarded")
            return False
        
        # Phase 6: Engine simulation cycle with depot-based simulation
        print(f"\n🔋 Phase 6: Engine simulation cycle...")
        print(f"   📡 Check telemetry server at localhost:5000 for GPS data!")
        print(f"   💡 Note: Routes have no geometry data - vehicles simulate at depot positions")
        
        # Parked phase - engines OFF  
        print(f"\n🚫 Engines OFF - vehicles parked at depot")
        await asyncio.sleep(3)
        
        # Moving phase - engines ON (even without route geometry, engine simulation runs)
        print(f"\n✅ Starting engines - simulating vehicle movement")
        for driver_id, driver in depot_drivers.items():
            await driver.start_engine()
        
        print(f"   🚗 Engines running for 8 seconds - GPS shows engine telemetry")
        print(f"   📍 Without route geometry, vehicles remain at depot coordinates")
        await asyncio.sleep(8)
        
        # Stopped phase - engines OFF
        print(f"\n🛑 Stopping engines - vehicles back to stationary")
        for driver_id, driver in depot_drivers.items():
            await driver.stop_engine()
        
        print(f"   ⏸️  Engines stopped for 3 seconds - GPS shows static positions")
        await asyncio.sleep(3)
        
        # Phase 7: Drivers leave vehicles
        print(f"\n🚪 Phase 7: Drivers leaving vehicles...")
        for driver_id, driver in depot_drivers.items():
            await driver.leave()
            route_name = driver.route_name
            print(f"   👋 {driver.person_name} left Route {route_name} vehicle")
            print(f"   📡 GPS device {driver.gps_device.component_id} deactivated")
        
        print(f"\n🎉 Depot vehicle simulation test completed!")
        print(f"📋 Telemetry server should show:")
        print(f"   • GPS connections when drivers boarded")
        print(f"   • Real route names in telemetry data ('{list(route_coordinates.keys())}')")
        print(f"   • Proper vehicle registrations and driver names")
        print(f"   • Static positions when engines OFF")
        print(f"   • Engine speed data when engines ON (even at static positions)")
        print(f"   • GPS disconnections when drivers left")
        print(f"   💡 This demonstrates proper depot integration even without route geometry")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        for driver in depot_drivers.values():
            try:
                await driver.gps_device.stop()
            except:
                pass
        
        if simulator:
            await simulator.shutdown()


if __name__ == "__main__":
    success = asyncio.run(test_depot_vehicle_simulation())
    print(f"\n{'🎉 Test completed successfully!' if success else '❌ Test failed'}")
    sys.exit(0 if success else 1)