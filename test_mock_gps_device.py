"""
Mock GPS Device - Test Telemetry Sender
Sends simulated GPS data to the Fleet Services API for testing
"""

import asyncio
import websockets
import json
import random
import time
from datetime import datetime


async def send_telemetry():
    """Send mock GPS telemetry to the server."""
    
    uri = "ws://localhost:8000/gps/device"
    
    print("🚗 Mock GPS Device - Connecting to Fleet Services...")
    print(f"   WebSocket: {uri}")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to GPS CentCom Server")
            print()
            
            # Base location (Barbados)
            base_lat = 13.0975
            base_lon = -59.6142
            
            # Send telemetry updates every 2 seconds
            for i in range(10):
                # Simulate movement (small random changes)
                lat = base_lat + (random.random() - 0.5) * 0.01
                lon = base_lon + (random.random() - 0.5) * 0.01
                speed = random.uniform(20, 60)
                heading = random.uniform(0, 360)
                
                telemetry = {
                    "deviceId": "TEST_DEVICE_001",
                    "route": "1A",
                    "vehicleReg": "BDS-TEST-101",
                    "lat": lat,
                    "lon": lon,
                    "speed": speed,
                    "heading": heading,
                    "driverId": "driver_test",
                    "driverName": {"firstName": "Test", "lastName": "Driver"},
                    "conductorId": None,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                # Send to server
                await websocket.send(json.dumps(telemetry))
                
                print(f"📡 Sent telemetry #{i+1}")
                print(f"   Position: {lat:.4f}, {lon:.4f}")
                print(f"   Speed: {speed:.1f} km/h | Heading: {heading:.1f}°")
                print()
                
                # Wait 2 seconds
                await asyncio.sleep(2)
            
            print("✅ Finished sending telemetry")
            print("   Keeping connection open for 10 more seconds...")
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print()
    print("═══════════════════════════════════════════════════════════")
    print("  Mock GPS Device - Test Telemetry Sender")
    print("═══════════════════════════════════════════════════════════")
    print()
    
    asyncio.run(send_telemetry())
