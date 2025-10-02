# ⚡ QUICK START: PostGIS Setup for ArkNet Transit

## 🎯 Goal
Add geographic data support for realistic commuter spawning across multiple countries.

---

## ✅ Pre-Flight Check

Run this to see what you have:
```powershell
python scripts/inspect_database_structure.py
```

Expected output:
- ✅ 28 countries
- ✅ 387 shapes (route geometry)
- ✅ routes with geojson_data
- ✅ stops with lat/lon
- ❌ PostGIS NOT INSTALLED
- ❌ Missing: pois, landuse_zones, regions, spawn_configs

---

## 🚀 5-Step Setup (45 minutes)

### 1. Enable PostGIS (5 min)

**Using pgAdmin:**
1. Open pgAdmin
2. Connect to database: `arknettransit`
3. Tools → Query Tool
4. Run:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT PostGIS_version();  -- Should return version 3.x
```

**OR using PowerShell:**
```powershell
# Find PostgreSQL (check these locations):
cd "C:\Program Files\PostgreSQL\16\bin"
# OR
cd "C:\Program Files\PostgreSQL\15\bin"

# Run psql
.\psql -U david -d arknettransit
# Enter password: Ga25w123!

# In psql:
CREATE EXTENSION IF NOT EXISTS postgis;
\dx  -- List extensions (should show postgis)
\q   -- Quit
```

---

### 2. Create Strapi Content Types (25 min)

**Option A: Use Strapi Content-Type Builder UI**

1. Start Strapi:
```powershell
cd arknet_fleet_manager\arknet-fleet-api
npm run develop
```

2. Open: http://localhost:1337/admin
3. Go to: Content-Type Builder
4. Click: "Create new collection type"
5. Create these 4 types:
   - **poi** (Point of Interest)
   - **landuse-zone** (Land Use Zone)
   - **region** (Region/Parish)
   - **spawn-config** (Spawn Configuration)

**Option B: Copy Schema Files (Faster)**

Copy the schema.json files from `POSTGIS_STRAPI_IMPLEMENTATION.md` sections 2.1-2.4 into:

```
arknet-fleet-api/src/api/
├── poi/content-types/poi/schema.json
├── landuse-zone/content-types/landuse-zone/schema.json
├── region/content-types/region/schema.json
└── spawn-config/content-types/spawn-config/schema.json
```

---

### 3. Update Country Schema (5 min)

Edit: `arknet-fleet-api/src/api/country/content-types/country/schema.json`

Add to `attributes` section:
```json
{
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
  }
}
```

---

### 4. Restart Strapi (2 min)

```powershell
# Stop if running (Ctrl+C)
npm run develop
```

Watch console - should see:
```
✔ Building build context
✔ Admin UI built successfully
✔ Server started successfully
```

Check database - new tables should exist:
- pois
- landuse_zones
- regions
- spawn_configs

---

### 5. Load Barbados Data (10 min)

**First, create API token:**

1. Strapi Admin → Settings → API Tokens
2. Create New API Token
   - Name: "Data Import"
   - Token type: "Full access"
   - Duration: "Unlimited"
3. Copy token

**Then load data:**

Create: `scripts/load_barbados_data.py`
```python
import json
import requests

STRAPI_URL = "http://localhost:1337/api"
STRAPI_TOKEN = "paste_your_token_here"

headers = {
    "Authorization": f"Bearer {STRAPI_TOKEN}",
    "Content-Type": "application/json"
}

# Get Barbados country ID
response = requests.get(f"{STRAPI_URL}/countries?filters[code][$eq]=BRB", headers=headers)
country_id = response.json()['data'][0]['id']
print(f"Found Barbados: ID {country_id}")

# Load bus stops
with open('commuter_service/geojson_data/barbados_busstops.geojson') as f:
    data = json.load(f)
    
count = 0
for feature in data['features'][:10]:  # Load first 10 as test
    coords = feature['geometry']['coordinates']
    poi_data = {
        "data": {
            "poi_type": "bus_station",
            "name": f"Bus Stop {feature['properties']['full_id']}",
            "latitude": coords[1],
            "longitude": coords[0],
            "spawn_weight": 2.0,
            "country": country_id,
            "is_active": True
        }
    }
    response = requests.post(f"{STRAPI_URL}/pois", json=poi_data, headers=headers)
    if response.status_code == 200:
        count += 1
        
print(f"✅ Loaded {count} bus stops")
```

Run:
```powershell
python scripts/load_barbados_data.py
```

---

## 🎉 Verification

1. **Check PostGIS:**
```sql
SELECT PostGIS_version();
```

2. **Check Strapi API:**
```powershell
# Get POIs for Barbados
curl http://localhost:1337/api/pois?filters[country][code][$eq]=BRB
```

3. **Check Strapi Admin:**
- Open: http://localhost:1337/admin
- Content Manager → POI
- Should see imported bus stops

---

## 📊 What You'll Have

```
Database: arknettransit (PostgreSQL + PostGIS)

Existing Data (Unchanged):
✅ 28 countries (code: BRB, JAM, USA, etc.)
✅ 1 route with geojson_data
✅ 387 shapes (GTFS geometry points)
✅ 2 depots with location

New Data (After Import):
📝 ~1,340 POIs (bus stops + amenities)
📝 ~2,176 landuse zones
📝 Parishes/regions
📝 Spawn configurations
```

---

## 🔧 Troubleshooting

**PostGIS install fails:**
- Download PostGIS Bundle from: https://postgis.net/install/
- Or use Stack Builder (comes with PostgreSQL)

**Strapi won't restart:**
- Check console for errors
- Verify schema.json files are valid JSON
- Delete `arknet-fleet-api/.cache` and try again

**Can't find psql:**
- PostgreSQL not in PATH
- Manually navigate to: `C:\Program Files\PostgreSQL\<version>\bin\`

**API token doesn't work:**
- Check token type is "Full access"
- Verify token is not expired
- Check `Authorization: Bearer <token>` header format

---

## 📚 Full Documentation

- **IMPLEMENTATION_SUMMARY.md** - Why this approach
- **POSTGIS_STRAPI_IMPLEMENTATION.md** - Complete guide with all code
- **POSTGIS_SETUP.md** - PostGIS installation details

---

## ⏭️ Next Steps

After setup:
1. ✅ Verify data in Strapi Admin
2. ✅ Implement PostGISDataProvider for Python
3. ✅ Create spawning strategies using Strapi API
4. ✅ Add more countries (Jamaica, Trinidad, etc.)

---

**Questions?** Check the full guides or run the inspection script again!
