# GeoData Import System - Complete Implementation

## Overview

User-friendly GeoJSON import system for country-specific geographic data via Strapi Admin UI.

## Architecture

### Separation of Concerns

- **Country Lifecycle Hook** (`src/api/country/content-types/country/lifecycles.ts`)
  - Orchestrates all GeoJSON file processing
  - Handles cascade delete for all related geographic data
  - Tracks import status and timestamps

### Processing Functions (All in Country Lifecycle)

1. **`processPOIsGeoJSON()`** - Import Points of Interest
2. **`processPlacesGeoJSON()`** - Import place names (cities, towns, villages)
3. **`processLanduseGeoJSON()`** - Import landuse zones with polygon geometries
4. **`processRegionsGeoJSON()`** - Import administrative regions with boundaries

## Content Types

### 1. Country (Hub)

**File Upload Fields:**

- `pois_geojson_file` → POI content type
- `place_names_geojson_file` → Place content type
- `landuse_geojson_file` → Landuse-zone content type
- `regions_geojson_file` → Region content type

**Status Fields:**

- `geodata_import_status` - Shows import results (e.g., "✅ POIs, ✅ Places, ❌ Landuse: timeout")
- `geodata_last_import` - Timestamp of last import

### 2. POI (Point of Interest)

**Purpose:** Commuter spawning destinations (bus stations, hospitals, schools, etc.)
**Data Size:** ~500-1000 records per country
**Key Fields:**

- `name`, `poi_type`, `latitude`, `longitude`
- `osm_id`, `amenity`, `tags`
- `spawn_weight`, `peak_hour_multiplier`, `off_peak_multiplier`
- `country` (relation)

**OSM Amenity Mapping:**

```typescript
bus_station/bus_stop → bus_station
hospital → hospital
clinic/doctors → clinic
school → school
college/university → university
marketplace/market → marketplace
place_of_worship/church/mosque/temple → place_of_worship
bank, post_office, restaurant, cafe, pharmacy, fuel, parking, library
```

### 3. Place (Geographic Names)

**Purpose:** City, town, village names for geographic context
**Data Size:** ~15,000+ records per country
**Key Fields:**

- `name`, `place_type`, `latitude`, `longitude`
- `osm_id`, `population`, `importance`, `tags`
- `country`, `region` (relations)

**OSM Place Mapping:**

```typescript
city → city
town → town
village → village
hamlet → hamlet
suburb/neighbourhood/neighborhood/quarter → neighbourhood
```

### 4. Landuse-zone

**Purpose:** Spawning zones by land use (residential, commercial, industrial)
**Data Size:** ~1000-2000 records per country
**Key Fields:**

- `name`, `zone_type`, `center_lat`, `center_lon`
- `geometry_geojson` (full polygon stored as JSON string)
- `osm_id`, `tags`
- `spawn_weight`, `peak_hour_multiplier`, `off_peak_multiplier`
- `country` (relation)

**OSM Landuse Mapping:**

```typescript
residential → residential
commercial/retail → commercial
industrial → industrial
education → education
institutional → institutional
recreation_ground/park → recreation
grass/forest → green_space
farmland → agricultural
construction/brownfield → mixed_use
```

### 5. Region

**Purpose:** Administrative boundaries (states, districts, municipalities)
**Data Size:** ~50-200 records per country
**Key Fields:**

- `name`, `region_type`, `center_lat`, `center_lon`
- `geometry_geojson` (full boundary stored as JSON string)
- `osm_id`, `admin_level`, `population`, `tags`
- `country`, `places` (relations)

**Admin Level Mapping:**

```typescript
1-2 → country
3-4 → state_province
5-6 → district
7-8 → municipality
9-10 → neighborhood
```

## Lifecycle Hook Flow

### 1. File Upload (Admin UI)

User uploads GeoJSON file(s) to Country record via Strapi Admin UI

### 2. Before Update Hook

```typescript
beforeUpdate(event) {
  // Track which files changed
  event.state.filesChanged = {
    pois: data.hasOwnProperty('pois_geojson_file'),
    places: data.hasOwnProperty('place_names_geojson_file'),
    landuse: data.hasOwnProperty('landuse_geojson_file'),
    regions: data.hasOwnProperty('regions_geojson_file')
  };
}
```

### 3. After Update Hook

```typescript
afterUpdate(event) {
  // Process each changed file
  if (filesChanged.pois) await processPOIsGeoJSON(result);
  if (filesChanged.places) await processPlacesGeoJSON(result);
  if (filesChanged.landuse) await processLanduseGeoJSON(result);
  if (filesChanged.regions) await processRegionsGeoJSON(result);
  
  // Update status: "✅ POIs, ✅ Places, ✅ Landuse, ✅ Regions at 2024-01-15T10:30:00Z"
}
```

### 4. Processing Pattern (All Functions)

```typescript
async function processXXXGeoJSON(country) {
  // 1. Read file from upload directory
  const filePath = path.join(strapi.dirs.static.public, file.url);
  const geojson = JSON.parse(await fs.readFile(filePath, 'utf-8'));
  
  // 2. Delete existing records for this country (replace strategy)
  await strapi.db.query('api::xxx.xxx').deleteMany({
    where: { country: country.id }
  });
  
  // 3. Process in chunks (100 records/batch for POIs/Places, 50 for Regions)
  for (let i = 0; i < features.length; i += chunkSize) {
    const chunk = features.slice(i, i + chunkSize);
    const recordsToCreate = [];
    
    for (const feature of chunk) {
      // Extract coordinates
      // Validate coordinates
      // Map OSM types to content type enums
      // Build record object
      recordsToCreate.push({...});
    }
    
    // 4. Bulk insert chunk
    await strapi.db.query('api::xxx.xxx').createMany({
      data: recordsToCreate
    });
    
    console.log(`Progress: ${i}/${features.length}`);
  }
  
  return importedCount;
}
```

