# Database Structure Audit - PostGIS & GTFS Compliance

**Date**: October 25, 2025  
**Status**: 🚨 CRITICAL - Multiple tables require PostGIS migration

---

## ❌ NON-COMPLIANT TABLES (Require Immediate Migration)

### 1. **GTFS CORE TABLES** - Missing PostGIS Geometry

#### `stops` - GTFS stops.txt

**Current Structure**: ❌ NOT COMPLIANT

- Uses `latitude` (numeric) and `longitude` (numeric)
- **MUST HAVE**: `geom geometry(Point, 4326)`
- **GTFS Standard**: stop_lat, stop_lon should be migrated to PostGIS Point

#### `shapes` - GTFS shapes.txt  

**Current Structure**: ❌ NOT COMPLIANT

- Individual point records: `shape_pt_lat`, `shape_pt_lon`, `shape_pt_sequence`
- **SHOULD HAVE**: Main shapes table with `geom geometry(LineString, 4326)`
- **Issue**: Violates same pattern as highways - should use PostGIS LineString

---

### 2. **SPATIAL ENTITY TABLES** - Missing PostGIS Geometry

#### `depots`

**Current Structure**: ❌ NOT COMPLIANT

- Uses `latitude` (double) and `longitude` (double)
- **MUST HAVE**: `geom geometry(Point, 4326)`

#### `landuse_zones`  

**Current Structure**: ❌ PARTIALLY MIGRATED

- Has `geom geometry(Polygon, 4326)` ✅
- Still has `landuse_shapes` + `landuse_shapes_landuse_zone_lnk` ⚠️
- **Action**: Keep PostGIS, deprecate shape tables

#### `pois`

**Current Structure**: ❌ PARTIALLY MIGRATED

- Has `geom geometry(Point, 4326)` ✅
- Still has `poi_shapes` + `poi_shapes_poi_lnk` ⚠️
- **Action**: Keep PostGIS, deprecate shape tables

#### `regions`

**Current Structure**: ❌ PARTIALLY MIGRATED

- Has `geom geometry(MultiPolygon, 4326)` ✅
- Still has `region_shapes` + `region_shapes_region_lnk` ⚠️
- **Action**: Keep PostGIS, deprecate shape tables

#### `highways`

**Current Structure**: ✅ MIGRATED (Oct 25, 2025)

- Has `geom geometry(LineString, 4326)` ✅
- Still has `highway_shapes` + `highway_shapes_highway_lnk` ⚠️
- **Status**: PostGIS active, old tables can be deprecated

---

### 3. **VEHICLE/GPS TABLES** - Need Point Geometry

#### `vehicles` (if has location)

- **Check**: Does it store current location?
- **If Yes**: Needs `geom geometry(Point, 4326)`

#### `vehicle_events`

- **Check**: Does it store event location?
- **If Yes**: Needs `geom geometry(Point, 4326)`

#### `active_passengers`

- **Check**: Does it store passenger location?
- **If Yes**: Needs `geom geometry(Point, 4326)`

---

## ✅ COMPLIANT TABLES

### PostGIS System Tables

- `spatial_ref_sys` ✅ (PostGIS system table)

---

## 🔧 REQUIRED MIGRATIONS

### Priority 1: GTFS Core Tables (CRITICAL)

```sql
-- stops.txt - Add PostGIS Point geometry
ALTER TABLE stops ADD COLUMN geom geometry(Point, 4326);
CREATE INDEX idx_stops_geom ON stops USING GIST (geom);

-- Migrate existing lat/lon to PostGIS
UPDATE stops 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Make geom NOT NULL after migration
ALTER TABLE stops ALTER COLUMN geom SET NOT NULL;
```

```sql
-- shapes.txt - Needs complete restructure
-- Option 1: Keep individual points (current GTFS standard)
-- Option 2: Add PostGIS LineString per shape_id (better performance)

-- RECOMMENDED: Add geometry column grouped by shape_id
CREATE TABLE shape_geometries (
  id serial PRIMARY KEY,
  shape_id varchar(255) UNIQUE,
  geom geometry(LineString, 4326) NOT NULL,
  created_at timestamp DEFAULT NOW()
);

CREATE INDEX idx_shape_geometries_geom ON shape_geometries USING GIST (geom);

-- Populate from existing shapes table
INSERT INTO shape_geometries (shape_id, geom)
SELECT 
  shape_id,
  ST_MakeLine(ST_MakePoint(shape_pt_lon, shape_pt_lat) ORDER BY shape_pt_sequence) as geom
FROM shapes
GROUP BY shape_id;
```

### Priority 2: Operational Tables (HIGH)

