"""Quick WebSocket connection test"""
import asyncio
import websockets
import json

async def test_ws():
    url = "ws://localhost:4000/ws/stream"
    print(f"Connecting to {url}...")
    
    try:
        async with websockets.connect(url) as ws:
            print("✅ Connected!")
            
            # Wait for welcome message
            message = await ws.recv()
            data = json.loads(message)
            print(f"📨 Received: {data}")
            
            # Send subscribe command
            await ws.send(json.dumps({"type": "subscribe", "route": "1"}))
            print("📤 Sent subscribe command")
            
            # Wait for response
            message = await ws.recv()
            data = json.loads(message)
            print(f"📨 Received: {data}")
            
            print("✅ WebSocket test successful!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ws())
