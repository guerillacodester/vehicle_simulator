# GeoJSON Import System - Architecture & Context (SINGLE SOURCE OF TRUTH)

**Date**: October 25, 2025  
**Project**: ArkNet Vehicle Simulator  
**Purpose**: Redis-based reverse geocoding + real-time geofencing + Poisson spawning integration  
**Status**: Planning Phase  
**Last Updated**: October 25, 2025 - Consolidated architecture decisions

> **📌 COMPANION DOCUMENT**: See `GEOJSON_IMPORT_TODO.md` for implementation plan

---

## 📋 **EXECUTIVE SUMMARY**

This document provides the **authoritative architecture reference** for implementing a GeoJSON import system integrated with:
- **Strapi CMS** action-buttons plugin for import triggers
- **Redis** for fast reverse geocoding (lat/lon → address)
- **PostGIS** for spatial queries and geofencing
- **Socket.IO** for real-time geofence notifications
- **Existing Poisson spawning system** for passenger generation

### **Current State**
- ✅ Strapi v5 with PostgreSQL + PostGIS
- ✅ Action-buttons plugin operational (window object handlers)
- ✅ Poisson spawning using SimpleSpatialZoneCache (loads amenity/landuse from Strapi API)
- ✅ Geofence API exists (`find_nearby_features_fast()` SQL function, ~2 sec query time)
- ❌ **Redis not implemented** (greenfield requirement)
- ❌ **GeoJSON import mechanism doesn't exist** (feasibility phase)
- ❌ **Real-time geofencing notifications not implemented**

---

## 🗂️ **DATA INVENTORY**

### **GeoJSON Files in `sample_data/` (11 files)**

| File | Features | Size | Target Table | Priority |
|------|----------|------|--------------|----------|
| `amenity.geojson` | 1,427 | 3.8MB | `poi` | **HIGH** - Spawning |
| `highway.geojson` | 22,719 | 43MB | `highway` | **HIGH** - Reverse geocoding |
| `landuse.geojson` | 2,267 | 4.3MB | `landuse_zone` | **HIGH** - Spawning weights |
| `building.geojson` | ? | **658MB** | `building` (new) | **MEDIUM** - Context |
| `admin_level_6_polygon.geojson` | ? | ? | `region` | **HIGH** - Parishes |
| `admin_level_8_polygon.geojson` | ? | ? | `region` | **MEDIUM** - Districts |
| `admin_level_9_polygon.geojson` | ? | ? | `region` | **LOW** - Sub-districts |
| `admin_level_10_polygon.geojson` | ? | ? | `place` | **LOW** - Localities |
| `natural.geojson` | ? | ? | `natural_feature` (new) | **LOW** - Context |
| `name.geojson` | ? | ? | TBD | **LOW** - Named places |
| `add_street_polygon.geojson` | ? | ? | TBD | **MEDIUM** - Addresses |

**Excluded**: `barbados_geocoded_stops_utm.geojson` (separate system)

---

## 🏗️ **ARCHITECTURE OVERVIEW**

### **System Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                    GEOJSON IMPORT FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. IMPORT TRIGGER (Strapi Admin UI)
   ↓
   User clicks action button on Country content-type
   ↓
   window.importGeoJSON(countryId, 'amenity') triggered
   ↓
   
2. BACKEND IMPORT SERVICE
   ↓
   POST /api/geojson-import
   ├── Validate country + file exists
   ├── Read sample_data/amenity.geojson
   ├── Parse JSON (streaming for large files)
   ├── Transform properties → database schema
   │   └── Extract centroid for polygons
   ├── Batch insert to PostgreSQL (poi table)
   ├── Update import metadata
   └── Return progress/results
   ↓
   
3. REDIS CACHE UPDATE
   ↓
   For each imported feature:
   ├── highway: GEOADD highways:barbados {lon} {lat} {highway_id}
   ├── poi: GEOADD pois:barbados {lon} {lat} {poi_id}
   └── Cache reverse geocode: SET geo:{lat}:{lon} "{address_string}"
   ↓
   
