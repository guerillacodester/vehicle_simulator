# Phase 4 Configuration Migration - UPDATED Architecture

**Date:** October 16, 2025  
**Branch:** branch-0.0.2.3  
**Status:** Step 2 Complete ✅ | Step 3 Simplified ✅

---

## 🎯 Overall Goal
Migrate from hardcoded configuration values to API-driven configuration system with database backend, supporting future admin UI for runtime parameter changes.

## 🏗️ **SIMPLIFIED ARCHITECTURE** (Updated)

```
┌────────────────────────────────────────────────┐
│  Python Simulator Components                  │
│  - Conductor                                   │
│  - VehicleDriver                               │
│  - Passenger Spawning                          │
└──────────────┬─────────────────────────────────┘
               │
               ↓
    ┌──────────────────────┐
    │ ConfigurationService │  ← Internal cache layer
    │   (Python singleton) │     • Polls Strapi every 30s
    │                      │     • Typed Python interface
    │                      │     • Change callbacks
    │                      │     • No HTTP server needed
    └──────────┬───────────┘
               │
               ↓
    ┌──────────────────────┐
    │   Strapi REST API    │  ← Single source of truth
    │   (Port 1337)        │     • REST endpoints (working)
    │                      │     • GraphQL (future)
    │                      │     • Admin UI (working)
    │                      │     • Auth & permissions
    └──────────┬───────────┘
               │
               ↓
    ┌──────────────────────┐
    │  PostgreSQL Database │
    │  operational_configs │
    └──────────────────────┘

External Clients/Future UI → Strapi API directly
```

**Design Decision:** NO separate FastAPI server
- ✅ Simpler operations (one server only)
- ✅ Strapi provides complete REST + GraphQL capability
- ✅ Less maintenance, fewer moving parts
- ✅ Industry-standard headless CMS pattern

---

## ✅ COMPLETED STEPS

### **STEP 1: Database Schema Creation** ✅
- **Status:** COMPLETE
- **Files Created:**
  - `arknet-fleet-api/src/api/operational-configuration/content-types/operational-configuration/schema.json`
  - `arknet-fleet-api/src/api/operational-configuration/content-types/operational-configuration/config.json`
  - `arknet-fleet-api/src/api/operational-configuration/controllers/operational-configuration.ts`
  - `arknet-fleet-api/src/api/operational-configuration/routes/operational-configuration.ts`
  - `arknet-fleet-api/src/api/operational-configuration/services/operational-configuration.ts`
  - `arknet_fleet_manager/operational_config_seed_data.json` (12 configs)
  - `arknet_fleet_manager/seed_operational_config.py`
  - `test_step1_config_collection.py`

- **Key Learnings:**
  - Strapi v5 requires `.ts` files (not `.js`)
  - `config.json` file is required for admin UI metadata
  - API permissions must be manually enabled in Strapi admin
  - Use `type: "text"` for values (not `type: "json"`) to avoid `.split()` errors
  - Store primitive values as JSON strings, parse on read

- **Verification:**
  ```bash
  python test_step1_config_collection.py
  ```
  Result: All 3 tests PASS ✅

### **STEP 2: Configuration Service Layer** ✅
- **Status:** COMPLETE
- **Files Created:**
  - `arknet_transit_simulator/services/config_service.py`
  - `test_step2_config_service.py`

- **Features Implemented:**
  - ✅ Singleton pattern for global access
  - ✅ Cached configuration with 30s auto-refresh
  - ✅ JSON string parsing (handles text-stored values)
  - ✅ Dot-notation queries: `config.get("section.parameter")`
  - ✅ Section queries: `config.get_section("conductor.proximity")`
  - ✅ Full metadata access with constraints
  - ✅ Default value fallbacks
  - ✅ Change callback registration
  - ✅ Cache freshness tracking

- **Verification:**
  ```bash
  python test_step2_config_service.py
  ```
  Result: All 7 tests PASS ✅

### **STEP 3: API Endpoints** ✅ **USING STRAPI DIRECTLY**
- **Status:** COMPLETE (simplified approach)
- **Decision:** Use Strapi's built-in REST API instead of custom FastAPI layer