```sql
-- depots - Add PostGIS Point
ALTER TABLE depots ADD COLUMN geom geometry(Point, 4326);
CREATE INDEX idx_depots_geom ON depots USING GIST (geom);

UPDATE depots
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

ALTER TABLE depots ALTER COLUMN geom SET NOT NULL;
```

### Priority 3: Cleanup Old Shape Tables (MEDIUM)

After verifying PostGIS geometry is working:

```sql
-- WARNING: Only run after confirming all imports use PostGIS!
-- DROP TABLE highway_shapes_highway_lnk CASCADE;
-- DROP TABLE highway_shapes CASCADE;
-- DROP TABLE landuse_shapes_landuse_zone_lnk CASCADE;
-- DROP TABLE landuse_shapes CASCADE;
-- DROP TABLE poi_shapes_poi_lnk CASCADE;
-- DROP TABLE poi_shapes CASCADE;
-- DROP TABLE region_shapes_region_lnk CASCADE;
-- DROP TABLE region_shapes CASCADE;
```

---

## 📋 GTFS COMPLIANCE CHECKLIST

### GTFS Required Files (Must Have PostGIS Where Applicable)

- [ ] **agency.txt** - ✅ No geometry needed
- [ ] **stops.txt** - ❌ NEEDS PostGIS Point
- [ ] **routes.txt** - ✅ No geometry needed  
- [ ] **trips.txt** - ✅ No geometry needed
- [ ] **stop_times.txt** - ✅ No geometry needed
- [ ] **calendar.txt** - ✅ No geometry needed (replaced by services table)
- [ ] **shapes.txt** - ❌ NEEDS PostGIS LineString aggregation

### GTFS Optional Files

- [x] **calendar_dates.txt** - ✅ Exists, no geometry
- [x] **fare_attributes.txt** - ✅ Exists, no geometry
- [x] **fare_rules.txt** - ✅ Exists, no geometry
- [x] **frequencies.txt** - ✅ Exists, no geometry
- [x] **transfers.txt** - ✅ Exists, no geometry
- [x] **feed_info.txt** - ✅ Exists, no geometry

---

## 🎯 MIGRATION STRATEGY

### Phase 1: Critical GTFS Tables (DO NOW)

1. ✅ highways - COMPLETED
2. ⏳ stops - ADD PostGIS Point
3. ⏳ shapes - ADD aggregated LineString table
4. ⏳ depots - ADD PostGIS Point

### Phase 2: Import Code Updates (DO NEXT)

1. ✅ Highway import - Uses PostGIS
2. ⏳ Update all other GeoJSON imports to use PostGIS
3. ⏳ Update GTFS import to populate PostGIS columns

### Phase 3: Verify & Cleanup (DO LAST)

1. Verify all spatial queries use PostGIS
2. Verify all imports populate PostGIS columns
3. Drop old shape point tables
4. Update documentation

---

## 🚨 BLOCKING ISSUES

### Issue #1: GTFS shapes.txt Pattern

**Problem**: Current `shapes` table uses individual point records (GTFS standard) but no aggregated geometry  
**Impact**: Cannot perform spatial queries on route shapes  
**Solution**: Create `shape_geometries` table with PostGIS LineString  
**Priority**: HIGH

### Issue #2: stops.txt Missing PostGIS

**Problem**: Cannot do spatial queries like "find stops near point"  
**Impact**: Cannot implement proximity searches, spatial analysis  
**Solution**: Add `geom` column to stops table  
**Priority**: CRITICAL

### Issue #3: depots Missing PostGIS

**Problem**: Cannot do spatial queries for depot locations  
**Impact**: Cannot find nearest depot, calculate distances  
**Solution**: Add `geom` column to depots table  
**Priority**: HIGH

---

## 📊 COST IMPACT

### Without PostGIS (Current State for Non-Migrated Tables)

- Complex JOINs for spatial operations
- Slow distance calculations using Haversine formula
- No spatial indexing
- Limited GIS functionality

### With PostGIS (Target State)

- Native spatial operations
- GIST indexes for fast queries
- Industry-standard GIS capabilities
- 10-100x performance improvement

---

## ✅ ACTION ITEMS

1. **IMMEDIATE**: Run comprehensive PostGIS migration script
2. **TODAY**: Update all GeoJSON import code to use PostGIS
3. **TODAY**: Update GTFS import code to populate PostGIS columns
4. **THIS WEEK**: Test all spatial queries
5. **THIS WEEK**: Drop deprecated shape tables after verification
6. **THIS WEEK**: Update all documentation

---

**Next Step**: Create and execute comprehensive migration script for all non-compliant tables.