4. SPATIAL INDEXING
   ↓
   PostGIS automatically creates GiST indexes on geometry columns
   ↓
   
5. GEOFENCING SETUP
   ↓
   Materialized views for geofence zones (already exists)
   ↓
   
6. POISSON SPAWNING INTEGRATION
   ↓
   SimpleSpatialZoneCache refreshes from updated Strapi API
   └── New amenities/landuse zones now included in spawn calculations
```

---

## 🔍 **DETAILED COMPONENT ANALYSIS**

### **1. GeoJSON Property Mapping**

#### **Highway (LineString geometry)**
```json
{
  "type": "Feature",
  "properties": {
    "full_id": "w5172465",
    "osm_id": "5172465",
    "osm_type": "way",
    "highway": "trunk",           // → highway.highway_type
    "name": "Tom Adams Highway",  // → highway.name
    "ref": "ABC",                 // → highway.ref
    "oneway": "yes",              // → highway.oneway
    "lanes": "2",                 // → highway.lanes
    "maxspeed": "80",             // → highway.maxspeed
    "surface": "asphalt"          // → highway.surface
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [[lon, lat], [lon, lat], ...]
  }
}
```

**Database Schema** (`highway/schema.json`):
- `highway_type`: Enum (motorway, trunk, primary, secondary, tertiary, residential, unclassified, service, other_*)
- `osm_id`: String (unique identifier)
- `name`: String
- `ref`: String (route number like "ABC", "H4")
- `oneway`: Boolean
- `lanes`: Integer
- `maxspeed`: String
- `surface`: String
- `geometry_geojson`: JSON (full LineString)
- `center_latitude`, `center_longitude`: Float (midpoint for indexing)

**Transformation Logic**:
```javascript
// Calculate midpoint of LineString
const coords = feature.geometry.coordinates;
const midIndex = Math.floor(coords.length / 2);
const [lon, lat] = coords[midIndex];

const highway = {
  osm_id: feature.properties.osm_id,
  highway_type: feature.properties.highway,
  name: feature.properties.name,
  ref: feature.properties.ref,
  oneway: feature.properties.oneway === 'yes',
  lanes: parseInt(feature.properties.lanes) || null,
  maxspeed: feature.properties.maxspeed,
  surface: feature.properties.surface,
  geometry_geojson: feature.geometry,
  center_latitude: lat,
  center_longitude: lon,
  country: countryId
};
```

---

#### **Landuse (MultiPolygon geometry)**
```json
{
  "type": "Feature",
  "properties": {
    "full_id": "r12727443",
    "osm_id": "12727443",
    "osm_type": "relation",
    "landuse": "farmland",       // → landuse_zone.landuse_type
    "name": null,                 // → landuse_zone.name
    "crop": null,                 // → landuse_zone.metadata
    "residential": null,          // → landuse_zone.metadata
    "type": "multipolygon"
  },
  "geometry": {
    "type": "MultiPolygon",
    "coordinates": [[[[lon, lat], ...]]]
  }
}
```

**Database Schema** (`landuse-zone/schema.json`):
- `osm_id`: String
- `landuse_type`: String (farmland, residential, grass, meadow, commercial, industrial)
- `name`: String
- `geometry_geojson`: JSON (full MultiPolygon)
- `population_density`: Float (calculated or default by type)
- `spawn_weight`: Float (for Poisson spawning - default by type)
- `peak_hour_multiplier`: Float (temporal modifier)
- `center_latitude`, `center_longitude`: Float (centroid)

**Transformation Logic**:
```javascript
// Calculate centroid of MultiPolygon using Turf.js or PostGIS
const centroid = calculateCentroid(feature.geometry);

