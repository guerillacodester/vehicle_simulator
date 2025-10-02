# GeoJSON Data Loading Analysis - Production Grade Assessment

## Current Implementation: Route Loading via Lifecycle Hooks

### How It Works

**File**: `src/api/route/content-types/route/lifecycles.ts`

**Mechanism**:
1. Admin manually uploads/pastes GeoJSON data into `routes.geojson_data` field via Strapi Admin UI
2. Lifecycle hooks trigger automatically:
   - `afterCreate` - Processes GeoJSON when new route is created
   - `beforeUpdate` - Processes GeoJSON when route is updated
   - `beforeDelete` - Cleans up shapes when route is deleted
3. Hook parses GeoJSON and creates normalized GTFS data:
   - Creates `route_shapes` records (one per LineString feature)
   - Creates `shapes` records (one per coordinate point)
   - Assigns UUIDs and maintains relationships

**Example Flow**:
```
Admin UI → Paste GeoJSON → Save Route
          ↓
   afterCreate/beforeUpdate lifecycle hook
          ↓
   Parse GeoJSON features
          ↓
   Create route-shapes entries
          ↓
   Create individual shape points (lat/lon/sequence)
          ↓
   GTFS-compliant normalized data in database
```

---

## ✅ Production-Grade Strengths

### 1. **Data Normalization** ✅
- Converts denormalized GeoJSON into GTFS-compliant normalized schema
- Maintains referential integrity (route → route-shapes → shapes)
- Prevents data duplication
- **Score: 9/10**

### 2. **Automatic Cleanup** ✅
- `beforeUpdate` clears old shapes before creating new ones
- `beforeDelete` cleans up orphaned data
- Prevents data accumulation bugs
- **Score: 9/10**

### 3. **Transaction Safety** ✅
- Uses Strapi's entity service (wraps database transactions)
- Rollback on errors
- **Score: 8/10**

### 4. **GTFS Compliance** ✅
- Follows GTFS specification perfectly
- Compatible with transit apps and tools
- **Score: 10/10**

### 5. **Audit Trail** ✅
- All changes via Admin UI are logged
- Strapi tracks who/when changes occurred
- **Score: 8/10**

---

## ❌ Production-Grade Concerns

### 1. **Performance Issues** ❌
**Problem**: Creates database records one-by-one in loops
```typescript
for (let i = 0; i < coordinates.length; i++) {
  await strapi.entityService.create('api::shape.shape', {...});  // Individual INSERT
}
```

**Impact**:
- For Route 1: 88 coordinates = 88 sequential INSERT statements
- For 10 routes with 100 coords each = 1,000+ database round trips
- Strapi overhead per insert: ~10-50ms
- Total time: Minutes instead of seconds

**Production Alternative**:
```typescript
// Bulk insert using raw query
await strapi.db.query('api::shape.shape').createMany(shapePointsArray);
```

**Score: 3/10** - Works but scales poorly

---

### 2. **Request Timeout Risk** ⚠️
**Problem**: Long-running lifecycle hooks block HTTP request
- Strapi default timeout: 60 seconds
- Processing 500 coordinates could exceed this
- No progress indicator for user

**Production Alternative**:
- Queue-based processing (Bull/BullMQ)
- Background job workers
- Webhook/event after completion

**Score: 4/10** - Risk of timeout on large datasets

---

### 3. **No Validation** ❌
**Problem**: Minimal GeoJSON validation
```typescript
if (feature.geometry && feature.geometry.type === 'LineString') {
```

**Missing**:
- Schema validation (is it valid GeoJSON?)
- Coordinate range checking (valid lat/lon?)
- Geometry type validation
- Properties validation

**Production Alternative**:
```typescript
import * as turf from '@turf/turf';
import Ajv from 'ajv';

// Validate with JSON schema
const ajv = new Ajv();
const validate = ajv.compile(geoJSONSchema);
if (!validate(geojson)) {
  throw new Error('Invalid GeoJSON');
}

// Validate coordinates
for (const [lon, lat] of coordinates) {
  if (lon < -180 || lon > 180 || lat < -90 || lat > 90) {
    throw new Error(`Invalid coordinates: [${lon}, ${lat}]`);
  }
}
```

**Score: 4/10** - Basic checks only

---

### 4. **Manual Data Entry** ❌
**Problem**: Relies on admin manually pasting GeoJSON
- Error-prone (copy/paste mistakes)
- No versioning
- No source tracking
- Difficult to bulk load

**Production Alternative**:
- Automated import scripts
- File upload endpoint
- Git-based workflow
- Migration/seed files

**Score: 3/10** - Not scalable

---

### 5. **No Rollback on Partial Failure** ⚠️
**Problem**: If processing fails halfway through:
```typescript
// Creates 50 shapes successfully
// Error on shape 51
// First 50 shapes remain in database (orphaned)
```

**Production Alternative**:
```typescript
await strapi.db.transaction(async (trx) => {
  // All creates use same transaction
  // Auto-rollback on error
});
```

**Score: 5/10** - Relies on Strapi's implicit transactions

---

### 6. **No Progress Feedback** ❌
**Problem**: User has no idea what's happening
- Spinner just spins
- No percentage complete
- No error details shown

**Production Alternative**:
- WebSocket progress updates
- Status endpoint
- Background job with polling

**Score: 2/10** - Black box processing

---

## 🎯 Overall Production Grade: **C+ (6.5/10)**

| Aspect | Score | Notes |
|--------|-------|-------|
| Data Model | 9/10 | ✅ Excellent GTFS compliance |
| Performance | 3/10 | ❌ Sequential inserts don't scale |
| Reliability | 5/10 | ⚠️ Timeout risk, partial failure |
| UX | 3/10 | ❌ Manual, no feedback |
| Maintainability | 7/10 | ✅ Clean code, well-structured |
| Security | 8/10 | ✅ Admin-only, audit trail |
| Validation | 4/10 | ❌ Minimal checks |

