# Geospatial Service API - Current Organization Analysis

## Current API Structure (As-Is)

### 1. **Geocoding API** (`/geocode`)
- POST `/geocode/reverse` - Convert lat/lon to address
- GET `/geocode/reverse` - Convert lat/lon to address (query params)

### 2. **Geofencing API** (`/geofence`)
- POST `/geofence/check` - Check if point is inside region/landuse
- POST `/geofence/check-batch` - Batch geofence checking

### 3. **Spatial Queries API** (`/spatial`)
- GET `/spatial/route-geometry/{route_id}` - Get route geometry
- POST `/spatial/route-buildings` - Buildings along route
- POST `/spatial/depot-catchment` - Buildings near depot
- GET `/spatial/depot-catchment` - Buildings near depot (query params)
- GET `/spatial/nearby-buildings` - Buildings near point

### 4. **Spawn Analysis API** (`/spawn`) **[NEW]**
- GET `/spawn/depot-analysis/{depot_id}` - Complete depot spawn analysis
- GET `/spawn/all-depots` - Spawn analysis for all depots
- GET `/spawn/route-analysis/{route_id}` - Complete route spawn analysis
- GET `/spawn/all-routes` - Spawn analysis for all routes
- GET `/spawn/system-overview` - Complete system spawn overview
- GET `/spawn/compare-scaling` - Compare different scaling factors

---

## SOLID/SOC Issues Identified

### Problems:
1. **Mixing Concerns**: `/spatial` has both raw data queries AND building queries
2. **Duplicated Endpoints**: Multiple ways to do same thing (POST vs GET for same operation)
3. **Missing Categories**: No dedicated Transit/Route/Depot/Building APIs
4. **Inconsistent Naming**: `route-buildings` vs `nearby-buildings` vs `depot-catchment`
5. **Business Logic in Wrong Place**: Spawn calculations mixed with spatial queries
6. **No Clear Ownership**: Who owns "buildings"? Spatial? Spawn? Both?

---

## Proposed Reorganization (SOLID/SOC Applied)

### **Category 1: CORE GEOSPATIAL SERVICES** (Infrastructure Layer)
**Purpose**: Low-level spatial operations, no business logic

#### A. **Geocoding API** (`/geocode`) ✅ Already correct
- GET `/geocode/reverse?lat={lat}&lon={lon}` - Lat/lon to address
- GET `/geocode/forward?address={address}` - Address to lat/lon [MISSING]

#### B. **Geofencing API** (`/geofence`) ✅ Already correct
- POST `/geofence/check` - Single point geofence check
- POST `/geofence/check-batch` - Batch geofence checking
- GET `/geofence/regions` - List all geofenced regions [MISSING]
- GET `/geofence/regions/{region_id}` - Get region details [MISSING]

---

### **Category 2: RESOURCE QUERY APIS** (Data Access Layer)
**Purpose**: CRUD operations on spatial resources, no calculations

#### C. **Buildings API** (`/buildings`) [NEW - REORGANIZED]
**Single Responsibility**: Everything about buildings
- GET `/buildings/near-point?lat={lat}&lon={lon}&radius={r}` - Buildings near point
- GET `/buildings/along-route?route_id={id}&buffer={b}` - Buildings along route
- GET `/buildings/{building_id}` - Get specific building [MISSING]
- GET `/buildings?bbox={minLat},{minLon},{maxLat},{maxLon}` - Buildings in bbox [MISSING]
- GET `/buildings/stats` - Building statistics [MISSING]

#### D. **Routes API** (`/routes`) [NEW - REORGANIZED]
**Single Responsibility**: Everything about routes/highways
- GET `/routes/{route_id}/geometry` - Get route geometry
- GET `/routes/{route_id}/details` - Get route details [MISSING]
- GET `/routes` - List all routes [MISSING]
- GET `/routes/{route_id}/length` - Calculate route length [MISSING]
- GET `/routes/{route_id}/bbox` - Get route bounding box [MISSING]

#### E. **Depots API** (`/depots`) [NEW]
**Single Responsibility**: Everything about depots/terminals
- GET `/depots/{depot_id}` - Get depot details [MISSING]
- GET `/depots` - List all depots [MISSING]
- GET `/depots/{depot_id}/routes` - Routes servicing this depot [MISSING]
- GET `/depots/{depot_id}/coverage-area` - Depot service area [MISSING]

#### F. **Regions API** (`/regions`) [NEW]
**Single Responsibility**: Administrative boundaries
- GET `/regions` - List all regions [MISSING]
- GET `/regions/{region_id}` - Get region details [MISSING]
- GET `/regions/towns` - List all towns [MISSING]
- GET `/regions/parishes` - List all parishes [MISSING]
- GET `/regions/at-point?lat={lat}&lon={lon}` - Find region at point [MISSING]

---

### **Category 3: ANALYSIS & BUSINESS LOGIC APIS** (Application Layer)
**Purpose**: Calculations, aggregations, business intelligence

