# GeoJSON Import Architecture

**Date:** October 24, 2025  
**Status:** Design Complete - Implementation Pending  
**Project:** ArkNet Fleet Manager - Strapi v5.23.5

---

## 📋 Context

This document captures the complete architectural design for implementing GeoJSON data import functionality into the Strapi CMS. The system will allow importing geographic data (POIs, Landuse Zones, Regions, Highways) from large GeoJSON files (~700MB) stored in the `sample_data/` directory.

---

## 🎯 Problem Statement

**Goal:** Enable admin users to import GeoJSON data via action buttons on Country records, with full tracking, validation, and safe deletion capabilities.

**Constraints:**
- GeoJSON files are 700MB+ (cannot store in DB as blobs)
- Must track which import created which records (for clean deletion)
- Must prevent accidental mass deletion
- Must handle errors gracefully
- Must show import progress
- Must support soft delete with recovery window

---

## ✅ Current State (What We Have)

### **Domain Models - Complete & Well-Designed**

#### **POI Content Type**
- Path: `src/api/poi/content-types/poi/schema.json`
- Fields: `latitude`, `longitude`, `poi_type`, `spawn_weight`, `peak_hour_multiplier`, `off_peak_multiplier`, `osm_id`, `amenity`, `tags`
- Relations: `country` (manyToOne), `region` (manyToOne), `poi_shapes` (oneToMany)

#### **Landuse Zone Content Type**
- Path: `src/api/landuse-zone/content-types/landuse-zone/schema.json`
- Fields: `zone_type`, `geometry_geojson`, `population_density`, `spawn_weight`, `peak_hour_multiplier`, `off_peak_multiplier`, `area_sq_km`
- Relations: `country` (manyToOne), `region` (manyToOne), `landuse_shapes` (oneToMany)

#### **Region Content Type**
- Path: `src/api/region/content-types/region/schema.json`
- Fields: `name`, `code`, `region_type`, `geometry_geojson`, `population`, `area_sq_km`
- Relations: `country` (manyToOne), `pois` (oneToMany), `landuse_zones` (oneToMany), `highways` (oneToMany)

#### **Highway Content Type**
- Path: `src/api/highway/content-types/highway/schema.json`
- Fields: `name`, `highway_type`, `osm_id`, `surface`, `lanes`, `maxspeed`, `oneway`
- Relations: `country` (manyToOne), `region` (manyToOne), `highway_shapes` (oneToMany)

### **Infrastructure**
- ✅ Strapi v5.23.5 on Node v22.20.0
- ✅ PostgreSQL with PostGIS enabled
- ✅ Cloudinary configured (1GB upload limit)
- ✅ `action-buttons` plugin registered in `config/plugins.ts`
- ✅ `allow-custom-files` plugin for .geojson support
- ✅ Country content type with relations to all 4 domain models

### **Sample Data Files**
Located in `sample_data/` directory:
- `amenity.geojson` → POI import (points of interest)
- `landuse.geojson` → Landuse Zone import
- `highway.geojson` → Highway import (roads, streets)
- `admin_level_6_polygon.geojson` → Region import (parishes)
- `admin_level_8_polygon.geojson` → Region import (districts)
- `admin_level_9_polygon.geojson` → Region import (sub-districts)
- `admin_level_10_polygon.geojson` → Region import (neighborhoods)

---

## ❌ What Needs to Change

### **Missing Components**

1. **No Import Tracking**
   - Missing `import_job_id` relation on POI, Landuse, Region, Highway
   - No `GeoJsonImporter` content type to track import jobs
   - Cannot identify which import created which records
   - Cannot cleanly delete imports

2. **No Import Infrastructure**
   - No action button configuration
   - No import controllers/services
   - No background job processing
   - No progress tracking or error handling

3. **Data Integrity Gaps**
   - No validation that imported data matches country
   - No duplicate detection (re-importing same file)
   - No soft delete mechanism
   - No cleanup scheduling

4. **Missing Lifecycle Hooks**
   - No `beforeDelete` protection on GeoJsonImporter
   - No cascade/soft delete on import deletion
   - No validation hooks on import creation

