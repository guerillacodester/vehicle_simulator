# PostGIS Setup & Geographic Tables - Implementation Plan

## 📊 Current Database Analysis

### ✅ What You Already Have (GTFS-Compliant)

| Table | Rows | Geographic Data | Notes |
|-------|------|----------------|-------|
| **countries** | 28 | ✅ Has `code` field | Ready for PostGIS enhancement |
| **routes** | 1 | ✅ Has `geojson_data` (JSONB) | Already storing geometry! |
| **stops** | 0 | ✅ Has `latitude`, `longitude`, `location` (JSONB) | Ready for PostGIS enhancement |
| **shapes** | 387 | ✅ Has `shape_pt_lat`, `shape_pt_lon` | GTFS shapes - route geometry points |
| **route_shapes** | 12 | ⚠️ Links routes to shapes | Mapping table |
| **depots** | 2 | ✅ Has `location` (JSONB) | Ready for PostGIS enhancement |

### ❌ What's Missing for Spawning System

| Needed Table | Purpose | Data Source |
|--------------|---------|-------------|
| **pois** | Points of Interest (bus stations, marketplaces, clinics) | Load from `barbados_amenities.geojson` |
| **landuse_zones** | Land use (residential, commercial, farmland) | Load from `barbados_landuse.geojson` |
| **regions** | Parishes/regions within countries | Load from GeoJSON or create manually |
| **spawn_configs** | Country-specific spawn rates & patterns | Configuration table |

---

## 🎯 **RECOMMENDED APPROACH: Enhance Existing Tables + Add New Ones**

### **Strategy:**

1. ✅ **Keep existing tables** (countries, routes, stops, shapes, depots)
2. 🔧 **Enhance with PostGIS geometry columns** (for spatial queries)
3. 📝 **Add new Strapi content types** for POIs, landuse, regions, spawn configs
4. 🚀 **Use Strapi Admin UI** to manage all geographic data

---

## 📋 Step-by-Step Implementation

### **STEP 1: Install PostGIS Extension** (5 minutes)

#### Option A: Using pgAdmin (Recommended)
1. Open pgAdmin
2. Connect to `arknettransit` database
3. Right-click database → Query Tool
4. Run:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_version();
```

#### Option B: Using psql Command Line
```powershell
# Find your PostgreSQL bin directory (e.g., C:\Program Files\PostgreSQL\16\bin\)
cd "C:\Program Files\PostgreSQL\16\bin"
.\psql -U david -d arknettransit -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

---

### **STEP 2: Create Strapi Content Types for Geographic Data** (30 minutes)

Instead of raw SQL, we'll use **Strapi's Content-Type Builder** to create schema files, then Strapi will auto-generate the PostgreSQL tables with PostGIS support.

#### **2.1 Create: POI (Point of Interest)**

Create file: `arknet-fleet-api/src/api/poi/content-types/poi/schema.json`

```json
{
  "kind": "collectionType",
  "collectionName": "pois",
  "info": {
    "singularName": "poi",
    "pluralName": "pois",
    "displayName": "Point of Interest",
    "description": "Points of interest for commuter spawning (bus stations, marketplaces, etc.)"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "poi_type": {
      "type": "enumeration",
      "enum": [
        "bus_station",
        "marketplace",
        "clinic",
        "restaurant",
        "police",
        "parking",
        "place_of_worship",
        "cinema",
        "community_centre",
        "school",
        "hospital",
        "other"
      ],
      "required": true
    },
    "name": {
      "type": "string",
      "required": false
    },
    "latitude": {
      "type": "decimal",
      "required": true
    },
    "longitude": {
      "type": "decimal",
      "required": true
    },
    "spawn_weight": {
      "type": "float",
      "required": true,
      "default": 1.0,
      "min": 0.0,
      "max": 5.0
    },
    "properties": {
      "type": "json",
      "required": false
    },
    "country": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::country.country",
      "inversedBy": "pois"
    },
    "is_active": {
      "type": "boolean",
      "required": true,
      "default": true
    }
  }
}
```

