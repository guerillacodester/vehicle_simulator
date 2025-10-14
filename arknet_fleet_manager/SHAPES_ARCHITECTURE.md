# GeoJSON Shapes Architecture - DEFINITIVE

**Date:** October 12, 2025  
**Decision:** Dedicated shapes tables per entity type (NOT shared shapes)

## Architecture Overview

We use **TWO DIFFERENT PATTERNS** for storing geometric data:

### Pattern 1: GTFS Routes (Shared Shapes Table)

```text
routes → route_shapes (junction) → shapes (shared coordinate storage)
trips → trips_shape_lnk (junction) → shapes (shared coordinate storage)
```

**Tables:** 3 per entity

- Entity table (routes, trips)
- Junction table (route_shapes, trips_shape_lnk)
- Shared shapes table (shapes)

**Use Case:** Multiple routes can share the same physical shape

### Pattern 2: GeoJSON Entities (Dedicated Shapes Tables)

```text
pois → poi_shapes (dedicated coordinate storage)
landuse_zones → landuse_shapes (dedicated coordinate storage)
regions → region_shapes (dedicated coordinate storage)
highways → highway_shapes (dedicated coordinate storage)
```

**Tables:** 2 per entity

- Parent entity table (metadata + centroid lat/lon)
- Dedicated shapes table (full geometry coordinates)

**Use Case:** Each entity owns its full geometry, simplifies deletion

## Why NOT Shared Shapes for GeoJSON?

1. **Different from GTFS:** Routes naturally share paths (Route 1A and 1B follow same street). POIs/Landuse/Highways don't share geometries.

2. **Simpler Deletion:** When deleting a highway, just cascade delete highway_shapes. No reference counting needed.

3. **Clear Ownership:** Each entity owns its complete geometry data.

4. **Storage Tradeoff:** Uses more space but avoids complex reference management.

## Database Tables Created

### GeoJSON Entities (4 types after removing Place)

1. **POIs (Points of Interest)**
   - `pois` - Metadata: name, poi_type, latitude, longitude, osm_id, amenity, etc.
   - `poi_shapes` - Geometry: shape_pt_lat, shape_pt_lon, shape_pt_sequence, ring_index, polygon_index
   - `poi_shapes_poi_lnk` - Junction table (Strapi auto-generated)

2. **Landuse Zones**
   - `landuse_zones` - Metadata: name, landuse_type, latitude, longitude, etc.
   - `landuse_shapes` - Geometry: shape_pt_lat, shape_pt_lon, shape_pt_sequence, ring_index, polygon_index
   - `landuse_shapes_landuse_zone_lnk` - Junction table

3. **Regions**
   - `regions` - Metadata: name, region_type, latitude, longitude, etc.
   - `region_shapes` - Geometry: shape_pt_lat, shape_pt_lon, shape_pt_sequence, ring_index, polygon_index
   - `region_shapes_region_lnk` - Junction table

4. **Highways** (KEPT - Place was duplicate)
   - `highways` - Metadata: name, highway_type, surface, lanes, maxspeed, oneway, etc.
   - `highway_shapes` - Geometry: shape_pt_lat, shape_pt_lon, shape_pt_sequence
   - `highway_shapes_highway_lnk` - Junction table

### Place Content Type - DELETED ❌

**Reason:** The `places` table (8,283 records) contained highway/street data wrongly categorized as "localities":

- Examples: "Tom Adams Highway", "Highway 4", "3rd Avenue", "4th Avenue"
- This was duplicate of highways data
- Deleted to avoid confusion and duplication

The `highways` content type has proper schema for road data (highway_type, surface, lanes, maxspeed, oneway).

## Shape Table Schema Pattern

All dedicated shapes tables follow this pattern:

```typescript
{
  shape_pt_lat: float (required) - Latitude of coordinate point
  shape_pt_lon: float (required) - Longitude of coordinate point
  shape_pt_sequence: integer (required) - Order of points in geometry
  ring_index: integer (default: 0) - For polygons with holes (inner rings)
  polygon_index: integer (default: 0) - For MultiPolygon features
  parent_relation: relation (manyToOne) - Links back to parent entity
}
```

**Note:** Highways use LineStrings so they don't need ring_index or polygon_index.

## Reverse Geocoding Use Cases

With full geometries stored, we can now perform:

1. **Find containing POI:** `ST_Contains(poi_polygon, point)` - "Am I inside this building/park?"
2. **Find containing landuse:** `ST_Contains(landuse_polygon, point)` - "Am I in residential/commercial zone?"
3. **Find containing region:** `ST_Contains(region_polygon, point)` - "Which parish am I in?"
4. **Find nearest highway:** `ST_Distance(highway_linestring, point)` - "What street am I on?"

Previous centroid-only storage made these queries impossible.

## Migration Status

### ✅ Completed

- Created all 4 dedicated shapes table schemas
- Updated parent entity schemas with inverse relations
- Removed Place content type (duplicate of highways)
- Removed place_names_geojson_file from Country schema
- Updated GeoJSON upload controller (removed 'places' fileType)
- Database schema created by Strapi

### ❌ Pending

- Remove Place references from lifecycle processing
- Refactor processPOIsGeoJSON to store full geometries
- Refactor processLanduseGeoJSON to store full geometries
- Refactor processRegionsGeoJSON to store full geometries
- Refactor processHighwaysGeoJSON to store full geometries
- Delete existing POIs/Landuse/Regions/Highways (have centroids only)
- Re-import all GeoJSON data with full geometries
- Create PostGIS reverse geocoding queries in reverse_geocode.py

## Next Steps

1. Clean up lifecycle.ts - remove all Place processing code
2. Refactor all 4 process*GeoJSON functions to create shape records
3. Test highway import with barbados_highway.json
4. Re-import all GeoJSON data to populate shapes tables
5. Create PostGIS spatial queries for reverse geocoding
