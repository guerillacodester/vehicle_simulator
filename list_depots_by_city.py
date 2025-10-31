import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("DEPOT LOCATIONS BY CITY")
print("=" * 80)

# Get all depots with city information
depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={"pagination[pageSize]": 100}
)

depots = depots_response.json()['data']

# Group by city
depots_by_city = {}

for depot in depots:
    city = depot.get('city', 'Unknown')
    parish = depot.get('parish', 'Unknown')
    
    if city not in depots_by_city:
        depots_by_city[city] = []
    
    depots_by_city[city].append({
        'name': depot.get('name', 'Unknown'),
        'parish': parish,
        'lat': depot.get('latitude'),
        'lon': depot.get('longitude')
    })

# Print by city
for city in sorted(depots_by_city.keys()):
    print(f"\n🏙️  {city.upper()}")
    print("=" * 80)
    
    for depot in depots_by_city[city]:
        print(f"  📍 {depot['name']}")
        print(f"     Parish: {depot['parish']}")
        if depot['lat'] and depot['lon']:
            print(f"     Location: ({depot['lat']}, {depot['lon']})")
            
            # Query buildings
            try:
                geospatial_response = requests.get(
                    "http://localhost:6000/spatial/nearby-buildings",
                    params={
                        "lat": depot['lat'],
                        "lon": depot['lon'],
                        "radius_meters": 800,
                        "limit": 5000
                    },
                    timeout=5
                )
                
                if geospatial_response.status_code == 200:
                    buildings = geospatial_response.json()
                    building_count = len(buildings.get('buildings', []))
                    
                    # Calculate spawn rate
                    spatial_factor = building_count * 0.3
                    lambda_param = spatial_factor * 1.2 * 1.3 * (0.1667/60.0)
                    spawn_per_hour = lambda_param * 360
                    
                    print(f"     Buildings (800m): {building_count}")
                    print(f"     Spawn rate: ~{spawn_per_hour:.1f} passengers/hour")
            except:
                pass
        else:
            print(f"     Location: No coordinates")

print("\n" + "=" * 80)
print("SUMMARY BY CITY")
print("=" * 80)

for city in sorted(depots_by_city.keys()):
    depot_count = len(depots_by_city[city])
    print(f"{city}: {depot_count} depot(s)")
