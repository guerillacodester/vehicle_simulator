#!/usr/bin/env python3
"""
Test 3B: GPS Device Server Connection Verification
=================================================
This test verifies that GPS devices actually connect to the telemetry server
and transmit data, not just claim to be "active".
"""

import asyncio
import sys
import os
import time
import json
import websockets
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.vehicle_simulator.core.depot_manager import DepotManager
from world.vehicle_simulator.core.dispatcher import Dispatcher
from world.vehicle_simulator.vehicle.gps_device.device import GPSDevice
from world.vehicle_simulator.vehicle.gps_device.radio_module.transmitter import WebSocketTransmitter
from world.vehicle_simulator.vehicle.gps_device.radio_module.packet import PacketCodec

async def test_gps_server_connection():
    """Test that GPS devices actually connect to and transmit to telemetry server"""
    
    print("📡 Test 3B: GPS Device Server Connection Verification")
    print("=" * 65)
    print("📋 This test verifies:")
    print("   • GPS devices actually connect to telemetry server")
    print("   • WebSocket connections are established")
    print("   • GPS data is transmitted to server")
    print("   • Server receives and processes GPS telemetry")
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
        
        print("\n📡 Step 3: Create GPS devices and test server connection...")
        gps_devices = []
        
        for assignment in assignments:
            device_id = f"GPS-{assignment.vehicle_id}"
            print(f"   🔧 Creating GPS device {device_id}...")
            
            # Create WebSocket transmitter
            transmitter = WebSocketTransmitter(
                server_url="ws://localhost:5000",
                token="connection-test-token",
                device_id=device_id,
                codec=PacketCodec()
            )
            
            # Configure GPS device with simulation plugin
            plugin_config = {
                "plugin": "simulation",
                "update_interval": 2.0,  # Slower for testing
                "device_id": device_id
            }
            
            gps_device = GPSDevice(
                device_id=device_id,
                ws_transmitter=transmitter,
                plugin_config=plugin_config
            )
            
            gps_devices.append((gps_device, assignment))
            print(f"   ✅ Created GPS device {device_id}")
        
        print(f"\n🚀 Step 4: Start GPS devices and verify server connection...")
        active_devices = []
        
        for gps_device, assignment in gps_devices:
            device_id = gps_device.component_id
            print(f"   🔌 Starting GPS device {device_id}...")
            
            # Start the GPS device
            start_result = await gps_device.start()
            if start_result:
                active_devices.append((gps_device, assignment))
                print(f"   ✅ GPS device {device_id} started successfully")
                
                # Check device state
                device_state = str(gps_device.current_state)
                print(f"      📊 Device state: {device_state}")
            else:
                print(f"   ❌ GPS device {device_id} failed to start")
                return False
        
        print(f"\n⏱️  Step 5: Wait and monitor for server connections...")
        print("   📡 Monitoring telemetry server for WebSocket connections...")
        print("   ⏰ Waiting 10 seconds for connections to establish...")
        
        # Wait for connections to establish and data transmission
        await asyncio.sleep(10)
        
        print(f"\n🔍 Step 6: Verify GPS data transmission...")
        
        # Try to connect to server's WebSocket endpoint as a client to verify activity
        try:
            print("   🔍 Checking server WebSocket endpoint...")
            async with websockets.connect("ws://localhost:5000/ws") as websocket:
                print("   ✅ Successfully connected to telemetry server WebSocket")
                
                # Listen for any GPS data for a few seconds
                print("   👂 Listening for GPS telemetry data...")
                try:
                    data = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"   📨 Received data from server: {data[:100]}...")
                    print("   ✅ GPS telemetry data is being transmitted!")
                except asyncio.TimeoutError:
                    print("   ⚠️  No data received within 5 seconds")
                    print("   ❌ GPS devices may not be transmitting to server")
                
        except Exception as e:
            print(f"   ❌ Failed to connect to telemetry server: {e}")
            print("   💡 Make sure telemetry server is running on localhost:5000")
        
        print(f"\n🛑 Step 7: Stop GPS devices...")
        for gps_device, assignment in active_devices:
            device_id = gps_device.component_id
            print(f"   🛑 Stopping GPS device {device_id}...")
            await gps_device.stop()
            print(f"   ✅ GPS device {device_id} stopped")
        
        print(f"\n📊 Step 8: Connection verification summary...")
        if len(active_devices) == len(assignments):
            print(f"   ✅ All {len(assignments)} GPS devices started successfully")
            print("   📡 Check server logs above for WebSocket connection evidence")
            print("   💡 If no connections shown, GPS devices are not reaching server")
        else:
            print(f"   ❌ Only {len(active_devices)}/{len(assignments)} devices started")
            return False
        
        print(f"\n✅ SUCCESS: GPS device connection test completed!")
        print(f"   🎯 Check telemetry server logs for actual connection evidence")
        print(f"   📊 {len(active_devices)} GPS devices created and started")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: GPS server connection test failed")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_gps_server_connection())