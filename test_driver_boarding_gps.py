#!/usr/bin/env python3
"""
Simple Driver Boarding GPS Test

When drivers board vehicles:
1. Driver boards vehicle (driver state: OFFSITE → ONSITE)  
2. GPS device turns ON (device state: OFF → ON)
3. GPS connects to telemetry server
4. GPS sends first coordinate from route geometry (vehicle parked, engine OFF)
5. You can see the GPS connection on the telemetry server
"""
import asyncio
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.fleet_manager.database import get_session
from world.fleet_manager.utils.gps_device_lookup import get_vehicle_gps_device_name
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec, make_packet
from world.vehicle_simulator.core.states import DeviceState, PersonState
from world.vehicle_simulator.vehicle.base_person import BasePerson
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer


class RealVehicleDriver(BasePerson):
    """Real vehicle driver that uses proper simulation system and connects to GPS device plugin."""
    
    def __init__(self, driver_id: str, driver_name: str, vehicle_id: str, route_coords: list, gps_device: GPSDevice):
        super().__init__(driver_id, "RealVehicleDriver", driver_name)
        
        self.vehicle_id = vehicle_id
        self.route_coords = route_coords
        self.gps_device = gps_device
        
        # Create a real VehicleDriver instance for simulation
        # NOTE: No engine_buffer provided = engine is OFF, speed=0, no movement
        self.vehicle_driver = VehicleDriver(
            driver_id=driver_id,
            driver_name=driver_name,
            vehicle_id=vehicle_id,
            route_coordinates=route_coords,  # Real route coordinates
            engine_buffer=None,  # No engine = parked vehicle, speed=0
            tick_time=1.0,  # Update every second
            mode="geodesic",  # Use proper geodesic interpolation
            direction="outbound"
        )
        
        # Connect the vehicle driver's telemetry to the GPS plugin
        self._simulation_active = False
        self._engine_running = False
        self._engine_buffer = None
        
    async def _start_implementation(self) -> bool:
        """Implementation for BasePerson - turn on GPS and start vehicle simulation."""
        try:
            # Turn on GPS device
            gps_success = await self.gps_device.start()
            if not gps_success:
                return False
            
            # Start the real vehicle simulation
            vehicle_success = await self.vehicle_driver.start()
            if not vehicle_success:
                await self.gps_device.stop()  # Clean up GPS if vehicle fails
                return False
                
            # Connect vehicle simulation to GPS plugin
            self._start_telemetry_bridge()
            self._simulation_active = True
            
            return True
        except Exception as e:
            print(f"   ❌ Failed to start simulation: {e}")
            return False
            
    async def _stop_implementation(self) -> bool:
        """Implementation for BasePerson - stop vehicle simulation and GPS."""
        try:
            self._simulation_active = False
            
            # Stop vehicle simulation
            if hasattr(self.vehicle_driver, 'stop'):
                await self.vehicle_driver.stop()
            
            # Stop GPS device
            return await self.gps_device.stop()
        except Exception as e:
            print(f"   ❌ Failed to stop simulation: {e}")
            return False
            
    def _start_telemetry_bridge(self):
        """Bridge real vehicle simulation telemetry to GPS device plugin."""
        # Connect the VehicleDriver's telemetry output to the GPS simulation plugin
        if hasattr(self.gps_device, 'plugin_manager') and self.gps_device.plugin_manager.active_plugin:
            plugin = self.gps_device.plugin_manager.active_plugin
            if hasattr(plugin, 'set_vehicle_state'):
                # Start continuous telemetry bridge - reads from VehicleDriver, feeds to GPS plugin
                self._telemetry_bridge_active = True
                asyncio.create_task(self._telemetry_bridge_worker())
                print(f"   🔗 Connected vehicle simulation to GPS plugin")
            else:
                print(f"   ⚠️  GPS plugin does not support vehicle state integration")
        else:
            print(f"   ⚠️  No GPS plugin available for telemetry bridge")
        
    async def board_vehicle(self):
        """Driver boards vehicle, starts GPS, and begins real vehicle simulation."""
        print(f"👨‍💼 {self.person_name} boarding vehicle {self.vehicle_id}")
        
        # Driver boards (state transition OFFSITE → ONSITE)
        success = await self.arrive()
        
        if success and self.current_state == PersonState.ONSITE:
            print(f"   ✅ Driver boarded - State: {self.current_state}")
            print(f"   📡 GPS turned ON - State: {self.gps_device.current_state}")
            print(f"   🎉 GPS device {self.gps_device.component_id} connected to server!")
            print(f"   🚗 Vehicle simulation started with real route interpolation")
            print(f"   🔋 Engine OFF - GPS will report static position until engine starts")
            return True
        else:
            print(f"   ❌ Driver failed to board - State: {self.current_state}")
            return False
    
    async def _telemetry_bridge_worker(self):
        """Worker that continuously reads from VehicleDriver telemetry and feeds GPS plugin."""
        print(f"   🔄 Starting telemetry bridge worker...")
        
        while self._simulation_active and hasattr(self, '_telemetry_bridge_active') and self._telemetry_bridge_active:
            try:
                # Read real telemetry data from VehicleDriver's step() method
                telemetry_data = self.vehicle_driver.step()
                
                if telemetry_data:
                    # DEBUG: Show what telemetry data we're receiving from VehicleDriver
                    print(f"   🔍 [DEBUG] {self.vehicle_id} telemetry: lat={telemetry_data.get('lat'):.6f}, lon={telemetry_data.get('lon'):.6f}, speed={telemetry_data.get('speed', 0.0):.1f}, engine={'ON' if self._engine_running else 'OFF'}")
                    
                    # This is REAL data from engine simulation + route interpolation
                    # Convert VehicleDriver telemetry to GPS plugin vehicle state format
                    vehicle_state = {
                        "lat": telemetry_data.get("lat"),
                        "lon": telemetry_data.get("lon"), 
                        "speed": telemetry_data.get("speed", 0.0),  # From engine data
                        "heading": telemetry_data.get("bearing", 0.0),  # From route interpolation (note: bearing not heading)
                        "route_id": telemetry_data.get("route_id", "UNKNOWN"),
                        "vehicle_reg": self.vehicle_id,
                        "driver_id": self.component_id,
                        "driver_name": {"first": self.person_name.split()[0], "last": self.person_name.split()[-1]},
                        "device_id": self.gps_device.component_id,
                        "timestamp": telemetry_data.get("timestamp")
                    }
                    
                    # Feed real simulation data to GPS plugin
                    if hasattr(self.gps_device, 'plugin_manager') and self.gps_device.plugin_manager.active_plugin:
                        plugin = self.gps_device.plugin_manager.active_plugin
                        if hasattr(plugin, 'set_vehicle_state'):
                            plugin.set_vehicle_state(vehicle_state)
                
                # Bridge update interval (sync with VehicleDriver tick_time)
                await asyncio.sleep(self.vehicle_driver.tick_time)
                
            except Exception as e:
                print(f"   ⚠️  Telemetry bridge error: {e}")
                await asyncio.sleep(1.0)
        
        print(f"   🛑 Telemetry bridge worker stopped")
    
    async def start_engine(self):
        """Start the vehicle engine and begin route movement simulation."""
        if self._engine_running:
            print(f"   ⚠️  Engine already running for {self.person_name}")
            return
            
        print(f"🔥 {self.person_name} starting engine in vehicle {self.vehicle_id}")
        
        # IMPORTANT: Set state BEFORE creating the async task
        self._engine_running = True
        
        # Create engine buffer for simulation
        self._engine_buffer = EngineBuffer()
        print(f"   🔧 Created engine buffer: {type(self._engine_buffer)} - {self._engine_buffer}")
        
        # Connect engine buffer to VehicleDriver
        self.vehicle_driver.engine_buffer = self._engine_buffer
        print(f"   🔧 Connected buffer to VehicleDriver: {self.vehicle_driver.engine_buffer}")
        
        # Start engine simulation - simple constant speed simulation
        self._engine_task = asyncio.create_task(self._engine_simulation_worker())
        
        # Give the engine task a moment to start
        await asyncio.sleep(0.1)
        
        print(f"   ✅ Engine started - vehicle will move along route")
        
    async def stop_engine(self):
        """Stop the vehicle engine - vehicle stops moving."""
        if not self._engine_running:
            print(f"   ⚠️  Engine already stopped for {self.person_name}")
            return
            
        print(f"🛑 {self.person_name} stopping engine in vehicle {self.vehicle_id}")
        
        # Stop engine simulation
        self._engine_running = False
        
        # Wait for engine task to finish cleanly
        if hasattr(self, '_engine_task') and self._engine_task:
            try:
                await asyncio.wait_for(self._engine_task, timeout=2.0)
            except asyncio.TimeoutError:
                print(f"   ⚠️  Engine task did not stop cleanly for {self.vehicle_id}")
        
        # Disconnect engine buffer from VehicleDriver
        self.vehicle_driver.engine_buffer = None
        self._engine_buffer = None
        
        print(f"   ✅ Engine stopped - vehicle stationary")
        
    async def _engine_simulation_worker(self):
        """Simple engine simulation that generates distance/speed data."""
        print(f"   🔄 Engine simulation started for {self.vehicle_id}")
        print(f"   📊 Initial state: _engine_running={self._engine_running}, _engine_buffer={'exists' if self._engine_buffer else 'None'}")
        
        total_distance = 0.0  # km
        cruise_speed = 25.0   # km/h (typical minibus speed)
        tick_interval = 1.0   # seconds
        
        start_time = time.time()
        tick_count = 0
        
        while self._engine_running and self._engine_buffer:
            try:
                # Calculate distance moved this tick
                distance_per_tick = cruise_speed * (tick_interval / 3600.0)  # km
                total_distance += distance_per_tick
                tick_count += 1
                
                current_time = time.time()
                engine_time = current_time - start_time
                
                # DEBUG: Show engine simulation progress
                print(f"   🚗 [ENGINE {self.vehicle_id}] Tick {tick_count}: distance={total_distance:.4f}km, speed={cruise_speed}km/h, running={self._engine_running}")
                
                # Create engine data entry
                engine_data = {
                    "timestamp": current_time,
                    "time": engine_time,  # seconds since engine start
                    "distance": total_distance,  # cumulative km
                    "cruise_speed": cruise_speed,  # km/h
                    "acceleration": 0.0,  # steady speed
                    "fuel_consumption": 0.1 * distance_per_tick  # simulated fuel
                }
                
                # Write to engine buffer for VehicleDriver to read
                self._engine_buffer.write(engine_data)
                
                await asyncio.sleep(tick_interval)
                
            except Exception as e:
                print(f"   ⚠️  Engine simulation error: {e}")
                break
        
        engine_time = time.time() - start_time
        print(f"   🛑 Engine simulation stopped for {self.vehicle_id} - running={self._engine_running}, buffer={'exists' if self._engine_buffer else 'None'}")
        print(f"   📊 Total distance: {total_distance:.4f} km in {engine_time:.1f} seconds ({tick_count} ticks)")
    

    
    async def leave_vehicle(self):
        """Driver leaves vehicle and turns off GPS."""
        print(f"\n👨‍💼 {self.person_name} leaving vehicle {self.vehicle_id}")
        
        # Turn off GPS device
        await self.gps_device.stop()
        print(f"   📡 GPS turned OFF - State: {self.gps_device.current_state}")
        
        # Driver leaves (state transition)  
        success = await self.depart()
        
        if success:
            print(f"   ✅ Driver departed - State: {self.current_state}")
            print(f"   🔌 GPS device disconnected from server")
        else:
            print(f"   ❌ Driver departure failed - State: {self.current_state}")


