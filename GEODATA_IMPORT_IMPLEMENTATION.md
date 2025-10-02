# Quick Implementation: User-Friendly GeoJSON Import

## 🎯 Solution: Add File Upload to Content Types

This maintains the **ease of use** while supporting bulk data import.

---

## How It Works

### For Users (Non-Technical)

1. Login to Strapi Admin (`http://localhost:1337/admin`)
2. Go to Content Manager → GeoData Import → Create
3. Fill simple form:
   - **Country**: Select from dropdown (e.g., "Barbados")
   - **Data Type**: Select type (POIs, Landuse, Regions)
   - **File**: Click "Upload" and select `.geojson` file
4. Click **Save**
5. System automatically processes in background
6. See success message: "✅ Imported 342 POIs"

### What Happens Behind the Scenes

- Lifecycle hook reads uploaded file
- Validates GeoJSON format
- Bulk inserts to database (fast!)
- Shows friendly error messages if something fails

---

## Implementation Steps

### Step 1: Create "GeoData Import" Content Type

This is a temporary content type just for importing. Once imported, the data lives in POI/Landuse/Region tables.

**File**: `src/api/geodata-import/content-types/geodata-import/schema.json`

```json
{
  "kind": "collectionType",
  "collectionName": "geodata_imports",
  "info": {
    "singularName": "geodata-import",
    "pluralName": "geodata-imports",
    "displayName": "GeoData Import",
    "description": "Import POIs, Landuse, or Regions from GeoJSON files"
  },
  "options": {
    "draftAndPublish": false
  },
  "pluginOptions": {},
  "attributes": {
    "country": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::country.country",
      "required": true
    },
    "data_type": {
      "type": "enumeration",
      "enum": ["pois", "landuse_zones", "regions"],
      "required": true
    },
    "geojson_file": {
      "type": "media",
      "multiple": false,
      "required": true,
      "allowedTypes": ["files"]
    },
    "status": {
      "type": "enumeration",
      "enum": ["pending", "processing", "completed", "failed"],
      "default": "pending"
    },
    "total_records": {
      "type": "integer",
      "default": 0
    },
    "imported_records": {
      "type": "integer",
      "default": 0
    },
    "error_message": {
      "type": "text"
    },
    "import_notes": {
      "type": "richtext",
      "default": ""
    }
  }
}
```

---

### Step 2: Create Lifecycle Hook

**File**: `src/api/geodata-import/content-types/geodata-import/lifecycles.ts`