---

## 🏗️ Architecture Design

### **Separation of Concerns**

```
┌─────────────────────────────────────────────────┐
│ DOMAIN LAYER (Existing - DO NOT MODIFY)        │
├─────────────────────────────────────────────────┤
│ POI (content type) - Stores actual POI data    │
│ Landuse Zone - Stores actual landuse data      │
│ Region - Stores actual region data             │
│ Highway - Stores actual highway data           │
│                                                 │
│ These represent real-world entities.           │
│ Already complete and well-designed.            │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ IMPORT ORCHESTRATION LAYER (NEW)               │
├─────────────────────────────────────────────────┤
│ GeoJsonImporter (content type) - NEW           │
│ ├─ Tracks import jobs (metadata)               │
│ ├─ Stores status, progress, errors             │
│ ├─ References country being imported to        │
│ └─ Links to imported records via import_job_id │
│                                                 │
│ This is infrastructure, not domain logic.      │
└─────────────────────────────────────────────────┘
```

### **Data Flow**

```
User Action (Admin UI)
    ↓
Country Record: "Barbados"
    ↓
[Import POIs] button clicked
    ↓
Controller creates GeoJsonImporter record
    status: 'pending'
    import_type: 'poi'
    country: 'barbados_id'
    file_path: 'sample_data/amenity.geojson'
    ↓
Service processes import
    ↓
Read sample_data/amenity.geojson (700MB)
    ↓
Parse GeoJSON features (5,247 features)
    ↓
For each feature:
    ↓
Create POI record
    name: feature.properties.name
    poi_type: feature.properties.amenity
    latitude: feature.geometry.coordinates[1]
    longitude: feature.geometry.coordinates[0]
    country: 'barbados_id'
    import_job: 'import_123'  ← Links back to import
    ↓
Update import progress
    records_imported: 5247
    status: 'completed'
    completed_at: now()
    ↓
User sees: ✅ "Successfully imported 5,247 POIs"
```

### **Deletion Flow**

```
User deletes GeoJsonImporter record #123
    ↓
beforeDelete lifecycle hook executes
    ↓
Query: COUNT POIs with import_job = 123
    Result: 5,247 records
    ↓
Check: Is count > 1000?
    Yes: Throw error "Use cleanup scheduling"
    No: Continue
    ↓
Soft delete all POIs with import_job = 123
    UPDATE pois SET deleted_at = NOW() WHERE import_job = 123
    ↓
Delete GeoJsonImporter record #123
    ↓
Result:
    - Import job removed from admin UI
    - POI records marked deleted (soft delete)
    - Data preserved for 7-day recovery window
    - Cleanup service purges after 7 days
```

---

## 📐 Schema Design

### **GeoJsonImporter Content Type (NEW)**

```json
{
  "kind": "collectionType",
  "collectionName": "geojson_importers",
  "info": {
    "singularName": "geojson-importer",
    "pluralName": "geojson-importers",
    "displayName": "GeoJSON Import Job"
  },
  "attributes": {
    "import_type": {
      "type": "enumeration",
      "enum": ["poi", "landuse", "region", "highway"],
      "required": true
    },
    "country": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::country.country",
      "inversedBy": "import_jobs"
    },
    "status": {
      "type": "enumeration",
      "enum": ["pending", "running", "completed", "failed"],
      "default": "pending",
      "required": true
    },
    "file_path": {
      "type": "string",
      "required": true
    },
    "records_imported": {
      "type": "integer",
      "default": 0
    },
    "records_failed": {
      "type": "integer",
      "default": 0
    },
    "error_message": {
      "type": "text"
    },
    "started_at": {
      "type": "datetime"
    },
    "completed_at": {
      "type": "datetime"
    },
    "deleted_at": {
      "type": "datetime"
    }
  }
}
```

### **Schema Modifications (Add to Existing)**

#### **Add to POI, Landuse, Region, Highway:**
```json
"import_job": {
  "type": "relation",
  "relation": "manyToOne",
  "target": "api::geojson-importer.geojson-importer"
},
"deleted_at": {
  "type": "datetime"
}
```

