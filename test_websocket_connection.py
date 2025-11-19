#!/usr/bin/env python3
"""Test websocket connection to GPSCentCom server"""
import asyncio
import websockets
import json

async def test_connection():
    auth_token = "supersecrettoken"
    uri = f"ws://localhost:5000/ws?token={auth_token}"
    
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  PYTHON WebSocket Test: GPSCentCom Connection          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"Connecting to: {uri}")
    print(f"Auth token: {auth_token}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[Connection] ✓ Connected successfully!\n")
            
            # Receive messages for 15 seconds
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(message)
                    print(f"[Message] Type: {data.get('type', 'unknown')}")
                    print(f"Raw: {json.dumps(data, indent=2)}\n")
            except asyncio.TimeoutError:
                print("[Test] Timeout - closing connection")
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[Error] Connection rejected with status: {e.status_code}")
        print(f"Headers: {e.headers}")
    except Exception as e:
        print(f"[Error] {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
