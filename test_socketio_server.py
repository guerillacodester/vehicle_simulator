"""
Mock Socket.IO Server for Testing
==================================
Simple Socket.IO server to test Conductor and VehicleDriver communication.

This server:
1. Accepts Socket.IO connections on port 3000
2. Logs all events received
3. Echoes conductor signals to demonstrate two-way communication
4. Tracks location updates from drivers

Usage:
    python test_socketio_server.py

Then in another terminal:
    python test_socketio_integration.py
"""

import socketio
import asyncio
from aiohttp import web
from datetime import datetime

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)
app = web.Application()
sio.attach(app)

# Track events
events_log = []
connected_clients = {}


@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    print(f"\n{'='*80}")
    print(f"✅ Client connected: {sid}")
    print(f"   Time: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")
    connected_clients[sid] = {
        'connected_at': datetime.now().isoformat(),
        'type': 'unknown'
    }


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    client_info = connected_clients.pop(sid, {})
    print(f"\n{'='*80}")
    print(f"❌ Client disconnected: {sid}")
    print(f"   Type: {client_info.get('type', 'unknown')}")
    print(f"   Time: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")


@sio.on('driver:location:update')
async def on_driver_location(sid, data):
    """Handle driver location updates."""
    connected_clients[sid]['type'] = 'driver'
    
    print(f"\n📍 DRIVER LOCATION UPDATE")
    print(f"   SID: {sid}")
    print(f"   Vehicle ID: {data.get('vehicle_id')}")
    print(f"   Driver ID: {data.get('driver_id')}")
    print(f"   Position: ({data.get('latitude'):.6f}, {data.get('longitude'):.6f})")
    print(f"   Speed: {data.get('speed'):.2f} km/h")
    print(f"   Heading: {data.get('heading'):.1f}°")
    print(f"   Timestamp: {data.get('timestamp')}")
    
    events_log.append({
        'event': 'driver:location:update',
        'sid': sid,
        'data': data,
        'received_at': datetime.now().isoformat()
    })


@sio.on('conductor:request:stop')
async def on_conductor_stop(sid, data):
    """Handle conductor stop request."""
    connected_clients[sid]['type'] = 'conductor'
    
    print(f"\n🛑 CONDUCTOR STOP REQUEST")
    print(f"   SID: {sid}")
    print(f"   Vehicle ID: {data.get('vehicle_id')}")
    print(f"   Conductor ID: {data.get('conductor_id')}")
    print(f"   Stop ID: {data.get('stop_id')}")
    print(f"   Passengers Boarding: {data.get('passengers_boarding')}")
    print(f"   Passengers Disembarking: {data.get('passengers_disembarking')}")
    print(f"   Duration: {data.get('duration_seconds')}s")
    print(f"   GPS Position: {data.get('gps_position')}")
    
    events_log.append({
        'event': 'conductor:request:stop',
        'sid': sid,
        'data': data,
        'received_at': datetime.now().isoformat()
    })
    
    # Echo stop request to all connected drivers (broadcast)
    print(f"   📤 Broadcasting stop request to all drivers...")
    await sio.emit('conductor:request:stop', data)


@sio.on('conductor:ready:depart')
async def on_conductor_depart(sid, data):
    """Handle conductor ready to depart signal."""
    connected_clients[sid]['type'] = 'conductor'
    
    print(f"\n🚀 CONDUCTOR READY TO DEPART")
    print(f"   SID: {sid}")
    print(f"   Vehicle ID: {data.get('vehicle_id')}")
    print(f"   Conductor ID: {data.get('conductor_id')}")
    print(f"   Passenger Count: {data.get('passenger_count')}")
    print(f"   Timestamp: {data.get('timestamp')}")
    
    events_log.append({
        'event': 'conductor:ready:depart',
        'sid': sid,
        'data': data,
        'received_at': datetime.now().isoformat()
    })
    
    # Echo depart signal to all connected drivers (broadcast)
    print(f"   📤 Broadcasting depart signal to all drivers...")
    await sio.emit('conductor:ready:depart', data)