---

## 🚀 Recommended Production Approach

### For POI/Landuse Data Loading

**Don't use lifecycle hooks for bulk data!**

Instead, create a proper data loading pipeline:

### Option 1: Database Seed/Migration Script (Recommended)

```python
# scripts/load_barbados_geodata.py

import json
import psycopg2
from psycopg2.extras import execute_values

def load_pois_from_geojson(geojson_path, country_id):
    """Load POIs from GeoJSON file directly to database"""
    
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    # Prepare bulk insert data
    pois = []
    for feature in data['features']:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        poi = (
            props.get('name'),
            props.get('amenity'),
            coords[1],  # latitude
            coords[0],  # longitude
            props.get('osm_id'),
            country_id,
            1.0,  # default spawn_weight
            True,  # is_active
        )
        pois.append(poi)
    
    # Bulk insert (1000x faster than individual inserts)
    conn = psycopg2.connect("dbname=arknettransit")
    cur = conn.cursor()
    
    execute_values(
        cur,
        """
        INSERT INTO pois 
        (name, amenity, latitude, longitude, osm_id, country_id, spawn_weight, is_active)
        VALUES %s
        """,
        pois
    )
    
    conn.commit()
    print(f"✅ Loaded {len(pois)} POIs")

# Load Barbados data
load_pois_from_geojson('data/barbados_amenities.geojson', country_id=28)
```

**Advantages**:
- ✅ 1000x faster (bulk inserts)
- ✅ Repeatable (can re-run)
- ✅ Versionable (in Git)
- ✅ Testable
- ✅ No timeout risk

---

### Option 2: Strapi API Endpoint with Background Job

```typescript
// src/api/poi/controllers/poi.ts

async bulkImport(ctx) {
  const { geojsonUrl, countryId } = ctx.request.body;
  
  // Queue background job
  const jobId = await strapi.service('api::poi.import-job').create({
    geojsonUrl,
    countryId,
    status: 'pending'
  });
  
  // Return immediately
  return { jobId, status: 'processing' };
}

// src/api/poi/services/import-job.ts
async processImport(jobId) {
  try {
    // Fetch GeoJSON
    const response = await fetch(job.geojsonUrl);
    const geojson = await response.json();
    
    // Bulk create
    const pois = geojson.features.map(feature => ({
      // ... map properties
    }));
    
    await strapi.db.query('api::poi.poi').createMany(pois);
    
    // Update job status
    await updateJob(jobId, { status: 'complete', count: pois.length });
    
  } catch (error) {
    await updateJob(jobId, { status: 'failed', error: error.message });
  }
}
```

**Advantages**:
- ✅ No request timeout
- ✅ Progress tracking
- ✅ Error handling
- ✅ Can retry

---

### Option 3: CLI Command

```typescript
// src/commands/import-geodata.ts

export default {
  name: 'import-geodata',
  async run({ strapi }) {
    console.log('Loading Barbados POIs...');
    
    const geojson = require('../../../data/barbados_amenities.geojson');
    
    const pois = geojson.features.map(feature => ({
      // ... transform
    }));
    
    await strapi.db.query('api::poi.poi').createMany(pois);
    
    console.log(`✅ Imported ${pois.length} POIs`);
  }
};
```

Run with: `npm run strapi import-geodata`

---

## 📊 Comparison: Lifecycle vs Production Approaches

| Aspect | Lifecycle Hook | Seed Script | Background Job | CLI Command |
|--------|----------------|-------------|----------------|-------------|
| **Performance** | 🔴 Slow | 🟢 Fast | 🟢 Fast | 🟢 Fast |
| **Scalability** | 🔴 Poor | 🟢 Excellent | 🟢 Excellent | 🟢 Good |
| **Timeout Risk** | 🔴 High | 🟢 None | 🟢 None | 🟡 Medium |
| **User Feedback** | 🔴 None | N/A | 🟢 Real-time | 🟢 CLI output |
| **Repeatability** | 🔴 Manual | 🟢 Automated | 🟢 Automated | 🟢 Automated |
| **Version Control** | 🔴 No | 🟢 Yes | 🟡 Partial | 🟢 Yes |
| **Testing** | 🔴 Hard | 🟢 Easy | 🟡 Medium | 🟢 Easy |
| **Complexity** | 🟢 Simple | 🟢 Simple | 🔴 Complex | 🟢 Simple |

---

## 🎯 Recommendation for This Project

### For Routes (Small Dataset - 1-5 routes)
**✅ Keep lifecycle hooks** - Works fine for small datasets

### For POIs/Landuse (Large Dataset - 1000s of records)
**✅ Use seed/migration script** - Best for bulk loading

### Implementation Priority:

1. **Immediate** (Now):
   - Create `scripts/load_barbados_geodata.py`
   - Load POIs and landuse zones via script
   - One-time bulk load

2. **Short-term** (Next sprint):
   - Add GeoJSON validation to route lifecycle
   - Improve error messages
   - Add coordinate validation

3. **Long-term** (Future):
   - Background job system for large imports
   - Admin UI file upload
   - Automatic re-import on data changes

---

## ✅ Conclusion

**Lifecycle hooks for routes**: ✅ **Acceptable for production**
- Small dataset (< 100 coordinates per route)
- Manual admin updates are rare
- Benefits outweigh performance cost

**Lifecycle hooks for POIs/Landuse**: ❌ **Not recommended**
- Too many records (1000s)
- Would take minutes per import
- High timeout risk
- Use bulk loading scripts instead

**Production Grade**: **6.5/10** - Good for current use case, needs improvement for scale
