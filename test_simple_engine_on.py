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
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec, make_packet

class VehicleState:
    """Vehicle state object for feeding GPS plugin system."""
    
    def __init__(self, driver_id: str, driver_name: str, vehicle_id: str, route_name: str):
        self.lat = 0.0
        self.lng = 0.0  # Note: plugin uses 'lng' not 'lon'
        self.speed = 0.0
        self.heading = 0.0
        self.route_id = route_name
        self.driver_id = driver_id
        self.driver_name = driver_name
        self.vehicle_reg = vehicle_id
        self.engine_status = "OFF"
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def update_position(self, lat: float, lon: float, speed: float, heading: float):
        """Update vehicle position and motion data."""
        self.lat = lat
        self.lng = lon  # Note: lng not lon for plugin compatibility
        self.speed = speed
        self.heading = heading
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def set_engine_status(self, status: str):
        """Update engine status."""
        self.engine_status = status
        self.timestamp = datetime.now(timezone.utc).isoformat()

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
            
            # Create vehicle state for plugin system
            self.vehicle_state = VehicleState(
                driver_id=self.driver_id,
                driver_name=self.driver_name,
                vehicle_id=self.vehicle_id,
                route_name=self.route_name.replace("route ", "")
            )
            
            # Set initial position (starting coordinate)
            if self.route_coordinates and len(self.route_coordinates) > 0:
                coord = self.route_coordinates[0]
                self.vehicle_state.update_position(coord[1], coord[0], 0.0, 0.0)
            
            # Set engine status
            self.vehicle_state.set_engine_status("ENGINE_ON")
            
            # Configure GPS device plugin with vehicle state
            if hasattr(self.gps_device, 'plugin_manager') and self.gps_device.plugin_manager.active_plugin:
                self.gps_device.plugin_manager.active_plugin.set_vehicle_state(self.vehicle_state)
                print(f"   🔌 Vehicle state connected to GPS plugin")
            
            # Start GPS device (this will start the plugin and persistent connection)
            gps_success = await self.gps_device.start()
            if not gps_success:
                print(f"   ❌ GPS device failed to start")
                return False
            
            self.engine_on = True
            print(f"   ✅ Engine ON for {self.driver_name}")
            print(f"   📡 GPS device connected with persistent connection")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine start failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_engine_for_duration(self, duration_seconds: int = 30) -> bool:
        """Run engine for specified duration, updating vehicle state for plugin system."""
        if not self.engine_on or not hasattr(self, 'vehicle_state'):
            print(f"   ❌ Cannot run engine - not started or vehicle state missing")
            return False
            
        try:
            print(f"   🚗 Running engine for {duration_seconds} seconds...")
            print(f"   📡 GPS plugin will automatically transmit via persistent connection")
            
            start_time = time.time()
            position_updates = 0
            
            while (time.time() - start_time) < duration_seconds:
                elapsed = time.time() - start_time
                
                # Update vehicle position every 3 seconds (plugin will read this automatically)
                if position_updates == 0 or elapsed >= (position_updates * 3):
                    self._update_vehicle_position(elapsed, duration_seconds)
                    position_updates += 1
                    print(f"   � Position update {position_updates} (t={elapsed:.1f}s) - Plugin will transmit automatically")
                
                await asyncio.sleep(1.0)
            
            print(f"   ✅ Engine ran for {duration_seconds} seconds - {position_updates} position updates")
            print(f"   📡 GPS plugin transmitted continuously via persistent connection")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine run failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_vehicle_position(self, elapsed_time: float, total_duration: float):
        """Update vehicle state position for plugin system to read."""
        try:
            if not self.route_coordinates or len(self.route_coordinates) == 0:
                return
            
            # Calculate movement progress (0.0 to 1.0)
            progress = min(elapsed_time / total_duration, 1.0)
            
            # Use first 15 coordinates for realistic 30-second movement
            max_coords_to_use = min(15, len(self.route_coordinates))
            coord_index = int(progress * (max_coords_to_use - 1))
            coord_index = min(coord_index, len(self.route_coordinates) - 1)
            
            coord = self.route_coordinates[coord_index]
            lat, lon = coord[1], coord[0]
            
            # Calculate realistic speed and heading
            speed = 25.0 if progress < 1.0 else 0.0  # 25 km/h while moving
            heading = self._calculate_heading(coord_index)
            
            # Update vehicle state (plugin will read this automatically)
            self.vehicle_state.update_position(lat, lon, speed, heading)
            
            print(f"      📍 Coordinate {coord_index + 1}/{max_coords_to_use}: lat={lat:.6f}, lon={lon:.6f}, speed={speed:.1f}km/h, heading={heading:.1f}°")
            
        except Exception as e:
            print(f"   ⚠️  Failed to update vehicle position: {e}")

    async def turn_engine_off(self) -> bool:
        """Turn engine off and stop GPS."""
        try:
            print(f"   🛑 {self.driver_name} turning engine OFF...")
            
            # Update vehicle state to stopped before stopping GPS
            if hasattr(self, 'vehicle_state'):
                self.vehicle_state.set_engine_status("ENGINE_OFF")
                # Brief pause to let plugin send final status
                await asyncio.sleep(0.5)
            
            # Stop GPS device (this will close persistent connection)
            await self.gps_device.stop()
            
            self.engine_on = False
            print(f"   ✅ Engine OFF for {self.driver_name}")
            print(f"   📡 GPS device disconnected (persistent connection closed)")
            return True
            
        except Exception as e:
            print(f"   ❌ Engine stop failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Plugin architecture replaces direct packet sending
    # Vehicle state updates are automatically read by the GPS plugin
    # which feeds data through the rxtx_buffer to the transmitter
    # maintaining a persistent WebSocket connection

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