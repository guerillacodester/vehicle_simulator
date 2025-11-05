# Fleet Management Quick Start Guide

## What is This?

The Fleet Management system provides **remote HTTP-based control** of the ArkNet transit simulator. It consists of:

1. **Fleet Management API** - Embedded FastAPI server in the simulator (port 5001)
2. **Fleet Connector** - Python client library for API communication
3. **Fleet Console** - Interactive CLI for fleet management

This architecture enables **future GUI development** (Next.js) using the same API.

## Quick Start

### Step 1: Start the Simulator with API

```powershell
# Start simulator with embedded Fleet Management API
python -m arknet_transit_simulator --mode depot
```

You should see:
```
🌐 Initializing Fleet Management API on port 5001...
✅ Fleet Management API initialized
🚀 Starting Fleet Management API server on http://0.0.0.0:5001
✅ Fleet Management API running at http://localhost:5001
   📖 API docs: http://localhost:5001/docs
   🔍 Health check: http://localhost:5001/health
```

### Step 2: Test the API (Optional)

```powershell
# Quick health check
curl http://localhost:5001/health

# Or open in browser
start http://localhost:5001/docs
```

### Step 3: Run the Fleet Console

```powershell
# In a NEW terminal window
python -m clients.fleet
```

You should see:
```
┌──────────────────────────────────────────────────────┐
│  ArkNet Fleet Management Console                     │
│  Connected to: http://localhost:5001                 │
│  Type 'help' for commands, 'exit' to quit            │
└──────────────────────────────────────────────────────┘
✅ Connected to Fleet API

fleet>
```

## Common Commands

### 1. Check System Status
```
fleet> status
```

Shows:
- API health
- Simulator running status
- Active vehicle count
- Event bus statistics
- WebSocket connections

### 2. List All Vehicles
```
fleet> vehicles
```

Shows table with:
- Vehicle ID (e.g., ZR102)
- Driver name
- Route ID
- Current position (lat/lon)
- Driver state (DRIVING, IDLE, etc.)
- Engine status (ON/OFF)
- GPS status (ON/OFF)
- Passenger count
- Boarding status (Active/Inactive)

### 3. Inspect Specific Vehicle
```
fleet> vehicle ZR102
```

Shows detailed state for one vehicle.

### 4. Start Vehicle Engine
```
fleet> start ZR102
```

Sends command to start the engine. You should see:
```
✅ Engine started for vehicle ZR102
```

### 5. Enable Passenger Boarding
```
fleet> enable ZR102
```

Enables the conductor's boarding system.

### 6. Trigger Manual Boarding
```
fleet> trigger ZR102
```

Forces the conductor to check for passengers at current location.
Shows how many passengers boarded.

### 7. Live Event Stream
```
fleet> stream
```

Streams real-time events from all vehicles:
```
📡 Starting event stream... (Ctrl+C to stop)
#1 [2025-01-20T10:30:15Z] engine_started - ZR102
#2 [2025-01-20T10:30:20Z] position_update - ZR102
#3 [2025-01-20T10:30:25Z] passenger_boarded - ZR102
```

Press `Ctrl+C` to stop streaming and return to console.

## Complete Command Reference

```
STATUS & MONITORING:
  status              - Show API health and connection status
  vehicles            - List all vehicles with current state
  vehicle <id>        - Show detailed state for specific vehicle
  conductors          - List all conductors
  conductor <id>      - Show conductor for specific vehicle

ENGINE CONTROL:
  start <id>          - Start engine for vehicle
  stop <id>           - Stop engine for vehicle

BOARDING CONTROL:
  enable <id>         - Enable boarding for vehicle
  disable <id>        - Disable boarding for vehicle
  trigger <id>        - Trigger manual boarding check

REAL-TIME:
  stream              - Start live event streaming (Ctrl+C to stop)

GENERAL:
  help                - Show this help message
  exit / quit         - Exit console
```

## Example Workflow

Here's a typical fleet management session:

```powershell
# Terminal 1: Start simulator
python -m arknet_transit_simulator --mode depot

# Terminal 2: Fleet console
python -m clients.fleet

# Commands in console:
fleet> status                     # ✅ Healthy, 1 active vehicle
fleet> vehicles                   # 📋 ZR102 - Jane Doe - Route 1
fleet> vehicle ZR102              # 🔍 Engine: OFF, Passengers: 0/45
fleet> start ZR102                # ✅ Engine started
fleet> enable ZR102               # ✅ Boarding enabled
fleet> trigger ZR102              # ✅ Boarded 3 passengers
fleet> vehicle ZR102              # 🔍 Engine: ON, Passengers: 3/45
fleet> stream                     # 📡 Watch live events...
fleet> exit                       # 👋 Goodbye!
```