**Strapi Endpoints (Already Working):**
```bash
# Get all configurations
GET http://localhost:1337/api/operational-configurations

# Get configurations by section
GET http://localhost:1337/api/operational-configurations?filters[section][$eq]=conductor.proximity

# Get specific configuration
GET http://localhost:1337/api/operational-configurations/:documentId

# Update configuration
PUT http://localhost:1337/api/operational-configurations/:documentId
Body: {"data": {"value": "0.25"}}

# Create new configuration
POST http://localhost:1337/api/operational-configurations
Body: {"data": {...}}

# Delete configuration
DELETE http://localhost:1337/api/operational-configurations/:documentId
```

**Access Patterns:**
- **Python components** → Use `ConfigurationService` (cached, typed)
- **External clients/UI** → Use Strapi REST API directly
- **Future GraphQL** → Enable Strapi GraphQL plugin (5 minutes)

---

## 📋 NEXT STEPS (When Resuming)

### **STEP 4: Update Components** ⏳
Replace hardcoded values with config service calls:

**Components to Update:**

1. **Conductor** (`arknet_transit_simulator/core/conductor.py`)
   - Replace `ConductorConfig` dataclass with dynamic config calls
   - Update: proximity settings, stop duration, operational params

2. **VehicleDriver** (`arknet_transit_simulator/core/vehicle_driver.py`)
   - Update waypoint threshold and broadcast interval

3. **Passenger Spawning** (spawning scripts)
   - Update spawn rates and geographic settings

**Migration Pattern:**
```python
# OLD (hardcoded):
from dataclasses import dataclass

@dataclass
class ConductorConfig:
    pickup_radius_km: float = 0.2
    boarding_time_window_minutes: float = 5.0

conductor = Conductor(config=ConductorConfig())

# NEW (dynamic):
from arknet_transit_simulator.services.config_service import get_config_service

config_service = await get_config_service()
pickup_radius = await config_service.get(
    "conductor.proximity.pickup_radius_km", 
    default=0.2
)
boarding_window = await config_service.get(
    "conductor.proximity.boarding_time_window_minutes",
    default=5.0
)

conductor = Conductor(
    pickup_radius_km=pickup_radius,
    boarding_time_window_minutes=boarding_window
)
```

### **STEP 5: End-to-End Testing** ⏳
- Test full configuration lifecycle
- Test hot-reload (change config in Strapi → system updates within 30s)
- Performance testing
- Integration testing with conductor/driver

---

## 📊 Configuration Parameters (12 Total)

### Conductor Configuration
**Section: conductor.proximity**
- `pickup_radius_km`: 0.2 (min: 0.05, max: 5.0, unit: km)
- `boarding_time_window_minutes`: 5.0

**Section: conductor.stop_duration**
- `min_seconds`: 15.0
- `max_seconds`: 180.0
- `per_passenger_boarding_time`: 8.0
- `per_passenger_disembarking_time`: 5.0

**Section: conductor.operational**
- `monitoring_interval_seconds`: 2.0
- `gps_precision_meters`: 10.0

### Driver Configuration
**Section: driver.waypoints**
- `proximity_threshold_km`: 0.05 (50 meters)
- `broadcast_interval_seconds`: 5.0

### Passenger Spawning
**Section: passenger_spawning.rates**
- `average_passengers_per_hour`: 30

**Section: passenger_spawning.geographic**
- `spawn_radius_meters`: 500.0

---

## 🔧 Quick Commands

### Start Strapi (Required)
```bash
cd arknet_fleet_manager/arknet-fleet-api
npm run develop
```

### Run Tests
```bash
# Step 1: Database schema test
python test_step1_config_collection.py

# Step 2: Config service test
python test_step2_config_service.py
```

### Access Points
- **Strapi Admin UI:** http://localhost:1337/admin
- **Strapi REST API:** http://localhost:1337/api/operational-configurations
- **Future GraphQL:** http://localhost:1337/graphql (after enabling plugin)

### Seed/Manage Data
```bash
# Seed initial configurations
cd arknet_fleet_manager
python seed_operational_config.py

# Delete all configs (if needed)
python delete_all_configs.py
```

---

## 🐛 Issues Resolved

