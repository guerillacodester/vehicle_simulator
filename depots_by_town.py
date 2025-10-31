import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("DEPOTS BY TOWN - BUILDING DENSITY COMPARISON")
print("=" * 80)

# Get towns
towns_response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={
        "populate": "admin_level",
        "pagination[pageSize]": 500
    }
)

towns = []
if towns_response.status_code == 200:
    all_regions = towns_response.json().get('data', [])
    for region in all_regions:
        admin_level = region.get('admin_level')
        if admin_level and admin_level.get('name', '').upper() in ['TOWN', 'TOWNS']:
            towns.append(region)

# Get depots
depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={"pagination[pageSize]": 100}
)

depots = depots_response.json().get('data', [])

print(f"\n🏙️  TOWNS IN BARBADOS: {len(towns)}")
print(f"📍 ACTIVE DEPOTS: {len(depots)}\n")

# Match depots to towns (simple proximity check)
depot_assignments = {}

for depot in depots:
    depot_lat = depot.get('latitude')
    depot_lon = depot.get('longitude')
    depot_name = depot.get('name')
    
    if not (depot_lat and depot_lon):
        continue
    
    # Find closest town
    closest_town = None
    min_distance = float('inf')
    
    for town in towns:
        town_lat = town.get('center_latitude')
        town_lon = town.get('center_longitude')
        town_name = town.get('name')
        
        if town_lat and town_lon:
            # Simple distance calculation
            distance = ((depot_lat - town_lat)**2 + (depot_lon - town_lon)**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_town = town_name
    
    if closest_town:
        if closest_town not in depot_assignments:
            depot_assignments[closest_town] = []
        depot_assignments[closest_town].append({
            'name': depot_name,
            'lat': depot_lat,
            'lon': depot_lon
        })

# Now query building density for each town's depots
for town_name in sorted(depot_assignments.keys()):
    print(f"\n{'='*80}")
    print(f"🏙️  {town_name.upper()}")
    print(f"{'='*80}")
    
    town_depots = depot_assignments[town_name]
    print(f"\nDepots in {town_name}: {len(town_depots)}")
    
    for depot in town_depots:
        print(f"\n  📍 {depot['name']}")
        print(f"     Location: ({depot['lat']}, {depot['lon']})")
        
        # Query buildings
        try:
            geo_response = requests.get(
                "http://localhost:6000/spatial/nearby-buildings",
                params={
                    "lat": depot['lat'],
                    "lon": depot['lon'],
                    "radius_meters": 800,
                    "limit": 5000
                },
                timeout=5
            )
            
            if geo_response.status_code == 200:
                buildings = geo_response.json()
                building_count = len(buildings.get('buildings', []))
                
                spatial_factor = building_count * 0.3
                lambda_param = spatial_factor * 1.2 * 1.3 * (0.1667/60.0)
                spawn_per_hour = lambda_param * 360
                
                print(f"     Buildings (800m): {building_count:,}")
                print(f"     Spawn rate: ~{spawn_per_hour:.1f} passengers/hour")
        except Exception as e:
            print(f"     Error querying buildings: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n✅ Found {len(towns)} towns with {len(depots)} total depots")
print(f"✅ Building density data retrieved for depot spawn calculations")
