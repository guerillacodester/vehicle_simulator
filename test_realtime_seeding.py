#!/usr/bin/env python3
"""
Real-time Seeding Monitor - Watch passenger spawn events live

Usage:
    # Terminal 1: Start this listener
    python test_realtime_seeding.py

    # Terminal 2: Start seeding
    python commuter_service/seed.py --day monday --route 1 --type route --start-hour 7 --end-hour 9
"""

import asyncio
import socketio
from datetime import datetime

# Connect to Socket.IO server
sio = socketio.AsyncClient()

# Event counters
event_count = 0
hourly_counts = {}

@sio.event
async def connect():
    print("=" * 80)
    print("🔴 CONNECTED TO SOCKET.IO SERVER")
    print("=" * 80)
    print("Listening for passenger spawn events...")
    print()

@sio.event
async def disconnect():
    print()
    print("=" * 80)
    print("⚫ DISCONNECTED FROM SOCKET.IO SERVER")
    print("=" * 80)
    print(f"Total events received: {event_count}")
    print()

@sio.on('commuter:spawned')
async def on_commuter_spawned(data):
    global event_count, hourly_counts
    event_count += 1
    
    # Extract hour from timestamp
    if 'spawn_time' in data:
        spawn_time = datetime.fromisoformat(data['spawn_time'].replace('Z', '+00:00'))
        hour = spawn_time.hour
        hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        print(f"🚶 #{event_count:>4} | Hour {hour:>2}:00 | Total this hour: {hourly_counts[hour]:>3} | Route: {data.get('route_id', 'N/A')[:8]}...")
    else:
        print(f"🚶 #{event_count:>4} | {data}")

@sio.on('*')
async def catch_all(event, data):
    """Catch any other events"""
    if event not in ['connect', 'disconnect', 'commuter:spawned']:
        print(f"📡 Event: {event} | Data: {data}")


async def main():
    print("=" * 80)
    print("REAL-TIME SEEDING MONITOR")
    print("=" * 80)
    print("Connecting to Socket.IO server at http://localhost:3001...")
    print()
    
    try:
        await sio.connect('http://localhost:3001')
        
        # Keep the connection alive
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping listener...")
        await sio.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure Socket.IO server is running!")
        print("Check if commuter service is emitting events to port 3001")


if __name__ == "__main__":
    asyncio.run(main())
