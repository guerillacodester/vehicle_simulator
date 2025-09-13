#!/usr/bin/env python3
"""
Enhanced Depot Test with Component Integration

This test integrates the depot management system with our VehicleDriver components
so that when drivers board vehicles, their GPS devices actually connect to the
telemetry server and you can see the connections server-side.
"""
import asyncio
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.fleet_manager.database import get_session
from world.fleet_manager.utils.gps_device_lookup import get_vehicle_gps_device_name
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from world.vehicle_simulator.vehicle.engine.engine_block import Engine
from world.vehicle_simulator.vehicle.engine.engine_buffer import EngineBuffer
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
from world.vehicle_simulator.speed_models.fixed_speed import FixedSpeed


class ComponentIntegratedDepot:
    """Depot that creates actual VehicleDriver components with GPS devices."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.dispatcher = None
        self.depot = None
        self.active_drivers = {}  # Store VehicleDriver instances
        self.db_session = None
        
    async def initialize(self):
        """Initialize depot with component integration."""
        print("🏢 Initializing Component-Integrated Depot")
        print("=" * 50)
        
        # Initialize database connection
        self.db_session = get_session()
        
        # Initialize standard depot/dispatcher
        self.dispatcher = Dispatcher("FleetDispatcher", self.api_url)
        self.depot = DepotManager("MainDepot")
        self.depot.set_dispatcher(self.dispatcher)
        
        # Initialize depot
        depot_ok = await self.depot.initialize()
        if not depot_ok:
            print("❌ Depot initialization failed")
            return False
            
        print("✅ Depot initialized successfully")
        return True
        
    async def create_vehicle_drivers(self):
        """Create VehicleDriver components from depot assignments."""
        print("\n🚗 Creating VehicleDriver Components")
        print("-" * 30)
        
        # Get driver assignments from dispatcher
        driver_assignments = await self.dispatcher.get_driver_assignments()
        vehicle_assignments = await self.dispatcher.get_vehicle_assignments()
        
        if not driver_assignments:
            print("❌ No driver assignments found")
            return False
            
        print(f"📋 Found {len(driver_assignments)} driver assignments")
        
        # Create VehicleDriver for each assignment
        for assignment in driver_assignments[:2]:  # Limit to first 2 for testing
            driver_id = assignment.driver_id
            driver_name = assignment.driver_name
            vehicle_id = assignment.vehicle_id
            
            print(f"\n👨‍💼 Creating components for {driver_name} ({driver_id})")
            print(f"   Vehicle: {vehicle_id}")
            
            # Look up GPS device for this vehicle
            gps_device_name = get_vehicle_gps_device_name(self.db_session, vehicle_id)
            if not gps_device_name:
                print(f"   ⚠️  No GPS device assigned to vehicle {vehicle_id}")
                # Assign a GPS device for testing
                await self._assign_test_gps_device(vehicle_id)
                gps_device_name = get_vehicle_gps_device_name(self.db_session, vehicle_id)
                
            print(f"   📡 GPS Device: {gps_device_name}")
            
            # Create vehicle components
            try:
                # Engine components
                buffer = EngineBuffer(size=10)
                speed_model = FixedSpeed(speed=45.0)
                engine = Engine(vehicle_id, speed_model, buffer, tick_time=1.0)
                
                # GPS Device components  
                transmitter = WebSocketTransmitter(
                    server_url="ws://localhost:5000",
                    token="depot_test_token",
                    device_id=gps_device_name,
                    codec=PacketCodec()
                )
                gps_device = GPSDevice(gps_device_name, transmitter)
                
                # Simple route for testing (around Bridgetown area)
                test_route = [
                    (-59.6167, 13.1000),  # Start
                    (-59.6000, 13.1000),  # East
                    (-59.6000, 13.1167),  # North
                    (-59.6167, 13.1167),  # West
                    (-59.6167, 13.1000)   # Back to start
                ]
                
                # Create VehicleDriver
                vehicle_driver = VehicleDriver(
                    driver_id=driver_id,
                    driver_name=driver_name,
                    vehicle_id=vehicle_id,
                    route_coordinates=test_route,
                    engine_buffer=buffer,
                    tick_time=1.0
                )
                
                # Connect components
                vehicle_driver.set_vehicle_components(engine=engine, gps_device=gps_device)
                
                # Store driver
                self.active_drivers[driver_id] = {
                    'driver': vehicle_driver,
                    'engine': engine,
                    'gps_device': gps_device,
                    'vehicle_id': vehicle_id,
                    'gps_device_name': gps_device_name
                }
                
                print(f"   ✅ Components created and connected")
                
            except Exception as e:
                print(f"   ❌ Failed to create components: {e}")
                continue
                
        print(f"\n✅ Created {len(self.active_drivers)} VehicleDriver components")
        return len(self.active_drivers) > 0
        
    async def _assign_test_gps_device(self, vehicle_reg: str):
        """Assign a GPS device to vehicle for testing."""
        try:
            from world.fleet_manager.models import Vehicle, GPSDevice as DBGPSDevice
            
            vehicle = self.db_session.query(Vehicle).filter(Vehicle.reg_code == vehicle_reg).first()
            available_device = self.db_session.query(DBGPSDevice).filter(
                DBGPSDevice.is_active == True,
                DBGPSDevice.assigned_vehicle == None
            ).first()
            
            if vehicle and available_device:
                vehicle.assigned_gps_device_id = available_device.device_id
                self.db_session.commit()
                print(f"   📡 Auto-assigned {available_device.device_name} to {vehicle_reg}")
                
        except Exception as e:
            print(f"   ⚠️  Could not auto-assign GPS device: {e}")
            
    async def simulate_driver_boarding(self):
        """Simulate drivers boarding their vehicles."""
        print("\n🚌 Simulating Driver Boarding Process")
        print("-" * 40)
        
        for driver_id, components in self.active_drivers.items():
            driver = components['driver']
            gps_device = components['gps_device']
            vehicle_id = components['vehicle_id']
            gps_device_name = components['gps_device_name']
            
            print(f"\n👨‍💼 {driver.person_name} boarding vehicle {vehicle_id}")
            print(f"   GPS Device: {gps_device_name}")
            print(f"   Initial States - Driver: {driver.current_state}, GPS: {gps_device.current_state}")
            
            # Driver boards vehicle
            success = await driver.arrive()
            
            if success:
                print(f"   ✅ Driver boarded successfully!")
                print(f"   📊 Final States - Driver: {driver.current_state}, GPS: {gps_device.current_state}")
                
                if gps_device.current_state.name == "ON":
                    print(f"   🎉 GPS device {gps_device_name} connected to telemetry server!")
                else:
                    print(f"   ❌ GPS device failed to connect (state: {gps_device.current_state})")
            else:
                print(f"   ❌ Driver failed to board vehicle")
                
        print(f"\n📡 Check telemetry server logs for GPS connections!")
        
    async def run_simulation(self, duration: int = 10):
        """Run the simulation for specified duration."""
        print(f"\n⏱️  Running simulation for {duration} seconds...")
        print("   (GPS devices should be transmitting telemetry)")
        
        for i in range(duration):
            await asyncio.sleep(1)
            if (i + 1) % 5 == 0:
                active_gps = sum(1 for c in self.active_drivers.values() 
                               if c['gps_device'].current_state.name == "ON")
                print(f"   ⏰ {i + 1}s - {active_gps}/{len(self.active_drivers)} GPS devices active")
                
    async def simulate_driver_departure(self):
        """Simulate drivers leaving their vehicles."""
        print(f"\n🚪 Simulating Driver Departure")
        print("-" * 30)
        
        for driver_id, components in self.active_drivers.items():
            driver = components['driver']
            gps_device = components['gps_device']
            vehicle_id = components['vehicle_id']
            gps_device_name = components['gps_device_name']
            
            print(f"\n👨‍💼 {driver.person_name} leaving vehicle {vehicle_id}")
            
            success = await driver.depart()
            
            if success:
                print(f"   ✅ Driver departed successfully!")
                print(f"   📊 Final States - Driver: {driver.current_state}, GPS: {gps_device.current_state}")
                
                if gps_device.current_state.name == "OFF":
                    print(f"   🔌 GPS device {gps_device_name} disconnected from server")
                else:
                    print(f"   ⚠️  GPS device still connected (state: {gps_device.current_state})")
            else:
                print(f"   ❌ Driver departure failed")
        
    async def shutdown(self):
        """Shutdown the simulation."""
        print(f"\n🛑 Shutting down simulation...")
        
        # Cleanup drivers
        for components in self.active_drivers.values():
            try:
                await components['driver'].depart()
            except:
                pass
                
        # Shutdown depot
        if self.depot:
            await self.depot.shutdown()
        if self.dispatcher:
            await self.dispatcher.shutdown()
            
        # Close database
        if self.db_session:
            self.db_session.close()
            
        print("✅ Shutdown complete")


async def main():
    """Run the enhanced depot test."""
    print("🧪 Enhanced Depot Test with GPS Device Integration")
    print("=" * 60)
    print("📋 This test demonstrates:")
    print("   • Depot initialization with real driver assignments")
    print("   • VehicleDriver component creation")
    print("   • GPS device lookup from database")
    print("   • Actual GPS connections to telemetry server")
    print("   • Real telemetry transmission")
    print()
    
    depot = ComponentIntegratedDepot()
    
    try:
        # Initialize
        if not await depot.initialize():
            return 1
            
        # Create vehicle drivers
        if not await depot.create_vehicle_drivers():
            return 1
            
        # Simulate boarding
        await depot.simulate_driver_boarding()
        
        # Run simulation
        await depot.run_simulation(duration=8)
        
        # Simulate departure
        await depot.simulate_driver_departure()
        
        print("\n🎉 Enhanced depot test completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await depot.shutdown()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))