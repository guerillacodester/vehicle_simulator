# Hardcoded Values Assessment Report
**Date**: October 31, 2025  
**Branch**: branch-0.0.2.8

## Executive Summary

Comprehensive scan of all Python subsystems for hardcoded URLs, ports, and API endpoints. Classification: **CRITICAL** (❌), **WARNING** (⚠️), or **OK** (✅).

---

## 1. Commuter Simulator (`commuter_simulator/`)

### ❌ CRITICAL - Hardcoded URLs

| File | Line | Hardcoded Value | Should Use |
|------|------|-----------------|------------|
| `main.py` | 42 | `fallback='http://localhost:1337'` | ✅ Already reads from config.ini |
| `infrastructure/database/strapi_client.py` | 75 | `base_url: str = "http://localhost:1337"` | config.ini via dependency injection |
| `infrastructure/database/passenger_repository.py` | 36 | `strapi_url or "http://localhost:1337"` | config.ini via dependency injection |
| `infrastructure/geospatial/client.py` | 28 | `base_url: str = "http://localhost:6000"` | config.ini via dependency injection |
| `infrastructure/persistence/strapi/passenger_repository.py` | 36 | `strapi_url or "http://localhost:1337"` | config.ini via dependency injection |
| `domain/services/spawning/depot_spawner.py` | 44 | `strapi_url: str = "http://localhost:1337"` | config.ini via dependency injection |
| `core/domain/spawner_engine/depot_spawner.py` | 44 | `strapi_url: str = "http://localhost:1337"` | config.ini via dependency injection |
| `core/domain/plugins/poisson_plugin.py` | 202 | `'geo_url', 'http://localhost:6000'` | config.ini via dependency injection |

### ⚠️ WARNING - Service/API Files

| File | Line | Hardcoded Value | Usage |
|------|------|-----------------|-------|
| `interfaces/http/manifest_api.py` | 91, 143 | `"http://localhost:1337"`, `port=4000` | FastAPI entry point - should read config |
| `api/manifest_api.py` | 91, 143 | `"http://localhost:1337"`, `port=4000` | FastAPI entry point - should read config |
| `services/manifest_builder.py` | 128 | `"http://localhost:6000"` | Uses env var with fallback (OK) |
| `application/queries/manifest_query.py` | 128 | `"http://localhost:6000"` | Uses env var with fallback (OK) |

### ✅ OK - Test Files (Acceptable)

- `tests/sim/test_route_spawn_requester.py` - Test URLs (OK for tests)
- `tests/sim/test_commuter_spawn.py` - Test URLs (OK for tests)
- `scripts/console/list_passengers.py` - CLI tool with env var fallback (OK)
- `interfaces/cli/list_passengers.py` - CLI tool with env var fallback (OK)
- `scripts/precompute_route_depot_associations.py` - Seed script (OK)

---

## 2. ArkNet Transit Simulator (`arknet_transit_simulator/`)

### ❌ CRITICAL - Hardcoded URLs in Core Components

| File | Line | Hardcoded Value | Impact |
|------|------|-----------------|--------|
| `simulator.py` | 93 | `api_url: str = "http://localhost:1337"` | Main simulator class |
| `simulator.py` | 334 | `'server_url', 'ws://localhost:5000'` | GPS WebSocket connection |
| `simulator.py` | 445 | `strapi_url="http://localhost:1337"` | Passenger repository |
| `vehicle/conductor.py` | 194 | `sio_url: str = "http://localhost:1337"` | Conductor SocketIO |
| `vehicle/driver/navigation/vehicle_driver.py` | 96 | `sio_url: str = "http://localhost:1337"` | Driver SocketIO |
| `core/dispatcher.py` | 635 | `api_base_url: str = "http://localhost:1337"` | Dispatcher initialization |
| `core/dispatcher.py` | 894 | `"http://localhost:8000"` | FastAPI switch method |
| `core/dispatcher.py` | 916 | `"http://localhost:1337"` | Strapi switch method |
| `services/config_service.py` | 55 | `self.strapi_url = "http://localhost:1337"` | Config service |
| `services/vehicle_performance.py` | 44 | `"http://localhost:1337"` | Uses env var with fallback (⚠️) |
| `providers/data_provider.py` | 28 | `server_url: str = "http://localhost:8000"` | Data provider |
| `config/config_loader.py` | 87 | `'server_url': 'ws://localhost:5000/'` | GPS config default |
| `config/config_loader.py` | 158 | `'api_url': 'http://localhost:8000'` | API config default |

