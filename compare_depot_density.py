import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("COMPARING DEPOT BUILDING DENSITY")
print("=" * 80)

# Get all depots
depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={"pagination[pageSize]": 100}
)

depots = depots_response.json()['data']

results = []

for depot in depots:
    depot_name = depot.get('name', 'Unknown')
    depot_id = depot.get('id')
    lat = depot.get('latitude')
    lon = depot.get('longitude')
    
    if lat and lon:
        # Query buildings near this depot
        try:
            geospatial_response = requests.get(
                "http://localhost:6000/spatial/nearby-buildings",
                params={
                    "lat": lat,
                    "lon": lon,
                    "radius_meters": 800,
                    "limit": 5000  # Get all buildings, no artificial cap
                },
                timeout=5
            )
            
            if geospatial_response.status_code == 200:
                buildings = geospatial_response.json()
                building_count = len(buildings.get('buildings', []))
                
                results.append({
                    'name': depot_name,
                    'id': depot_id,
                    'lat': lat,
                    'lon': lon,
                    'buildings': building_count
                })
            else:
                results.append({
                    'name': depot_name,
                    'id': depot_id,
                    'lat': lat,
                    'lon': lon,
                    'buildings': 'ERROR'
                })
        except Exception as e:
            results.append({
                'name': depot_name,
                'id': depot_id,
                'lat': lat,
                'lon': lon,
                'buildings': f'ERROR: {str(e)}'
            })
    else:
        results.append({
            'name': depot_name,
            'id': depot_id,
            'lat': 'N/A',
            'lon': 'N/A',
            'buildings': 'NO LOCATION'
        })

# Sort by building count (descending)
results_with_buildings = [r for r in results if isinstance(r['buildings'], int)]
results_without_buildings = [r for r in results if not isinstance(r['buildings'], int)]
results_sorted = sorted(results_with_buildings, key=lambda x: x['buildings'], reverse=True) + results_without_buildings

print("\nDEPOT BUILDING DENSITY RANKING:\n")
print(f"{'Rank':<6} {'Depot Name':<40} {'Buildings':<12} {'Location':<30}")
print("=" * 90)

for i, result in enumerate(results_sorted, 1):
    if isinstance(result['buildings'], int):
        rank = str(i)
        buildings = f"{result['buildings']} bldgs"
        
        # Calculate spawn rate estimate
        passengers_per_building = 0.3
        hourly_rate = 1.2  # Average
        day_mult = 1.3  # Friday
        time_window = 0.1667 / 60.0
        
        lambda_param = result['buildings'] * passengers_per_building * hourly_rate * day_mult * time_window
        spawn_per_hour = lambda_param * 360  # 360 cycles per hour (10s intervals)
        
        location = f"({result['lat']:.4f}, {result['lon']:.4f})"
    else:
        rank = "-"
        buildings = result['buildings']
        spawn_per_hour = 0
        location = f"({result['lat']}, {result['lon']})"
    
    print(f"{rank:<6} {result['name']:<40} {buildings:<12} {location:<30}")
    
    if isinstance(result['buildings'], int):
        print(f"       → Estimated spawn rate: ~{spawn_per_hour:.1f} passengers/hour")

print("\n" + "=" * 80)
print("URBAN vs RURAL COMPARISON")
print("=" * 80)

# Find Cheapside (Bridgetown urban) and Speightstown (rural)
cheapside = next((r for r in results if 'Cheapside' in r['name']), None)
speightstown = next((r for r in results if 'Speightstown' in r['name']), None)

if cheapside and speightstown:
    if isinstance(cheapside['buildings'], int) and isinstance(speightstown['buildings'], int):
        print(f"\n🏙️  CHEAPSIDE (Bridgetown - Urban):")
        print(f"   Buildings within 800m: {cheapside['buildings']}")
        print(f"   Location: ({cheapside['lat']}, {cheapside['lon']})")
        
        cheapside_lambda = cheapside['buildings'] * 0.3 * 1.2 * 1.3 * (0.1667/60.0)
        cheapside_hourly = cheapside_lambda * 360
        print(f"   Estimated spawn rate: ~{cheapside_hourly:.1f} passengers/hour")
        
        print(f"\n🌾  SPEIGHTSTOWN (Rural):")
        print(f"   Buildings within 800m: {speightstown['buildings']}")
        print(f"   Location: ({speightstown['lat']}, {speightstown['lon']})")
        
        speightstown_lambda = speightstown['buildings'] * 0.3 * 1.2 * 1.3 * (0.1667/60.0)
        speightstown_hourly = speightstown_lambda * 360
        print(f"   Estimated spawn rate: ~{speightstown_hourly:.1f} passengers/hour")
        
        if cheapside['buildings'] > 0 and speightstown['buildings'] > 0:
            ratio = cheapside['buildings'] / speightstown['buildings']
            print(f"\n📊 DENSITY RATIO:")
            print(f"   Cheapside has {ratio:.2f}x the building density of Speightstown")
            print(f"   Cheapside would spawn {ratio:.2f}x more passengers")
        elif cheapside['buildings'] == speightstown['buildings']:
            print(f"\n📊 SAME DENSITY:")
            print(f"   Both depots have identical building density ({cheapside['buildings']} buildings)")
            print(f"   This is expected if they're in similar areas or if one is near a route terminus")

print("\n" + "=" * 80)
print("COMPARISON TO CURRENT DEFAULT (spatial_base=2.0)")
print("=" * 80)

print(f"""
Current depot spawning uses: spatial_base = 2.0 (hardcoded)
  Lambda = 2.0 × 1.2 × 1.3 × (0.1667/60) = 0.0087
  Spawn rate: ~3.6 passengers/hour

With GeoJSON data (using Speightstown as example):
  spatial_factor = {speightstown['buildings'] if isinstance(speightstown['buildings'], int) else 'N/A'} × 0.3 = {speightstown['buildings'] * 0.3 if isinstance(speightstown['buildings'], int) else 'N/A'}
  Lambda = {speightstown['buildings'] * 0.3 if isinstance(speightstown['buildings'], int) else 'N/A'} × 1.2 × 1.3 × (0.1667/60) = {speightstown_lambda if isinstance(speightstown['buildings'], int) else 'N/A':.4f}
  Spawn rate: ~{speightstown_hourly if isinstance(speightstown['buildings'], int) else 'N/A':.1f} passengers/hour

Improvement: {(speightstown_hourly / 3.6) if isinstance(speightstown['buildings'], int) else 'N/A'}x increase in spawn rate
""")