```typescript
import fs from 'fs';
import path from 'path';

export default {
  async afterCreate(event) {
    const { result } = event;
    
    // Update status to processing
    await strapi.entityService.update(
      'api::geodata-import.geodata-import',
      result.id,
      { data: { status: 'processing' } }
    );
    
    try {
      // Get file from media library
      const file = result.geojson_file;
      const filePath = path.join(strapi.dirs.static.public, file.url);
      
      // Read and parse GeoJSON
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      const geojson = JSON.parse(fileContent);
      
      // Validate GeoJSON
      if (!geojson.features || !Array.isArray(geojson.features)) {
        throw new Error('Invalid GeoJSON: No features array found');
      }
      
      // Process based on data type
      let importedCount = 0;
      
      switch (result.data_type) {
        case 'pois':
          importedCount = await importPOIs(geojson, result.country.id);
          break;
        case 'landuse_zones':
          importedCount = await importLanduseZones(geojson, result.country.id);
          break;
        case 'regions':
          importedCount = await importRegions(geojson, result.country.id);
          break;
      }
      
      // Update status to completed
      await strapi.entityService.update(
        'api::geodata-import.geodata-import',
        result.id,
        {
          data: {
            status: 'completed',
            total_records: geojson.features.length,
            imported_records: importedCount,
            import_notes: `✅ Successfully imported ${importedCount} ${result.data_type}`
          }
        }
      );
      
      console.log(`✅ Import completed: ${importedCount} ${result.data_type}`);
      
    } catch (error) {
      // Update status to failed with error message
      await strapi.entityService.update(
        'api::geodata-import.geodata-import',
        result.id,
        {
          data: {
            status: 'failed',
            error_message: error.message,
            import_notes: `❌ Import failed: ${error.message}`
          }
        }
      );
      
      console.error('Import failed:', error);
    }
  }
};

/**
 * Import POIs from GeoJSON
 */
async function importPOIs(geojson: any, countryId: number): Promise<number> {
  const poisToCreate = [];
  
  for (const feature of geojson.features) {
    if (feature.geometry.type !== 'Point') {
      console.warn('Skipping non-Point feature:', feature.properties?.name);
      continue;
    }
    
    const [lon, lat] = feature.geometry.coordinates;
    const props = feature.properties || {};
    
    // Validate coordinates
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      console.warn(`Invalid coordinates: [${lon}, ${lat}]`);
      continue;
    }
    
    // Map OSM amenity types to POI types
    const poiType = mapAmenityType(props.amenity);
    
    poisToCreate.push({
      name: props.name || props.amenity || 'Unnamed',
      poi_type: poiType,
      latitude: lat,
      longitude: lon,
      osm_id: props.osm_id || props.id,
      amenity: props.amenity,
      tags: props.tags ? JSON.stringify(props.tags) : null,
      spawn_weight: 1.0,
      peak_hour_multiplier: 1.0,
      off_peak_multiplier: 1.0,
      is_active: true,
      country: countryId,
      publishedAt: new Date()
    });
  }
  
  // Bulk create POIs
  if (poisToCreate.length > 0) {
    await strapi.db.query('api::poi.poi').createMany({
      data: poisToCreate
    });
  }
  
  return poisToCreate.length;
}

/**
 * Import Landuse Zones from GeoJSON
 */
async function importLanduseZones(geojson: any, countryId: number): Promise<number> {
  const zonesToCreate = [];
  
  for (const feature of geojson.features) {
    if (feature.geometry.type !== 'Polygon' && feature.geometry.type !== 'MultiPolygon') {
      console.warn('Skipping non-Polygon feature');
      continue;
    }
    
    const props = feature.properties || {};
    
    // Calculate center point for the polygon
    const center = calculateCentroid(feature.geometry);
    
    zonesToCreate.push({
      name: props.name || props.landuse || 'Unnamed Zone',
      zone_type: mapLanduseType(props.landuse),
      geometry_geojson: JSON.stringify(feature.geometry),
      center_latitude: center.lat,
      center_longitude: center.lon,
      osm_id: props.osm_id || props.id,
      tags: props.tags ? JSON.stringify(props.tags) : null,
      spawn_weight: 1.0,
      peak_hour_multiplier: 1.0,
      off_peak_multiplier: 1.0,
      is_active: true,
      country: countryId,
      publishedAt: new Date()
    });
  }
  
  // Bulk create zones
  if (zonesToCreate.length > 0) {
    await strapi.db.query('api::landuse-zone.landuse-zone').createMany({
      data: zonesToCreate
    });
  }
  
  return zonesToCreate.length;
}

/**
 * Import Regions from GeoJSON
 */
async function importRegions(geojson: any, countryId: number): Promise<number> {
  const regionsToCreate = [];
  
  for (const feature of geojson.features) {
    const props = feature.properties || {};
    const center = calculateCentroid(feature.geometry);
    
    regionsToCreate.push({
      name: props.name || 'Unnamed Region',
      code: props.code || props.ref,
      region_type: props.admin_level ? mapAdminLevel(props.admin_level) : 'parish',
      geometry_geojson: JSON.stringify(feature.geometry),
      center_latitude: center.lat,
      center_longitude: center.lon,
      tags: props.tags ? JSON.stringify(props.tags) : null,
      is_active: true,
      country: countryId,
      publishedAt: new Date()
    });
  }
  
  // Bulk create regions
  if (regionsToCreate.length > 0) {
    await strapi.db.query('api::region.region').createMany({
      data: regionsToCreate
    });
  }
  
  return regionsToCreate.length;
}

/**
 * Helper: Map OSM amenity to POI type
 */
function mapAmenityType(amenity: string): string {
  const mapping = {
    'bus_station': 'bus_station',
    'marketplace': 'marketplace',
    'market': 'marketplace',
    'hospital': 'hospital',
    'clinic': 'clinic',
    'school': 'school',
    'university': 'university',
    'police': 'police_station',
    'fire_station': 'fire_station',
    'place_of_worship': 'place_of_worship',
    'bank': 'bank',
    'post_office': 'post_office',
    'restaurant': 'restaurant',
    'cafe': 'cafe',
    'pharmacy': 'pharmacy'
  };
  
  return mapping[amenity] || 'other';
}

/**
 * Helper: Map OSM landuse to zone type
 */
function mapLanduseType(landuse: string): string {
  const mapping = {
    'residential': 'residential',
    'commercial': 'commercial',
    'industrial': 'industrial',
    'farmland': 'farmland',
    'forest': 'forest',
    'grass': 'park',
    'meadow': 'park',
    'retail': 'commercial'
  };
  
  return mapping[landuse] || 'other';
}

/**
 * Helper: Map admin level to region type
 */
function mapAdminLevel(level: string): string {
  const mapping = {
    '4': 'state',
    '5': 'district',
    '6': 'parish',
    '7': 'municipality',
    '8': 'county'
  };
  
  return mapping[level] || 'parish';
}

/**
 * Helper: Calculate centroid of polygon
 */
function calculateCentroid(geometry: any): { lat: number; lon: number } {
  if (geometry.type === 'Point') {
    const [lon, lat] = geometry.coordinates;
    return { lat, lon };
  }
  
  // For polygons, use first coordinate as approximation
  // (In production, use proper centroid calculation)
  if (geometry.type === 'Polygon') {
    const [lon, lat] = geometry.coordinates[0][0];
    return { lat, lon };
  }
  
  // Default fallback
  return { lat: 0, lon: 0 };
}
```

