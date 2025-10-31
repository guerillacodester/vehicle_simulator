import requests

STRAPI_URL = "http://localhost:1337"

# Get Speightstown depot
depot_doc_id = "ft3t8jc5jnzg461uod6to898"

print("=" * 80)
print("CHECKING DEPOT LOCATION DATA")
print("=" * 80)

# Get depot details with all fields
depot_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={
        "filters[documentId][$eq]": depot_doc_id,
        "pagination[pageSize]": 1
    }
)

depot_data = depot_response.json()['data']
if depot_data:
    depot = depot_data[0]
    print(f"\nDepot: {depot['name']}")
    print(f"  ID: {depot['id']}")
    print(f"  DocumentID: {depot['documentId']}")
    
    # Check for location fields
    print("\n📍 Location Data:")
    lat = depot.get('latitude')
    lon = depot.get('longitude')
    
    if lat and lon:
        print(f"  ✅ Latitude: {lat}")
        print(f"  ✅ Longitude: {lon}")
        
        print("\n" + "=" * 80)
        print("TESTING GEOSPATIAL API QUERY")
        print("=" * 80)
        
        # Test querying buildings near this depot
        geospatial_response = requests.get(
            "http://localhost:6000/spatial/nearby-buildings",
            params={
                "lat": lat,
                "lon": lon,
                "radius_meters": 800,
                "limit": 200
            }
        )
        
        if geospatial_response.status_code == 200:
            buildings = geospatial_response.json()
            building_count = len(buildings.get('buildings', []))
            
            print(f"\n✅ Geospatial API Response:")
            print(f"   Buildings found within 800m: {building_count}")
            
            if building_count > 0:
                print(f"\n   Sample buildings:")
                for i, building in enumerate(buildings.get('buildings', [])[:3], 1):
                    props = building.get('properties', {})
                    print(f"   {i}. Type: {props.get('building', 'unknown')}, "
                          f"Distance: {props.get('distance_meters', 'N/A')}m")
            
            print("\n" + "=" * 80)
            print("COMPARISON: ROUTE vs DEPOT SPAWNING")
            print("=" * 80)
            
            print(f"""
Route Spawner (Route 1):
  - Queries 6 sample points along route geometry
  - Gets buildings within 800m of each point
  - Found: 200 buildings
  - Lambda calculation: {building_count} × 0.3 × hourly × day × time_window

Depot Spawner (Speightstown) - PROPOSED:
  - Query single point at depot location ({lat}, {lon})
  - Get buildings within 800m of depot
  - Found: {building_count} buildings
  - Lambda calculation: {building_count} × 0.3 × hourly × day × time_window

This would give depot spawning approximately:
  {building_count} / 200 = {building_count/200:.1%} of route spawning rate
""")
            
        else:
            print(f"\n❌ Geospatial API error: {geospatial_response.status_code}")
            print(f"   {geospatial_response.text}")
    else:
        print("  ❌ No latitude/longitude fields found")
        print("\n  Available fields:")
        for key, value in depot.items():
            if value is not None:
                print(f"    - {key}: {value}")

print("\n" + "=" * 80)
print("DATA SOURCE FOR OPTION 1")
print("=" * 80)

print("""
Option 1 would use:
  1. Depot location (lat/lon) from Strapi database 'depots' table
  2. Buildings GeoJSON data from PostGIS via geospatial service
  3. Same query method as route spawner:
     GET http://localhost:6000/spatial/nearby-buildings
     ?lat={depot.latitude}&lon={depot.longitude}&radius_meters=800&limit=200

This requires:
  ✅ Depot has latitude/longitude fields in database
  ✅ Geospatial service has buildings data in PostGIS
  ✅ Same API endpoint used by route spawner
  
No new data sources needed - everything already exists!
""")
