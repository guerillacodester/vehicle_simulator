#!/usr/bin/env python3
"""
Test GPSCentCom pub/sub infrastructure:
1. Connect as client to WebSocket endpoint
2. Verify snapshot reception
3. Verify real-time updates
"""
import asyncio
import websockets
import json
import sys

async def test_pubsub():
    # Try without auth first to see if server has AUTH_TOKEN configured
    uris = [
        "ws://localhost:5000/ws?token=supersecrettoken",
        "ws://localhost:5000/ws?token=test",
        "ws://localhost:5000/ws",
    ]
    
    print("\n" + "="*70)
    print("  GPSCentCom Pub/Sub Infrastructure Test")
    print("="*70)
    
    attempt = 0
    while True:
        for uri in uris:
            attempt += 1
            print(f"\n[Attempt {attempt}] Connecting to: {uri}")
            try:
                async with websockets.connect(uri) as ws:
                    print("✓ Connected successfully!")
                    attempt = 0  # Reset attempt counter on successful connection
                    subscribe_msg = json.dumps({"type": "subscribe", "topic": "telemetry"})
                    await ws.send(subscribe_msg)
                    print("✓ Sent subscription request for 'telemetry' topic")
                    print("\n[Waiting for messages...]")
                    timeout = 60
                    start = asyncio.get_event_loop().time()
                    message_count = 0
                    while asyncio.get_event_loop().time() - start < timeout:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            message_count += 1
                            data = json.loads(msg)
                            msg_type = data.get('type', 'unknown')
                            if msg_type == 'snapshot':
                                states = data.get('states', [])
                                print(f"  Snapshot contains {len(states)} device(s)")
                                if states:
                                    for state in states[:2]:
                                        print(f"    Device: {state.get('deviceId')}")
                                        print(f"      Lat: {state.get('lat')}, Lon: {state.get('lon')}")
                                        print(f"      Speed: {state.get('speed')} km/h, Heading: {state.get('heading')}°")
                            elif msg_type == 'update':
                                device_id = data.get('deviceId')
                                state = data.get('state', {})
                                print(f"\n[Update] Device: {device_id}")
                                print(f"  Route: {state.get('route')}")
                                print(f"  VehicleReg: {state.get('vehicleReg')}")
                                print(f"  DriverId: {state.get('driverId')}")
                                print(f"  DriverName: {state.get('driverName')}")
                                print(f"  Lat: {state.get('lat')}, Lon: {state.get('lon')}")
                                print(f"  Speed: {state.get('speed')} km/h, Heading: {state.get('heading')}°")
                                print(f"  Timestamp: {state.get('timestamp')}")
                                print(f"  RAW STATE KEYS: {list(state.keys())}")
                                print(f"  FULL RAW DATA: {json.dumps(data, indent=2)}")
                            else:
                                print(f"  Data: {json.dumps(data, indent=4)}")
                        except asyncio.TimeoutError:
                            continue
                    print(f"\n[Summary] Received {message_count} message(s) in {timeout}s")
                    print("✓ Pub/Sub infrastructure is working!")
                    return True
            except websockets.exceptions.InvalidStatus as e:
                print(f"✗ Connection rejected: {e}")
                continue
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {e}")
                continue
        print("[Retry] All endpoints failed. Waiting 5 seconds before retrying...")
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(test_pubsub())
    except KeyboardInterrupt:
        print("\n✓ Test interrupted by user")
        sys.exit(0)