// Default spawn weights by landuse type
const spawnWeights = {
  residential: 0.8,
  commercial: 0.6,
  industrial: 0.3,
  farmland: 0.1,
  grass: 0.05,
  meadow: 0.05
};

const landuse = {
  osm_id: feature.properties.osm_id,
  landuse_type: feature.properties.landuse,
  name: feature.properties.name,
  geometry_geojson: feature.geometry,
  population_density: calculateDensity(feature.properties.landuse),
  spawn_weight: spawnWeights[feature.properties.landuse] || 0.5,
  peak_hour_multiplier: 1.0,
  center_latitude: centroid[1],
  center_longitude: centroid[0],
  country: countryId
};
```

---

#### **Amenity (MultiPolygon/Point geometry)**
```json
{
  "type": "Feature",
  "properties": {
    "full_id": "...",
    "osm_id": "...",
    "amenity": "school",          // → poi.poi_type
    "name": "St. Mary's School",  // → poi.name
    "building": "yes",            // → poi.metadata
    "addr:street": "Main St",     // → poi.address
    "addr:city": "Bridgetown"     // → poi.metadata
  },
  "geometry": {
    "type": "MultiPolygon",  // OR "Point"
    "coordinates": ...
  }
}
```

**Database Schema** (`poi/schema.json`):
- `osm_id`: String
- `poi_type`: String (school, hospital, restaurant, mall, park, etc.)
- `name`: String
- `latitude`, `longitude`: Float (**centroid if polygon**)
- `address`: String
- `metadata`: JSON (all other properties)
- `activity_level`: Float (for Poisson spawning)

**⚠️ CRITICAL ISSUE**: POI schema expects Point coordinates but amenities are often MultiPolygons!

**Solution Options**:
1. **Option A (Simple)**: Extract centroid only, lose shape data
   ```javascript
   const centroid = calculateCentroid(feature.geometry);
   poi.latitude = centroid[1];
   poi.longitude = centroid[0];
   ```

2. **Option B (Complete)**: Create `poi_shape` table for polygons
   ```sql
   -- poi table: centroid only
   latitude FLOAT, longitude FLOAT
   
   -- poi_shape table: full geometry
   poi_id → poi.id
   geometry_geojson JSON
   ```

3. **Option C (Hybrid)**: Store both in metadata
   ```javascript
   poi.latitude = centroid[1];
   poi.longitude = centroid[0];
   poi.metadata = {
     ...feature.properties,
     original_geometry: feature.geometry  // Full polygon
   };
   ```

**Recommendation**: **Option B** - Maintain data integrity, enable polygon-based queries

---

### **2. Redis Architecture**

#### **Why Redis?**
- Current PostGIS query: ~2 seconds for `find_nearby_features_fast()`
- Target: <200ms for reverse geocoding
- Need: Real-time geofence notifications (100+ vehicles)

#### **Redis Data Structures**

**Option A: Geospatial Indexes (GEOADD/GEORADIUS)**
```redis
# Store highways by country
GEOADD highways:barbados -59.5905 13.0806 highway:5172465
GEOADD highways:barbados -59.5837 13.1133 highway:5179386

# Store POIs by country
GEOADD pois:barbados -59.6016 13.0947 poi:amenity_123
GEOADD pois:barbados -59.5684 13.0701 poi:amenity_456

# Reverse geocoding query (nearest highway + POI within 50m)
GEORADIUS highways:barbados -59.5905 13.0806 50 m WITHDIST COUNT 1
GEORADIUS pois:barbados -59.5905 13.0806 50 m WITHDIST COUNT 1

# Performance: O(log(N)) - sub-millisecond for 50k points
```

**Option B: Reverse Geocode Cache (SET/GET)**
```redis
# Pre-computed reverse geocodes (rounded to 5 decimals = ~1m precision)
SET geo:13.08062:-59.59050 "Tom Adams Highway, Bridgetown"
SET geo:13.11330:-59.58370 "Highway 4, St. Michael"

