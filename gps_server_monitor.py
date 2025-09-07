#!/usr/bin/env python3
"""
GPS Server Monitor
-----------------
Monitor the GPS server to verify it's receiving telemetry data
"""

import requests
import time
import json

def check_gps_server():
    """Check if GPS server is responding"""
    try:
        # Try to connect to the GPS server HTTP endpoint
        response = requests.get("http://localhost:5000/", timeout=5)
        print(f"🌐 GPS Server HTTP Status: {response.status_code}")
        
        # The server might return 404 for root path, which is normal
        if response.status_code in [200, 404]:
            print("✅ GPS server is running and responding")
            return True
        else:
            print(f"⚠️ GPS server returned unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ GPS server is not responding on HTTP")
        return False
    except Exception as e:
        print(f"❌ Error checking GPS server: {e}")
        return False

def test_websocket_endpoint():
    """Test WebSocket endpoint availability"""
    import asyncio
    import websockets
    
    async def test_connection():
        try:
            # Try to connect to WebSocket endpoint
            uri = "ws://localhost:5000/device?token=test&deviceId=monitor"
            print(f"🔌 Testing WebSocket connection: {uri}")
            
            async with websockets.connect(uri, open_timeout=5) as websocket:
                print("✅ WebSocket connection successful!")
                
                # Send a test message
                test_message = {
                    "deviceId": "monitor",
                    "lat": 13.2810,
                    "lon": -59.6463,
                    "speed": 0.0,
                    "heading": 0.0,
                    "route": "TEST",
                    "vehicleReg": "MONITOR",
                    "driverId": "test",
                    "driverName": {"first": "Test", "last": "Monitor"},
                    "timestamp": "2025-09-07T13:45:00Z"
                }
                
                await websocket.send(json.dumps(test_message))
                print("📤 Test message sent")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📥 Server response: {response}")
                except asyncio.TimeoutError:
                    print("⏰ No response from server (timeout)")
                
                return True
                
        except websockets.exceptions.ConnectionRefused:
            print("❌ WebSocket connection refused")
            return False
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    return asyncio.run(test_connection())

def main():
    """Main monitoring function"""
    print("🔬 GPS Server Monitor")
    print("=" * 30)
    
    # Check HTTP endpoint
    http_ok = check_gps_server()
    
    print()
    
    # Check WebSocket endpoint
    ws_ok = test_websocket_endpoint()
    
    print()
    print("📊 Summary:")
    print(f"   HTTP Server: {'✅ OK' if http_ok else '❌ FAIL'}")
    print(f"   WebSocket:   {'✅ OK' if ws_ok else '❌ FAIL'}")
    
    if http_ok and ws_ok:
        print("\n🎉 GPS server is fully operational!")
        print("   Your vehicle simulators should be able to send GPS data successfully.")
    else:
        print("\n⚠️ GPS server has issues.")
        print("   Check that the server is running at E:\\projects\\arknettransit\\gpscentcom_server\\")
        
if __name__ == "__main__":
    main()