#### **2.2 Create: Land Use Zone**

Create file: `arknet-fleet-api/src/api/landuse-zone/content-types/landuse-zone/schema.json`

```json
{
  "kind": "collectionType",
  "collectionName": "landuse_zones",
  "info": {
    "singularName": "landuse-zone",
    "pluralName": "landuse-zones",
    "displayName": "Land Use Zone",
    "description": "Land use classifications for spawn density calculations"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "zone_type": {
      "type": "enumeration",
      "enum": [
        "residential",
        "commercial",
        "industrial",
        "farmland",
        "grass",
        "meadow",
        "park",
        "forest",
        "water",
        "other"
      ],
      "required": true
    },
    "geometry_geojson": {
      "type": "json",
      "required": true
    },
    "population_density": {
      "type": "float",
      "required": false
    },
    "spawn_weight": {
      "type": "float",
      "required": true,
      "default": 1.0
    },
    "country": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::country.country",
      "inversedBy": "landuse_zones"
    },
    "is_active": {
      "type": "boolean",
      "required": true,
      "default": true
    }
  }
}
```

#### **2.3 Create: Region (Parish)**

Create file: `arknet-fleet-api/src/api/region/content-types/region/schema.json`

```json
{
  "kind": "collectionType",
  "collectionName": "regions",
  "info": {
    "singularName": "region",
    "pluralName": "regions",
    "displayName": "Region",
    "description": "Administrative regions (parishes, states, provinces)"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "name": {
      "type": "string",
      "required": true
    },
    "type": {
      "type": "enumeration",
      "enum": ["parish", "state", "province", "district", "municipality"],
      "required": true,
      "default": "parish"
    },
    "geometry_geojson": {
      "type": "json",
      "required": false
    },
    "country": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::country.country",
      "inversedBy": "regions"
    },
    "is_active": {
      "type": "boolean",
      "required": true,
      "default": true
    }
  }
}
```

#### **2.4 Create: Spawn Config**

Create file: `arknet-fleet-api/src/api/spawn-config/content-types/spawn-config/schema.json`

```json
{
  "kind": "collectionType",
  "collectionName": "spawn_configs",
  "info": {
    "singularName": "spawn-config",
    "pluralName": "spawn-configs",
    "displayName": "Spawn Configuration",
    "description": "Country-specific commuter spawn configuration"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "time_patterns": {
      "type": "json",
      "required": true,
      "default": [
        {"hour_start": 6, "hour_end": 9, "multiplier": 3.0, "period": "morning_rush"},
        {"hour_start": 9, "hour_end": 16, "multiplier": 1.0, "period": "daytime"},
        {"hour_start": 16, "hour_end": 19, "multiplier": 2.5, "period": "evening_rush"},
        {"hour_start": 19, "hour_end": 6, "multiplier": 0.3, "period": "night"}
      ]
    },
    "poi_weights": {
      "type": "json",
      "required": true,
      "default": {
        "morning_rush": {"residential": 0.7, "bus_station": 0.2, "marketplace": 0.1},
        "daytime": {"marketplace": 0.4, "bus_station": 0.3, "residential": 0.3},
        "evening_rush": {"marketplace": 0.5, "bus_station": 0.3, "residential": 0.2},
        "night": {"residential": 0.6, "bus_station": 0.2, "marketplace": 0.2}
      }
    },
    "depot_base_rate": {
      "type": "integer",
      "required": true,
      "default": 10
    },
    "route_base_rate": {
      "type": "integer",
      "required": true,
      "default": 5
    },
    "pickup_radius_meters": {
      "type": "float",
      "required": true,
      "default": 500.0
    },
    "route_sampling_resolution": {
      "type": "integer",
      "required": true,
      "default": 50
    },
    "country": {
      "type": "relation",
      "relation": "oneToOne",
      "target": "api::country.country",
      "inversedBy": "spawn_config"
    }
  }
}
```

