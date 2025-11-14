# 🚨 START HERE - ROUTE GEOMETRY

**If you're working on anything related to routes, read this first.**

## The Problem

The database is **broken for route geometry**. Don't use it.

## The Solution

**GeoJSON files** in `arknet_transit_simulator/data/` are the **ONLY** source of truth.

```
Route 1 Example:
- File: arknet_transit_simulator/data/route_1.geojson
- Points: 418 coordinates
- Segments: 27 LineString features (ordered by "layer" property)
- Distance: 13.347 km
```

## What to Read

📖 **`ROUTE_GEOMETRY_BIBLE.md`** - Complete implementation guide

## Quick Reference

### ✅ CORRECT: Read from GeoJSON

```python
import json

def get_route_geometry(route_code):
    with open(f'arknet_transit_simulator/data/route_{route_code}.geojson') as f:
        data = json.load(f)
    
    # Sort by layer property to maintain order
    features = sorted(data['features'], key=lambda f: f['properties']['layer'])
    
    # Concatenate all coordinates
    coords = []
    for feature in features:
        coords.extend(feature['geometry']['coordinates'])
    
    return {'type': 'LineString', 'coordinates': coords}
```

### ❌ WRONG: Query database

```typescript
// DON'T DO THIS - Database is fragmented with no ordering
const shapes = await strapi.entityService.findMany('api::shape.shape', {
  filters: { shape_id: { $in: shapeIds } }
});
```

## Files Updated with Warnings

- ✅ `/ROUTE_GEOMETRY_BIBLE.md` - Master documentation
- ✅ `/CONTEXT.md` - Project context updated
- ✅ `/TODO.md` - Tasks updated with route geometry refs
- ✅ `/arknet_fleet_manager/arknet-fleet-api/src/api/route/controllers/route.ts` - Warning added
- ✅ This file - Quick start guide

---

**Last Updated**: November 9, 2025
**Issue**: Route geometry reconstruction from database
**Resolution**: Use GeoJSON files as single source of truth
**Status**: ✅ DOCUMENTED
