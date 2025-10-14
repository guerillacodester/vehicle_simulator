# 🎯 Next Steps - Quick Reference
**Vehicle Simulator Project - October 13, 2025**

---

## ⚡ IMMEDIATE ACTIONS (Next Session)

### **Step 1: Clean Database (5 minutes)**
```powershell
# Method 1: Via API (PowerShell)
$response = Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers/cleanup/expired" -Method Delete
Write-Host "Deleted $($response.deleted_count) expired passengers"

# Method 2: Via Python script
python -c "import asyncio, aiohttp; asyncio.run((lambda: aiohttp.request('DELETE', 'http://localhost:1337/api/active-passengers/cleanup/expired'))())"

# Verify cleanup
Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers/stats/count" | ConvertTo-Json
```

### **Step 2: Fix Expiration Loop (10 minutes)**

**File:** `commuter_service/depot_reservoir.py` (line ~788)

Add after line 789:
```python
if expired_ids:
    self.logger.info(f"Expired {len(expired_ids)} commuters")
    
    # 🆕 ADD THIS: Cleanup database
    deleted_count = await self.db.delete_expired()
    if deleted_count > 0:
        self.logger.info(f"🗑️  Deleted {deleted_count} expired passengers from database")
```

**File:** `commuter_service/route_reservoir.py` (line ~823)

Add same code block after expiration loop.

### **Step 3: Restart Commuter Service (2 minutes)**
```powershell
# Stop current service (Ctrl+C or)
Get-Process python | Stop-Process -Force

# Restart with fix
cd e:\projects\github\vehicle_simulator
python start_commuter_service.py
```

### **Step 4: Start Vehicle Simulator (5 minutes)**
```powershell
# Option 1: As module
python -m arknet_transit_simulator

# Option 2: Direct entry point
python arknet_transit_simulator/main.py

# Option 3: If there's a startup script
python start_vehicle_simulator.py
```

**Expected Output:**
```
🚌 Vehicle Simulator Starting...
✅ Loaded Route 1A geometry (88 points)
🚗 Spawned vehicle VEH_001 at depot BGI_CONSTITUTION_04
📡 Connected to Socket.IO: http://localhost:1337
🎯 Vehicle driving Route 1A...
```

---

## 📋 VERIFICATION CHECKLIST

### **After Database Cleanup:**
- [ ] Old passengers deleted (count should drop from 4,167 to <100)
- [ ] New spawns still working
- [ ] Expiration loop logging "Deleted X from database"

### **After Vehicle Simulator Starts:**
- [ ] Vehicle appears on map (if dashboard running)
- [ ] GPS position updates every 1-5 seconds
- [ ] Vehicle follows Route 1A path
- [ ] Socket.IO events emitting

### **After Conductor Integration:**
- [ ] Vehicle stops at depot
- [ ] Conductor detects nearby passengers
- [ ] Boarding events triggered
- [ ] Database shows status: WAITING → ONBOARD
- [ ] Vehicle continues with passengers
- [ ] Alighting events triggered at destination
- [ ] Database shows status: ONBOARD → COMPLETED

---

## 🔍 DEBUGGING COMMANDS

### **Check Spawn Status:**
```powershell
# Current passenger count
Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers/stats/count"

# Recent spawns (last 5)
Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers?pagination[pageSize]=5&sort=createdAt:desc"

# Waiting passengers only
Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers/by-status/WAITING"

# Passengers near a location (depot)
Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers/near-location?lat=13.0965&lon=-59.6086&radius=100"
```

### **Check Vehicle Status:**
```powershell
# If vehicle API exists
Invoke-RestMethod -Uri "http://localhost:1337/api/vehicles"

# Check Socket.IO connections
# (View in Strapi admin or check terminal output)
```

### **Monitor Real-Time:**
```powershell
# Start spawn monitor (already running)
python monitor_realtime_spawns.py

# Watch database size
while ($true) {
    $count = (Invoke-RestMethod -Uri "http://localhost:1337/api/active-passengers/stats/count").total
    Write-Host "$(Get-Date -Format 'HH:mm:ss') - Active passengers: $count"
    Start-Sleep -Seconds 10
}
```

---

## 🏗️ CONDUCTOR MODULE (To Be Created)

**File:** `arknet_transit_simulator/vehicle/conductor.py`

**Purpose:** Simulate driver decisions for boarding/alighting

**Key Functions:**
```python
class VehicleConductor:
    def __init__(self, vehicle_id: str, event_client: EventClient):
        self.vehicle_id = vehicle_id
        self.event_client = event_client
        self.onboard_passengers = []
    
    async def arrive_at_stop(self, location: tuple, route_id: str):
        """Called when vehicle stops"""
        # Query nearby passengers
        # Decide who can board (capacity, route match)
        # Trigger boarding events
        pass
    
    async def board_passenger(self, passenger_id: str):
        """Board a passenger"""
        success = await passenger_events.board_passenger(
            self.event_client,
            passenger_id,
            self.vehicle_id,
            location=(lat, lon)
        )
        if success:
            self.onboard_passengers.append(passenger_id)
    
    async def check_alighting(self, location: tuple):
        """Check if passengers want to alight"""
        # For each onboard passenger:
        #   - Check if near destination
        #   - Trigger alight event
        pass
```

---

## 📊 SUCCESS METRICS

### **After First Hour:**
- [ ] 100 new passengers spawned
- [ ] Old passengers cleaned up
- [ ] Vehicle made 2-3 round trips on Route 1A
- [ ] 5-10 passengers boarded
- [ ] 5-10 passengers alighted
- [ ] Database shows all status transitions
- [ ] No errors in logs

### **After Full Day:**
- [ ] 2,400 passengers spawned (100/hr × 24hr)
- [ ] Spawn rates vary by time of day
- [ ] Multiple vehicles operating
- [ ] Passenger wait times < 15 minutes
- [ ] Expiration rate < 5%
- [ ] Database stable size (~500-1000 active)

---

## 🚨 COMMON ISSUES & SOLUTIONS

### **Issue: "Module not found" when starting simulator**
```powershell
# Ensure you're in project root
cd e:\projects\github\vehicle_simulator

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Try with explicit path
set PYTHONPATH=e:\projects\github\vehicle_simulator
python -m arknet_transit_simulator
```

### **Issue: Database cleanup not deleting**
- Check API endpoint method (DELETE not POST)
- Verify expires_at timestamps are in past
- Check Strapi permissions for active-passenger delete

### **Issue: Vehicle not picking up passengers**
- Verify conductor module integrated
- Check passenger query radius (should be 50-100m)
- Confirm Socket.IO connection established
- Check vehicle is actually stopping at depot

---

## 📚 DOCUMENTATION LINKS

- [Project Status Report](./PROJECT_STATUS.md) - Full system overview
- [Architecture Doc](./ARCHITECTURE_DEFINITIVE.md) - System design
- [Spawn Debugging](./SPAWN_DEBUGGING_SESSION.md) - Calibration details
- [Hardware Events](./arknet_transit_simulator/vehicle/hardware_events/README.md) - Event system guide

---

## 🎯 GOAL FOR NEXT SESSION

**Complete first end-to-end passenger journey:**
1. ✅ Passenger spawns at depot
2. ✅ Vehicle arrives and picks up passenger
3. ✅ Passenger rides to destination
4. ✅ Passenger alights near destination
5. ✅ Complete journey tracked in database

**Time Estimate:** 4-6 hours

**Complexity:** Medium (integration work)

**Blockers:** None (infrastructure ready)

---

**Ready to start? Begin with Step 1: Clean Database** 🚀