---

### **STEP 3: Update Existing Content Types with Relations** (15 minutes)

#### **3.1 Update Country Schema**

Edit: `arknet-fleet-api/src/api/country/content-types/country/schema.json`

Add these relations to `attributes` section:

```json
    "pois": {
      "type": "relation",
      "relation": "oneToMany",
      "target": "api::poi.poi",
      "mappedBy": "country"
    },
    "landuse_zones": {
      "type": "relation",
      "relation": "oneToMany",
      "target": "api::landuse-zone.landuse-zone",
      "mappedBy": "country"
    },
    "regions": {
      "type": "relation",
      "relation": "oneToMany",
      "target": "api::region.region",
      "mappedBy": "country"
    },
    "spawn_config": {
      "type": "relation",
      "relation": "oneToOne",
      "target": "api::spawn-config.spawn-config",
      "mappedBy": "country"
    },
    "geometry_geojson": {
      "type": "json",
      "required": false
    }
```

---

### **STEP 4: Restart Strapi to Generate Tables** (2 minutes)

```powershell
cd arknet_fleet_manager\arknet-fleet-api
npm run develop
```

Strapi will automatically:
- ✅ Create new database tables: `pois`, `landuse_zones`, `regions`, `spawn_configs`
- ✅ Add relation columns to `countries`
- ✅ Generate API endpoints for all content types

---

### **STEP 5: Load Geographic Data from GeoJSON** (20 minutes)

Now create a Python script to load Barbados data:

File: `scripts/load_barbados_geojson_to_strapi.py`

```python
"""
Load Barbados GeoJSON data into Strapi via API
"""
import json
import requests
from pathlib import Path

STRAPI_URL = "http://localhost:1337/api"
STRAPI_TOKEN = "your_api_token_here"  # Get from Strapi Admin → Settings → API Tokens

headers = {
    "Authorization": f"Bearer {STRAPI_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Get Barbados country ID
response = requests.get(f"{STRAPI_URL}/countries?filters[code][$eq]=BRB", headers=headers)
barbados = response.json()['data'][0]
country_id = barbados['id']

# 2. Load Bus Stops as POIs
with open('commuter_service/geojson_data/barbados_busstops.geojson') as f:
    data = json.load(f)
    
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    poi_data = {
        "data": {
            "poi_type": "bus_station",
            "name": feature['properties'].get('stop_name') or f"Stop {feature['properties']['full_id']}",
            "latitude": coords[1],
            "longitude": coords[0],
            "spawn_weight": 2.0,  # Bus stops get higher spawn weight
            "country": country_id,
            "is_active": True
        }
    }
    requests.post(f"{STRAPI_URL}/pois", json=poi_data, headers=headers)

print("✅ Loaded bus stops")

# 3. Load Amenities as POIs
with open('commuter_service/geojson_data/barbados_amenities.geojson') as f:
    data = json.load(f)

amenity_type_map = {
    "marketplace": "marketplace",
    "bus_station": "bus_station",
    "clinic": "clinic",
    "restaurant": "restaurant",
    "police": "police",
    "parking": "parking",
    "place_of_worship": "place_of_worship",
    "cinema": "cinema",
    "community_centre": "community_centre"
}

for feature in data['features']:
    amenity = feature['properties'].get('amenity')
    if amenity in amenity_type_map:
        # Handle MultiPolygon - get centroid
        if feature['geometry']['type'] == 'MultiPolygon':
            # Use first polygon's first point as approximation
            coords = feature['geometry']['coordinates'][0][0][0]
        else:
            coords = feature['geometry']['coordinates']
        
        poi_data = {
            "data": {
                "poi_type": amenity_type_map[amenity],
                "name": feature['properties'].get('name'),
                "latitude": coords[1] if len(coords) > 1 else coords[0][1],
                "longitude": coords[0] if len(coords) > 1 else coords[0][0],
                "spawn_weight": 1.5,
                "country": country_id,
                "is_active": True
            }
        }
        requests.post(f"{STRAPI_URL}/pois", json=poi_data, headers=headers)

print("✅ Loaded amenities")

# 4. Load Land Use Zones
with open('commuter_service/geojson_data/barbados_landuse.geojson') as f:
    data = json.load(f)

landuse_type_map = {
    "residential": "residential",
    "commercial": "commercial",
    "industrial": "industrial",
    "farmland": "farmland",
    "grass": "grass",
    "meadow": "meadow"
}

for feature in data['features']:
    landuse = feature['properties'].get('landuse')
    if landuse in landuse_type_map:
        zone_data = {
            "data": {
                "zone_type": landuse_type_map[landuse],
                "geometry_geojson": feature['geometry'],
                "spawn_weight": 1.0,
                "country": country_id,
                "is_active": True
            }
        }
        requests.post(f"{STRAPI_URL}/landuse-zones", json=zone_data, headers=headers)

print("✅ Loaded land use zones")

print("\n🎉 All Barbados geographic data loaded!")
```