@sio.on('conductor:query:passengers')
async def on_query_passengers(sid, data):
    """Handle passenger query from conductor."""
    connected_clients[sid]['type'] = 'conductor'
    
    print(f"\n🔍 CONDUCTOR QUERY PASSENGERS")
    print(f"   SID: {sid}")
    print(f"   Depot ID: {data.get('depot_id')}")
    print(f"   Route ID: {data.get('route_id')}")
    print(f"   Current Position: {data.get('current_position')}")
    
    events_log.append({
        'event': 'conductor:query:passengers',
        'sid': sid,
        'data': data,
        'received_at': datetime.now().isoformat()
    })
    
    # Mock response with some test passengers
    mock_response = {
        'passengers': [
            {
                'passenger_id': 'P001',
                'pickup_lat': 40.7128,
                'pickup_lon': -74.0060,
                'dropoff_lat': 40.7589,
                'dropoff_lon': -73.9851,
                'time_window_start': datetime.now().isoformat(),
                'time_window_end': datetime.now().isoformat()
            },
            {
                'passenger_id': 'P002',
                'pickup_lat': 40.7200,
                'pickup_lon': -74.0100,
                'dropoff_lat': 40.7600,
                'dropoff_lon': -73.9900,
                'time_window_start': datetime.now().isoformat(),
                'time_window_end': datetime.now().isoformat()
            }
        ]
    }
    
    print(f"   📤 Returning {len(mock_response['passengers'])} passengers")
    return mock_response


@sio.on('passenger:board:vehicle')
async def on_passenger_board(sid, data):
    """Handle passenger boarding event."""
    print(f"\n👤 PASSENGER BOARD VEHICLE")
    print(f"   SID: {sid}")
    print(f"   Passenger ID: {data.get('passenger_id')}")
    print(f"   Vehicle ID: {data.get('vehicle_id')}")
    print(f"   Location: {data.get('location')}")
    print(f"   Timestamp: {data.get('timestamp')}")
    
    events_log.append({
        'event': 'passenger:board:vehicle',
        'sid': sid,
        'data': data,
        'received_at': datetime.now().isoformat()
    })


@sio.on('passenger:alight:vehicle')
async def on_passenger_alight(sid, data):
    """Handle passenger alighting event."""
    print(f"\n👤 PASSENGER ALIGHT VEHICLE")
    print(f"   SID: {sid}")
    print(f"   Passenger ID: {data.get('passenger_id')}")
    print(f"   Vehicle ID: {data.get('vehicle_id')}")
    print(f"   Location: {data.get('location')}")
    print(f"   Timestamp: {data.get('timestamp')}")
    
    events_log.append({
        'event': 'passenger:alight:vehicle',
        'sid': sid,
        'data': data,
        'received_at': datetime.now().isoformat()
    })


# Web routes for monitoring
async def get_status(request):
    """Return server status."""
    return web.json_response({
        'status': 'running',
        'connected_clients': len(connected_clients),
        'clients': connected_clients,
        'total_events': len(events_log),
        'server_time': datetime.now().isoformat()
    })


async def get_events(request):
    """Return event log."""
    limit = int(request.query.get('limit', 50))
    return web.json_response({
        'events': events_log[-limit:],
        'total': len(events_log)
    })


async def clear_events(request):
    """Clear event log."""
    global events_log
    count = len(events_log)
    events_log = []
    return web.json_response({
        'status': 'cleared',
        'events_cleared': count
    })


# Add web routes
app.router.add_get('/status', get_status)
app.router.add_get('/events', get_events)
app.router.add_post('/clear', clear_events)


if __name__ == '__main__':
    print("\n" + "="*80)
    print("Socket.IO Test Server")
    print("="*80)
    print("\nServer Configuration:")
    print("  - Socket.IO endpoint: http://localhost:3000")
    print("  - CORS: Enabled (all origins)")
    print("  - Async mode: aiohttp")
    print("\nWeb Endpoints:")
    print("  - GET  /status  - Server status and connected clients")
    print("  - GET  /events  - Event log (add ?limit=N for last N events)")
    print("  - POST /clear   - Clear event log")
    print("\nSupported Socket.IO Events:")
    print("  - driver:location:update      (Driver → Server)")
    print("  - conductor:request:stop      (Conductor → Server → Driver)")
    print("  - conductor:ready:depart      (Conductor → Server → Driver)")
    print("  - conductor:query:passengers  (Conductor ↔ Server)")
    print("  - passenger:board:vehicle     (Passenger → Server)")
    print("  - passenger:alight:vehicle    (Passenger → Server)")
    print("\n" + "="*80)
    print("\nStarting server on http://localhost:3000")
    print("Press Ctrl+C to stop\n")
    print("="*80 + "\n")
    
    web.run_app(app, host='0.0.0.0', port=3000)
