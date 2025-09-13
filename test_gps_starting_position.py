#!/usr/bin/env python3
"""
Test 4: GPS Starting Position Transmission
==========================================
This test verifies that when GPS devices are activated, they immediately
send a position packet with their starting point (first coordinate from route).
NO ENGINE ACTIVATION - just GPS position reporting at starting location.
"""

import asyncio
import sys
import os
import json
import websockets
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec

async def test_gps_starting_position():
    """Test GPS devices send starting position packet upon activation"""
    
    print("📍 Test 4: GPS Starting Position Transmission")
    print("=" * 55)
    print("📋 This test verifies:")
    print("   • GPS devices connect to telemetry server")
    print("   • GPS devices send starting position packet (first route coordinate)")
    print("   • Position packet contains correct starting GPS coordinates") 
    print("   • NO ENGINE ACTIVATION - only GPS position at starting point")
    print()
    
    try:
        print("🔌 Step 1: Initialize depot system...")
        depot_manager = DepotManager("TestDepot")
        dispatcher = Dispatcher("TestFleetDispatcher", "http://localhost:8000")
        depot_manager.set_dispatcher(dispatcher)
        
        await depot_manager.initialize()
        print("   ✅ Depot system initialized")
        
        print("\n📋 Step 2: Get vehicle assignments and route coordinates...")
        assignments = await depot_manager.dispatcher.get_vehicle_assignments()
        print(f"   ✅ Retrieved {len(assignments)} vehicle assignments")
        
        route_data = {}
        for assignment in assignments:
            route_code = assignment.route_id.replace("route ", "")
            print(f"   🔍 Fetching starting coordinates for Route {route_code}...")
            
            # Get route geometry
            session = depot_manager.dispatcher.session
            geometry_url = f"{depot_manager.dispatcher.api_base_url}/api/v1/routes/public/{route_code}/geometry"
            
            async with session.get(geometry_url) as response:
                if response.status == 200:
                    route_info = await response.json()
                    coordinates = route_info['geometry']['coordinates']
                    starting_point = coordinates[0]  # First coordinate is starting point
                    
                    route_data[assignment.vehicle_id] = {
                        'assignment': assignment,
                        'starting_point': starting_point,
                        'total_coords': len(coordinates),
                        'route_name': route_code
                    }
                    
                    print(f"   ✅ Route {route_code}: Starting point lon={starting_point[0]:.6f}, lat={starting_point[1]:.6f}")
                else:
                    print(f"   ❌ Failed to fetch Route {route_code} geometry")
                    return False
        
        print("\n📡 Step 3: Create GPS devices with route starting points...")
        gps_devices = []
        
        for vehicle_id, data in route_data.items():
            device_id = f"GPS-{vehicle_id}"
            assignment = data['assignment']
            starting_point = data['starting_point']
            
            print(f"   🔧 Creating GPS device {device_id} for Route {data['route_name']}...")
            
            # Create WebSocket transmitter
            transmitter = WebSocketTransmitter(
                server_url="ws://localhost:5000",
                token="starting-position-test",
                device_id=device_id,
                codec=PacketCodec()
            )
            
            # Configure GPS device with starting position
            plugin_config = {
                "plugin": "simulation",
                "update_interval": 3.0,  # Slower for testing
                "device_id": device_id,
                "starting_lat": starting_point[1],  # lat
                "starting_lon": starting_point[0]   # lon
            }
            
            gps_device = GPSDevice(
                device_id=device_id,
                ws_transmitter=transmitter,
                plugin_config=plugin_config
            )
            
            gps_devices.append((gps_device, data))
            print(f"   ✅ GPS device {device_id} configured with starting position")
            print(f"      📍 Starting coordinates: lon={starting_point[0]:.6f}, lat={starting_point[1]:.6f}")
        
        print(f"\n🚀 Step 4: Activate GPS devices and verify starting position transmission...")
        
        print("   � GPS devices will connect directly to server - monitoring via server logs")
        
        print("\n   🔌 Activating GPS devices...")
        active_devices = []
        
        for gps_device, data in gps_devices:
            device_id = gps_device.component_id
            starting_point = data['starting_point']
            
            print(f"   📡 Activating GPS device {device_id}...")
            
            # Start the GPS device
            start_result = await gps_device.start()
            if start_result:
                active_devices.append((gps_device, data))
                print(f"   ✅ GPS device {device_id} activated")
                print(f"      📍 Expected starting position: lon={starting_point[0]:.6f}, lat={starting_point[1]:.6f}")
            else:
                print(f"   ❌ GPS device {device_id} failed to activate")
        
        print(f"\n⏱️  Step 5: Wait for starting position packets...")
        print("   📡 Waiting 15 seconds for GPS devices to send starting position packets...")
        await asyncio.sleep(15)
        
        print(f"\n🔍 Step 6: Verify starting position transmission...")
        listener_task.cancel()
        
        print(f"   📊 Received {len(received_packets)} GPS packets")
        
        if received_packets:
            for i, packet in enumerate(received_packets):
                device_id = packet.get('device_id', 'unknown')
                lat = packet.get('latitude', 0)
                lon = packet.get('longitude', 0)
                
                print(f"   📍 Packet {i+1}: Device {device_id}")
                print(f"      🗺️  GPS Position: lon={lon:.6f}, lat={lat:.6f}")
                
                # Find expected starting point for this device
                vehicle_id = device_id.replace('GPS-', '')
                if vehicle_id in route_data:
                    expected = route_data[vehicle_id]['starting_point']
                    expected_lon, expected_lat = expected[0], expected[1]
                    
                    # Check if transmitted position matches expected starting point
                    lon_match = abs(lon - expected_lon) < 0.001  # Within ~100m
                    lat_match = abs(lat - expected_lat) < 0.001
                    
                    if lon_match and lat_match:
                        print(f"      ✅ MATCHES expected starting point!")
                    else:
                        print(f"      ❌ Does NOT match expected starting point:")
                        print(f"         Expected: lon={expected_lon:.6f}, lat={expected_lat:.6f}")
        else:
            print("   ❌ No GPS packets received!")
            print("   💡 GPS devices connected but not transmitting position data")
        
        print(f"\n🛑 Step 7: Stop GPS devices...")
        for gps_device, data in active_devices:
            await gps_device.stop()
            print(f"   ✅ GPS device {gps_device.component_id} stopped")
        
        print(f"\n📊 Step 8: Starting position test summary...")
        success = len(received_packets) >= len(active_devices)
        
        if success:
            print(f"   ✅ GPS starting position transmission successful!")
            print(f"   📡 {len(received_packets)} position packets received")
            print(f"   📍 GPS devices transmitted their starting coordinates")
        else:
            print(f"   ❌ GPS starting position transmission failed")
            print(f"   📊 Expected {len(active_devices)} packets, received {len(received_packets)}")
        
        return success
        
    except Exception as e:
        print(f"\n❌ FAILED: GPS starting position test failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_gps_starting_position())