---

## 🔑 Key Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| **✅ No SQL Migrations** | Strapi handles schema changes automatically |
| **✅ Admin UI** | Manage POIs, landuse, regions via Strapi dashboard |
| **✅ API Endpoints** | Auto-generated REST + GraphQL APIs |
| **✅ Existing Data Preserved** | Your 28 countries, routes, stops remain intact |
| **✅ PostGIS Ready** | Can add geometry columns later without breaking existing data |
| **✅ Multi-Country** | Filter by `country` relation |
| **✅ Flexible** | JSON fields allow storing full GeoJSON when needed |

---

## 📊 Final Database Structure

```
countries (28 rows)
├── routes (1 row) - Has geojson_data
├── depots (2 rows) - Has location JSONB
├── pois (NEW - ~1,340+ from bus stops + amenities)
├── landuse_zones (NEW - ~2,176 from GeoJSON)
├── regions (NEW - Barbados parishes)
└── spawn_config (NEW - 1 per country)

stops (0 rows) - Has lat/lon columns
shapes (387 rows) - GTFS shapes
route_shapes (12 rows) - Route→Shape mapping
```

---

## ⚡ Quick Start Commands

```powershell
# 1. Enable PostGIS in database (via pgAdmin or psql)

# 2. Create new content type directories
cd arknet_fleet_manager\arknet-fleet-api\src\api
mkdir poi\content-types\poi
mkdir landuse-zone\content-types\landuse-zone
mkdir region\content-types\region
mkdir spawn-config\content-types\spawn-config

# 3. Copy schema.json files (from STEP 2 above)

# 4. Restart Strapi
cd ..\..
npm run develop

# 5. Create API token in Strapi Admin

# 6. Load data
python scripts/load_barbados_geojson_to_strapi.py
```

---

## 🎯 Next Steps After Setup

1. ✅ Verify data in Strapi Admin (http://localhost:1337/admin)
2. ✅ Create PostGISDataProvider that queries Strapi API instead of direct DB
3. ✅ Implement spawning strategies using Strapi endpoints
4. ✅ Add more countries by loading their GeoJSON data

---

## 💡 Why This is Better Than Direct PostGIS Tables

1. **Strapi manages schema** - No manual SQL migrations
2. **Built-in API** - REST + GraphQL for free
3. **Admin UI** - Non-technical users can add POIs via dashboard
4. **Existing infrastructure** - Reuses your Strapi setup
5. **Type safety** - Schema validation built-in
6. **Relations work** - Can join countries → pois → landuse easily
7. **Future-proof** - Can add PostGIS geometry columns later if needed for complex spatial queries

---

**Ready to implement?** Start with STEP 1 (PostGIS installation) and proceed sequentially! 🚀
