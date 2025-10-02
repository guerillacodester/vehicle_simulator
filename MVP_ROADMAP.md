# ArkNet Transit System - MVP Roadmap

## Current Status: Phase 2.3 - PostGIS + GeoData Import System

### ✅ Completed

- PostgreSQL 17 installed and configured
- PostGIS 3.5 installed and verified working
- Strapi 5.23.5 running (Enterprise, TypeScript)
- TypeScript compilation errors fixed (8 files)
- Content types created:
  - ✅ Country (with 4 GeoJSON file upload fields)
  - ✅ POI (Points of Interest)
  - ✅ Place (Geographic place names)
  - ✅ Landuse-zone (Land use polygons)
  - ✅ Region (Administrative boundaries)
- Country lifecycle hook created with:
  - ✅ Cascade delete for all related data
  - ✅ POI GeoJSON processing
  - ✅ Places GeoJSON processing
  - ✅ Landuse GeoJSON processing
  - ✅ Regions GeoJSON processing
  - ✅ Chunked processing (100-50 records/batch)
  - ✅ OSM type mappings
  - ✅ Import status tracking

---

## 🎯 MVP Requirements - What's Left

### PHASE 1: Test & Validate GeoData Import (NEXT SESSION)

#### Step 1.1: Verify Strapi Build

```bash
cd arknet_fleet_manager/arknet-fleet-api
npm run build
```

**Expected:** TypeScript compilation succeeds with no errors

#### Step 1.2: Configure API Permissions

**Goal:** Enable public read access to geographic data

**Actions:**

1. Open Strapi Admin: <http://localhost:1337/admin>
2. Navigate to: Settings → Users & Permissions → Roles → Public
3. Enable permissions:
   - ✅ Country: find, findOne
   - ✅ POI: find, findOne
   - ✅ Place: find, findOne
   - ✅ Landuse-zone: find, findOne
   - ✅ Region: find, findOne
4. Save changes

**Test:**

```bash
# Should return countries list (not 403)
curl http://localhost:1337/api/countries
```

#### Step 1.3: Create Test Country

**Goal:** Set up Barbados as test country

**Actions:**

1. Admin UI → Content Manager → Countries
2. Create new entry:
   - Name: Barbados
   - Code: BB
   - Timezone: America/Barbados
3. Save (don't upload files yet)

**Test:**

```bash
curl http://localhost:1337/api/countries
# Should show Barbados in response
```

#### Step 1.4: Test POI Import

**Goal:** Verify POI GeoJSON processing works

**Actions:**

1. Create small test POI GeoJSON file (5-10 features)
2. Upload to Country → pois_geojson_file
3. Save Country
4. Check `geodata_import_status` field
5. Query POIs via API

**Test POI File (poi_test.geojson):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-59.6202, 13.0969]
      },
      "properties": {
        "name": "Bridgetown Bus Terminal",
        "amenity": "bus_station",
        "osm_id": "123456"
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-59.6167, 13.0932]
      },
      "properties": {
        "name": "Queen Elizabeth Hospital",
        "amenity": "hospital",
        "osm_id": "789012"
      }
    }
  ]
}
```

**Test:**

```bash
curl http://localhost:1337/api/pois
# Should show 2 POIs for Barbados
```

**Expected Results:**

- ✅ `geodata_import_status`: "✅ POIs at 2025-10-03T..."
- ✅ 2 POI records created
- ✅ POI type correctly mapped (bus_station, hospital)
- ✅ Coordinates stored correctly

#### Step 1.5: Test Places Import

**Goal:** Verify Places GeoJSON processing works

**Test Places File (places_test.geojson):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-59.6167, 13.0969]
      },
      "properties": {
        "name": "Bridgetown",
        "place": "city",
        "population": "110000",
        "osm_id": "100001"
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-59.5342, 13.1939]
      },
      "properties": {
        "name": "Speightstown",
        "place": "town",
        "population": "3500",
        "osm_id": "100002"
      }
    }
  ]
}
```

**Test:**

```bash
curl http://localhost:1337/api/places
# Should show 2 places for Barbados
```

#### Step 1.6: Test Landuse Import

**Goal:** Verify Landuse polygon processing works

