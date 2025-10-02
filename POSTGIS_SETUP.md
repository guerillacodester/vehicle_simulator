# PostGIS Database Setup Guide

## Overview
This guide will help you set up PostGIS for the ArkNet Transit System, enabling geographic data storage and spatial queries for multi-country simulation support.

---

## Prerequisites

✅ **PostgreSQL is installed** (confirmed)
- Find your PostgreSQL installation directory (typically `C:\Program Files\PostgreSQL\<version>\`)
- Look for `psql.exe` in the `bin` folder

---

## Step 1: Enable PostGIS Extension

### Option A: Using pgAdmin (Recommended for Windows)

1. **Open pgAdmin** (should be installed with PostgreSQL)
2. **Connect to your PostgreSQL server**
3. **Navigate to your Strapi database** (or create a new database):
   - Right-click **Databases** → **Create** → **Database**
   - Name: `arknet_transit` (or your preferred name)
   - Owner: `postgres` (or your DB user)
4. **Enable PostGIS extension**:
   - Expand your database → Right-click **Extensions**
   - Click **Create** → **Extension**
   - In the **Name** dropdown, select: `postgis`
   - Click **Save**

### Option B: Using SQL Query (via pgAdmin Query Tool)

1. Open pgAdmin and connect to your database
2. Right-click your database → **Query Tool**
3. Run these commands:

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify installation
SELECT PostGIS_version();

-- Check installed extensions
SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis';
```

Expected output:
```
postgis | 3.x.x
```

---

## Step 2: Create PostGIS Schema for Geographic Data

Run the migration script provided in `scripts/migrations/001_create_geo_tables.sql`:

```sql
-- This will create:
-- - countries table
-- - regions table
-- - pois (points of interest) table
-- - bus_stops table
-- - landuse_zones table
-- - routes table
-- - spawn_configs table
```

### Using pgAdmin:
1. Open Query Tool on your database
2. Open `scripts/migrations/001_create_geo_tables.sql`
3. Execute (F5)

### Using Python Script:
```bash
python scripts/setup_postgis_schema.py
```

---

## Step 3: Configure Strapi Database Connection

### Update `.env` file in `arknet_fleet_manager/arknet-fleet-api/`:

```bash
# Database Configuration
DATABASE_CLIENT=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=arknet_transit
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password_here
DATABASE_SSL=false

# Or use connection string (alternative)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/arknet_transit
```

**⚠️ Important:** Replace `your_password_here` with your actual PostgreSQL password!

---

## Step 4: Load Country Geographic Data

Once the schema is created, load Barbados (BRB) GeoJSON data into PostGIS:

```bash
# From project root
python scripts/load_country_geojson.py --country BRB
```

This will load:
- ✅ 1,340 bus stops
- ✅ 1,427 amenities (marketplaces, bus stations, clinics, etc.)
- ✅ 2,176+ land use zones (residential, commercial, farmland)
- ✅ Route geometries (route_1, route_1A, route_1B)

---

## Step 5: Verify Setup

Run the verification script:

```bash
python scripts/verify_postgis_setup.py
```

Expected output:
```
✅ PostGIS extension installed: 3.x.x
✅ Geographic tables created: 7 tables found
✅ Barbados (BRB) data loaded:
   - 1,340 bus stops
   - 1,427 POIs
   - 2,176 land use zones
   - 3 routes
✅ Spatial indexes created
✅ Sample spatial query successful
```

---

## Troubleshooting

### Issue: "CREATE EXTENSION IF NOT EXISTS postgis" fails

**Solution:** PostGIS might not be installed. Download and install PostGIS:
- **Download:** https://postgis.net/install/
- **Windows:** Use Stack Builder (comes with PostgreSQL installer)
  1. Run Stack Builder from Start Menu
  2. Select your PostgreSQL installation
  3. Expand "Spatial Extensions"
  4. Check "PostGIS Bundle"
  5. Install

### Issue: "permission denied to create extension"

**Solution:** You need superuser privileges:
```sql
-- Connect as superuser (postgres)
ALTER USER your_username WITH SUPERUSER;

-- Or grant specific extension creation privileges
GRANT CREATE ON DATABASE arknet_transit TO your_username;
```

### Issue: Connection refused when running Python scripts

**Solution:** Check PostgreSQL service is running:
- **Windows:** Services → PostgreSQL (should be "Running")
- Or run: `net start postgresql-x64-<version>`

### Issue: Python can't connect to database

**Solution:** Install/update psycopg2:
```bash
pip install psycopg2-binary --upgrade
```

---

## Quick Reference: Find PostgreSQL Installation

### Windows - Common Locations:
```
C:\Program Files\PostgreSQL\16\bin\psql.exe
C:\Program Files\PostgreSQL\15\bin\psql.exe
C:\Program Files\PostgreSQL\14\bin\psql.exe
```

### Add PostgreSQL to PATH (Optional):
1. Search "Environment Variables" in Windows Start Menu
2. Edit "Path" system variable
3. Add: `C:\Program Files\PostgreSQL\<version>\bin`
4. Restart terminal

---

## Architecture Summary

```
┌─────────────────────────────────────────┐
│     Strapi API (Port 1337)              │
│     - Routes, Depots, Vehicles          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  PostgreSQL Database (Port 5432)        │
│  ┌────────────────────────────────────┐ │
│  │  Strapi Schema (public)            │ │
│  │  - routes, depots, vehicles        │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  Geographic Schema (public/geo)    │ │
│  │  - countries (with PostGIS)        │ │
│  │  - regions                         │ │
│  │  - pois (bus stations, markets)    │ │
│  │  - bus_stops (1,340 for Barbados)  │ │
│  │  - landuse_zones                   │ │
│  │  - routes (geometry)               │ │
│  │  - spawn_configs                   │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                  ▲
                  │
┌─────────────────┴───────────────────────┐
│  Commuter Service (Python)              │
│  - PostGISDataProvider                  │
│  - DepotSpawningStrategy                │
│  - RouteSpawningStrategy                │
└─────────────────────────────────────────┘
```

---

## Next Steps After Setup

1. ✅ Configure `.env` with database credentials
2. ✅ Run `001_create_geo_tables.sql` migration
3. ✅ Load Barbados data with `load_country_geojson.py`
4. ✅ Verify with `verify_postgis_setup.py`
5. ✅ Start Strapi: `npm run dev`
6. ✅ Test spawning strategies with PostGIS provider

---

## Benefits of PostGIS

- 🌍 **Multi-Country Support**: Switch between countries via environment variable
- ⚡ **Performance**: Spatial indexes (ST_DWithin, ST_Contains) 1000x faster than file parsing
- 🔧 **Flexibility**: Update geographic data via SQL/API without code changes
- 📊 **Scalability**: Handle millions of geographic features efficiently
- 🧪 **Testability**: In-memory databases for unit tests
- 🎯 **Accuracy**: Real spatial calculations (distance, containment, intersection)

---

## Support

If you encounter issues:
1. Check PostgreSQL service is running
2. Verify database credentials in `.env`
3. Run `verify_postgis_setup.py` for diagnostics
4. Check logs in `arknet_fleet_manager/arknet-fleet-api/`
