# Geofence PostGIS Architecture (GTFS-Adherent)

## Problem with Current Design
The current `geofence` content type stores geometry directly (circle params, polygon JSON) which:
- ❌ Doesn't follow GTFS normalization patterns
- ❌ Doesn't leverage PostGIS capabilities
- ❌ Inconsistent with existing `route` → `route-shape` → `shape` architecture
- ❌ Can't share geometry definitions between geofences
- ❌ No proper spatial indexing

## Correct Architecture (Aligned with Routes)

### Pattern: Routes
```
route (metadata) 
  → route-shape (junction with variant_code) 
    → shape (point sequences with shape_id)
```

### Pattern: Geofences (NEW)
```
geofence (metadata)
  → geofence-geometry (junction with geometry_type)
    → geometry-point (point sequences with geometry_id) OR reuse shape table
```

## Schema Design

### 1. `geofence` (Content Type)
**Purpose**: Geofence metadata and configuration
**Collection**: `geofences`

```json
{
  "attributes": {
    "geofence_id": {
      "type": "uid",
      "required": true
    },
    "name": {
      "type": "string",
      "required": true
    },
    "type": {
      "type": "enumeration",
      "enum": ["depot", "boarding_zone", "service_area", "restricted", "proximity", "custom"],
      "required": true,
      "default": "custom"
    },
    "enabled": {
      "type": "boolean",
      "required": true,
      "default": true
    },
    "valid_from": {
      "type": "datetime",
      "required": false
    },
    "valid_to": {
      "type": "datetime",
      "required": false
    },
    "metadata": {
      "type": "json",
      "required": false
    },
    "geofence_geometries": {
      "type": "relation",
      "relation": "oneToMany",
      "target": "api::geofence-geometry.geofence-geometry",
      "mappedBy": "geofence"
    }
  }
}
```

### 2. `geofence-geometry` (Content Type - Junction Table)
**Purpose**: Link geofences to geometries with type/variant info
**Collection**: `geofence_geometries`

```json
{
  "attributes": {
    "geofence": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::geofence.geofence",
      "inversedBy": "geofence_geometries"
    },
    "geometry_id": {
      "type": "string",
      "required": true
    },
    "geometry_type": {
      "type": "enumeration",
      "enum": ["circle", "polygon", "linestring"],
      "required": true,
      "default": "polygon"
    },
    "is_primary": {
      "type": "boolean",
      "default": true,
      "required": false
    },
    "buffer_meters": {
      "type": "float",
      "required": false,
      "min": 0,
      "max": 10000
    }
  }
}
```

### 3. Option A: Reuse `shape` Table
**Pros**: 
- ✅ No duplication
- ✅ Share geometry between routes and geofences
- ✅ Already has PostGIS setup

**Cons**:
- ❌ Conceptually mixing routes and geofences
- ❌ `shape` naming is route-specific

### 3. Option B: Create `geometry-point` Table (RECOMMENDED)
**Purpose**: Store point sequences for any geometry type
**Collection**: `geometry_points`

```json
{
  "attributes": {
    "geometry_id": {
      "type": "string",
      "required": true,
      "unique": false
    },
    "point_lat": {
      "type": "float",
      "required": true,
      "min": -90,
      "max": 90
    },
    "point_lon": {
      "type": "float",
      "required": true,
      "min": -180,
      "max": 180
    },
    "point_sequence": {
      "type": "integer",
      "required": true,
      "min": 0
    },
    "point_elevation": {
      "type": "float",
      "required": false
    },
    "is_active": {
      "type": "boolean",
      "required": true,
      "default": true
    }
  }
}
```

## PostGIS Integration

### SQL Views (Created in PostgreSQL)

```sql
-- Materialize geofence polygons as PostGIS geometries
CREATE MATERIALIZED VIEW geofence_polygons AS
SELECT 
  g.id,
  g.geofence_id,
  g.name,
  g.type,
  gg.geometry_id,
  gg.geometry_type,
  ST_MakePolygon(
    ST_MakeLine(
      ARRAY(
        SELECT ST_MakePoint(gp.point_lon, gp.point_lat)
        FROM geometry_points gp
        WHERE gp.geometry_id = gg.geometry_id
        ORDER BY gp.point_sequence
      )
    )
  )::geography AS geom,
  ST_Area(
    ST_MakePolygon(
      ST_MakeLine(
        ARRAY(
          SELECT ST_MakePoint(gp.point_lon, gp.point_lat)
          FROM geometry_points gp
          WHERE gp.geometry_id = gg.geometry_id
          ORDER BY gp.point_sequence
        )
      )
    )::geography
  ) AS area_sqm
FROM geofences g
JOIN geofence_geometries gg ON g.id = gg.geofence_id
WHERE gg.geometry_type = 'polygon'
  AND g.enabled = true;

CREATE INDEX idx_geofence_polygons_geom ON geofence_polygons USING GIST(geom);

-- Materialize geofence circles as PostGIS geometries
CREATE MATERIALIZED VIEW geofence_circles AS
SELECT 
  g.id,
  g.geofence_id,
  g.name,
  g.type,
  gg.geometry_id,
  gg.geometry_type,
  gp.point_lat AS center_lat,
  gp.point_lon AS center_lon,
  gg.buffer_meters AS radius_meters,
  ST_Buffer(
    ST_MakePoint(gp.point_lon, gp.point_lat)::geography,
    gg.buffer_meters
  ) AS geom
FROM geofences g
JOIN geofence_geometries gg ON g.id = gg.geofence_id
JOIN geometry_points gp ON gp.geometry_id = gg.geometry_id
WHERE gg.geometry_type = 'circle'
  AND gp.point_sequence = 0
  AND g.enabled = true;

CREATE INDEX idx_geofence_circles_geom ON geofence_circles USING GIST(geom);
```

