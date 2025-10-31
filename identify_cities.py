import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("DEPOT LOCATIONS - IDENTIFYING CITIES BY COORDINATES")
print("=" * 80)

# Get all depots
depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={"pagination[pageSize]": 100}
)

depots = depots_response.json()['data']

# Bridgetown is roughly around 13.10 lat, -59.62 lon
# Speightstown is roughly around 13.25 lat, -59.64 lon

bridgetown_depots = []
speightstown_depots = []
other_depots = []

for depot in depots:
    lat = depot.get('latitude')
    lon = depot.get('longitude')
    name = depot.get('name', 'Unknown')
    
    if lat and lon:
        # Classify by latitude (Bridgetown is south ~13.10, Speightstown is north ~13.25)
        if lat < 13.15:
            city = "BRIDGETOWN (Capital)"
            bridgetown_depots.append(depot)
        elif lat > 13.20:
            city = "SPEIGHTSTOWN (North)"
            speightstown_depots.append(depot)
        else:
            city = "OTHER"
            other_depots.append(depot)

print("\n🏙️  BRIDGETOWN (Capital - South)")
print("=" * 80)
for depot in bridgetown_depots:
    print(f"\n  📍 {depot['name']}")
    lat = depot['latitude']
    lon = depot['longitude']
    print(f"     Location: ({lat}, {lon})")
    
    # Query buildings
    geospatial_response = requests.get(
        "http://localhost:6000/spatial/nearby-buildings",
        params={
            "lat": lat,
            "lon": lon,
            "radius_meters": 800,
            "limit": 5000
        },
        timeout=5
    )
    
    if geospatial_response.status_code == 200:
        buildings = geospatial_response.json()
        building_count = len(buildings.get('buildings', []))
        
        spatial_factor = building_count * 0.3
        lambda_param = spatial_factor * 1.2 * 1.3 * (0.1667/60.0)
        spawn_per_hour = lambda_param * 360
        
        print(f"     Buildings (800m): {building_count:,}")
        print(f"     Spawn rate: ~{spawn_per_hour:.1f} passengers/hour")

print("\n\n🌾 SPEIGHTSTOWN (North - Rural)")
print("=" * 80)
for depot in speightstown_depots:
    print(f"\n  📍 {depot['name']}")
    lat = depot['latitude']
    lon = depot['longitude']
    print(f"     Location: ({lat}, {lon})")
    
    # Query buildings
    geospatial_response = requests.get(
        "http://localhost:6000/spatial/nearby-buildings",
        params={
            "lat": lat,
            "lon": lon,
            "radius_meters": 800,
            "limit": 5000
        },
        timeout=5
    )
    
    if geospatial_response.status_code == 200:
        buildings = geospatial_response.json()
        building_count = len(buildings.get('buildings', []))
        
        spatial_factor = building_count * 0.3
        lambda_param = spatial_factor * 1.2 * 1.3 * (0.1667/60.0)
        spawn_per_hour = lambda_param * 360
        
        print(f"     Buildings (800m): {building_count:,}")
        print(f"     Spawn rate: ~{spawn_per_hour:.1f} passengers/hour")

if other_depots:
    print("\n\n📍 OTHER LOCATIONS")
    print("=" * 80)
    for depot in other_depots:
        print(f"  • {depot['name']} ({depot.get('latitude')}, {depot.get('longitude')})")

print("\n" + "=" * 80)
print("URBAN vs RURAL COMPARISON")
print("=" * 80)

if bridgetown_depots and speightstown_depots:
    # Calculate averages
    bridgetown_avg = 0
    for depot in bridgetown_depots:
        geospatial_response = requests.get(
            "http://localhost:6000/spatial/nearby-buildings",
            params={
                "lat": depot['latitude'],
                "lon": depot['longitude'],
                "radius_meters": 800,
                "limit": 5000
            },
            timeout=5
        )
        if geospatial_response.status_code == 200:
            buildings = geospatial_response.json()
            bridgetown_avg += len(buildings.get('buildings', []))
    
    bridgetown_avg = bridgetown_avg / len(bridgetown_depots) if bridgetown_depots else 0
    
    speightstown_avg = 0
    for depot in speightstown_depots:
        geospatial_response = requests.get(
            "http://localhost:6000/spatial/nearby-buildings",
            params={
                "lat": depot['latitude'],
                "lon": depot['longitude'],
                "radius_meters": 800,
                "limit": 5000
            },
            timeout=5
        )
        if geospatial_response.status_code == 200:
            buildings = geospatial_response.json()
            speightstown_avg += len(buildings.get('buildings', []))
    
    speightstown_avg = speightstown_avg / len(speightstown_depots) if speightstown_depots else 0
    
    print(f"\nBridgetown (Urban - Capital):")
    print(f"  Depots: {len(bridgetown_depots)}")
    print(f"  Avg buildings: {bridgetown_avg:.0f}")
    print(f"  Avg spawn rate: ~{bridgetown_avg * 0.3 * 1.2 * 1.3 * (0.1667/60.0) * 360:.1f} passengers/hour")
    
    print(f"\nSpeightstown (Rural - North):")
    print(f"  Depots: {len(speightstown_depots)}")
    print(f"  Avg buildings: {speightstown_avg:.0f}")
    print(f"  Avg spawn rate: ~{speightstown_avg * 0.3 * 1.2 * 1.3 * (0.1667/60.0) * 360:.1f} passengers/hour")
    
    if bridgetown_avg > 0 and speightstown_avg > 0:
        ratio = bridgetown_avg / speightstown_avg
        print(f"\nDensity Ratio: Bridgetown has {ratio:.2f}x the building density of Speightstown")
