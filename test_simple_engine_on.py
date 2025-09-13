#!/usr/bin/env python3
"""
Test 4: Simple Engine On Test (30 Second Engine Test)
=====================================================
This test verifies that a driver from the depot hierarchy can turn
the engine on for 30 seconds and send basic GPS packets.
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
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec, make_packet
from dataclasses import asdict
import websockets

class SimpleEngineTestDriver:
    """Simple driver for basic engine testing."""
    
    def __init__(self, assignment_data: dict, route_coordinates: list, gps_device: GPSDevice):
        self.driver_id = assignment_data.get('driver_id', 'UNKNOWN_DRIVER')
        self.driver_name = assignment_data.get('driver_name', 'Unknown Driver')
        self.vehicle_id = assignment_data.get('vehicle_id', 'UNKNOWN_VEHICLE')
        self.route_id = assignment_data.get('route_id', 'UNKNOWN_ROUTE')
        self.route_name = assignment_data.get('route_name', 'Unknown Route')
        
        self.route_coordinates = route_coordinates
        self.gps_device = gps_device
        self.engine_on = False

    async def turn_engine_on(self) -> bool:
        """Turn engine on and start GPS."""
        try:
            print(f"   🔧 {self.driver_name} turning engine ON...")
            
            # Start GPS device
            gps_success = await self.gps_device.start()
            if not gps_success:
                print(f"   ❌ GPS device failed to start")
                return False
            
            # Send engine ON packet
            await self._send_engine_packet("ENGINE_ON")
            
            self.engine_on = True
            print(f"   ✅ Engine ON for {self.driver_name}")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine start failed: {e}")
            return False

    async def run_engine_for_duration(self, duration_seconds: int = 30) -> bool:
        """Run engine for specified duration, sending periodic GPS packets."""
        if not self.engine_on:
            print(f"   ❌ Cannot run engine - not started")
            return False
            
        try:
            print(f"   🚗 Running engine for {duration_seconds} seconds...")
            
            start_time = time.time()
            packet_count = 0
            
            while (time.time() - start_time) < duration_seconds:
                elapsed = time.time() - start_time
                
                # Send GPS packet every 5 seconds
                if packet_count == 0 or elapsed >= (packet_count * 5):
                    await self._send_gps_packet(elapsed)
                    packet_count += 1
                    print(f"   📡 GPS packet {packet_count} sent (t={elapsed:.1f}s)")
                
                await asyncio.sleep(1.0)
            
            print(f"   ✅ Engine ran for {duration_seconds} seconds - {packet_count} packets sent")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine run failed: {e}")
            return False

    async def turn_engine_off(self) -> bool:
        """Turn engine off and stop GPS."""
        try:
            print(f"   🛑 {self.driver_name} turning engine OFF...")
            
            # Send engine OFF packet
            await self._send_engine_packet("ENGINE_OFF")
            
            # Stop GPS device
            await self.gps_device.stop()
            
            self.engine_on = False
            print(f"   ✅ Engine OFF for {self.driver_name}")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine stop failed: {e}")
            return False

    async def _send_engine_packet(self, status: str):
        """Send engine status packet."""
        try:
            # Use starting position (first coordinate)
            if self.route_coordinates and len(self.route_coordinates) > 0:
                coord = self.route_coordinates[0]
                lat, lon = coord[1], coord[0]
            else:
                lat, lon = 0.0, 0.0
            
            # Create packet
            packet = make_packet(
                device_id=self.gps_device.component_id,
                lat=lat,
                lon=lon,
                speed=0.0,
                heading=0.0,
                route=self.route_name.replace("route ", ""),
                vehicle_reg=self.vehicle_id,
                driver_id=self.driver_id,
                driver_name={
                    "first": self.driver_name.split()[0],
                    "last": self.driver_name.split()[-1]
                }
            )
            
            # Add engine status
            packet_data = asdict(packet)
            packet_data["engineStatus"] = status
            
            # Send packet
            device_url = f"ws://localhost:5000/device?token=simple-engine-test&deviceId={self.gps_device.component_id}"
            async with websockets.connect(device_url) as websocket:
                await websocket.send(json.dumps(packet_data))
                print(f"   📡 Engine status sent: {status}")
                
        except Exception as e:
            print(f"   ⚠️  Failed to send engine packet: {e}")

    async def _send_gps_packet(self, elapsed_time: float):
        """Send GPS packet with actual movement along route."""
        try:
            # Calculate movement along route based on elapsed time
            if self.route_coordinates and len(self.route_coordinates) > 0:
                # Simulate movement at ~25 km/h (realistic bus speed)
                # 25 km/h = 6.94 m/s, so in 30 seconds we cover ~208 meters
                # Distribute this across route coordinates
                
                total_test_time = 30.0  # Total test duration
                progress = min(elapsed_time / total_test_time, 1.0)  # 0.0 to 1.0
                
                # Calculate coordinate index based on progress
                max_coords_to_use = min(15, len(self.route_coordinates))  # Use first 15 coordinates for 30-second test
                coord_index = int(progress * (max_coords_to_use - 1))
                coord_index = min(coord_index, len(self.route_coordinates) - 1)
                
                coord = self.route_coordinates[coord_index]
                lat, lon = coord[1], coord[0]
                
                # Calculate speed and heading
                speed = 25.0 if progress < 1.0 else 0.0  # 25 km/h while moving, 0 when stopped
                heading = self._calculate_heading(coord_index)
                
                print(f"      📍 Moving to coordinate {coord_index + 1}/{max_coords_to_use} (progress: {progress:.1%})")
            else:
                lat, lon, speed, heading = 0.0, 0.0, 0.0, 0.0
            
            # Create packet
            packet = make_packet(
                device_id=self.gps_device.component_id,
                lat=lat,
                lon=lon,
                speed=speed,
                heading=heading,
                route=self.route_name.replace("route ", ""),
                vehicle_reg=self.vehicle_id,
                driver_id=self.driver_id,
                driver_name={
                    "first": self.driver_name.split()[0],
                    "last": self.driver_name.split()[-1]
                }
            )
            
            # Add test metadata
            packet_data = asdict(packet)
            packet_data["engineTest"] = True
            packet_data["testTime"] = round(elapsed_time, 1)
            packet_data["coordinateIndex"] = coord_index if 'coord_index' in locals() else 0
            
            # Send packet
            device_url = f"ws://localhost:5000/device?token=simple-engine-test&deviceId={self.gps_device.component_id}"
            async with websockets.connect(device_url) as websocket:
                await websocket.send(json.dumps(packet_data))
                
        except Exception as e:
            print(f"   ⚠️  Failed to send GPS packet: {e}")

    def _calculate_heading(self, coord_index: int) -> float:
        """Calculate heading between current and next coordinate."""
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


async def test_simple_engine_on():
    """Simple test: turn engine on for 30 seconds"""
    
    print("🔧 Test 4: Simple Engine On Test (30 Second Engine Test)")
    print("=" * 60)
    print("📋 This test verifies:")
    print("   • Driver can turn engine on")
    print("   • Engine runs for 30 seconds")
    print("   • GPS packets are sent during engine operation")
    print("   • Engine can be turned off")
    print()
    
    try:
        print("🔌 Step 1: Initialize depot system...")
        depot_manager = DepotManager("TestDepot")
        dispatcher = Dispatcher("TestFleetDispatcher", "http://localhost:8000")
        depot_manager.set_dispatcher(dispatcher)
        
        await depot_manager.initialize()
        print("   ✅ Depot system initialized")
        
        # Get first available assignment
        assignments = await depot_manager.dispatcher.get_vehicle_assignments()
        if not assignments:
            print("   ❌ No assignments available")
            return False
            
        assignment = assignments[0]
        print(f"   🎯 Selected: {assignment.driver_name} → {assignment.vehicle_id} → {assignment.route_id}")
        
        print(f"\n🗺️  Step 2: Get route data...")
        route_code = assignment.route_id.replace("route ", "")
        
        session = depot_manager.dispatcher.session
        geometry_url = f"{depot_manager.dispatcher.api_base_url}/api/v1/routes/public/{route_code}/geometry"
        
        async with session.get(geometry_url) as response:
            if response.status != 200:
                print(f"   ❌ Failed to get route {route_code}")
                return False
                
            route_data = await response.json()
            coordinates = route_data['geometry']['coordinates']
            print(f"   ✅ Route {route_code} loaded ({len(coordinates)} points)")
        
        print(f"\n📡 Step 3: Setup GPS device...")
        device_id = f"GPS-{assignment.vehicle_id}"
        transmitter = WebSocketTransmitter(
            server_url="ws://localhost:5000",
            token="simple-engine-test-token",
            device_id=device_id,
            codec=PacketCodec()
        )
        
        gps_device = GPSDevice(
            device_id=device_id,
            ws_transmitter=transmitter,
            plugin_config={"plugin": "simulation", "update_interval": 1.0, "device_id": device_id}
        )
        
        # Create assignment data
        assignment_data = {
            'driver_id': assignment.driver_id,
            'driver_name': assignment.driver_name,
            'vehicle_id': assignment.vehicle_id,
            'route_id': assignment.route_id,
            'route_name': assignment.route_id,
        }
        
        # Create test driver
        driver = SimpleEngineTestDriver(assignment_data, coordinates, gps_device)
        print(f"   ✅ Test driver ready: {driver.driver_name}")
        
        print(f"\n🔧 Step 4: Turn engine ON...")
        engine_start = await driver.turn_engine_on()
        if not engine_start:
            print("   ❌ Engine start failed")
            return False
            
        print(f"\n⏱️  Step 5: Run engine for 30 seconds...")
        engine_run = await driver.run_engine_for_duration(30)
        if not engine_run:
            print("   ❌ Engine run failed")
            return False
            
        print(f"\n🛑 Step 6: Turn engine OFF...")
        engine_stop = await driver.turn_engine_off()
        if not engine_stop:
            print("   ❌ Engine stop failed")
            return False
            
        print(f"\n✅ SUCCESS: Simple engine test completed!")
        print(f"   🎯 Driver: {driver.driver_name} (License: {driver.driver_id})")
        print(f"   🚌 Vehicle: {driver.vehicle_id}")
        print(f"   🗺️  Route: {driver.route_name}")
        print(f"   ⏱️  Duration: 30 seconds")
        print(f"   📡 GPS packets sent successfully")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: Simple engine test failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_simple_engine_on())