#### **Add to Country:**
```json
"import_jobs": {
  "type": "relation",
  "relation": "oneToMany",
  "target": "api::geojson-importer.geojson-importer",
  "mappedBy": "country"
}
```

---

## 🔘 Action Button Configuration

**File:** `config/action-buttons.js` (create new)

```javascript
module.exports = {
  config: {
    contentTypes: [
      {
        uid: 'api::country.country',
        buttons: [
          {
            label: 'Import POIs',
            type: 'EXECUTE_FUNCTION',
            icon: 'map-marker',
            color: 'primary',
            handler: 'geojson-importer.importPois'
          },
          {
            label: 'Import Landuse Zones',
            type: 'EXECUTE_FUNCTION',
            icon: 'layer-group',
            color: 'success',
            handler: 'geojson-importer.importLanduse'
          },
          {
            label: 'Import Regions',
            type: 'EXECUTE_FUNCTION',
            icon: 'globe',
            color: 'info',
            handler: 'geojson-importer.importRegions'
          },
          {
            label: 'Import Highways',
            type: 'EXECUTE_FUNCTION',
            icon: 'road',
            color: 'warning',
            handler: 'geojson-importer.importHighways'
          }
        ]
      }
    ]
  }
};
```

---

## 🎮 Controller Design

**File:** `src/api/geojson-importer/controllers/geojson-importer.js`

```javascript
module.exports = {
  async importPois(ctx) {
    const { countryId } = ctx.params;
    
    // Validate country exists
    const country = await strapi.entityService.findOne(
      'api::country.country',
      countryId
    );
    
    if (!country) {
      return ctx.badRequest('Country not found');
    }
    
    // Create import job
    const importJob = await strapi.entityService.create(
      'api::geojson-importer.geojson-importer',
      {
        data: {
          import_type: 'poi',
          country: countryId,
          status: 'pending',
          file_path: 'sample_data/amenity.geojson',
          started_at: new Date()
        }
      }
    );
    
    // Process import (inline for MVP, queue for production)
    try {
      await strapi.service('api::geojson-importer.geojson-importer')
        .processImport(importJob.id);
      
      ctx.send({ 
        success: true, 
        importJobId: importJob.id,
        message: 'Import started successfully'
      });
    } catch (error) {
      await strapi.entityService.update(
        'api::geojson-importer.geojson-importer',
        importJob.id,
        {
          data: {
            status: 'failed',
            error_message: error.message
          }
        }
      );
      
      ctx.badRequest(error.message);
    }
  },
  
  // Similar functions for importLanduse, importRegions, importHighways
};
```

---

## ⚙️ Service Design

**File:** `src/api/geojson-importer/services/geojson-importer.js`

