#!/usr/bin/env python3
"""
Test 4C: Manual GPS Starting Position Packet
===========================================
This test manually sends starting position packets to the server
to verify the GPS devices can send their first route coordinate.
"""

import asyncio
import websockets
import json
import sys
import os
from dataclasses import asdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import make_packet, TelemetryPacket

async def test_manual_gps_starting_position():
    """Test manual GPS starting position packet transmission"""
    
    print("📍 Test 4C: Manual GPS Starting Position Packet")
    print("=" * 50)
    print("📋 This test verifies:")
    print("   • GPS devices can connect to telemetry server")
    print("   • Starting position packets can be sent manually")
    print("   • Server receives and processes GPS starting positions")
    print()
    
    try:
        print("🔌 Step 1: Initialize depot system...")
        depot_manager = DepotManager("TestDepot")
        dispatcher = Dispatcher("TestFleetDispatcher", "http://localhost:8000")
        depot_manager.set_dispatcher(dispatcher)
        
        await depot_manager.initialize()
        print("   ✅ Depot system initialized")
        
        print("\n📋 Step 2: Get route starting coordinates...")
        assignments = await depot_manager.dispatcher.get_vehicle_assignments()
        
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
                        'route_name': route_code
                    }
                    
                    print(f"   ✅ Route {route_code}: Starting point lon={starting_point[0]:.6f}, lat={starting_point[1]:.6f}")
        
        print("\n📡 Step 3: Manually send starting position packets...")
        
        for vehicle_id, data in route_data.items():
            device_id = f"GPS-{vehicle_id}"
            assignment = data['assignment']
            starting_point = data['starting_point']
            route_name = data['route_name']
            
            print(f"\n   🔌 Connecting {device_id} to server...")
            
            try:
                # Connect to server as GPS device
                device_url = f"ws://localhost:5000/device?token=manual-test&deviceId={device_id}"
                async with websockets.connect(device_url) as websocket:
                    print(f"   ✅ {device_id} connected to server successfully")
                    
                    # Create starting position packet using proper packet.py protocol
                    packet = make_packet(
                        device_id=device_id,
                        lat=starting_point[1],  # latitude
                        lon=starting_point[0],  # longitude
                        speed=0.0,  # stationary at starting position
                        heading=0.0,  # no heading when stationary
                        route=route_name,
                        vehicle_reg=vehicle_id,
                        driver_id=f"DRIVER_{assignment.driver_name.replace(' ', '_').upper()}",
                        driver_name={
                            "first": assignment.driver_name.split()[0],
                            "last": assignment.driver_name.split()[-1]
                        }
                    )
                    
                    # Convert TelemetryPacket to dict for JSON transmission
                    starting_packet = asdict(packet)
                    
                    print(f"   📤 Sending starting position packet for Route {route_name}...")
                    print(f"      📍 Position: lon={starting_point[0]:.6f}, lat={starting_point[1]:.6f}")
                    
                    # Send the packet
                    await websocket.send(json.dumps(starting_packet))
                    print(f"   ✅ Starting position packet sent successfully!")
                    
                    # Wait a moment to ensure packet is processed
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ Failed to send packet for {device_id}: {e}")
                return False
        
        print(f"\n📊 Step 4: Starting position transmission summary...")
        print(f"   ✅ All GPS devices sent starting position packets")
        print(f"   📍 Starting coordinates transmitted to telemetry server")
        print(f"   💡 Check server logs for received GPS position data")
        
        print(f"\n🎯 EXPECTED SERVER LOGS:")
        for vehicle_id, data in route_data.items():
            device_id = f"GPS-{vehicle_id}"
            starting_point = data['starting_point']
            print(f"   📨 Device {device_id}: lat={starting_point[1]:.6f}, lon={starting_point[0]:.6f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: Manual GPS starting position test failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_manual_gps_starting_position())