### ⚠️ WARNING - CLI Args (Acceptable with defaults)

| File | Line | Hardcoded Value | Usage |
|------|------|-----------------|-------|
| `__main__.py` | 24 | `default='http://localhost:1337'` | CLI argument default (OK) |

---

## 3. Geospatial Service (`geospatial_service/`)

### ❌ CRITICAL

| File | Line | Hardcoded Value | Should Use |
|------|------|-----------------|------------|
| `main.py` | 119 | `port=6000` | config.ini or environment variable |

### ✅ OK

| File | Line | Hardcoded Value | Usage |
|------|------|-----------------|-------|
| `config/database.py` | 17 | `"localhost"` | Database host with env var fallback (OK) |
| `tests/test_client_manual.py` | 22 | `"http://localhost:6000"` | Test file (OK) |

---

## 4. GPSCentCom Server (`gpscentcom_server/`)

### ✅ OK - Uses CLI Args and Config Files

- Port configured via CLI arguments (see `server_cli_args.py`)
- No hardcoded ports in main server code
- Examples in documentation use `127.0.0.1:5000` (documentation only - OK)

---

## 5. Launcher System (`launcher/`, `launch.py`)

### ✅ EXCELLENT - Properly Uses config.ini

| File | What It Does | Status |
|------|--------------|--------|
| `launcher/config.py` | Reads all config from config.ini with fallbacks | ✅ Perfect |
| `launcher/factory.py` | Constructs URLs from config | ✅ Good |
| `launch.py` | Hardcoded monitor port `7000` and service health URLs | ⚠️ Monitor port should be configurable |

### ⚠️ WARNING

| File | Line | Hardcoded Value | Issue |
|------|------|-----------------|-------|
| `launch.py` | 144 | `health_url="http://localhost:6000/health"` | Hardcoded, should use infra_config.geospatial_port |
| `launch.py` | 155 | `health_url="http://localhost:4000/health"` | Hardcoded, should use infra_config.manifest_port |
| `launch.py` | 250 | `port=7000` | Monitor port hardcoded |

---

## 6. Test Scripts (`test/`)

### ✅ OK - Test Files (Hardcoding Acceptable)

- `test_admin_import.py` - `"http://localhost:1337"`
- `test_amenity_import.py` - `"http://localhost:1337"`
- `test_highway_import.py` - `"http://localhost:1337"`
- `test_landuse_import.py` - `"http://localhost:1337"`
- `test_geospatial_api.py` - `"http://localhost:6000"`

**Status**: Acceptable for test files - they need known endpoints.

---

## 7. Utility Scripts

### ⚠️ WARNING - Hardcoded but Acceptable

| File | Hardcoded Value | Usage |
|------|-----------------|-------|
| `test_commuter_spawning.py` | `"http://localhost:4000"` | Test script - should use config |
| `reset_passengers.py` | `"http://localhost:1337"` | Utility script - should use config |
| `seeds/create_route1_spawn_config.py` | `"http://localhost:1337/api"` | Seed script (OK) |
| `arknet_fleet_manager/seed_operational_config.py` | `"http://localhost:1337"` | Seed script (OK) |
| `arknet_fleet_manager/delete_all_configs.py` | `"http://localhost:1337"` | Utility script (OK) |
| `arknet_fleet_manager/fix_permissions.py` | `"http://localhost:1337"` | Utility script (OK) |

---

## 8. Deprecated Services (`commuter_service_deprecated/`)

### ❌ CRITICAL - But Deprecated

**Status**: ⚠️ Marked for deletion - not worth fixing.

Multiple hardcoded URLs found:
- `"http://localhost:1337"` in multiple files
- SocketIO URLs hardcoded
- Strapi URLs hardcoded

**Recommendation**: Delete entire `commuter_service_deprecated/` folder as planned.

---

## 9. GPS Telemetry Client (`gps_telemetry_client/`)

### ⚠️ WARNING - Different Port Than GPSCentCom

| File | Line | Hardcoded Value | Issue |
|------|------|-----------------|-------|
| `client.py` | 51 | `"http://localhost:8000"` | **WRONG PORT!** Should be 5000 (GPSCentCom port) |
| `test_client.py` | 203 | `default='http://localhost:8000'` | **WRONG PORT!** Should be 5000 |

**CRITICAL**: GPS Telemetry Client defaults to port 8000, but GPSCentCom runs on 5000!

---

## 10. Start/Launch Scripts