# Query (instant)
GET geo:13.08062:-59.59050
# → "Tom Adams Highway, Bridgetown"

# With fallback to geospatial if not cached
```

**Option C: Hybrid (Recommended)**
```redis
# 1. Geospatial indexes for spatial queries
GEOADD highways:barbados -59.5905 13.0806 highway:5172465

# 2. Detail lookups (hash for efficiency)
HSET highway:5172465 name "Tom Adams Highway" type "trunk" ref "ABC"

# 3. Reverse geocode cache (hot paths only)
SET geo:13.08062:-59.59050 "Tom Adams Highway, Bridgetown"

# Query flow:
# 1. Try cache: GET geo:13.08062:-59.59050
# 2. If miss: GEORADIUS highways:barbados ...
# 3. Get details: HGET highway:{id} name
# 4. Cache result: SET geo:13.08062:-59.59050 ...
```

**Memory Estimation**:
- **Highways**: 22,719 × (24 bytes geospatial + 200 bytes hash) = ~5MB
- **POIs**: 1,427 × 224 bytes = ~320KB
- **Landuse**: 2,267 × 224 bytes = ~510KB
- **Cache**: 100k entries × 100 bytes = ~10MB
- **Total**: ~16MB per country (negligible)

---

### **3. Action Buttons Plugin Integration**

#### **Current Plugin Architecture** (from `strapi-plugin-action-buttons/ARCHITECTURE.md`)

```
┌─────────────────────────────────────────┐
│   Strapi Admin UI (Country Edit)       │
│   ┌─────────────────────────────────┐   │
│   │ [Import Amenities]              │   │ ← Action Button
│   │ [Import Highway]                │   │
│   │ [Import Landuse]                │   │
│   │ [View Import Stats]             │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
              │ onClick
              ▼
┌─────────────────────────────────────────┐
│   CustomFieldButton Component           │
│   (React)                                │
│                                          │
│   const buttonConfig = {                │
│     label: "Import Amenities",          │
│     onClick: "importGeoJSON",           │
│     metadata: {                          │
│       fileType: "amenity"                │
│     }                                    │
│   }                                      │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   window.importGeoJSON()                │
│   (Global handler)                       │
│                                          │
│   function importGeoJSON(entityId,      │
│     metadata) {                          │
│     const fileType = metadata.fileType; │
│     fetch('/api/geojson-import', {      │
│       method: 'POST',                    │
│       body: JSON.stringify({            │
│         countryId: entityId,             │
│         fileType: fileType               │
│       })                                 │
│     });                                  │
│   }                                      │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   Strapi API Endpoint                   │
│   /api/geojson-import                   │
│                                          │
│   POST handler:                          │
│   1. Validate country exists             │
│   2. Check file exists in sample_data/  │
│   3. Start import job (async)           │
│   4. Return job ID                       │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   Import Service (Background Job)       │
│                                          │
│   - Stream parse GeoJSON                │
│   - Transform features                   │
│   - Batch insert to PostgreSQL          │
│   - Update Redis                         │
│   - Emit Socket.IO progress events      │
│   - Update country.geodata_import_status│
└─────────────────────────────────────────┘
```

#### **Country Schema Additions**

Add to `country/schema.json`:
```json
{
  "geodata_import_buttons": {
    "type": "customField",
    "customField": "plugin::action-buttons.button-group",
    "options": {
      "buttons": [
        {
          "label": "Import Amenities",
          "onClick": "importGeoJSON",
          "metadata": { "fileType": "amenity" },
          "variant": "primary"
        },
        {
          "label": "Import Highways",
          "onClick": "importGeoJSON",
          "metadata": { "fileType": "highway" },
          "variant": "primary"
        },
        {
          "label": "Import Landuse",
          "onClick": "importGeoJSON",
          "metadata": { "fileType": "landuse" },
          "variant": "primary"
        },
        {
          "label": "Import Buildings",
          "onClick": "importGeoJSON",
          "metadata": { "fileType": "building" },
          "variant": "secondary"
        },
        {
          "label": "Import Admin Boundaries",
          "onClick": "importGeoJSON",
          "metadata": { "fileType": "admin" },
          "variant": "secondary"
        },
        {
          "label": "View Import Stats",
          "onClick": "viewImportStats",
          "metadata": {},
          "variant": "tertiary"
        },
        {
          "label": "Clear Redis Cache",
          "onClick": "clearRedisCache",
          "metadata": {},
          "variant": "danger"
        }
      ]
    }
  },
  
  "geodata_import_status": {
    "type": "json",
    "default": {
      "amenity": { "imported": false, "count": 0, "lastImport": null },
      "highway": { "imported": false, "count": 0, "lastImport": null },
      "landuse": { "imported": false, "count": 0, "lastImport": null },
      "building": { "imported": false, "count": 0, "lastImport": null },
      "admin": { "imported": false, "count": 0, "lastImport": null }
    }
  }
}
```

---

### **4. Geofencing Notifications**

#### **Current Geofence System**
- ✅ SQL function: `find_nearby_features_fast(lat, lon, radius)`
- ✅ Materialized views: `create_geofence_postgis_views.sql`
- ✅ API endpoint: `/api/geofence/find-nearby-features-fast`
- ❌ **No real-time notifications**

#### **Real-Time Notification Architecture**

**Option A: Polling (Current)**
```javascript
// Vehicle polls every 5 seconds
setInterval(() => {
  const { lat, lon } = vehicle.currentPosition;
  fetch(`/api/geofence/find-nearby-features-fast?lat=${lat}&lon=${lon}`)
    .then(res => res.json())
    .then(data => {
      if (data.highway || data.poi) {
        console.log('Entered:', data);
      }
    });
}, 5000);

