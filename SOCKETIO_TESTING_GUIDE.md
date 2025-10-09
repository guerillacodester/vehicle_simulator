# Socket.IO Testing Guide

## 🎯 Purpose

Test the Socket.IO integration for Priority 2:
- Conductor ↔ Driver communication
- Driver location broadcasting
- Fallback to callbacks

## 📋 Prerequisites

### 1. Install Socket.IO Python Client

```bash
pip install python-socketio aiohttp
```

### 2. Check Dependencies

```bash
# Verify installations
python -c "import socketio; print('Socket.IO version:', socketio.__version__)"
python -c "import aiohttp; print('aiohttp version:', aiohttp.__version__)"
```

## 🚀 Running the Tests

### Step 1: Start the Mock Socket.IO Server

Open **Terminal 1**:

```bash
cd e:\projects\github\vehicle_simulator
python test_socketio_server.py
```

You should see:
```
================================================================================
Socket.IO Test Server
================================================================================

Server Configuration:
  - Socket.IO endpoint: http://localhost:3000
  - CORS: Enabled (all origins)

Starting server on http://localhost:3000
================================================================================
```

**Keep this terminal open!**

### Step 2: Run the Quick Tests

Open **Terminal 2**:

```bash
cd e:\projects\github\vehicle_simulator
python quick_test_socketio.py
```

This will run 4 tests:
1. **Connection Test** - Verify Conductor and Driver can connect
2. **Stop/Depart Test** - Test conductor signals to driver
3. **Location Broadcasting** - Test driver location updates
4. **Fallback Test** - Test callback fallback when Socket.IO disabled

### Step 3: Monitor Server Console

Watch **Terminal 1** for Socket.IO events:

```
📍 DRIVER LOCATION UPDATE
   Vehicle ID: QUICK_TEST_VEH
   Position: (40.712800, -74.006000)
   Speed: 25.50 km/h

🛑 CONDUCTOR STOP REQUEST
   Vehicle ID: STOP_TEST_VEH
   Duration: 3s

🚀 CONDUCTOR READY TO DEPART
   Passenger Count: 22
```

## 📊 Expected Results

### ✅ Successful Test Output

```
================================================================================
TEST SUMMARY
================================================================================

  1. Connection Test:      ✅ PASS
  2. Stop/Depart Test:     ✅ PASS
  3. Location Test:        ✅ PASS
  4. Fallback Test:        ✅ PASS

  Total: 4/4 tests passed

================================================================================

🎉 All tests PASSED!
```

### ❌ Common Errors

#### Error: "Socket.IO connection failed"

**Solution**: Make sure the Socket.IO server is running on port 3000

```bash
# Check if port 3000 is in use
netstat -ano | findstr :3000

# If another service is using it, change the port in test_socketio_server.py
```

#### Error: "Module 'socketio' not found"

**Solution**: Install python-socketio

```bash
pip install python-socketio aiohttp
```

#### Error: "Cannot find module arknet_transit_simulator"

**Solution**: Run tests from the project root directory

```bash
cd e:\projects\github\vehicle_simulator
python quick_test_socketio.py
```

## 🔍 Detailed Testing

### Check Server Status

While tests are running, visit:

```
http://localhost:3000/status
```

Returns:
```json
{
  "status": "running",
  "connected_clients": 2,
  "clients": {
    "abc123": {"type": "conductor", "connected_at": "2025-10-09T20:30:00"},
    "def456": {"type": "driver", "connected_at": "2025-10-09T20:30:01"}
  },
  "total_events": 45
}
```

### View Event Log

```
http://localhost:3000/events?limit=10
```

Returns last 10 events received by server.

### Clear Event Log

```bash
curl -X POST http://localhost:3000/clear
```

## 🧪 Manual Testing

### Test Individual Components

#### Test Conductor Only

```python
import asyncio
from arknet_transit_simulator.vehicle.conductor import Conductor

async def test():
    conductor = Conductor(
        conductor_id="MANUAL_COND",
        conductor_name="Manual Test",
        vehicle_id="VEH001",
        assigned_route_id="1A",
        sio_url="http://localhost:3000"
    )
    await conductor.start()
    await asyncio.sleep(5)
    await conductor.stop()

asyncio.run(test())
```

#### Test Driver Only

```python
import asyncio
from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

async def test():
    driver = VehicleDriver(
        driver_id="MANUAL_DRV",
        driver_name="Manual Driver",
        vehicle_id="VEH001",
        route_coordinates=[[40.7128, -74.0060], [40.7589, -73.9851]],
        route_name="1A",
        sio_url="http://localhost:3000"
    )
    await driver.start()
    await driver.start_engine()
    await asyncio.sleep(15)  # Watch location broadcasts
    await driver.stop()

asyncio.run(test())
```

## 📝 What Each Test Validates

### Test 1: Connection Test
- ✅ Conductor can connect to Socket.IO server
- ✅ Driver can connect to Socket.IO server
- ✅ Connection state is tracked correctly
- ✅ Both components start successfully

### Test 2: Stop/Depart Test
- ✅ Conductor can send stop request via Socket.IO
- ✅ Driver receives stop signal and stops engine
- ✅ Conductor can send depart signal via Socket.IO
- ✅ Driver receives depart signal and restarts engine
- ✅ State transitions are correct (ONBOARD → WAITING → ONBOARD)

### Test 3: Location Broadcasting
- ✅ Driver starts location broadcasting task
- ✅ Location updates sent every 5 seconds when ONBOARD
- ✅ Server receives location updates with correct format
- ✅ Location data includes lat, lon, speed, heading

### Test 4: Fallback Test
- ✅ System works without Socket.IO (use_socketio=False)
- ✅ Callbacks are used when Socket.IO disabled
- ✅ Stop signal delivered via callback
- ✅ Continue signal delivered via callback

## 🐛 Debugging

### Enable Socket.IO Debug Logging

Edit `conductor.py` or `vehicle_driver.py`:

```python
# Change this:
self.sio = socketio.AsyncClient(logger=False, engineio_logger=False)

# To this:
self.sio = socketio.AsyncClient(logger=True, engineio_logger=True)
```

### Check Server Logs

The Socket.IO server prints all events. Look for:

```
✅ Client connected: abc123
📍 DRIVER LOCATION UPDATE
🛑 CONDUCTOR STOP REQUEST
🚀 CONDUCTOR READY TO DEPART
```

### Test with curl

```bash
# Check server is running
curl http://localhost:3000/status

# View events
curl http://localhost:3000/events?limit=5
```

## ✅ Success Criteria

All tests should pass with:
- 4/4 tests passing
- No connection errors
- Server console showing events
- No exceptions in test output

## 🎉 Next Steps After Testing

Once all tests pass:

1. **✅ Step 1 Complete**: TypeScript event types
2. **✅ Step 2 Complete**: Conductor Socket.IO integration
3. **✅ Step 3 Complete**: Driver Socket.IO integration
4. **🔄 Step 4 (Optional)**: Add passenger lifecycle events to LocationAwareCommuter
5. **📝 Step 5**: Create comprehensive documentation
6. **🚀 Step 6**: Deploy to production

## 📚 Additional Resources

- Socket.IO Python Docs: https://python-socketio.readthedocs.io/
- aiohttp Docs: https://docs.aiohttp.org/
- Project Architecture: `COMPLETE_ARCHITECTURE_ANALYSIS.md`
- Integration Roadmap: `SOCKETIO_INTEGRATION_ROADMAP.md`

