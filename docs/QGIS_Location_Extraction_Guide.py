"""
QGIS Location Data Extraction Guide

This guide shows how to extract location names from various sources in QGIS
and export them as GeoJSON for the passenger simulation system.
"""

# QGIS Location Data Extraction Methods

EXTRACTION_METHODS = """
🗺️ QGIS LOCATION DATA EXTRACTION GUIDE
=====================================

METHOD 1: OpenStreetMap Data via QuickOSM Plugin
-----------------------------------------------
1. Install QuickOSM Plugin:
   - Plugins → Manage and Install Plugins → Search "QuickOSM" → Install

2. Extract Points of Interest (POI):
   - Vector → QuickOSM → QuickOSM
   - Key: "amenity" 
   - Value: leave blank (gets all amenities)
   - In: select your area (draw bbox around Route 1)
   - Run Query

3. Common OSM Amenity Types for Passenger Generation:
   - amenity=hospital, clinic, pharmacy (Healthcare)
   - amenity=school, university, college (Education)  
   - amenity=bank, post_office, town_hall (Government)
   - amenity=restaurant, cafe, pub, bar (Commercial)
   - amenity=place_of_worship (Religious)
   - amenity=fuel, bus_station (Transport)

4. Export Results:
   - Right-click layer → Export → Save Features As
   - Format: GeoJSON
   - File name: barbados_amenities.geojson


METHOD 2: Building/Address Data  
------------------------------
1. Get Building Footprints:
   - QuickOSM: Key="building", Value="" (all buildings)
   - or Key="addr:housenumber" (addressed buildings)

2. Get Place Names:
   - QuickOSM: Key="name" (named places)
   - Key="place", Value="village,hamlet,suburb" (settlements)

3. Combine Queries:
   - Run multiple QuickOSM queries
   - Merge layers: Vector → Data Management Tools → Merge Vector Layers


METHOD 3: Google My Maps Import
------------------------------
1. Create Google My Map with local knowledge
2. Add points for known locations around route
3. Export as KML
4. Import KML to QGIS: Layer → Add Layer → Add Vector Layer
5. Export as GeoJSON


METHOD 4: Manual Digitizing in QGIS
----------------------------------  
1. Add Basemap:
   - Browser Panel → XYZ Tiles → OpenStreetMap
   - or Plugin → QuickMapServices → Google Satellite

2. Create New Layer:
   - Layer → Create Layer → New Shapefile Layer
   - Geometry: Point
   - Add fields: name (Text), type (Text), category (Text)

3. Toggle Editing:
   - Right-click layer → Toggle Editing
   - Add Point Feature tool
   - Click map locations, enter attributes

4. Save and Export as GeoJSON


METHOD 5: Import Existing Data
-----------------------------
1. CSV/Excel with Coordinates:
   - Prepare: Name, Latitude, Longitude, Type columns
   - Layer → Add Layer → Add Delimited Text Layer
   - Set coordinate fields, CRS (WGS84)

2. Government GIS Data:
   - Check Barbados GIS portal for official POI data
   - Import shapefiles/KML directly

3. GPS Survey Data:
   - Import GPX tracks/waypoints from field surveys


RECOMMENDED WORKFLOW FOR ROUTE 1:
=================================

Step 1: Install QuickOSM Plugin
Step 2: Define Route 1 Study Area
   - Draw polygon around route corridor (~1km buffer)
   - Save as "route1_study_area.gpkg"

Step 3: Extract OSM Amenities  
   - QuickOSM queries for each amenity type
   - Save all to same GeoPackage with different layers

Step 4: Manual Quality Check
   - Review extracted points on map
   - Add missing important locations manually  
   - Remove irrelevant/duplicate points

Step 5: Standardize Attributes
   - Ensure consistent "name" field
   - Add "passenger_type" field:
     * residential, commercial, educational, healthcare, 
     * government, religious, recreation, industrial, transport

Step 6: Export Final GeoJSON
   - Select all relevant layers
   - Export → GeoJSON for passenger simulation


SAMPLE QGIS PYTHON SCRIPT:
==========================
"""

def create_qgis_extraction_script():
    """Create a Python script that can be run in QGIS Python Console"""
    
    script = """
# QGIS Python Console Script for Location Extraction
# Copy and paste this into QGIS Python Console (Plugins → Python Console)

import processing

# Define study area (Barbados Route 1 bounding box)
# Adjust these coordinates to your actual route area
bbox = '-59.65,-59.61,13.10,13.29'  # left,right,bottom,top

# List of OSM amenity queries to run
amenity_queries = [
    ('healthcare', 'hospital clinic pharmacy medical'),
    ('education', 'school university college kindergarten'),  
    ('government', 'townhall post_office police fire_station'),
    ('commercial', 'restaurant cafe shop supermarket bank'),
    ('transport', 'bus_station fuel parking ferry_terminal'),
    ('religious', 'place_of_worship'),
    ('recreation', 'pub bar cinema theatre park')
]

# Create output GeoPackage
output_gpkg = 'C:/temp/route1_locations.gpkg'

for category, amenities in amenity_queries:
    print(f"Extracting {category} locations...")
    
    # Run QuickOSM query
    result = processing.run("quickosm:buildqueryextent", {
        'KEY': 'amenity',
        'VALUE': amenities.replace(' ', '|'),  # OR query
        'EXTENT': bbox,
        'OUTPUT': f'{output_gpkg}|layername={category}'
    })
    
    print(f"  Found {result['OUTPUT_POINTS'].featureCount()} {category} locations")

print("\\nExtraction complete! Check layers in:", output_gpkg)
print("\\nNext steps:")
print("1. Review and clean data in QGIS")  
print("2. Add missing locations manually")
print("3. Export as GeoJSON for passenger simulation")
"""
    
    return script

if __name__ == "__main__":
    print(EXTRACTION_METHODS)
    print("\n" + "="*50)
    print(create_qgis_extraction_script())