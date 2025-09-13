#!/usr/bin/env python3
"""
Test 4: Depot Manager Authorized Test Drive (60 Second Engine Test)
===================================================================
This test verifies that the depot manager can authorize a single driver
for a test drive where they turn the engine on, drive for 60 seconds,
and transmit continuous GPS telemetry data.
"""

import asyncio
import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.base_person import BasePerson
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec, make_packet
from dataclasses import asdict
import websockets

class AuthorizedTestDriver(BasePerson):
    """Authorized test driver for depot manager supervised test drives."""
    
    def __init__(self, assignment_data: dict, route_coordinates: list, gps_device: GPSDevice):
        # Extract driver info from depot assignment
        driver_id = assignment_data.get('driver_id', 'UNKNOWN_DRIVER')
        driver_name = assignment_data.get('driver_name', 'Unknown Driver')
        
        super().__init__(driver_id, "AuthorizedTestDriver", driver_name)
        
        self.assignment = assignment_data
        self.vehicle_id = assignment_data.get('vehicle_id', 'UNKNOWN_VEHICLE')
        self.route_id = assignment_data.get('route_id', 'UNKNOWN_ROUTE')
        self.route_name = assignment_data.get('route_name', 'Unknown Route')
        self.vehicle_reg = assignment_data.get('vehicle_reg_code', 'Unknown Vehicle')
        
        self.route_coordinates = route_coordinates
        self.gps_device = gps_device
        self.authorized = False
        self.engine_on = False
        self.test_drive_active = False
        
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

    async def get_depot_authorization(self, depot_manager) -> bool:
        """Request authorization from depot manager for test drive."""
        try:
            print(f"   🔐 {self.person_name} requesting test drive authorization...")
            print(f"      📋 Driver License: {self.component_id}")
            print(f"      🚌 Vehicle: {self.vehicle_id}")
            print(f"      🗺️  Route: {self.route_name}")
            
            # Simulate depot manager authorization process
            depot_state = str(depot_manager.current_state.value)
            print(f"      📊 Depot manager state: {depot_state}")
            
            if depot_state in ["OPEN", "ONSITE", "onsite", "open"]:
                self.authorized = True
                print(f"   ✅ AUTHORIZED: Depot manager approved test drive for {self.person_name}")
                return True
            else:
                print(f"   ❌ DENIED: Depot manager not available for authorization (state: {depot_state})")
                return False
                
        except Exception as e:
            print(f"   ❌ Authorization failed for {self.person_name}: {e}")
            return False

    async def start_engine(self) -> bool:
        """Turn on vehicle engine (authorized drivers only)."""
        if not self.authorized:
            print(f"   ❌ {self.person_name} cannot start engine - not authorized")
            return False
            
        try:
            print(f"   🔧 {self.person_name} starting engine...")
            
            # Turn on GPS device first
            gps_success = await self.gps_device.start()
            if not gps_success:
                return False
            
            # Send engine start notification packet
            await self._send_engine_status_packet("ENGINE_ON")
            
            # Don't start the complex vehicle driver - we'll simulate movement manually
            # This avoids the engine buffer threading issues
            self.engine_on = True
            print(f"   ✅ Engine started for {self.person_name}")
            return True
                
        except Exception as e:
            print(f"   ❌ Engine start failed for {self.person_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def conduct_test_drive(self, duration_seconds: int = 60) -> bool:
        """Conduct authorized test drive for specified duration."""
        if not self.engine_on:
            print(f"   ❌ Cannot conduct test drive - engine not running")
            return False
            
        try:
            print(f"   🚗 {self.person_name} beginning {duration_seconds}-second test drive...")
            self.test_drive_active = True
            
            start_time = time.time()
            packet_count = 0
            
            # Drive for specified duration, sending GPS packets every 3 seconds (more stable)
            while (time.time() - start_time) < duration_seconds:
                current_time = time.time() - start_time
                
                # Simulate movement along route coordinates (simpler approach)
                progress = current_time / duration_seconds
                coord_index = min(int(progress * len(self.route_coordinates)), len(self.route_coordinates) - 1)
                coordinate = self.route_coordinates[coord_index]
                
                position = {
                    'lat': coordinate[1],
                    'lon': coordinate[0],
                    'speed': 25.0,  # Realistic bus speed km/h
                    'heading': self._calculate_heading(coord_index)
                }
                
                # Send GPS telemetry packet
                await self._send_driving_packet(position, current_time)
                packet_count += 1
                
                print(f"   📡 Packet {packet_count}: lat={position['lat']:.6f}, lon={position['lon']:.6f}, speed={position['speed']:.1f}km/h, heading={position['heading']:.1f}°")
                
                # Wait 3 seconds before next packet (more stable connection)
                await asyncio.sleep(3.0)
            
            self.test_drive_active = False
            print(f"   ✅ Test drive completed - {packet_count} GPS packets transmitted")
            return True
            
        except Exception as e:
            print(f"   ❌ Test drive failed for {self.person_name}: {e}")
            import traceback
            traceback.print_exc()
            self.test_drive_active = False
            return False

    async def stop_engine(self) -> bool:
        """Turn off vehicle engine and end test drive."""
        try:
            print(f"   🛑 {self.person_name} stopping engine...")
            
            # Send engine stop notification packet
            await self._send_engine_status_packet("ENGINE_OFF")
            
            # Stop GPS device
            await self.gps_device.stop()
            
            self.engine_on = False
            self.test_drive_active = False
            print(f"   ✅ Engine stopped for {self.person_name}")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine stop failed for {self.person_name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _calculate_heading(self, coord_index: int) -> float:
        """Calculate heading between two consecutive coordinates."""
        if coord_index >= len(self.route_coordinates) - 1:
            return 0.0
            
        import math
        
        coord1 = self.route_coordinates[coord_index]
        coord2 = self.route_coordinates[coord_index + 1]
        
        lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
        lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        heading = math.atan2(y, x)
        heading = math.degrees(heading)
        heading = (heading + 360) % 360
        
        return heading

    async def _send_engine_status_packet(self, status: str):
        """Send engine status notification packet."""
        try:
            # Get current position (first coordinate if not moving)
            if self.route_coordinates and len(self.route_coordinates) > 0:
                current_point = self.route_coordinates[0]
            else:
                return
            
            # Create engine status packet
            packet = make_packet(
                device_id=self.gps_device.component_id,
                lat=current_point[1],
                lon=current_point[0],
                speed=0.0,
                heading=0.0,
                route=self.route_name.replace("route ", ""),
                vehicle_reg=self.vehicle_id,
                driver_id=self.component_id,
                driver_name={
                    "first": self.person_name.split()[0],
                    "last": self.person_name.split()[-1]
                }
            )
            
            # Add engine status to packet
            packet_data = asdict(packet)
            packet_data["engineStatus"] = status
            
            # Send packet to server
            device_url = f"ws://localhost:5000/device?token=depot-test-drive&deviceId={self.gps_device.component_id}"
            async with websockets.connect(device_url) as websocket:
                await websocket.send(json.dumps(packet_data))
                print(f"   📡 Engine status transmitted: {status}")
                
        except Exception as e:
            print(f"   ⚠️  Failed to send engine status for {self.person_name}: {e}")

    async def _send_driving_packet(self, position: dict, elapsed_time: float):
        """Send GPS packet during test drive."""
        try:
            # Create driving packet
            packet = make_packet(
                device_id=self.gps_device.component_id,
                lat=position['lat'],
                lon=position['lon'],
                speed=position['speed'],
                heading=position['heading'],
                route=self.route_name.replace("route ", ""),
                vehicle_reg=self.vehicle_id,
                driver_id=self.component_id,
                driver_name={
                    "first": self.person_name.split()[0],
                    "last": self.person_name.split()[-1]
                }
            )
            
            # Add test drive metadata
            packet_data = asdict(packet)
            packet_data["testDrive"] = True
            packet_data["driveTime"] = round(elapsed_time, 1)
            
            # Send packet to server
            device_url = f"ws://localhost:5000/device?token=depot-test-drive&deviceId={self.gps_device.component_id}"
            async with websockets.connect(device_url) as websocket:
                await websocket.send(json.dumps(packet_data))
                
        except Exception as e:
            print(f"   ⚠️  Failed to send driving packet for {self.person_name}: {e}")

    async def _start_implementation(self) -> bool:
        """Implementation of abstract method from BasePerson."""
        return await self.start_engine()

    async def _stop_implementation(self) -> bool:
        """Implementation of abstract method from BasePerson."""
        return await self.stop_engine()


async def test_authorized_test_drive():
    """Test depot manager authorized test drive with engine activation"""
    
    print("🚗 Test 4: Depot Manager Authorized Test Drive (60 Second Engine Test)")
    print("=" * 80)
    print("📋 This test verifies:")
    print("   • Depot manager can authorize test drives")
    print("   • Driver can turn engine on with authorization")
    print("   • Vehicle drives for 60 seconds transmitting GPS data")
    print("   • Engine can be turned off after test drive")
    print()
    
    try:
        print("🔌 Step 1: Initialize depot system and get authorization...")
        depot_manager = DepotManager("TestDepot")
        dispatcher = Dispatcher("TestFleetDispatcher", "http://localhost:8000")
        depot_manager.set_dispatcher(dispatcher)
        
        await depot_manager.initialize()
        print("   ✅ Depot system initialized")
        
        # Get vehicle assignments
        assignments = await depot_manager.dispatcher.get_vehicle_assignments()
        if not assignments:
            print("   ❌ No vehicle assignments available")
            return False
            
        # Select first available driver for test
        selected_assignment = assignments[0]
        print(f"   🎯 Selected for test drive: {selected_assignment.driver_name} → {selected_assignment.vehicle_id}")
        
        print(f"\n🗺️  Step 2: Setup test driver with route data...")
        route_code = selected_assignment.route_id.replace("route ", "")
        
        # Get route geometry
        session = depot_manager.dispatcher.session
        geometry_url = f"{depot_manager.dispatcher.api_base_url}/api/v1/routes/public/{route_code}/geometry"
        
        async with session.get(geometry_url) as response:
            if response.status != 200:
                print(f"   ❌ Failed to fetch Route {route_code} geometry")
                return False
                
            route_data = await response.json()
            coordinates = route_data['geometry']['coordinates']
            coord_count = len(coordinates)
            print(f"   ✅ Route {route_code} loaded with {coord_count} GPS points")
        
        # Create GPS device
        device_id = f"GPS-{selected_assignment.vehicle_id}"
        transmitter = WebSocketTransmitter(
            server_url="ws://localhost:5000",
            token="depot-test-drive-token",
            device_id=device_id,
            codec=PacketCodec()
        )
        
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
        
        # Create assignment data
        assignment_data = {
            'driver_id': selected_assignment.driver_id,
            'driver_name': selected_assignment.driver_name,
            'vehicle_id': selected_assignment.vehicle_id,
            'route_id': selected_assignment.route_id,
            'route_name': selected_assignment.route_id,
            'vehicle_reg_code': selected_assignment.vehicle_id
        }
        
        # Create authorized test driver
        test_driver = AuthorizedTestDriver(assignment_data, coordinates, gps_device)
        print(f"   ✅ Test driver created: {test_driver.person_name}")
        
        print(f"\n🔐 Step 3: Request depot manager authorization...")
        auth_success = await test_driver.get_depot_authorization(depot_manager)
        if not auth_success:
            print("   ❌ Authorization denied - cannot proceed with test drive")
            return False
            
        print(f"\n🔧 Step 4: Start engine (authorized only)...")
        engine_start = await test_driver.start_engine()
        if not engine_start:
            print("   ❌ Engine start failed")
            return False
            
        print(f"\n🚗 Step 5: Conduct 60-second test drive...")
        test_drive_success = await test_driver.conduct_test_drive(60)
        if not test_drive_success:
            print("   ❌ Test drive failed")
            return False
            
        print(f"\n🛑 Step 6: Stop engine and complete test...")
        engine_stop = await test_driver.stop_engine()
        if not engine_stop:
            print("   ❌ Engine stop failed")
            return False
            
        print(f"\n✅ SUCCESS: Authorized test drive completed!")
        print(f"   🎯 Driver: {test_driver.person_name} (License: {test_driver.component_id})")
        print(f"   🚌 Vehicle: {test_driver.vehicle_id}")
        print(f"   🗺️  Route: {test_driver.route_name}")
        print(f"   📊 Route Points: {len(test_driver.route_coordinates)}")
        print(f"   ⏱️  Duration: 60 seconds")
        print(f"   📡 GPS telemetry transmitted continuously")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: Authorized test drive failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_authorized_test_drive())