// Pros: Simple
// Cons: 100 vehicles = 1200 req/min, stale data, latency
```

**Option B: Redis Pub/Sub (Recommended)**
```javascript
// GPS device publishes position
redis.publish('vehicle:position', JSON.stringify({
  vehicleId: 'V123',
  lat: 13.0806,
  lon: -59.5905,
  timestamp: Date.now()
}));

// Geofence service subscribes
redis.subscribe('vehicle:position', async (message) => {
  const { vehicleId, lat, lon } = JSON.parse(message);
  
  // Fast Redis geospatial query
  const nearbyHighways = await redis.georadius(
    'highways:barbados', lon, lat, 50, 'm'
  );
  
  const nearbyPOIs = await redis.georadius(
    'pois:barbados', lon, lat, 50, 'm'
  );
  
  // Emit to vehicle via Socket.IO
  io.to(vehicleId).emit('geofence:entered', {
    highway: nearbyHighways[0],
    poi: nearbyPOIs[0]
  });
});

// Pros: Real-time, scalable, <10ms latency
// Cons: Requires Redis infrastructure
```

**Option C: PostgreSQL NOTIFY/LISTEN**
```sql
-- Trigger on GPS position update
CREATE OR REPLACE FUNCTION notify_geofence()
RETURNS trigger AS $$
DECLARE
  nearby_features json;
BEGIN
  SELECT json_build_object(
    'highway', (SELECT name FROM highway 
                WHERE ST_DWithin(geometry, 
                  ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326), 
                  50) LIMIT 1),
    'poi', (SELECT name FROM poi 
            WHERE ST_DWithin(ST_MakePoint(longitude, latitude), 
              ST_MakePoint(NEW.longitude, NEW.latitude), 
              0.0005) LIMIT 1)
  ) INTO nearby_features;
  
  PERFORM pg_notify('geofence', 
    json_build_object('vehicleId', NEW.vehicle_id, 'features', nearby_features)::text
  );
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER geofence_notify
AFTER INSERT OR UPDATE ON gps_positions
FOR EACH ROW EXECUTE FUNCTION notify_geofence();

