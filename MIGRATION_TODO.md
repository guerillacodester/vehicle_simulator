# Dispatcher FastAPI → Strapi Migration TODO

## Migration Status: ✅ **PHASE 1 COMPLETE - READY FOR PHASE 2**

### **Phase 1: Strategy Pattern Foundation** ✅ **COMPLETED**

- [x] **Step 1.1**: Create ApiStrategy abstract base class ✅ **COMPLETED**
  - [x] Added ABC imports and ApiStrategy interface
  - [x] Test: Abstract methods defined correctly
  - [x] Test: Syntax validation passed
  
- [x] **Step 1.2**: Extract HTTP methods to FastApiStrategy ✅ **COMPLETED**
  - [x] Moved `get_vehicle_assignments()` → FastApiStrategy  
  - [x] Moved `get_all_depot_vehicles()` → FastApiStrategy
  - [x] Moved `get_driver_assignments()` → FastApiStrategy
  - [x] Moved `get_route_info()` → FastApiStrategy
  - [x] Test: All methods extracted successfully
  - [x] Test: Syntax validation passed

- [x] **Step 1.3**: Refactor Dispatcher Constructor ✅ **COMPLETED**
  - [x] Updated constructor to accept `ApiStrategy` parameter
  - [x] Default to `FastApiStrategy` for backwards compatibility
  - [x] Updated `initialize()` method to use strategy pattern
  - [x] Updated `shutdown()` method to use strategy pattern
  - [x] Delegated all API methods to strategy
  - [x] Test: Dispatcher constructor refactored successfully
  - [x] Test: All public methods delegate to API strategy

### **Phase 2: Route Data Migration** ✅ **COMPLETED**

- [x] **Step 2.1**: Implement GTFS-compliant StrapiStrategy ✅ **COMPLETED**
  - [x] Created StrapiStrategy class with proper GTFS structure
  - [x] Implemented routes → route-shapes → shapes lookup chain
  - [x] Test: Route "1A" fetches correctly via Strapi ✅
  - [x] Test: Response structure compatible with RouteInfo ✅
  
- [x] **Step 2.2**: Implement GTFS route geometry mapping ✅ **COMPLETED**
  - [x] Extract geometry from routes → route-shapes → shapes tables (NOT geojson_data)
  - [x] Map coordinate arrays to GeoJSON LineString format  
  - [x] Test: GPS coordinates extracted correctly ✅ (88 points)
  - [x] Test: Coordinate data quality higher than FastAPI ✅ (88 vs 84 points)
  
- [ ] **Step 2.3**: Test route buffer integration
  - [ ] Test RouteBuffer with Strapi route data
  - [ ] Test: RouteBuffer accepts Strapi route data
  - [ ] Test: GPS indexing works with Strapi geometry

### **Phase 3: Vehicle Data Migration**

- [ ] **Step 3.1**: Implement basic vehicle list mapping
  - [ ] Update `get_all_depot_vehicles()` for Strapi
  - [ ] Map vehicle performance data
  - [ ] Test: Vehicle list returns from Strapi
  - [ ] Test: Vehicle performance data correctly mapped
  
- [ ] **Step 3.2**: Implement vehicle-driver relationship mapping
  - [ ] Update `get_vehicle_assignments()` for Strapi populate
  - [ ] Map nested relationships to flat structure
  - [ ] Test: Vehicle assignments extract driver relationships
  - [ ] Test: VehicleAssignment objects created correctly
  
- [ ] **Step 3.3**: Implement driver assignment mapping
  - [ ] Update `get_driver_assignments()` from vehicle data
  - [ ] Map reverse relationship (driver from vehicle)
  - [ ] Test: Driver assignments work from vehicle data
  - [ ] Test: DriverAssignment objects match FastAPI format

### **Phase 4: Integration Testing**

- [ ] **Step 4.1**: End-to-end simulator test with Strapi
  - [ ] Run simulator with `use_strapi=True`
  - [ ] Test: Simulator starts successfully with Strapi API
  - [ ] Test: Route data loads without errors
  
- [ ] **Step 4.2**: Vehicle movement simulation test
  - [ ] Test vehicle GPS movement with Strapi data
  - [ ] Test: Vehicles follow GPS coordinates from Strapi
  - [ ] Test: Performance characteristics applied correctly
  
- [ ] **Step 4.3**: Driver-vehicle assignment test
  - [ ] Test depot manager with Strapi assignments
  - [ ] Test: Driver assignments work in depot manager
  - [ ] Test: Route assignments distributed correctly

### **Phase 5: Cleanup & Finalization**

- [ ] **Step 5.1**: Remove FastAPI client code
  - [ ] Remove old FastAPI HTTP calls
  - [ ] Clean up unused imports
  - [ ] Test: All functionality works without FastAPI dependency
  - [ ] Test: Error handling graceful
  
- [ ] **Step 5.2**: Update default configuration
  - [ ] Update simulator default API URL to port 1337
  - [ ] Update CLI argument defaults
  - [ ] Test: Simulator defaults to Strapi (port 1337)
  - [ ] Test: CLI arguments work correctly
  
- [ ] **Step 5.3**: Documentation and validation
  - [ ] Update code comments
  - [ ] Validate all original functionality
  - [ ] Test: All original functionality preserved
  - [ ] Test: Performance equivalent or better

## **API Endpoint Mappings Confirmed ✅**

| FastAPI Endpoint | Strapi Endpoint | Status |
|------------------|-----------------|--------|
| `GET /health` | `GET /api/drivers` (for connectivity) | ✅ Compatible |
| `GET /api/v1/search/vehicle-driver-pairs` | `GET /api/vehicles?populate=*` | ✅ Compatible |
| `GET /api/v1/vehicles/public` | `GET /api/vehicles` | ✅ Compatible |
| `GET /api/v1/routes/public/{code}` | `GET /api/routes?filters[short_name][$eq]={code}` | ✅ Compatible |
| `GET /api/v1/routes/public/{code}/geometry` | Same route endpoint (includes geojson_data) | ✅ Compatible |

## **Data Structure Mappings**

### Vehicle-Driver Pairs

**FastAPI Response** → **Strapi Mapping**

- `registration` → `reg_code`
- `vehicle_status` → `vehicle_status.name`
- `vehicle_capacity` → `capacity`
- `driver_name` → `assigned_driver.name`
- `driver_license` → `assigned_driver.license_no`
- `driver_employment_status` → `assigned_driver.employment_status`
- `route_code` → `preferred_route.short_name`
- `route_name` → `preferred_route.long_name`
- `depot_name` → `home_depot.name`

### Route Geometry

**FastAPI Response** → **Strapi Mapping**

- `geometry.coordinates[]` → `geojson_data.features[].geometry.coordinates[]`
- `coordinate_count` → Calculate from coordinates array length

## **SUCCESS CRITERIA** 🎯

**Ultimate Test**:

```bash
python -m arknet_transit_simulator --mode depot --duration 5 --debug --api-type strapi
```

**Must produce IDENTICAL output to FastAPI version, including:**

- ✅ API connection successful
- ✅ 4 vehicle assignments fetched
- ✅ 4 driver assignments fetched  
- ✅ Route 1A: 84 GPS coordinates
- ✅ Route 1: 88 GPS coordinates
- ✅ 2 active vehicles (ZR101, ZR400)
- ✅ Same passenger distribution
- ✅ Same GPS telemetry to port 5000

**Key Change**: HTTP calls `localhost:8000` → `localhost:1337`

## **Next Action**: Begin Step 1.1 - Create ApiStrategy pattern implementation