```javascript
const fs = require('fs');
const path = require('path');

module.exports = {
  async processImport(importJobId) {
    const importJob = await strapi.entityService.findOne(
      'api::geojson-importer.geojson-importer',
      importJobId,
      { populate: ['country'] }
    );
    
    // Update status to running
    await strapi.entityService.update(
      'api::geojson-importer.geojson-importer',
      importJobId,
      { data: { status: 'running' } }
    );
    
    // Read GeoJSON file
    const filePath = path.join(process.cwd(), importJob.file_path);
    const geojson = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    // Validate
    if (!geojson.features || !Array.isArray(geojson.features)) {
      throw new Error('Invalid GeoJSON structure');
    }
    
    // Get target model
    const targetModel = {
      'poi': 'api::poi.poi',
      'landuse': 'api::landuse-zone.landuse-zone',
      'region': 'api::region.region',
      'highway': 'api::highway.highway'
    }[importJob.import_type];
    
    // Process features in batches
    const batchSize = 1000;
    let imported = 0;
    
    for (let i = 0; i < geojson.features.length; i += batchSize) {
      const batch = geojson.features.slice(i, i + batchSize);
      
      for (const feature of batch) {
        const data = this.mapFeatureToModel(
          feature, 
          importJob.import_type, 
          importJob.country.id,
          importJobId
        );
        
        await strapi.entityService.create(targetModel, { data });
        imported++;
      }
      
      // Update progress
      await strapi.entityService.update(
        'api::geojson-importer.geojson-importer',
        importJobId,
        { data: { records_imported: imported } }
      );
    }
    
    // Mark complete
    await strapi.entityService.update(
      'api::geojson-importer.geojson-importer',
      importJobId,
      {
        data: {
          status: 'completed',
          completed_at: new Date(),
          records_imported: imported
        }
      }
    );
  },
  
  mapFeatureToModel(feature, importType, countryId, importJobId) {
    const base = {
      country: countryId,
      import_job: importJobId
    };
    
    switch (importType) {
      case 'poi':
        return {
          ...base,
          name: feature.properties.name || 'Unnamed',
          poi_type: feature.properties.amenity || 'other',
          latitude: feature.geometry.coordinates[1],
          longitude: feature.geometry.coordinates[0],
          osm_id: feature.properties.osm_id,
          amenity: feature.properties.amenity,
          tags: feature.properties
        };
      
      case 'landuse':
        return {
          ...base,
          zone_type: feature.properties.landuse || 'other',
          name: feature.properties.name,
          geometry_geojson: feature.geometry,
          osm_id: feature.properties.osm_id,
          tags: feature.properties
        };
      
      case 'region':
        return {
          ...base,
          name: feature.properties.name,
          region_type: this.mapAdminLevel(feature.properties.admin_level),
          geometry_geojson: feature.geometry,
          code: feature.properties.code,
          tags: feature.properties
        };
      
      case 'highway':
        return {
          ...base,
          name: feature.properties.name || 'Unnamed Road',
          highway_type: feature.properties.highway || 'other',
          osm_id: feature.properties.osm_id,
          surface: feature.properties.surface,
          lanes: feature.properties.lanes,
          maxspeed: feature.properties.maxspeed,
          oneway: feature.properties.oneway === 'yes'
        };
    }
  },
  
  mapAdminLevel(level) {
    const mapping = {
      '6': 'parish',
      '8': 'district',
      '9': 'municipality',
      '10': 'county'
    };
    return mapping[level] || 'other';
  }
};
```

---

## 🔒 Lifecycle Hooks

**File:** `src/api/geojson-importer/content-types/geojson-importer/lifecycles.js`

```javascript
module.exports = {
  async beforeDelete(event) {
    const { id } = event.params.where;
    
    // Get import job details
    const importJob = await strapi.entityService.findOne(
      'api::geojson-importer.geojson-importer',
      id,
      { populate: ['country'] }
    );
    
    if (!importJob) return;
    
    // Get target model
    const targetModel = {
      'poi': 'api::poi.poi',
      'landuse': 'api::landuse-zone.landuse-zone',
      'region': 'api::region.region',
      'highway': 'api::highway.highway'
    }[importJob.import_type];
    
    // Count records to delete
    const count = await strapi.db.query(targetModel).count({
      where: { import_job: id }
    });
    
    // Safety check
    if (count > 1000) {
      throw new Error(
        `Cannot delete import with ${count} records. ` +
        `This would cause mass deletion. ` +
        `Use cleanup scheduling instead.`
      );
    }
    
    // Soft delete imported records
    await strapi.db.query(targetModel).updateMany({
      where: { import_job: id },
      data: { deleted_at: new Date() }
    });
    
    strapi.log.info(
      `Soft deleted ${count} ${importJob.import_type} records ` +
      `from import job ${id}`
    );
  }
};
```

---

## 🧹 Cleanup Service

**File:** `src/api/geojson-importer/services/cleanup.js`

```javascript
module.exports = {
  async cleanupDeletedRecords() {
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    
    const models = [
      'api::poi.poi',
      'api::landuse-zone.landuse-zone',
      'api::region.region',
      'api::highway.highway'
    ];
    
    for (const model of models) {
      const deleted = await strapi.db.query(model).deleteMany({
        where: {
          deleted_at: { $lt: sevenDaysAgo }
        }
      });
      
      strapi.log.info(
        `Cleanup: Permanently deleted ${deleted.count} ` +
        `${model} records older than 7 days`
      );
    }
  }
};
```

