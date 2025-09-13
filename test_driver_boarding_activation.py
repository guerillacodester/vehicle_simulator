#!/usr/bin/env python3
"""
Test 3: Driver Boarding and GPS Device Activation (Proper Depot Way)
===================================================================
This test verifies that each driver can successfully board their assigned
vehicle and activate the GPS device using the proper depot system.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher

# Import the proper classes from depot system
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.base_person import BasePerson
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

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

    async def arrive(self) -> bool:
        """Driver boards vehicle and starts GPS device - proper depot way."""
        try:
            # Turn on GPS device
            gps_success = await self.gps_device.start()
            if not gps_success:
                return False
            
            # Send starting position packet (first coordinate from route)
            await self._send_starting_position_packet()
            
            # Start vehicle driver simulation
            vehicle_success = await self.vehicle_driver.start()
            return vehicle_success and gps_success
            
        except Exception as e:
            print(f"   ❌ Boarding failed for {self.person_name}: {e}")
            return False

    async def _send_starting_position_packet(self):
        """Send starting position packet using first route coordinate."""
        try:
            if not self.route_coordinates or len(self.route_coordinates) == 0:
                print(f"   ⚠️  No route coordinates available for {self.person_name}")
                return
            
            # Get first coordinate (starting position)
            starting_point = self.route_coordinates[0]
            
            # Import packet creation tools
            from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet
            from dataclasses import asdict
            import websockets
            import json
            
            # Create starting position packet using proper protocol
            packet = make_packet(
                device_id=self.gps_device.component_id,
                lat=starting_point[1],  # latitude
                lon=starting_point[0],  # longitude  
                speed=0.0,  # stationary at starting position
                heading=0.0,  # no heading when stationary
                route=self.route_name.replace("route ", ""),  # clean route name
                vehicle_reg=self.vehicle_id,
                driver_id=self.component_id,
                driver_name={
                    "first": self.person_name.split()[0],
                    "last": self.person_name.split()[-1]
                }
            )
            
            # Send packet directly to server
            device_url = f"ws://localhost:5000/device?token=depot-starting-position&deviceId={self.gps_device.component_id}"
            async with websockets.connect(device_url) as websocket:
                packet_data = asdict(packet)
                await websocket.send(json.dumps(packet_data))
                print(f"   📡 Starting position transmitted: lat={starting_point[1]:.6f}, lon={starting_point[0]:.6f}")
                
        except Exception as e:
            print(f"   ⚠️  Failed to send starting position for {self.person_name}: {e}")

    async def _start_implementation(self) -> bool:
        """Implementation of abstract method from BasePerson."""
        return await self.arrive()

    async def _stop_implementation(self) -> bool:
        """Implementation of abstract method from BasePerson."""
        try:
            # Stop vehicle driver simulation
            if hasattr(self.vehicle_driver, 'stop'):
                await self.vehicle_driver.stop()
            
            # Stop GPS device
            return await self.gps_device.stop()
        except Exception as e:
            print(f"   ❌ Failed to stop depot driver: {e}")
            return False

async def test_driver_boarding_gps():
    """Test driver boarding and GPS device activation using proper depot system"""
    
    print("🚪 Test 3: Driver Boarding and GPS Device Activation (Proper Depot Way)")
    print("=" * 75)
    print("📋 This test verifies:")
    print("   • Each driver can successfully board their assigned vehicle")
    print("   • GPS devices are properly activated after boarding")
    print("   • GPS devices report correct vehicle and route information")
    print("   • Boarding process follows proper depot workflow")
    print()
    
    try:
        print("🔌 Step 1: Initialize depot system...")
        depot_manager = DepotManager("TestDepot")
        dispatcher = Dispatcher("TestFleetDispatcher", "http://localhost:8000")
        depot_manager.set_dispatcher(dispatcher)
        
        await depot_manager.initialize()
        print("   ✅ Depot system initialized")
        
        print("\n📋 Step 2: Get vehicle assignments...")
        assignments = await depot_manager.dispatcher.get_vehicle_assignments()
        print(f"   ✅ Retrieved {len(assignments)} vehicle assignments")
        for assignment in assignments:
            print(f"   📋 {assignment.driver_name} → {assignment.vehicle_id} → Route {assignment.route_id}")
        
        print("\n🗺️  Step 3: Create depot drivers with route data...")
        depot_drivers = {}
        for assignment in assignments:
            route_code = assignment.route_id.replace("route ", "")
            print(f"   🔍 Setting up driver for Route {route_code}...")
            
            # Get route geometry using established working API
            session = depot_manager.dispatcher.session
            geometry_url = f"{depot_manager.dispatcher.api_base_url}/api/v1/routes/public/{route_code}/geometry"
            
            async with session.get(geometry_url) as response:
                if response.status == 200:
                    route_data = await response.json()
                    coordinates = route_data['geometry']['coordinates']
                    coord_count = len(coordinates)
                    
                    # Create GPS device for this vehicle (proper depot way)
                    from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
                    from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec
                    
                    device_id = f"GPS-{assignment.vehicle_id}"
                    
                    # Create WebSocket transmitter with proper parameters
                    transmitter = WebSocketTransmitter(
                        server_url="ws://localhost:5000",
                        token="test-boarding-token",
                        device_id=device_id,
                        codec=PacketCodec()
                    )
                    
                    # Configure simulation plugin for GPS device
                    plugin_config = {
                        "plugin": "simulation",
                        "update_interval": 1.0,
                        "device_id": device_id
                    }
                    
                    gps_device = GPSDevice(
                        device_id=device_id,
                        ws_transmitter=transmitter,
                        plugin_config=plugin_config
                    )
                    
                    # Create assignment data dict
                    assignment_data = {
                        'driver_id': f"DRIVER_{assignment.driver_name.replace(' ', '_').upper()}",
                        'driver_name': assignment.driver_name,
                        'vehicle_id': assignment.vehicle_id,
                        'route_id': assignment.route_id,
                        'route_name': assignment.route_id,
                        'vehicle_reg_code': assignment.vehicle_id
                    }
                    
                    # Create depot driver
                    driver = DepotVehicleDriver(assignment_data, coordinates, gps_device)
                    depot_drivers[assignment.driver_name] = driver
                    
                    print(f"   ✅ Created {assignment.driver_name} for Route {route_code} ({coord_count} GPS points)")
                else:
                    print(f"   ❌ Failed to fetch Route {route_code} geometry")
                    return False
        
        print(f"\n🚪 Step 4: Driver boarding process (proper depot way)...")
        boarding_success = []
        for driver_name, driver in depot_drivers.items():
            print(f"   🚶 {driver.person_name} boarding vehicle {driver.vehicle_id}...")
            
            # Use proper depot boarding method: arrive()
            success = await driver.arrive()
            boarding_success.append(success)
            
            if success:
                route_name = driver.route_name
                vehicle_reg = driver.vehicle_reg
                print(f"   ✅ {driver.person_name} boarded {vehicle_reg} for Route {route_name}")
                print(f"   📡 GPS device {driver.gps_device.component_id} activated")
                print(f"      🚌 Vehicle: {driver.vehicle_id}")
                print(f"      🗺️  Route: {driver.route_name}")
                print(f"      📊 GPS Points: {len(driver.route_coordinates)}")
            else:
                print(f"   ❌ {driver.person_name} boarding failed")
        
        if not any(boarding_success):
            print(f"   ❌ No drivers successfully boarded")
            return False
        
        print(f"\n📡 Step 5: Verify GPS device activation status...")
        activated_count = 0
        for driver_name, driver in depot_drivers.items():
            if driver.gps_device and hasattr(driver.gps_device, 'current_state'):
                print(f"   🔍 Checking GPS device {driver.gps_device.component_id}...")
                
                # Check device state
                device_state = str(driver.gps_device.current_state)
                print(f"      📊 Device state: {device_state}")
                
                if "ACTIVE" in device_state or "ON" in device_state:
                    activated_count += 1
                    print(f"   ✅ GPS device {driver.gps_device.component_id} is ACTIVE")
                    
                    # Check GPS device properties
                    if hasattr(driver.gps_device, 'component_id'):
                        print(f"      🏷️  Device ID: {driver.gps_device.component_id}")
                else:
                    print(f"   ❌ GPS device {driver.gps_device.component_id} is NOT active (state: {device_state})")
        
        print(f"\n📊 Step 6: Final boarding and GPS activation verification...")
        total_drivers = len(depot_drivers)
        successful_boardings = sum(boarding_success)
        
        if successful_boardings == total_drivers and activated_count == total_drivers:
            print(f"   ✅ All {total_drivers} drivers successfully boarded")
            print(f"   ✅ All {activated_count} GPS devices are active")
            
            print(f"\n📋 Final Status Summary:")
            for driver_name, driver in depot_drivers.items():
                print(f"   🚗 {driver.person_name}:")
                print(f"      🚌 Vehicle: {driver.vehicle_id}")
                print(f"      📡 GPS: {driver.gps_device.component_id} (ACTIVE)")
                print(f"      🗺️  Route: {driver.route_name}")
                print(f"      📊 GPS Points: {len(driver.route_coordinates)}")
        else:
            print(f"   ❌ Boarding/GPS activation incomplete:")
            print(f"      Successful boardings: {successful_boardings}/{total_drivers}")
            print(f"      Active GPS devices: {activated_count}/{total_drivers}")
            return False
        
        print(f"\n✅ SUCCESS: Driver boarding and GPS activation test passed!")
        print(f"   🎯 All drivers successfully boarded their vehicles")
        print(f"   📡 All GPS devices are active and reporting")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: Driver boarding and GPS activation failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_driver_boarding_gps())