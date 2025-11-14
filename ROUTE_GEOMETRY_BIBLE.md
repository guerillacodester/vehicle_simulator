# 🚨 ROUTE GEOMETRY: THE SINGLE SOURCE OF TRUTH 🚨

**READ THIS BEFORE TOUCHING ANY ROUTE-RELATED CODE**

## ⚠️ CRITICAL FACTS

### 1. **THE DATABASE IS FRAGMENTED - DO NOT USE IT DIRECTLY**

The PostgreSQL database stores routes in **27+ separate shape fragments** with **NO ORDERING INFORMATION**.

- ❌ **WRONG**: Querying `route_shapes` + `shapes` tables and concatenating results
- ❌ **WRONG**: Using the "default" shape (it's only 1.3km, not the full route)
- ❌ **WRONG**: Concatenating all shapes (gives 91km of random jumps)

**WHY IT'S BROKEN**:
- Route 1 has 54 `route_shapes` entries (27 unique shapes, duplicated)
- Each shape is 0.1km - 1.4km (small segments)
- No `sequence` or `order` column exists
- The shapes were imported from GeoJSON but lost their ordering

### 2. **THE GEOJSON FILE IS THE MASTER SOURCE**

**Location**: `arknet_transit_simulator/data/route_1.geojson`

**Structure**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "layer": "1_1",  // ← THIS IS THE SEQUENCE ORDER!
        "start": "-59.6154822486, 13.3265769508",
        "end": "-59.6234272934, 13.3178896974",
        "cost": 1312.1017777192051
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [ [...], [...], ... ]
      }
    },
    // ... 26 more features with layers 1_2, 1_3, ..., 3_8
  ]
}
```

**FACTS**:
- ✅ **418 total coordinates** across 27 ordered segments
- ✅ **13.347 km** total distance (the "~12km" route)
- ✅ Segments ordered by `layer` property: `1_1`, `1_2`, ..., `3_8`
- ✅ First coordinate: `[-59.615521, 13.326607]`
- ✅ Last coordinate: `[-59.642139, 13.250097]`

## 📋 HOW TO GET ROUTE GEOMETRY (THE RIGHT WAY)

### Option A: **Read GeoJSON File Directly** (RECOMMENDED)

```python
import json
from pathlib import Path

def get_route_geometry(route_code: str):
    """
    Get complete route geometry from GeoJSON file.
    
    This is THE SINGLE SOURCE OF TRUTH for route geometry.
    """
    geojson_path = Path(f"arknet_transit_simulator/data/route_{route_code}.geojson")
    
    if not geojson_path.exists():
        raise FileNotFoundError(f"Route {route_code} GeoJSON not found")
    
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    # Extract all coordinates in layer order
    features = sorted(data['features'], key=lambda f: f['properties']['layer'])
    
    all_coords = []
    for feature in features:
        coords = feature['geometry']['coordinates']
        all_coords.extend(coords)
    
    return {
        'type': 'LineString',
        'coordinates': all_coords
    }
```

### Option B: **Store Complete Geometry in Strapi**

If you must use Strapi, store the **COMPLETE LineString** in a `route_geometry` JSONB column:

```sql
ALTER TABLE routes ADD COLUMN route_geometry JSONB;

-- Update with complete geometry from GeoJSON
UPDATE routes 
SET route_geometry = '{"type": "LineString", "coordinates": [[...all 418 points...]]}'
WHERE short_name = '1';
```

Then in Strapi controller:

```typescript
async findOne(ctx) {
  const { id } = ctx.params;
  
  const route = await strapi.entityService.findOne('api::route.route', id);
  
  if (!route) {
    return ctx.notFound('Route not found');
  }
  
  // Return the COMPLETE geometry from route_geometry column
  return {
    id: route.id,
    short_name: route.short_name,
    long_name: route.long_name,
    geometry: route.route_geometry  // ← THE COMPLETE 418-point LineString
  };
}
```

### Option C: **Serve GeoJSON via API** (BEST FOR PRODUCTION)

Create a dedicated endpoint that serves the GeoJSON files directly:

```python
# geospatial_service/api/routes.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

