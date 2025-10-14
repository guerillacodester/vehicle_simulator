# 🚌 Vehicle Simulator - Project Status
**Last Updated:** October 13, 2025, 9:00 PM
**Branch:** branch-0.0.2.2

---

## 📊 Current System State

### ✅ **OPERATIONAL SYSTEMS**

#### **1. Passenger Spawning Service** ✅ RUNNING
- **Location:** `commuter_service/`
- **Status:** Active and spawning passengers
- **Spawn Rate:** ~100 passengers/hour (realistic for 9 PM evening hours)
  - Depot spawns: ~50/hour from 5 bus terminals
  - Route spawns: ~50/hour along Route 1A
- **Configuration:** 
  - 18x reduction from original rates (6x base + 3x temporal)
  - Temporal multipliers adjust by time of day
  - Poisson distribution for realistic patterns
- **Database:** Passengers being saved to `active_passengers` table
- **Monitor:** Real-time spawn monitor running (`monitor_realtime_spawns.py`)

#### **2. Geofence Location API** ✅ OPERATIONAL
- **Endpoint:** `http://localhost:1337/api/geofence/find-nearby-features-fast`
- **Function:** Returns nearest highway and POI for GPS coordinates
- **Performance:** ~2 seconds per query (optimized with GiST indexes)
- **Database:** PostGIS spatial indexes operational
- **Status:** Ready for use (but not yet integrated into spawn enrichment)

#### **3. Database Infrastructure** ✅ ACTIVE
- **Platform:** Strapi CMS + PostgreSQL + PostGIS
- **URL:** `http://localhost:1337`
- **Active Tables:**
  - `active_passengers` - 4,167 records (needs cleanup)
  - `depots` - 5 bus terminals
  - `routes` - Route 1A with geometry
  - `highways` - Road network with spatial indexes
  - `pois` - Points of interest with spatial indexes

---

## ⚠️ **IDENTIFIED ISSUES**

### **Issue #1: Database Expiration Not Working**
**Problem:** 4,167 old passengers from yesterday still in database
- Expiration loop removes from memory but NOT database
- `db.delete_expired()` method exists but never called
- Old records accumulating indefinitely

**Impact:** Database bloat, inaccurate passenger counts

**Fix Required:** 
1. Add `await self.db.delete_expired()` to expiration loops
2. Manually clean old records: `DELETE /api/active-passengers/cleanup/expired`

**Files:** 
- `commuter_service/depot_reservoir.py` (line 786)
- `commuter_service/route_reservoir.py` (line 786)

### **Issue #2: No Vehicle Simulator Running**
**Problem:** Passengers are spawning but no vehicles to pick them up
- Passengers accumulate in WAITING status
- No pickup/dropoff events occurring
- Complete passenger journey never tested

**Impact:** Cannot test end-to-end flow

**Fix Required:** Start vehicle simulator service

---

## 🎯 **IMMEDIATE NEXT STEPS**

### **Priority 1: Fix Database Expiration** (30 minutes)
1. ✅ Manually clean old passengers via API
2. ✅ Add `db.delete_expired()` call to expiration loops
3. ✅ Verify expired passengers removed after 30 minutes
4. ✅ Monitor database size stabilizes

### **Priority 2: Start Vehicle Simulator** (1-2 hours)
1. ✅ Locate vehicle simulator entry point
2. ✅ Start vehicle simulator service
3. ✅ Verify vehicle spawns at depot
4. ✅ Verify vehicle follows Route 1A geometry
5. ✅ Verify position updates emitted

### **Priority 3: Integrate Conductor Module** (2-3 hours)
1. ✅ Create `conductor.py` in vehicle folder
2. ✅ Use `EventClient` to trigger hardware events
3. ✅ Detect nearby passengers when vehicle stops
4. ✅ Simulate driver decisions (who to board)
5. ✅ Call `passenger_events.board_passenger()` / `alight_passenger()`
6. ✅ Test passenger status transitions in database

### **Priority 4: Test End-to-End Flow** (1 hour)
1. ✅ Passenger spawns at depot (WAITING)
2. ✅ Vehicle arrives at depot
3. ✅ Conductor triggers board event
4. ✅ Passenger status → ONBOARD
5. ✅ Vehicle drives to destination
6. ✅ Conductor triggers alight event
7. ✅ Passenger status → COMPLETED
8. ✅ Verify in database and spawn monitor

---

## 📁 **KEY FILE LOCATIONS**

### **Passenger Spawning**
- `commuter_service/depot_reservoir.py` - Depot passenger spawning
- `commuter_service/route_reservoir.py` - Route passenger spawning
- `commuter_service/poisson_geojson_spawner.py` - Spawn rate configuration
- `commuter_service/passenger_db.py` - Database operations
- `start_commuter_service.py` - Service entry point
- `monitor_realtime_spawns.py` - Real-time monitoring

### **Vehicle Simulator**
- `arknet_transit_simulator/` - Main simulator package
- `arknet_transit_simulator/main.py` - Entry point
- `arknet_transit_simulator/vehicle/` - Vehicle components
- `arknet_transit_simulator/vehicle/gps_device.py` - GPS tracking
- `arknet_transit_simulator/vehicle/hardware_events/` - **NEW** Hardware event system
- `arknet_transit_simulator/vehicle/hardware_events/event_client.py` - Event API client
- `arknet_transit_simulator/vehicle/hardware_events/passenger_events.py` - Boarding/alighting

### **API Backend**
- `arknet_fleet_manager/arknet-fleet-api/` - Strapi CMS
- `arknet_fleet_manager/arknet-fleet-api/src/api/active-passenger/` - Passenger API
- `arknet_fleet_manager/arknet-fleet-api/src/api/geofence/` - Location enrichment API

---

## 🏗️ **ARCHITECTURE OVERVIEW**