## Troubleshooting

### "Failed to connect: Connection refused"

**Problem:** API server not running.

**Solution:** 
1. Start simulator: `python -m arknet_transit_simulator --mode depot`
2. Check port 5001 is not in use: `netstat -ano | findstr :5001`
3. Try custom port: `python -m arknet_transit_simulator --mode depot --api-port 8080`

### "No vehicles found"

**Problem:** Vehicles haven't initialized yet.

**Solution:**
1. Wait 5-10 seconds after starting simulator
2. Check simulator logs for errors
3. Verify Strapi is running (vehicles come from Strapi API)

### "Vehicle not found: ZR102"

**Problem:** Using wrong vehicle ID.

**Solution:**
1. Use `vehicles` command to see available IDs
2. Check vehicle exists in Strapi database

### Events not streaming

**Problem:** EventBus wiring not implemented yet.

**Solution:**
- Event emissions need to be wired in VehicleDriver and Conductor classes
- This is the next development task
- For now, API calls work but events won't stream

## API Configuration

### Custom Port
```powershell
# Simulator with custom API port
python -m arknet_transit_simulator --mode depot --api-port 8080

# Console with custom port
python -m clients.fleet --url http://localhost:8080
```

### Disable API
```powershell
# Run simulator without embedded API
python -m arknet_transit_simulator --mode depot --no-api
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Terminal 2: Fleet Console                      │
│  Interactive CLI with commands                  │
└───────────────┬─────────────────────────────────┘
                │
                │ HTTP/WebSocket
                │ localhost:5001
                ▼
┌─────────────────────────────────────────────────┐
│  Terminal 1: Simulator + Embedded API           │
│  ┌───────────────────────────────────────────┐  │
│  │  Fleet Management API (FastAPI)           │  │
│  │  - /health, /api/vehicles, /api/conductors│  │
│  │  - POST control endpoints                 │  │
│  │  - WebSocket /ws/events                   │  │
│  └─────────────┬─────────────────────────────┘  │
│                │ Direct Memory Access            │
│                ▼                                 │
│  ┌───────────────────────────────────────────┐  │
│  │  CleanVehicleSimulator                    │  │
│  │  - active_drivers []                      │  │
│  │  - depot, dispatcher                      │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Key Points:**
- API is **embedded** in simulator process (not separate service)
- **Zero latency** - direct Python object access
- **Same pattern** as commuter_service client
- Ready for **Next.js GUI** (same API)

## Next Steps

1. ✅ **Test the console** - Verify connection and commands work
2. ⏳ **Wire event emissions** - Add `event_bus.emit()` calls in simulator
3. ⏳ **Test WebSocket streaming** - Verify events flow to console
4. ⏳ **Build Next.js GUI** - Create visual dashboard using same API

## Files Created

```
clients/fleet/
├── __init__.py           # Package exports
├── __main__.py           # Entry point (python -m clients.fleet)
├── connector.py          # HTTP/WebSocket client
├── fleet_console.py      # Interactive CLI
├── models.py             # Pydantic models
└── README.md             # Documentation

arknet_transit_simulator/api/
├── __init__.py
├── app.py                # FastAPI factory
├── dependencies.py       # Dependency injection
├── models.py             # API response models
├── API_REFERENCE.md      # Complete API docs
├── events/
│   ├── __init__.py
│   ├── event_bus.py      # EventBus implementation
│   └── event_types.py    # Event type enum
└── routes/
    ├── __init__.py
    ├── vehicles.py       # Vehicle state endpoints
    ├── conductors.py     # Conductor state endpoints
    ├── control.py        # Control command endpoints
    └── websockets.py     # WebSocket streaming
```

## See Also

- [Fleet Client README](clients/fleet/README.md) - Full documentation
- [API Reference](arknet_transit_simulator/api/API_REFERENCE.md) - Complete API docs
- [Commuter Console Guide](COMMUTER_CONSOLE_GUIDE.txt) - Similar system for passengers