async def test_driver_boarding_gps():
    """Test drivers boarding and GPS connections."""
    print("🧪 Driver Boarding GPS Connection Test")
    print("=" * 45)
    print("📋 This test shows:")
    print("   • Driver boards vehicle (PersonState: OFFSITE → ONSITE)")  
    print("   • GPS device turns ON (DeviceState: OFF → ON)")
    print("   • GPS connects to telemetry server")
    print("   • GPS sends initial route coordinate (vehicle parked)")
    print("   • Check telemetry server for GPS connections!")
    print()
    
    db = get_session()
    drivers = {}
    
    try:
        # Test assignments (driver → vehicle)
        test_assignments = [
            {"driver_id": "LIC001", "driver_name": "John Smith", "vehicle_id": "ZR101"},
            {"driver_id": "LIC002", "driver_name": "Jane Doe", "vehicle_id": "ZR400"}
        ]
        
        # Simple test routes (Bridgetown area coordinates)
        test_routes = {
            "ZR101": [(-59.6167, 13.1000), (-59.6000, 13.1000), (-59.6000, 13.1167)],  # Route 1
            "ZR400": [(-59.6200, 13.1100), (-59.6100, 13.1100), (-59.6100, 13.1200)]   # Route 2
        }
        
        print("🔍 Setting up driver assignments...")
        
        for assignment in test_assignments:
            driver_id = assignment["driver_id"]
            driver_name = assignment["driver_name"]
            vehicle_id = assignment["vehicle_id"]
            
            # Look up GPS device for vehicle
            gps_device_name = get_vehicle_gps_device_name(db, vehicle_id)
            
            if not gps_device_name:
                print(f"   ❌ No GPS device assigned to {vehicle_id}")
                # Auto-assign for testing
                await auto_assign_gps(db, vehicle_id)
                gps_device_name = get_vehicle_gps_device_name(db, vehicle_id)
            
            if gps_device_name:
                print(f"   📋 {driver_name} → {vehicle_id} → GPS: {gps_device_name}")
                
                # Create GPS device with minimal plugin config
                transmitter = WebSocketTransmitter(
                    server_url="ws://localhost:5000",
                    token="driver_boarding_test",
                    device_id=gps_device_name,
                    codec=PacketCodec()
                )
                
                # Minimal plugin config for testing
                plugin_config = {
                    "type": "simulation",
                    "device_id": gps_device_name,
                    "update_interval": 2.0
                }
                
                gps_device = GPSDevice(gps_device_name, transmitter, plugin_config)
                
                # Get route coordinates for this vehicle
                route_coords = test_routes.get(vehicle_id, [(-59.6167, 13.1000)])
                
                # Create simple driver
                driver = RealVehicleDriver(driver_id, driver_name, vehicle_id, route_coords, gps_device)
                drivers[driver_id] = driver
                
        if not drivers:
            print("❌ No drivers created for testing")
            return False
            
        print(f"\n✅ Created {len(drivers)} driver assignments")
        
        # Simulate drivers boarding vehicles
        print(f"\n🚌 Drivers boarding vehicles...")
        boarding_success = []
        
        for driver_id, driver in drivers.items():
            success = await driver.board_vehicle()
            boarding_success.append(success)
            
            if success:
                print(f"   🎉 {driver.person_name} successfully boarded with GPS active")
            else:
                print(f"   ❌ {driver.person_name} boarding failed")
        
        if not any(boarding_success):
            print("\n❌ No drivers successfully boarded")
            return False
        
        # Engine simulation - demonstrate engine ON/OFF cycle
        print(f"\n🔋 Starting engine simulation cycle...")
        print(f"   📡 Check telemetry server for GPS coordinates during engine states!")
        
        # Phase 1: Engine OFF - GPS reports static position (parked at route start)
        print(f"\n🚫 Phase 1: Engine OFF - vehicles parked")
        print(f"   📍 GPS should report static positions at route start points")
        await asyncio.sleep(5)
        
        # Phase 2: Engine ON - vehicles start moving along routes
        print(f"\n✅ Phase 2: Turning engines ON - vehicles moving")
        for driver_id, driver in drivers.items():
            await driver.start_engine()
        
        print(f"   🚗 Engines running for 5 seconds - vehicles moving along routes")
        print(f"   � GPS should report changing positions with speed > 0")
        await asyncio.sleep(5)
        
        # Phase 3: Engine OFF - vehicles stop where they are
        print(f"\n🛑 Phase 3: Turning engines OFF - vehicles stopped")
        for driver_id, driver in drivers.items():
            await driver.stop_engine()
            
        print(f"   ⏸️  Engines stopped for 5 seconds - vehicles stationary")
        print(f"   📍 GPS should report static positions at current route locations")
        await asyncio.sleep(5)
        
        # Drivers finish and leave
        print(f"\n🚪 Drivers finishing shift and leaving...")
        for driver_id, driver in drivers.items():
            await driver.leave_vehicle()
        
        print(f"\n🎉 Driver boarding GPS test completed!")
        print(f"📋 Telemetry server should show:")
        print(f"   • GPS device connections when drivers boarded")
        print(f"   • Initial position coordinates for each vehicle")
        print(f"   • GPS device disconnections when drivers left")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup GPS devices
        for driver in drivers.values():
            try:
                await driver.gps_device.stop()
            except:
                pass
        db.close()


async def auto_assign_gps(db, vehicle_reg: str):
    """Auto-assign available GPS device to vehicle for testing."""
    try:
        from world.fleet_manager.models import Vehicle, GPSDevice as DBGPSDevice
        
        vehicle = db.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg).first()
        available_device = db.query(DBGPSDevice).filter(
            DBGPSDevice.is_active == True,
            DBGPSDevice.assigned_vehicle == None
        ).first()
        
        if vehicle and available_device:
            vehicle.assigned_gps_device_id = available_device.device_id
            db.commit()
            print(f"   📡 Auto-assigned {available_device.device_name} to {vehicle_reg}")
            
    except Exception as e:
        print(f"   ⚠️  Auto-assignment failed: {e}")


if __name__ == "__main__":
    success = asyncio.run(test_driver_boarding_gps())
    print(f"\n{'🎉 Test completed successfully!' if success else '❌ Test failed'}")
    sys.exit(0 if success else 1)