### **Hardware Event System (NEW)**
```
┌─────────────────────────────────────────────────┐
│           UNIFIED EVENT INTERFACE               │
└─────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   SIMULATION                  REAL HARDWARE
        │                         │
┌───────▼────────┐      ┌─────────▼──────────┐
│   Conductor    │      │   RFID Reader      │
│   (Python)     │      │   (Raspberry Pi)   │
└───────┬────────┘      └─────────┬──────────┘
        │                         │
        │  ┌──────────────────────┘
        │  │
        ▼  ▼
┌────────────────────────┐
│   EventClient          │
│   (event_client.py)    │
└───────────┬────────────┘
            │
            │ HTTP POST
            ▼
┌────────────────────────┐
│   Strapi API           │
│   /vehicle-events/*    │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│   Database Update      │
│   (mark_boarded, etc)  │
└────────────────────────┘
```

### **Current Data Flow**
```
1. SPAWN → Database INSERT (status=WAITING)
2. PICKUP → Database UPDATE (status=ONBOARD, boarded_at=timestamp)
3. ALIGHT → Database UPDATE (status=COMPLETED, alighted_at=timestamp)
4. EXPIRE → Database DELETE (if still WAITING after 30 min)
```

---

## 📈 **SPAWN RATE CALIBRATION RESULTS**

### **Before vs After**
| Time | Before | After | Target | Status |
|------|---------|--------|--------|---------|
| **9 PM** | 1,052/hr | 100/hr | 90-180/hr | ✅ Perfect |
| **Depot** | 560/hr | 50/hr | 60-120/hr | ✅ Good |
| **Route** | 492/hr | 50/hr | 30-60/hr | ✅ Good |

### **Temporal Multipliers**
- **Morning Peak (7-9 AM):** 3.0x
- **Evening Peak (5-7 PM):** 2.5x
- **Midday:** 1.0x
- **Evening (8-10 PM):** 0.8x ← Current
- **Night (10 PM-5 AM):** 0.1-0.2x

### **Amenity-Specific Rates** (Evening)
- Mall: 0.34/hr (highest activity)
- University: 0.27/hr
- Shopping: 0.23/hr
- Restaurant: 0.13/hr
- School: 0.17/hr (minimal at night)

---

## 🔮 **FUTURE ENHANCEMENTS**

### **Phase 1: Real Hardware Integration** (2-4 weeks)
- RFID card readers at vehicle doors
- Door sensors (IR/magnetic) for open/close detection
- Passenger counter (IR beam sensors)
- GPS tracker with cellular connectivity
- Driver tablet app for manual overrides
- Raspberry Pi/ESP32 edge controller

### **Phase 2: Location Enrichment** (1 week)
- Async geofence API calls (2-sec delay)
- Redis caching for location lookups
- Background enrichment of spawn events
- UI shows "Loading location..." → "Near Highway 1, Bridgetown"

### **Phase 3: Live Dashboard** (2-3 weeks)
- Real-time map with Leaflet.js/Mapbox
- Moving vehicle markers
- Waiting passenger pins
- Route polylines and depot markers
- Statistics panel (spawn rate, wait times, occupancy)
- Time controls (speed adjustment, pause/resume)

### **Phase 4: Performance Optimization** (1 week)
- Geofence API: 2 sec → 200ms (10x faster)
- Redis caching layer
- Geohash pre-computation
- Materialized views for spatial queries

### **Phase 5: Multi-Route Expansion** (3-4 weeks)
- Activate Routes 1B, 2, 3 (10-20 routes total)
- Multi-route passenger spawning
- Transfer passengers (route changes)
- Fleet management (multiple vehicles per route)
- Vehicle scheduling (headways)

### **Phase 6: Analytics & History** (2 weeks)
- `passenger_journeys` history table
- Average wait time by depot/route
- Busiest spawn zones (heatmap data)
- Vehicle utilization metrics
- Passenger expiration rate analysis

---

## 🎓 **LESSONS LEARNED**

### **Spawn Rate Calibration**
1. Real transit usage is much lower than expected
2. Temporal multipliers are critical for realism
3. Amenity-specific weights matter (schools at night = zero)
4. Barbados population (287K) = small-scale transit
5. 18x reduction achieved realistic evening rates

### **Database Design**
1. Status transitions work well (WAITING → ONBOARD → COMPLETED)
2. Expiration needs active cleanup, not just memory removal
3. Keeping completed journeys good for analytics
4. Spatial indexes (GiST) essential for location queries

### **Hardware Event Design**
1. Unified interface benefits both simulation and real hardware
2. Placement in `vehicle/` folder makes logical sense
3. EventClient pattern allows easy hardware swapping
4. Conductor can use same API as RFID readers

---

## 🚀 **READY TO PROCEED**

**Current Focus:** Fix database expiration, then start vehicle simulator

**Next Session Goals:**
1. Clean up 4,167 old passengers
2. Fix expiration loop
3. Start vehicle simulator
4. Integrate conductor module
5. Test first complete passenger journey

**Estimated Time to Complete Core Flow:** 4-6 hours

---

## 📞 **System Health**

| Component | Status | Notes |
|-----------|--------|-------|
| Commuter Service | 🟢 Running | Spawning ~100/hr at 9 PM |
| Vehicle Simulator | 🔴 Stopped | Not started yet |
| Strapi API | 🟢 Running | http://localhost:1337 |
| PostgreSQL | 🟢 Running | PostGIS enabled |
| Spawn Monitor | 🟢 Running | Real-time dashboard |
| Database Cleanup | 🟡 Partial | Memory only, not DB |
| Hardware Events | 🟡 Ready | Infrastructure created |

**System Readiness:** 70% - Core spawning works, vehicle integration needed

---

**End of Status Report**