**Cron Configuration:** Add to `config/server.js`

```javascript
module.exports = {
  cron: {
    enabled: true,
    tasks: {
      '0 2 * * *': async () => {
        // Run cleanup daily at 2am
        await strapi.service('api::geojson-importer.cleanup')
          .cleanupDeletedRecords();
      }
    }
  }
};
```

---

## 🧪 Testing Strategy

### **Test 1: POI Import**
1. Navigate to Country "Barbados"
2. Click "Import POIs" button
3. Verify GeoJsonImporter record created with `status='pending'`
4. Check POI table has new records from `amenity.geojson`
5. Verify `import_job` relation set on POI records
6. Check status changes to `'completed'`
7. Verify `records_imported` count accurate

### **Test 2: Deletion & Soft Delete**
1. Delete import job from Test 1
2. Verify `beforeDelete` hook executes
3. Check POI records have `deleted_at` timestamp
4. Verify POIs still in database (soft delete)
5. Confirm no cascade to other imports
6. Test deletion protection (> 1000 records)
7. Verify error thrown for mass deletion

### **Test 3: Error Handling**
1. Import with invalid file path
2. Verify `error_message` captured
3. Check `status='failed'`
4. Test concurrent imports
5. Verify duplicate prevention
6. Test malformed GeoJSON
7. Validate error messages in admin UI

### **Test 4: All Import Types**
1. Import POIs (amenity.geojson)
2. Import Landuse (landuse.geojson)
3. Import Regions (admin_level_6_polygon.geojson)
4. Import Highways (highway.geojson)
5. Verify all target tables populated
6. Check `import_job_id` tracking
7. Validate data integrity

---

## 📊 File Mapping

| Import Type | Source File | Target Table | Key Fields |
|-------------|-------------|--------------|------------|
| POI | `sample_data/amenity.geojson` | `pois` | name, poi_type, lat/lon, amenity |
| Landuse | `sample_data/landuse.geojson` | `landuse_zones` | zone_type, geometry_geojson |
| Region | `sample_data/admin_level_*_polygon.geojson` | `regions` | name, region_type, geometry_geojson |
| Highway | `sample_data/highway.geojson` | `highways` | name, highway_type, osm_id |

---

## 🚀 Next Steps After Implementation

Once GeoJSON import is complete, proceed with:

1. **Redis Cache** - Location service caching for reverse geocoding
2. **Reverse Geocoding** - Highway/POI/Region lookup by coordinates
3. **Poisson Spawning** - Temporal passenger generation using imported POI/Landuse data
4. **Depot Integration** - Spawn weights based on proximity to depots/routes

---

## 🎓 Key Architectural Decisions

### **Why Single GeoJsonImporter Content Type?**
- **DRY Principle:** One controller, one service, one lifecycle hook
- **Maintainability:** Fix bugs once, not 4 times
- **Consistency:** All imports behave identically
- **Extensibility:** Add new import types without new content types

### **Why Separate Domain Tables?**
- **Domain Separation:** POI ≠ Landuse ≠ Region ≠ Highway (different schemas)
- **Single Responsibility:** Each table represents one concept
- **Proper Data Modeling:** Import tracking is metadata, not domain logic

### **Why Soft Delete?**
- **Recovery Window:** 7-day grace period for accidental deletions
- **Audit Trail:** Track when records were deleted
- **Data Integrity:** Prevent immediate data loss
- **Cleanup Automation:** Scheduled purge prevents database bloat

### **Why Import Tracking?**
- **Precise Deletion:** Know exactly which records to delete
- **Audit History:** Track which imports created which data
- **Data Provenance:** Trace back to source file
- **Validation:** Detect duplicate imports

---

## 📝 Implementation Checklist

See TODO list for granular step-by-step tasks (20 items).

---

**End of Architecture Document**