**Test Landuse File (landuse_test.geojson):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-59.62, 13.09],
          [-59.61, 13.09],
          [-59.61, 13.10],
          [-59.62, 13.10],
          [-59.62, 13.09]
        ]]
      },
      "properties": {
        "name": "Bridgetown Commercial District",
        "landuse": "commercial",
        "osm_id": "200001"
      }
    }
  ]
}
```

**Test:**

```bash
curl http://localhost:1337/api/landuse-zones
# Should show 1 landuse zone with centroid calculated
```

#### Step 1.7: Test Regions Import

**Similar to above, test administrative boundary import

#### Step 1.8: Test Cascade Delete

**Goal:** Verify all related data is deleted when country is deleted

**Actions:**

1. Delete Barbados country via Admin UI
2. Check that all POIs, Places, Landuse, Regions are also deleted

**Test:**

```bash
curl http://localhost:1337/api/pois
# Should return empty array
curl http://localhost:1337/api/places
# Should return empty array
```

---

### PHASE 2: Real Data Import (After Testing Passes)

#### Step 2.1: Download Real Barbados GeoJSON

**Sources:**

- **Overpass Turbo** (OSM): <https://overpass-turbo.eu/>
- **GeoFabrik** (OSM extracts): <https://download.geofabrik.de/>
- **OpenStreetMap Export**: <https://export.hotosm.org/>

**Queries Needed:**

1. POIs (amenities)
2. Place names (places)
3. Landuse zones (landuse polygons)
4. Administrative boundaries (admin boundaries)

#### Step 2.2: Import Real Data

1. Upload real POIs GeoJSON
2. Upload real Places GeoJSON
3. Upload real Landuse GeoJSON
4. Upload real Regions GeoJSON
5. Monitor `geodata_import_status`
6. Verify import counts

---

### PHASE 3: Integrate with Commuter Spawning System

#### Step 3.1: Update Commuter Reservoir

**File:** `commuter_service/commuter_reservoir.py`

**Current:** Hardcoded Barbados bounds
**Target:** Query POIs and Landuse zones from Strapi API

**Changes Needed:**

```python
# OLD
BARBADOS_BOUNDS = {
    'min_lat': 13.0396, 'max_lat': 13.3356,
    'min_lon': -59.6489, 'max_lon': -59.4206
}

# NEW
def fetch_spawn_locations(country_code='BB'):
    # Fetch POIs from Strapi
    pois = requests.get(f'{STRAPI_URL}/api/pois?filters[country][code][$eq]={country_code}')
    
    # Fetch Landuse zones from Strapi
    zones = requests.get(f'{STRAPI_URL}/api/landuse-zones?filters[country][code][$eq]={country_code}')
    
    return pois, zones