### Point-in-Polygon Query
```sql
-- Check if a point is inside any geofence
SELECT g.geofence_id, g.name, g.type
FROM geofence_polygons g
WHERE ST_Contains(g.geom, ST_MakePoint($lon, $lat)::geography)
  AND g.enabled = true;

-- Check if point is inside any circle
SELECT g.geofence_id, g.name, g.type,
       ST_Distance(g.geom, ST_MakePoint($lon, $lat)::geography) as distance_m
FROM geofence_circles g
WHERE ST_DWithin(g.geom, ST_MakePoint($lon, $lat)::geography, 0)
  AND g.enabled = true;
```

## Data Examples

### Example 1: Depot Geofence (Circle)
```
geofence:
  geofence_id: "depot-kingston-01"
  name: "Kingston Central Depot"
  type: "depot"
  enabled: true

geofence-geometry:
  geofence: [relation to above]
  geometry_id: "geom-depot-kingston-01-circle"
  geometry_type: "circle"
  is_primary: true
  buffer_meters: 100.0

geometry-point:
  geometry_id: "geom-depot-kingston-01-circle"
  point_lat: 18.0179
  point_lon: -76.8099
  point_sequence: 0  # Center point for circle
```

### Example 2: Boarding Zone (Polygon)
```
geofence:
  geofence_id: "boarding-half-way-tree-01"
  name: "Half Way Tree Boarding Zone"
  type: "boarding_zone"
  enabled: true

geofence-geometry:
  geofence: [relation to above]
  geometry_id: "geom-boarding-hwt-01-poly"
  geometry_type: "polygon"
  is_primary: true
  buffer_meters: null

geometry-point (4 points forming rectangle):
  1. geometry_id: "geom-boarding-hwt-01-poly", point_sequence: 0, lat: 18.0127, lon: -76.7950
  2. geometry_id: "geom-boarding-hwt-01-poly", point_sequence: 1, lat: 18.0135, lon: -76.7950
  3. geometry_id: "geom-boarding-hwt-01-poly", point_sequence: 2, lat: 18.0135, lon: -76.7940
  4. geometry_id: "geom-boarding-hwt-01-poly", point_sequence: 3, lat: 18.0127, lon: -76.7940
  5. geometry_id: "geom-boarding-hwt-01-poly", point_sequence: 4, lat: 18.0127, lon: -76.7950  # Close polygon
```

## Migration from Old Schema

If you already have geofences with embedded geometry:

```python
# Python migration script
import requests

old_geofences = strapi_client.get_geofences()

for old_gf in old_geofences:
    # Create new geofence metadata
    new_gf = strapi_client.create_geofence({
        "geofence_id": old_gf['id'],
        "name": old_gf['name'],
        "type": old_gf['type'],
        "enabled": old_gf['enabled']
    })
    
    # Create geometry points
    if old_gf['geometry_type'] == 'circle':
        # Create center point
        strapi_client.create_geometry_point({
            "geometry_id": f"geom-{old_gf['id']}-circle",
            "point_lat": old_gf['center_lat'],
            "point_lon": old_gf['center_lon'],
            "point_sequence": 0
        })
        
        # Create junction
        strapi_client.create_geofence_geometry({
            "geofence": new_gf['id'],
            "geometry_id": f"geom-{old_gf['id']}-circle",
            "geometry_type": "circle",
            "buffer_meters": old_gf['radius_meters']
        })
    
    elif old_gf['geometry_type'] == 'polygon':
        geometry_id = f"geom-{old_gf['id']}-poly"
        
        # Create polygon points
        for idx, coord in enumerate(old_gf['polygon']):
            strapi_client.create_geometry_point({
                "geometry_id": geometry_id,
                "point_lat": coord['lat'],
                "point_lon": coord['lon'],
                "point_sequence": idx
            })
        
        # Create junction
        strapi_client.create_geofence_geometry({
            "geofence": new_gf['id'],
            "geometry_id": geometry_id,
            "geometry_type": "polygon"
        })
```

## Benefits

✅ **GTFS-Adherent**: Follows same pattern as routes → route-shapes → shapes
✅ **PostGIS-Ready**: Point sequences can be materialized into PostGIS geometries
✅ **Normalized**: No geometry duplication, reusable geometry definitions
✅ **Flexible**: Support circles, polygons, linestrings via geometry_type
✅ **Spatial Indexing**: PostGIS GIST indexes for fast point-in-polygon queries
✅ **Versioning**: Can have multiple geometries per geofence (primary/secondary)
✅ **Buffer Support**: Can add buffer zones via buffer_meters field

## Next Steps

1. ✅ Delete current `geofence` content type
2. ✅ Create `geofence` (metadata only)
3. ✅ Create `geofence-geometry` (junction table)
4. ✅ Create `geometry-point` (point sequences)
5. ✅ Create PostGIS materialized views
6. ✅ Test CRUD operations
7. ✅ Implement Python LocationService with PostGIS queries
