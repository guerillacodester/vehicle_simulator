#!/usr/bin/env python3
"""
Simple test to verify telemetry server connection
"""
import asyncio
import websockets
import json


async def test_connection():
    print("🧪 Testing connection to telemetry server...")
    
    try:
        # Test basic connection
        print("📡 Connecting to ws://localhost:5000...")
        async with websockets.connect("ws://localhost:5000") as websocket:
            print("✅ Connected successfully!")
            
            # Send a test packet
            test_packet = {
                "deviceId": "TEST001",
                "lat": 13.1,
                "lon": -59.6,
                "speed": 45.0,
                "heading": 90.0,
                "route": "1A",
                "vehicleReg": "ZR101",
                "timestamp": "2025-09-12T20:51:00Z",
                "driverName": {"first": "Test", "last": "Driver"}
            }
            
            print("📤 Sending test packet...")
            await websocket.send(json.dumps(test_packet))
            print("✅ Packet sent successfully!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused - server not running on port 5000")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    try:
        # Test /device endpoint
        print("\n📡 Testing /device endpoint...")
        test_packet_device = {
            "deviceId": "TEST002",
            "lat": 13.2,
            "lon": -59.7,
            "speed": 55.0,
            "heading": 180.0,
            "route": "1B",
            "vehicleReg": "ZR102",
            "timestamp": "2025-09-12T20:51:30Z",
            "driverName": {"first": "Device", "last": "Test"}
        }
        
        async with websockets.connect("ws://localhost:5000/device?token=test&deviceId=TEST002") as websocket:
            print("✅ Connected to /device endpoint successfully!")
            
            # Send a test packet
            print("📤 Sending test packet to /device...")
            await websocket.send(json.dumps(test_packet_device))
            print("✅ Packet sent to /device successfully!")
            
    except ConnectionRefusedError:
        print("❌ Connection refused to /device endpoint")
    except Exception as e:
        print(f"❌ Connection to /device failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())