### Issue 1: Strapi Admin UI ".split is not a function" Error ✅
**Problem:** JSON fields with primitive values caused JavaScript errors in admin panel

**Solution:** Changed schema from `type: "json"` to `type: "text"` for value fields
- Store values as JSON strings: `"0.2"` instead of `0.2`
- Parse in ConfigurationService: `json.loads(value_raw)`
- Constraints remain as JSON objects (works fine)

**Files Updated:**
- `schema.json`: Changed value/default_value to `type: "text"`
- `config_service.py`: Added JSON parsing logic
- `update_seed_data.py`: Convert values to JSON strings

### Issue 2: Content Type Not Loading ✅
**Problem:** Schema files existed but API returned 404

**Root Cause:** Missing `config.json` and `.js` files instead of `.ts`

**Solution:**
- Created `config.json` with admin UI metadata
- Renamed all `.js` files to `.ts`
- Cleared cache and rebuilt Strapi
- Enabled API permissions in admin

---

## 📁 Important File Locations

### Strapi Content Type
```
arknet_fleet_manager/arknet-fleet-api/src/api/operational-configuration/
├── content-types/operational-configuration/
│   ├── schema.json          # Field definitions
│   └── config.json          # Admin UI metadata
├── controllers/operational-configuration.ts
├── routes/operational-configuration.ts
└── services/operational-configuration.ts
```

### Configuration Service
```
arknet_transit_simulator/services/config_service.py
```

### Tests
```
test_step1_config_collection.py
test_step2_config_service.py
```

### Seed Data & Scripts
```
arknet_fleet_manager/
├── operational_config_seed_data.json
├── seed_operational_config.py
├── delete_all_configs.py
└── update_seed_data.py
```

---

## 🎯 Success Criteria

- [x] Database schema created and accessible
- [x] API endpoints working (Strapi REST)
- [x] Configuration service implemented
- [x] Caching working with auto-refresh
- [x] Strapi admin UI working (no errors)
- [x] JSON string parsing working
- [ ] ~~REST API endpoints created (FastAPI)~~ **REMOVED - Using Strapi only**
- [ ] Components updated to use config service
- [ ] Hot-reload working
- [ ] End-to-end tests passing

---

## 💡 Future Enhancements (Post-Phase 4)

1. **Enable GraphQL** - Strapi GraphQL plugin for flexible queries
2. **Admin UI** - Custom React admin panel (use Strapi API)
3. **Config Versioning** - Track configuration changes over time
4. **Environment Profiles** - Dev/Staging/Production config sets
5. **Server-side Validation** - Strapi lifecycle hooks for constraint enforcement
6. **Audit Logging** - Track who changed what and when
7. **Config Export/Import** - Backup and restore configurations
8. **Custom Strapi Routes** - If business logic needed (TypeScript in Strapi)

---

## 📖 API Examples

### Using Strapi REST API Directly

**Get all configurations:**
```bash
curl http://localhost:1337/api/operational-configurations
```

**Filter by section:**
```bash
curl "http://localhost:1337/api/operational-configurations?filters[section][\$eq]=conductor.proximity"
```

**Update a configuration:**
```bash
curl -X PUT http://localhost:1337/api/operational-configurations/sevl9gn2jou45p2enk5mhia1 \
  -H "Content-Type: application/json" \
  -d '{"data": {"value": "0.25"}}'
```

### Using Configuration Service (Python)

```python
from arknet_transit_simulator.services.config_service import get_config_service

# Initialize
config = await get_config_service()

# Get single value
radius = await config.get("conductor.proximity.pickup_radius_km", default=0.2)

# Get section
proximity_config = await config.get_section("conductor.proximity")
# Returns: {"pickup_radius_km": 0.2, "boarding_time_window_minutes": 5.0}

# Get full metadata
full_config = await config.get_full("conductor.proximity.pickup_radius_km")
# Returns: {value, value_type, constraints, description, ...}

# Register change callback
def on_change(key, old_val, new_val):
    print(f"Config changed: {key} = {old_val} → {new_val}")

config.on_change("conductor.proximity.pickup_radius_km", on_change)
```

---

**Resume Point:** Ready to implement Step 4 (Update Components)

**Architecture Status:** ✅ Simplified and production-ready