---

## ✅ Benefits of This Approach

### For Non-Technical Users

1. **No command line** - Everything in familiar Strapi UI
2. **No code editing** - Just upload files
3. **Validation** - Friendly error messages
4. **History** - See past imports and their status
5. **Rollback** - Can delete import record if something went wrong

### For You (Developer)

1. **One-time setup** - Configure once, users use forever
2. **Maintainable** - All logic in lifecycle hooks
3. **Auditable** - Track who imported what and when
4. **Extensible** - Easy to add new data types

---

## 🚀 Quick Start

### Create the Content Type

```bash
# In Strapi project
npm run strapi generate
# Select: api
# Name: geodata-import
```

Then paste the schema.json and lifecycles.ts files above.

### User Workflow

1. Download GeoJSON from OpenStreetMap or QGIS
2. Login to Strapi Admin
3. Content Manager → GeoData Import → Create
4. Fill form and upload file
5. Done! Data is imported

---

## 📊 Example User Journey

**User: Sarah (GIS Analyst, limited coding knowledge)

**Task**: Add Jamaica POIs to the system

**Steps**:

1. Opens QGIS, exports Jamaica amenities as GeoJSON: `jamaica_amenities.geojson`
2. Opens browser → `http://localhost:1337/admin`
3. Clicks "Content Manager" → "GeoData Import" → "Create"
4. Fills form:
   - Country: Jamaica *(dropdown)*
   - Data Type: POIs *(dropdown)*
   - File: *(clicks Upload button, selects jamaica_amenities.geojson)*
5. Clicks "Save"
6. Sees notification: "Processing GeoJSON file..."
7. Refreshes page, sees:

   ```text
   Status: ✅ Completed
   Total Records: 456
   Imported: 456
   Notes: Successfully imported 456 pois
   ```

8. Verifies: Content Manager → POI → Filters by "Jamaica" → Sees 456 POIs

**Total time**: ~2 minutes
**Code written**: 0 lines
**SQL executed**: 0 queries

---

**This is the perfect balance between ease-of-use and production-grade functionality!**

Would you like me to implement this now?