@router.get("/routes/{route_code}/geometry")
async def get_route_geometry_from_source(route_code: str):
    """
    Get route geometry from authoritative GeoJSON source.
    
    This is the SINGLE SOURCE OF TRUTH - do NOT reconstruct from database fragments.
    """
    geojson_path = Path(f"../arknet_transit_simulator/data/route_{route_code}.geojson")
    
    if not geojson_path.exists():
        raise HTTPException(404, f"Route {route_code} not found")
    
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    # Sort features by layer to maintain correct order
    features = sorted(data['features'], key=lambda f: f['properties']['layer'])
    
    # Concatenate all coordinates
    all_coords = []
    for feature in features:
        all_coords.extend(feature['geometry']['coordinates'])
    
    return {
        'route_id': route_code,
        'geometry': {
            'type': 'LineString',
            'coordinates': all_coords
        },
        'num_points': len(all_coords),
        'num_segments': len(features),
        'source': 'geojson_master_file'
    }
```

## 🔥 WHAT NOT TO DO

### ❌ DON'T: Query route_shapes + shapes tables

```typescript
// THIS GIVES YOU GARBAGE
const routeShapes = await strapi.entityService.findMany('api::route-shape.route-shape', {
  filters: { route_id: routeId }
});

const shapes = await strapi.entityService.findMany('api::shape.shape', {
  filters: { shape_id: { $in: shapeIds } }
});

// ❌ This returns 415 unordered points that jump around randomly (91km total)
```

### ❌ DON'T: Use the "default" shape

```typescript
// THIS ONLY GIVES YOU 1.3KM (ONE SEGMENT)
const routeShapes = await strapi.entityService.findMany('api::route-shape.route-shape', {
  filters: { 
    route_id: routeId,
    is_default: true  // ❌ This is only 26 points, not the full route
  }
});
```

### ❌ DON'T: Try to reconstruct ordering from database

The database has **NO SEQUENCE INFORMATION**. The `layer` property from GeoJSON was not imported.

## 📊 VERIFICATION

After implementing any route geometry solution, verify with:

```python
from geopy.distance import geodesic

# Calculate cumulative distance
total_distance = 0.0
for i in range(1, len(coordinates)):
    prev_coords = (coordinates[i-1][1], coordinates[i-1][0])  # (lat, lon)
    curr_coords = (coordinates[i][1], coordinates[i][0])
    total_distance += geodesic(prev_coords, curr_coords).kilometers

assert 12.0 <= total_distance <= 14.0, f"Route 1 should be ~13km, got {total_distance:.1f}km"
assert len(coordinates) >= 400, f"Route 1 should have ~418 points, got {len(coordinates)}"
```

**Expected results for Route 1**:
- ✅ Distance: **13.347 km** (±0.5km acceptable)
- ✅ Points: **418 coordinates**
- ✅ Segments: **27 LineString features**

## 🎯 DISPATCHER INTEGRATION

The dispatcher fetches routes from the Fleet Manager API:

```python
# arknet_transit_simulator/core/dispatcher.py

async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
    # Dispatcher expects: GET /api/v1/routes/public/{route_code}/geometry
    
    async with self.session.get(
        f"{self.api_base_url}/api/v1/routes/public/{route_code}/geometry"
    ) as response:
        data = await response.json()
        
        # MUST return complete geometry with ~418 points for route 1
        geometry = data.get('geometry')
        
        # Verify it's the complete route
        coords = geometry.get('coordinates', [])
        assert len(coords) >= 400, "Incomplete route geometry!"
```

## 🚀 ACTION ITEMS

1. ✅ **Confirm**: GeoJSON files are the master source (located in `arknet_transit_simulator/data/`)
2. ⚠️ **TODO**: Create API endpoint to serve GeoJSON geometry directly
3. ⚠️ **TODO**: Update Strapi controller to either:
   - Store complete geometry in `route_geometry` JSONB column, OR
   - Proxy requests to GeoJSON-serving API
4. ⚠️ **TODO**: Add sequence/order column to `route_shapes` table if database must be used
5. ✅ **DONE**: Document this nightmare so we never waste time on it again

## 📝 DECISION LOG

**Date**: 2025-11-09
**Context**: Spent hours debugging why route distance was wrong
**Root Cause**: Database fragmentation without ordering information
**Resolution**: Use GeoJSON files as single source of truth
**Never Again**: This document exists so we don't repeat this mistake

---

**If you're reading this because routes are broken again, follow Option A or Option C above. DO NOT try to "fix" the database queries. The database is fundamentally incomplete.**