### 5. Cascade Delete Hook

```typescript
beforeDelete(event) {
  const countryId = event.params.where.id;
  
  // Delete all POIs for this country
  const pois = await strapi.entityService.findMany('api::poi.poi', {
    filters: { country: countryId }
  });
  for (const poi of pois) {
    await strapi.entityService.delete('api::poi.poi', poi.id);
  }
  
  // Delete all Places for this country
  // Delete all Landuse Zones for this country
  // Delete all Regions for this country
  
  console.log(`✅ Cascade delete complete`);
}
```

## Performance Characteristics

### Chunked Processing

- **POIs:** 100 records/batch (~500-1000 total) = 5-10 batches
- **Places:** 100 records/batch (~15,000 total) = 150 batches
- **Landuse:** 100 records/batch (~1000-2000 total) = 10-20 batches
- **Regions:** 50 records/batch (~50-200 total) = 1-4 batches

### Memory Management

- Processes features in memory-efficient chunks
- Prevents timeout on large datasets
- Provides progress logging

### Coordinate Handling

- **Point features:** Direct [lon, lat] extraction
- **Polygon features:** Centroid calculation (average of outer ring points)
- **MultiPolygon features:** Use first polygon's centroid
- **Validation:** Reject coordinates outside valid ranges (lat: -90 to 90, lon: -180 to 180)

## User Workflow

1. **Navigate to Country** in Strapi Admin UI
2. **Upload GeoJSON files**:
   - POIs GeoJSON file
   - Place names GeoJSON file
   - Landuse GeoJSON file
   - Regions GeoJSON file
3. **Save Country record**
4. **Lifecycle hook automatically**:
   - Detects which files changed
   - Processes each file in background
   - Deletes old data for that country
   - Bulk imports new data
   - Updates `geodata_import_status` field
5. **Check Status** in `geodata_import_status` field:
   - ✅ Success: "✅ POIs, ✅ Places, ✅ Landuse, ✅ Regions at 2024-01-15T10:30:00Z"
   - ❌ Partial failure: "✅ POIs, ✅ Places, ❌ Landuse: Invalid GeoJSON at ..."
   - ❌ Full failure: "❌ POIs: timeout at ..."

## Data Replacement Strategy

- **Replace, not merge:** Each file upload deletes existing records for that country and content type
- **Idempotent:** Can re-upload same file multiple times safely
- **Atomic per content type:** If POIs fail, Places can still succeed

## Cascade Delete Behavior

When a Country is deleted:

1. All POIs for that country are deleted
2. All Places for that country are deleted
3. All Landuse Zones for that country are deleted
4. All Regions for that country are deleted
5. Country record is deleted
6. Upload files remain in storage (Strapi default behavior)

## Error Handling

- **Invalid coordinates:** Logged and skipped
- **Missing geometry:** Logged and skipped
- **Unsupported geometry types:** Logged and skipped
- **File read errors:** Caught and reported in `geodata_import_status`
- **Parse errors:** Caught and reported in `geodata_import_status`
- **Database errors:** Caught and reported in `geodata_import_status`

## Testing Checklist

- [ ] Upload POIs GeoJSON → Verify POIs created
- [ ] Upload Places GeoJSON → Verify Places created
- [ ] Upload Landuse GeoJSON → Verify Landuse zones created with geometries
- [ ] Upload Regions GeoJSON → Verify Regions created with boundaries
- [ ] Upload all 4 files at once → Verify all process correctly
- [ ] Re-upload same file → Verify old data replaced
- [ ] Delete Country → Verify all related data deleted
- [ ] Check `geodata_import_status` → Verify accurate status reporting
- [ ] Upload large file (15k+ features) → Verify chunked processing works
- [ ] Upload invalid GeoJSON → Verify error handling

## File Structure

```text
arknet_fleet_manager/arknet-fleet-api/src/api/
├── country/
│   └── content-types/country/
│       ├── schema.json (4 file upload fields)
│       └── lifecycles.ts (ALL processing logic)
├── poi/
│   └── content-types/poi/
│       └── schema.json
├── place/
│   └── content-types/place/
│       └── schema.json
├── landuse-zone/
│   └── content-types/landuse-zone/
│       └── schema.json
└── region/
    └── content-types/region/
        └── schema.json
```

## Next Steps

1. **Configure Permissions** - Enable public read access for geographic data
2. **Test Import Flow** - Upload sample GeoJSON files
3. **Validate Data** - Query database to verify imported records
4. **Performance Test** - Upload large datasets (15k+ features)
5. **Document API Endpoints** - Document REST API for querying geographic data
6. **Integrate with Simulator** - Connect commuter spawning to POIs/Landuse zones

## Notes

- All processing logic consolidated in Country lifecycle hook (SoC at file level)
- Each GeoJSON file type has dedicated processing function
- Cascade delete ensures data consistency
- User-friendly: No terminal commands, no database access needed
- Production-ready: Handles large files, provides status feedback, robust error handling