// Pros: No additional infrastructure
// Cons: Slower than Redis, postgres load
```

**Recommendation**: **Option B (Redis Pub/Sub)** - Real-time, scalable, aligns with Redis reverse geocoding

---

### **5. Poisson Spawning Integration**

#### **Current Spawning System**
File: `commuter_service/poisson_geojson_spawner.py`

```python
class PoissonGeoJSONSpawner:
    def __init__(self):
        self.zone_cache = SimpleSpatialZoneCache()  # Loads from Strapi API
        
    async def _calculate_poisson_rate(self, zone: PopulationZone, context: str):
        # Base rate from zone properties
        base_rate = zone.population_density * zone.spawn_weight
        
        # Temporal multiplier (18x reduction for realistic rates)
        peak_multiplier = self._get_peak_multiplier(datetime.now().hour)
        
        # Context modifier
        if context == 'depot':
            context_modifier = 1.0  # Journey starts
        elif context == 'route':
            context_modifier = 0.5  # Already traveling
            
        # Amenity-specific activity levels (evening 9 PM)
        activity_levels = {
            'mall': 0.34,
            'university': 0.27,
            'school': 0.17,
            'hospital': 0.12
        }
        
        activity = activity_levels.get(zone.amenity_type, 0.2)
        
        return base_rate * peak_multiplier * context_modifier * activity / 18.0
