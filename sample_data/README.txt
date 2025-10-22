# Sample Data

This folder contains GeoJSON files used to design and build the Strapi content types and PostGIS database schema.

**Purpose:**
- Reference files for database schema design
- Sample data structure for GTFS and custom tables
- Used to create Strapi content types with proper field definitions

**Contents:**
- GTFS standard files (routes, stops, shapes, etc.)
- Custom geographic data (landuse zones, POIs, regions)
- Population and activity data

**Note:** 
These files are for schema design only. The actual system loads data via Strapi REST API from PostGIS database, not from local files.