#### G. **Spawn Analysis API** (`/spawn`) ✅ Partially complete
**Single Responsibility**: Passenger spawn rate calculations
- GET `/spawn/depots/{depot_id}/analysis` - Depot spawn analysis
- GET `/spawn/depots` - All depots spawn analysis
- GET `/spawn/routes/{route_id}/analysis` - Route spawn analysis
- GET `/spawn/routes` - All routes spawn analysis
- GET `/spawn/system-overview` - System-wide overview
- GET `/spawn/compare-scaling` - Compare scaling factors
- POST `/spawn/calculate` - Custom spawn calculation [MISSING]
- GET `/spawn/recommendations` - Suggested spawn parameters [MISSING]

#### H. **Density Analysis API** (`/density`) [NEW - MISSING]
**Single Responsibility**: Population/building density metrics
- GET `/density/heatmap?bbox={bbox}` - Building density heatmap
- GET `/density/routes/{route_id}` - Density along route
- GET `/density/depots/{depot_id}` - Density around depot
- GET `/density/regions/{region_id}` - Regional density
- GET `/density/compare?depots={id1},{id2}` - Compare depot densities

#### I. **Coverage Analysis API** (`/coverage`) [NEW - MISSING]
**Single Responsibility**: Service coverage & accessibility
- GET `/coverage/routes` - Route network coverage map
- GET `/coverage/depots` - Depot coverage areas
- GET `/coverage/gaps` - Identify coverage gaps
- GET `/coverage/overlap` - Route overlap analysis
- GET `/coverage/accessibility?lat={lat}&lon={lon}` - Nearest transit access

#### J. **Route Planning API** (`/planning`) [NEW - MISSING]
**Single Responsibility**: Route optimization & planning support
- POST `/planning/optimal-route` - Calculate optimal route
- GET `/planning/route-alternatives` - Alternative route suggestions
- POST `/planning/service-area` - Calculate service area polygon
- GET `/planning/demand-hotspots` - Identify high-demand areas

---

## Summary of Changes Needed

### **MOVE** (Reorganize existing):
1. `/spatial/route-buildings` → `/buildings/along-route`
2. `/spatial/nearby-buildings` → `/buildings/near-point`
3. `/spatial/depot-catchment` → `/buildings/near-point` (same endpoint)
4. `/spatial/route-geometry` → `/routes/{id}/geometry`
5. `/spawn/depot-analysis/{id}` → `/spawn/depots/{id}/analysis`
6. `/spawn/route-analysis/{id}` → `/spawn/routes/{id}/analysis`
7. `/spawn/all-depots` → `/spawn/depots`
8. `/spawn/all-routes` → `/spawn/routes`

### **ADD** (New endpoints needed):
1. **Buildings API**: `/buildings/{id}`, `/buildings?bbox=...`, `/buildings/stats`
2. **Routes API**: `/routes`, `/routes/{id}/details`, `/routes/{id}/length`
3. **Depots API**: `/depots`, `/depots/{id}`, `/depots/{id}/routes`
4. **Regions API**: `/regions`, `/regions/towns`, `/regions/at-point`
5. **Density API**: Full new category
6. **Coverage API**: Full new category
7. **Planning API**: Full new category
8. **Geocoding**: Forward geocoding (`/geocode/forward`)

### **REMOVE** (Deprecated):
1. Duplicate POST/GET endpoints - standardize on GET for queries
2. `/spatial` prefix - split into domain-specific APIs

---

## Final API Categories (SOLID/SOC Compliant)

```
CORE GEOSPATIAL (Infrastructure)
├── /geocode      - Address ↔ Coordinates
└── /geofence     - Point-in-polygon checks

RESOURCES (Data Access)
├── /buildings    - Building queries
├── /routes       - Route/highway queries
├── /depots       - Depot/terminal queries
└── /regions      - Administrative boundaries

ANALYSIS (Business Logic)
├── /spawn        - Spawn rate calculations
├── /density      - Density analysis
├── /coverage     - Service coverage metrics
└── /planning     - Route planning support
```

---

## Implementation Priority

### **Phase 1 (Immediate)** - Fix current chaos:
1. Create `/buildings` API - consolidate building queries
2. Create `/routes` API - consolidate route queries
3. Create `/depots` API - depot information
4. Update `/spawn` paths to be consistent
5. Deprecate `/spatial` (migrate to specific APIs)

### **Phase 2 (Next)** - Add missing core:
1. `/regions` API - towns, parishes, boundaries
2. Forward geocoding
3. Geofence region listing

### **Phase 3 (Future)** - Advanced analytics:
1. `/density` API - heatmaps and metrics
2. `/coverage` API - service area analysis
3. `/planning` API - optimization tools

---

## Benefits of Reorganization

✅ **Single Responsibility**: Each API owns one domain
✅ **Clear Ownership**: No confusion about which API to use
✅ **No Duplication**: One way to do each operation
✅ **Consistent Naming**: RESTful resource paths
✅ **Separation of Concerns**: Infrastructure vs Data vs Business Logic
✅ **Easy to Extend**: Add new analysis without touching core
✅ **Testable**: Each API can be tested independently
✅ **Discoverable**: Logical categorization