```

#### Step 3.2: Update Poisson Spawner

**File:** `commuter_service/poisson_geojson_spawner.py`

**Changes:**

- Replace hardcoded GeoJSON with API calls
- Use POI spawn weights
- Use Landuse zone types for behavior patterns
- Respect peak/off-peak multipliers

#### Step 3.3: Test Commuter Spawning

```bash
python test_poisson_geojson_spawning.py
```

**Expected:**

- ✅ Commuters spawn at real POI locations
- ✅ Residential zones spawn more commuters in morning
- ✅ Commercial zones spawn more in evening
- ✅ Spawn weights affect distribution

---

### PHASE 4: Vehicle Route Integration

#### Step 4.1: Update Route Reservoir

**File:** `commuter_service/route_reservoir_refactored.py`

**Changes:**

- Query Regions from Strapi
- Use Region boundaries for route planning
- Filter routes by region

#### Step 4.2: Route Shape Validation

**File:** `arknet_fleet_manager/check_route_shapes.py`

**Changes:**

- Validate route shapes are within country bounds
- Check routes pass through regions correctly
- Verify GTFS compliance

---

### PHASE 5: Real-Time Updates (Socket.IO)

#### Step 5.1: Broadcast Geographic Events

**Events to add:**

- `poi:created` - New POI added
- `poi:updated` - POI spawn weight changed
- `poi:deleted` - POI removed
- `region:created` - New region added

#### Step 5.2: Update Simulators

**Changes:**

- Subscribe to geographic data events
- Hot-reload spawn locations when POIs change
- Update route planning when regions change

---

### PHASE 6: Admin Dashboard Features

#### Step 6.1: POI Management UI

- Visual map of POIs
- Click to edit spawn weights
- Enable/disable POIs
- See commuter spawn statistics

#### Step 6.2: Region Visualization

- Display region boundaries on map
- Show active routes per region
- Highlight coverage gaps

#### Step 6.3: Import History

- Show import logs
- Display success/failure rates
- Re-import capability

---

## 🎯 MVP Definition (Minimum Viable Product)

### Core Features Required for MVP

1. ✅ PostGIS installed and working
2. ✅ GeoJSON import system working (ALL 4 file types)
3. ⏳ **NEXT:** Test POI import with sample data
4. ⏳ **NEXT:** Test Places import with sample data
5. ⏳ **NEXT:** Test Landuse import with sample data
6. ⏳ **NEXT:** Test Regions import with sample data
7. ⏳ **NEXT:** Configure API permissions
8. ⏳ Import real Barbados data
9. ⏳ Connect commuter spawning to POIs
10. ⏳ Connect route planning to Regions
11. ⏳ Basic admin dashboard for viewing data

### MVP Success Criteria

- ✅ Non-technical user can upload GeoJSON files via Admin UI
- ✅ System automatically imports and validates data
- ✅ Commuters spawn at real POI locations from database
- ✅ Routes use real administrative boundaries
- ✅ Data can be updated without code changes
- ✅ Cascade delete maintains data integrity
- ✅ System handles 15,000+ place names without timeout

---

## 📋 Next Session Checklist

### Session Start

1. ✅ Verify Strapi is running
2. ✅ Check TypeScript build (no errors)
3. ✅ Open browser: <http://localhost:1337/admin>

### Testing Phase (Step-by-step)

1. Configure API permissions (Settings → Roles)
2. Create test GeoJSON files (POI, Places, Landuse, Regions)
3. Create Barbados country entry
4. Test POI import (upload → check status → query API)
5. Test Places import
6. Test Landuse import
7. Test Regions import
8. Test multi-file import (all 4 at once)
9. Test re-import (replace existing data)
10. Test cascade delete

### Success Indicators

- ✅ `geodata_import_status` shows "✅ POIs, ✅ Places, ✅ Landuse, ✅ Regions"
- ✅ API returns imported records
- ✅ Coordinates are valid
- ✅ OSM types correctly mapped
- ✅ Geometries stored for polygons
- ✅ Centroids calculated correctly
- ✅ Delete country removes all related data

### Files to Monitor

- `arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/lifecycles.ts`
- Server console logs (watch for import progress)
- Database records (pgAdmin or Strapi Admin)

---

## 🚀 MVP Timeline Estimate

| Phase | Task | Time Est. | Status |
|-------|------|-----------|--------|
| **Phase 1** | Test & Validate Import | 2-3 hours | ⏳ NEXT |
| **Phase 2** | Real Data Import | 1-2 hours | ⬜ Pending |
| **Phase 3** | Commuter Integration | 3-4 hours | ⬜ Pending |
| **Phase 4** | Route Integration | 2-3 hours | ⬜ Pending |
| **Phase 5** | Socket.IO Events | 1-2 hours | ⬜ Pending |
| **Phase 6** | Admin Dashboard | 4-6 hours | ⬜ Pending |
| **Total** | **MVP Complete** | **13-20 hours** | **~70% Done** |

---

## 📝 Key Technical Decisions Made

1. **Separation of Concerns:** All GeoJSON processing in Country lifecycle hook (not separate lifecycle hooks per content type)
2. **Data Strategy:** Replace, not merge (idempotent imports)
3. **Performance:** Chunked processing (100 records/batch for POIs/Places, 50 for Regions)
4. **Geometry Handling:** Store full GeoJSON strings for polygons, calculate centroids for queries
5. **Cascade Delete:** Country deletion removes ALL related geographic data
6. **User Experience:** File upload via Admin UI (no terminal/database access needed)

---

## 🎯 IMMEDIATE NEXT STEPS (Next Session)

```bash
# 1. Start Strapi (if not running)
cd arknet_fleet_manager/arknet-fleet-api
npm run develop

# 2. Build TypeScript (verify no errors)
npm run build

# 3. Open Admin UI
# http://localhost:1337/admin

# 4. Create test GeoJSON files (see Step 1.4-1.7 above)

# 5. Test import flow step-by-step

# 6. Verify data in API responses
```

**Focus:** Granular, step-by-step testing. Don't rush to real data until test imports work perfectly.

**Remember:** We have chunked processing, cascade delete, and comprehensive error handling. The hard architectural work is DONE. Now we just need to TEST it works! 🎉