### ✅ GOOD - Migrated to config.ini

| File | Status |
|------|--------|
| `start_fleet_services.py` | ✅ Migrated from dotenv to config.ini |
| `start_all_systems.py` | ✅ Uses config.ini |
| `start_services.py` | ⚠️ Hardcoded `BASE_URL = "http://localhost:7000"` (monitor API) |

---

## Summary by Priority

### 🔥 CRITICAL (Must Fix)

1. **arknet_transit_simulator/** - Hardcoded URLs throughout core components
   - `simulator.py`, `vehicle/conductor.py`, `vehicle/driver.py`
   - `core/dispatcher.py`, `services/config_service.py`
   
2. **commuter_simulator/** - Default parameters in constructors
   - All `__init__` methods with `strapi_url="http://localhost:1337"` defaults
   - GeospatialClient with `base_url="http://localhost:6000"` default

3. **gps_telemetry_client/** - WRONG PORT (8000 instead of 5000)
   - Will fail to connect to GPSCentCom

4. **geospatial_service/main.py** - Hardcoded port 6000
   - Should read from config or env var

5. **manifest API** - Hardcoded Strapi URL and port 4000
   - `commuter_simulator/interfaces/http/manifest_api.py`
   - `commuter_simulator/api/manifest_api.py`

### ⚠️ MEDIUM (Should Fix)

1. **launch.py** - Hardcoded health check URLs for geospatial (6000) and manifest (4000)
2. **launch.py** - Hardcoded monitor port 7000
3. **Utility scripts** - Should read from config.ini instead of hardcoding

### ✅ LOW (Acceptable)

1. **Test files** - Hardcoded values OK for tests
2. **Seed scripts** - Hardcoded values OK for one-time setup
3. **Deprecated code** - Will be deleted anyway

---

## Recommended Actions

### Immediate (Before Production):

1. **Fix GPS Telemetry Client port mismatch** (8000 → 5000)
2. **Refactor arknet_transit_simulator** to accept config/URLs via constructor
3. **Update geospatial_service/main.py** to read port from config
4. **Update manifest API** to read URLs from config

### Medium Priority:

1. **Fix launch.py hardcoded health URLs** (lines 144, 155)
2. **Add monitor_port to config.ini** for launch.py
3. **Update utility scripts** to read from config.ini

### Low Priority:

1. **Delete commuter_service_deprecated/** (already planned)
2. Document acceptable hardcoding in test files

---

## Configuration Strategy

### What Should Be Where:

```
config.ini (Infrastructure):
├── strapi_url = http://localhost:1337
├── strapi_port = 1337
├── gpscentcom_port = 5000
├── geospatial_port = 6000
├── manifest_port = 4000
└── monitor_port = 7000 (NEW)

.env (Secrets Only):
├── STRAPI_API_TOKEN=<secret>
└── (no URLs or ports)

Database (Runtime Settings):
└── operational-configurations table
    ├── continuous_mode
    ├── spawn_interval_seconds
    └── enable flags
```

### Constructor Pattern (Recommended):

**BAD** (Current):
```python
def __init__(self, strapi_url: str = "http://localhost:1337"):
    self.strapi_url = strapi_url
```

**GOOD** (Should Be):
```python
def __init__(self, strapi_url: str):
    """strapi_url: Injected from config.ini - no default"""
    self.strapi_url = strapi_url
```

**ACCEPTABLE** (With Clear Comment):
```python
def __init__(self, strapi_url: str | None = None):
    """strapi_url: Optional, defaults to config.ini value"""
    config = load_config()
    self.strapi_url = strapi_url or config['infrastructure']['strapi_url']
```

---

## Compliance Score

| Subsystem | Critical Issues | Medium Issues | Compliant? |
|-----------|----------------|---------------|------------|
| commuter_simulator | 8 | 2 | ❌ |
| arknet_transit_simulator | 13 | 1 | ❌ |
| geospatial_service | 1 | 0 | ⚠️ |
| gpscentcom_server | 0 | 0 | ✅ |
| launcher | 0 | 3 | ⚠️ |
| gps_telemetry_client | 1 | 0 | ❌ |

**Overall System Compliance**: **45% (Needs Work)**

---

## Next Steps

1. Create refactoring plan for arknet_transit_simulator (largest subsystem)
2. Fix GPS telemetry client port mismatch immediately
3. Update geospatial service to read port from config
4. Add monitor_port to config.ini
5. Document dependency injection pattern for future development
