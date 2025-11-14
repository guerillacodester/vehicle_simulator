# Fleet Management Client

Remote client for the ArkNet Fleet Management API. Provides both programmatic access (connector) and interactive CLI (console).

## Installation

```powershell
# Install dependencies
pip install httpx websockets rich  # rich is optional but recommended
```

## Quick Start

### 1. Start the Simulator with API

```powershell
# Terminal 1: Start simulator with embedded API
python -m arknet_transit_simulator --mode depot
```

The Fleet Management API will start on `http://localhost:5001` by default.

### 2. Run the Fleet Console

```powershell
# Terminal 2: Launch interactive console
python -m clients.fleet

# Or with custom URL:
python -m clients.fleet --url http://localhost:8080
```

## Console Commands

### Status & Monitoring
```
status              # Show API health and system status
vehicles            # List all vehicles with current state
vehicle ZR102       # Show detailed state for specific vehicle
conductors          # List all conductors
conductor ZR102     # Show conductor for specific vehicle
```

### Engine Control
```
start ZR102         # Start engine for vehicle ZR102
stop ZR102          # Stop engine for vehicle ZR102
```

### Boarding Control
```
enable ZR102        # Enable passenger boarding
disable ZR102       # Disable passenger boarding
trigger ZR102       # Manually trigger boarding check at current position
```

### Real-Time Streaming
```
stream              # Start live event stream (Ctrl+C to stop)
```

### General
```
help                # Show command list
exit                # Exit console
```

## Programmatic Usage

### Basic Example

```python
import asyncio
from clients.fleet import FleetConnector

async def main():
    # Create connector
    connector = FleetConnector(base_url="http://localhost:5001")
    
    # Get all vehicles
    vehicles = await connector.get_vehicles()
    for vehicle in vehicles:
        print(f"{vehicle.vehicle_id}: {vehicle.passenger_count}/{vehicle.capacity}")
    
    # Start engine
    result = await connector.start_engine("ZR102")
    print(result.message)
    
    # Enable boarding
    result = await connector.enable_boarding("ZR102")
    print(result.message)
    
    # Cleanup
    await connector.close()

asyncio.run(main())
```

### Real-Time Event Streaming

```python
import asyncio
from clients.fleet import FleetConnector

async def main():
    connector = FleetConnector()
    
    # Subscribe to events
    def on_engine_started(data):
        print(f"Engine started: {data['vehicle_id']}")
    
    def on_passenger_boarded(data):
        print(f"Passenger boarded: {data}")
    
    connector.on('engine_started', on_engine_started)
    connector.on('passenger_boarded', on_passenger_boarded)
    
    # Connect WebSocket
    await connector.connect_websocket()
    
    # Keep running
    await asyncio.sleep(60)
    
    # Cleanup
    await connector.close()

asyncio.run(main())
```

### Available API Methods

#### Health & Status
- `get_health()` → `HealthResponse`
- `get_websocket_status()` → `Dict`

#### Vehicles
- `get_vehicles()` → `List[VehicleState]`
- `get_vehicle(vehicle_id)` → `VehicleState`

#### Conductors
- `get_conductors()` → `List[ConductorState]`
- `get_conductor(vehicle_id)` → `ConductorState`

#### Engine Control
- `start_engine(vehicle_id)` → `CommandResult`
- `stop_engine(vehicle_id)` → `CommandResult`

#### Boarding Control
- `enable_boarding(vehicle_id)` → `CommandResult`
- `disable_boarding(vehicle_id)` → `CommandResult`
- `trigger_boarding(vehicle_id)` → `CommandResult`

#### WebSocket
- `connect_websocket()` - Connect to event stream
- `disconnect_websocket()` - Disconnect
- `on(event_type, callback)` - Subscribe to events
- `off(event_type, callback)` - Unsubscribe

### Event Types

Subscribe to these event types:
- `engine_started` - Vehicle engine started
- `engine_stopped` - Vehicle engine stopped
- `position_update` - GPS position updated
- `passenger_boarded` - Passenger boarded vehicle
- `passenger_alighted` - Passenger left vehicle
- `boarding_enabled` - Boarding system activated
- `boarding_disabled` - Boarding system deactivated
- `connect` - WebSocket connected
- `disconnect` - WebSocket disconnected

## Example Workflow

```powershell
# Terminal 1: Start simulator
python -m arknet_transit_simulator --mode depot

# Terminal 2: Fleet console
python -m clients.fleet

# In console:
fleet> status                     # Check system health
fleet> vehicles                   # List all vehicles
fleet> vehicle ZR102              # Inspect ZR102
fleet> start ZR102                # Start engine
fleet> enable ZR102               # Enable boarding
fleet> trigger ZR102              # Trigger boarding
fleet> stream                     # Watch live events (Ctrl+C to stop)
fleet> exit
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  Fleet Console (Interactive CLI)            │
│  - Rich terminal UI                         │
│  - Command parser                           │
│  - Live event display                       │
└────────────────┬────────────────────────────┘
                 │
                 │ uses
                 ▼
┌─────────────────────────────────────────────┐
│  Fleet Connector (HTTP/WebSocket Client)    │
│  - REST API calls (httpx)                   │
│  - WebSocket streaming (websockets)         │
│  - Observable pattern (callbacks)           │
│  - Auto-reconnect                           │
└────────────────┬────────────────────────────┘
                 │
                 │ HTTP/WS
                 ▼
┌─────────────────────────────────────────────┐
│  Fleet Management API (Embedded in Sim)     │
│  - FastAPI + uvicorn                        │
│  - Direct memory access to simulator        │
│  - Real-time EventBus                       │
└─────────────────────────────────────────────┘
```

## Files

- `connector.py` - HTTP/WebSocket client for Fleet API
- `fleet_console.py` - Interactive CLI application
- `models.py` - Pydantic models for type safety
- `__main__.py` - Entry point for `python -m clients.fleet`
- `README.md` - This file

## Dependencies

### Required
- `httpx` - Async HTTP client
- `websockets` - WebSocket client
- `pydantic` - Data validation

### Optional
- `rich` - Beautiful terminal output (highly recommended)

```powershell
pip install httpx websockets pydantic rich
```

## Troubleshooting

### "Failed to connect"
- Make sure simulator is running: `python -m arknet_transit_simulator --mode depot`
- Check API is enabled (default: yes, disable with `--no-api`)
- Verify port (default: 5001, change with `--api-port 8080`)

### "Vehicle not found"
- Use `vehicles` command to see available vehicle IDs
- Wait for vehicles to initialize (takes a few seconds after simulator starts)

### WebSocket not streaming events
- Events are only emitted when things happen (engine starts, passengers board, etc.)
- Try triggering actions: `start ZR102`, `trigger ZR102`
- Check event wiring in simulator (may not be implemented yet)

## Next Steps

- Wire event emissions in simulator (VehicleDriver, Conductor)
- Add batch operations (start all engines)
- Add filtering (by route, state)
- Add event history/replay
- Build Next.js GUI using same connector

## See Also

- [API Reference](../../arknet_transit_simulator/api/API_REFERENCE.md)
- [Commuter Client](../commuter/README.md) - Similar pattern for passenger management
