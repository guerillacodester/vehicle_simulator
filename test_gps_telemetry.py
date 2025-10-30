"""
Simple GPS telemetry test - Send mock GPS data to test the client-server flow
"""
import asyncio
import websockets
import json
import time
from datetime import datetime


async def send_test_telemetry():
    """Send test GPS telemetry to the fleet services API."""
    
    device_id = "TEST_DEVICE_001"
    uri = f"ws://localhost:8000/gps/device?deviceId={device_id}"
    
    print("🚗 Connecting to GPS CentCom Server...")
    print(f"   URI: {uri}")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            print()
            
            # Simulate a vehicle driving along a route
            base_lat = 13.0975
            base_lon = -59.6142
            
            for i in range(10):
                # Create telemetry packet
                telemetry = {
                    "deviceId": "TEST_DEVICE_001",
                    "route": "1A",
                    "vehicleReg": "TEST-VEH-123",
                    "lat": base_lat + (i * 0.001),  # Move north
                    "lon": base_lon + (i * 0.001),  # Move east
                    "speed": 45.0 + (i * 2),
                    "heading": 45.0,
                    "driverId": "test_driver_001",
                    "driverName": {"first": "Test", "last": "Driver"},
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                # Send to server
                await websocket.send(json.dumps(telemetry))
                print(f"📡 Sent update {i+1}/10: Lat={telemetry['lat']:.4f}, Lon={telemetry['lon']:.4f}, Speed={telemetry['speed']:.1f} km/h")
                
                # Wait 1 second between updates
                await asyncio.sleep(1)
            
            print()
            print("✅ Test telemetry sent successfully!")
            print("   Use 'python -m gps_telemetry_client.test_client list' to verify")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure Fleet Services API is running:")
        print("   python start_fleet_services.py")


if __name__ == "__main__":
    print()
    print("═══════════════════════════════════════════════════════════")
    print("  GPS Telemetry Test - Mock Vehicle")
    print("═══════════════════════════════════════════════════════════")
    print()
    
    asyncio.run(send_test_telemetry())
    
    print()
    print("═══════════════════════════════════════════════════════════")
    print()
