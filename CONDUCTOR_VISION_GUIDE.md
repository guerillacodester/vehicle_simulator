# Conductor Vision Test - Quick Start Guide

This guide will help you see what the conductor "sees" during a journey.

## Prerequisites

1. **Strapi running** (localhost:1337)
2. **GPSCentCom server running** (localhost:5000)
3. **Geospatial service running** (localhost:6000)
4. **Commuter service running** (localhost:4000)

## Step 1: Start All Services

```powershell
# Terminal 1: Start launcher (starts all services)
python launch.py

# OR start services individually:
# Terminal 1: Strapi
cd arknet_fleet_manager\arknet-fleet-api
npm run develop

# Terminal 2: GPSCentCom
cd gpscentcom_server
python server_main.py

# Terminal 3: Geospatial Service
cd geospatial_service
python main.py

# Terminal 4: Commuter Service
cd commuter_service
python -m uvicorn main:app --host 0.0.0.0 --port 4000
```

## Step 2: Seed Passengers

Seed passengers for Route 1 during morning hours (7-9 AM):

```powershell
python commuter_service/seed.py --route 1 --day monday --start-hour 7 --end-hour 9 --type route
```

Expected output:
```
✅ Seeded 87 passengers for route 1 (monday, 07:00-09:00)
```

## Step 3: Run Conductor Vision Test

```powershell
python test_conductor_vision.py --route 1 --duration 300
```

## What You'll See

### 1. **Conductor Looking for Passengers**
```
🔵 Conductor COND-DRV001 👁️  LOOKING FOR PASSENGERS:
   📍 Position: (13.082700, -59.613800)
   🚏 Route: 1
   🔍 Pickup radius: 0.2 km
   💺 Seats available: 40/40
```

### 2. **Passengers Found**
```
🔵 Conductor COND-DRV001: ✅ Found 5 eligible passengers:
   1. 🟢 Passenger PASS_ABC123
      📍 Position: (13.082650, -59.613750)
      📏 Distance: 8.3 meters
   2. 🟢 Passenger PASS_DEF456
      📍 Position: (13.082720, -59.613820)
      📏 Distance: 4.1 meters
   ...
```

### 3. **Boarding Process**
```
🔵 Conductor COND-DRV001: 🚪 BOARDING 5 passengers...
🔵 Conductor COND-DRV001: ✅ Successfully boarded 5 passengers
   💺 Current occupancy: 5/40
   💺 Seats remaining: 35
```

### 4. **Driver Communication**
```
🔵 Conductor COND-DRV001 🛑 SIGNALING DRIVER TO STOP:
   🚏 Stop ID: STOP-001
   🚪 Boarding: 3 passengers
   🚪 Disembarking: 0 passengers
   ⏱️  Duration: 24 seconds
   📍 Position: (13.082700, -59.613800)

🟡 Driver DRV001: ⏸️  Stopping engine for passenger operations...

🔵 Conductor COND-DRV001 🚀 SIGNALING DRIVER TO CONTINUE:
   💺 Passengers on board: 8
   ⏰ Time: 14:23:45

🟡 Driver DRV001: ▶️  Starting engine, resuming journey...
```

### 5. **Journey Progress**
```
🔵 Conductor COND-DRV001: 🚪 BOARDING ENABLED
   💺 Seats available: 32/40
   🔍 Will check for passengers at waypoints

🔵 Conductor COND-DRV001 👁️  LOOKING FOR PASSENGERS:
   📍 Position: (13.085200, -59.615300)
   ...
```

## Legend

- 🔵 **Blue** = Conductor actions/thoughts
- 🟡 **Yellow** = Driver actions
- 🟢 **Green** = Passenger events
- 👁️  = Conductor looking/checking
- 🚪 = Boarding/disembarking
- 🛑 = Stop signal
- 🚀 = Continue signal
- 💺 = Capacity/seats
- 📍 = GPS position
- 🚏 = Stop/route info

## Troubleshooting

### No passengers found
```
🔵 Conductor COND-DRV001: ❌ No passengers found at this location
```
**Solution**:
- Check that passengers were seeded: `python commuter_service/seed.py --route 1 ...`
- Verify route ID matches: Conductor looking for route "1", passengers spawned for route "1"
- Check Strapi: <http://localhost:1337/admin> → Active Passengers collection

### Vehicle full message
```
🔵 Conductor ZR102: Vehicle FULL (40/40), skipping passenger check
```
**This is normal** - conductor won't look for more passengers when vehicle is at capacity.

### No driver communication
```
🔵 Conductor COND-DRV001: ⚠️  NO COMMUNICATION METHOD AVAILABLE TO SIGNAL DRIVER!
```
**Solution**: 
- Ensure `enable_boarding_after` is set in simulator (5 seconds default)
- Check that driver and conductor are linked in simulator initialization

## Advanced Options

### Debug Mode
See all internal logs:
```powershell
python test_conductor_vision.py --route 1 --duration 300 --debug
```

### Shorter Test Run
Run for 1 minute:
```powershell
python test_conductor_vision.py --route 1 --duration 60
```

### Different Route
Test route 2:
```powershell
# Seed passengers for route 2
python commuter_service/seed.py --route 2 --day monday --start-hour 7 --end-hour 9 --type route

# Run test
python test_conductor_vision.py --route 2 --duration 300
```

## What Conductor Vision Tests

1. ✅ **Passenger Detection** - Does conductor see passengers near the vehicle?
2. ✅ **Distance Calculation** - Are distances computed correctly?
3. ✅ **Boarding Logic** - Does conductor board passengers successfully?
4. ✅ **Capacity Management** - Does conductor respect vehicle capacity?
5. ✅ **Driver Communication** - Does conductor signal driver to stop/start?
6. ✅ **State Management** - Does conductor track passengers on board correctly?

## Next Steps

After confirming conductor vision works:

1. **Test Depot Passengers** - Seed depot-spawned passengers
2. **Test Alighting** - Test passengers getting off at destination
3. **Test Full Journey** - Run 24-hour simulation with full passenger manifest
4. **Add Reservoir Integration** - Wire conductor to use RouteReservoir.query() instead of direct DB calls
5. **Enable Socket.IO Events** - Add real-time passenger spawn notifications

## Related Files

- Test script: `test_conductor_vision.py`
- Conductor code: `arknet_transit_simulator/vehicle/conductor.py`
- Seeding tool: `commuter_service/seed.py`
- Architecture docs: `CONTEXT.md` → "Conductor-Reservoir Integration Status"