```

#### **Integration with New GeoJSON Data**

**Before Import**:
- SimpleSpatialZoneCache loads ~50 amenities/landuse zones from Strapi
- Spawn rates: ~50/hr depot + ~50/hr route = 100/hr total

**After Import**:
- SimpleSpatialZoneCache loads 1,427 amenities + 2,267 landuse zones
- More granular spatial coverage
- More accurate population density
- More amenity types with specific activity levels

**Required Changes**:
1. **None to Python code** - SimpleSpatialZoneCache already fetches from Strapi API
2. **Update activity levels** in `poisson_geojson_spawner.py` for new amenity types:
   ```python
   activity_levels = {
       # Existing
       'mall': 0.34,
       'university': 0.27,
       'school': 0.17,
       'hospital': 0.12,
       # New from OSM
       'restaurant': 0.25,
       'cafe': 0.20,
       'bank': 0.15,
       'pharmacy': 0.18,
       'parking': 0.08,
       'fuel': 0.10,
       'bus_station': 0.30,
       # ... (add all OSM amenity types)
   }
   ```
3. **Refresh cache** after import:
   ```python
   # Automatically refreshes on next spawn cycle
   await spawner.zone_cache.refresh_zones()
   ```

**Expected Impact**:
- ✅ Finer-grained spatial distribution (more realistic spawning locations)
- ✅ Better coverage of rural/suburban areas
- ⚠️ May need to **re-calibrate spawn weights** to maintain ~100/hr total rate
- ⚠️ Performance: Loading 3,694 zones vs 50 zones - may need pagination/filtering

---

## 🚀 **IMPLEMENTATION STRATEGY**

### **Phase 1: Foundation (Redis + Import Service)**
1. Set up Redis server
2. Create GeoJSON import API endpoint
3. Implement streaming JSON parser
4. Build property transformation logic
5. Implement batch PostgreSQL insert

### **Phase 2: Core Data (Highway + POI + Landuse)**
1. Import highway.geojson → highway table + Redis GEOADD
2. Import amenity.geojson → poi table + Redis GEOADD (handle polygon centroids)
3. Import landuse.geojson → landuse_zone table
4. Test reverse geocoding speed (Redis vs PostGIS)

### **Phase 3: Action Buttons UI**
1. Add button fields to country schema
2. Implement window handlers (importGeoJSON, viewImportStats)
3. Add import status tracking
4. Build progress monitoring UI

### **Phase 4: Geofencing Notifications**
1. Implement Redis Pub/Sub for vehicle positions
2. Create geofence detection service
3. Integrate with Socket.IO for real-time events
4. Test with 10+ concurrent vehicles

### **Phase 5: Extended Data (Buildings + Admin)**
1. Import admin_level_*.geojson → region/place tables
2. Import building.geojson (658MB - streaming critical)
3. Import natural.geojson, name.geojson, add_street_polygon.geojson
4. Optimize Redis memory usage

### **Phase 6: Poisson Integration & Calibration**
1. Update activity_levels for all OSM amenity types
2. Re-calibrate spawn weights to maintain target rates
3. Test spawning distribution across all zones
4. Monitor performance with full dataset

---

## ⚠️ **CRITICAL DECISIONS REQUIRED**

### **Decision 1: POI Geometry Handling**
**Problem**: Amenities are MultiPolygons but poi table expects Point coordinates

**Options**:
- [ ] **A**: Extract centroid only (simple, loses shape data)
- [ ] **B**: Create poi_shape table (complete, maintains integrity)
- [ ] **C**: Store both in metadata (hybrid, JSON bloat)

**Recommendation**: **Option B**

---

### **Decision 2: Redis Architecture**
**Problem**: Multiple Redis data structure options

**Options**:
- [ ] **A**: Geospatial only (GEOADD/GEORADIUS)
- [ ] **B**: Cache only (SET/GET reverse geocodes)
- [ ] **C**: Hybrid (geospatial + hash + cache)

**Recommendation**: **Option C**

---

### **Decision 3: Import Scope**
**Problem**: 11 files with varying priority and size

**Options**:
- [ ] **A**: Import all 11 files immediately (complete, high effort)
- [ ] **B**: Import top 3 only (highway, amenity, landuse) - MVP
- [ ] **C**: Phased approach (3 core → 5 admin → 3 supporting)

**Recommendation**: **Option C**

---

### **Decision 4: Geofencing Implementation**
**Problem**: Multiple notification architectures

**Options**:
- [ ] **A**: Polling (simple, high latency)
- [ ] **B**: Redis Pub/Sub (real-time, requires Redis)
- [ ] **C**: PostgreSQL NOTIFY/LISTEN (no new infra, slower)

**Recommendation**: **Option B** (aligns with Redis reverse geocoding)

---

## 📊 **PERFORMANCE TARGETS**

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Reverse Geocoding | ~2000ms | <200ms | Redis GEORADIUS |
| Geofence Detection | N/A | <10ms | Redis Pub/Sub |
| Import Speed | N/A | >1000 features/sec | Batch insert (100 rows) |
| Memory Usage | 0MB | <50MB per country | Redis optimized structures |
| Spawn Rate | 100/hr | 90-180/hr | Re-calibrate weights |

---

## 🔧 **TECHNICAL REQUIREMENTS**

### **Infrastructure**
- [ ] Redis 7.x server (standalone or cluster)
- [ ] Redis client library (ioredis for Node.js)
- [ ] Streaming JSON parser (JSONStream or oboe.js)
- [ ] Turf.js for centroid calculations
- [ ] Socket.IO (already exists)

### **Database Schema Changes**
- [ ] Add `poi_shape` table (if Decision 1 = Option B)
- [ ] Add `building` table
- [ ] Add `natural_feature` table
- [ ] Update `country` schema with import buttons
- [ ] Add spatial indexes on all geometry columns

### **API Endpoints**
- [ ] `POST /api/geojson-import` - Start import job
- [ ] `GET /api/geojson-import/:jobId` - Check progress
- [ ] `POST /api/redis-cache/clear` - Clear reverse geocode cache
- [ ] `GET /api/import-stats/:countryId` - View import statistics

---

## 📝 **NEXT STEPS**

See `GEOJSON_IMPORT_TODO.md` for granular step-by-step implementation plan.

---

**Document Version**: 1.0  
**Last Updated**: October 25, 2025  
**Author**: GitHub Copilot + guerillacodester
