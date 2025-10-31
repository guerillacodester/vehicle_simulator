import requests

STRAPI_URL = "http://localhost:1337"

# Get Speightstown depot
depot_doc_id = "ft3t8jc5jnzg461uod6to898"

print("=" * 80)
print("CHECKING DEPOT SPAWN CONFIGURATION")
print("=" * 80)

# Get depot details
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
    print(f"  Code: {depot.get('depot_code', 'N/A')}")

# Check for spawn config linked to this depot
print("\n" + "=" * 80)
print("CHECKING FOR DEPOT SPAWN CONFIG IN DATABASE")
print("=" * 80)

spawn_config_response = requests.get(
    f"{STRAPI_URL}/api/spawn-configs",
    params={
        "filters[depot][documentId][$eq]": depot_doc_id,
        "populate": "*",
        "pagination[pageSize]": 100
    }
)

spawn_configs = spawn_config_response.json()['data']

if spawn_configs:
    print(f"\n✅ Found {len(spawn_configs)} spawn configuration(s) for this depot:\n")
    for config in spawn_configs:
        print(f"Config ID: {config['id']}")
        print(f"Config Name: {config.get('config_name', 'N/A')}")
        print(f"DocumentID: {config['documentId']}")
        
        # Get the config content
        spawn_config_json = config.get('spawn_config')
        if spawn_config_json:
            import json
            print("\nConfiguration details:")
            dist_params = spawn_config_json.get('distribution_params', {})
            print(f"  spatial_base: {dist_params.get('spatial_base', 'N/A')}")
            print(f"  passengers_per_building_per_hour: {dist_params.get('passengers_per_building_per_hour', 'N/A')}")
            
            hourly_rates = spawn_config_json.get('hourly_rates', {})
            if hourly_rates:
                print(f"  hourly_rates: {len(hourly_rates)} hours defined")
                print(f"    Peak hours: 8am={hourly_rates.get('8', 'N/A')}, 5pm={hourly_rates.get('17', 'N/A')}")
            
            day_mults = spawn_config_json.get('day_multipliers', {})
            if day_mults:
                print(f"  day_multipliers: {len(day_mults)} days defined")
                print(f"    Weekday={day_mults.get('0', 'N/A')}, Weekend={day_mults.get('6', 'N/A')}")
else:
    print("\n❌ NO spawn configuration found for this depot")
    print("   The spawner will use DEFAULT configuration")

# Show what the default configuration is
print("\n" + "=" * 80)
print("DEFAULT DEPOT SPAWN CONFIGURATION (hardcoded in spawner)")
print("=" * 80)

print("""
distribution_params:
  spatial_base: 2.0
  hourly_rates:
    6am: 0.8, 7am: 1.2, 8am: 1.5 (morning rush)
    9am: 1.0, 10am: 0.6, 11am: 0.5
    12pm: 0.7, 1pm: 0.6, 2pm: 0.5
    3pm: 0.6, 4pm: 0.8, 5pm: 1.3 (evening rush)
    6pm: 1.2, 7pm: 0.9, 8pm: 0.5
  day_multipliers:
    Monday: 1.2, Tue-Thu: 1.1, Friday: 1.3
    Saturday: 0.4, Sunday: 0.3
""")

print("\n" + "=" * 80)
print("CALCULATION BREAKDOWN")
print("=" * 80)

print("""
Current calculation for depot:
  Lambda = spatial_base × hourly_rate × day_multiplier × (time_window / 60.0)
  Lambda = 2.0 × 1.2 × 1.3 × (0.1667 / 60.0)
  Lambda = 2.0 × 1.2 × 1.3 × 0.00278
  Lambda = 0.0087 ≈ 0.01

This means approximately 0.01 passengers per 10-second cycle.
Over 1 hour (360 cycles): 0.01 × 360 = 3.6 passengers/hour

Compare to Route spawner:
  Lambda = building_count × pass/bldg × hourly × day × (time_window / 60.0)
  Lambda = 200 × 0.3 × 1.5 × 1.3 × 0.00278
  Lambda = 0.325

This means approximately 0.32 passengers per 10-second cycle.
Over 1 hour (360 cycles): 0.32 × 360 = 115 passengers/hour
""")

print("\n" + "=" * 80)
print("ROOT CAUSE")
print("=" * 80)

print("""
The depot spawner uses a FIXED spatial_base=2.0, while the route spawner 
uses ACTUAL GEOJSON DATA (200 buildings × 0.3 passengers/building = 60 base rate).

This is why depot spawning is so low:
  - Depot: spatial_base = 2.0 (arbitrary constant)
  - Route: spatial_factor = 60.0 (data-driven: 200 buildings × 0.3)

The depot spawner needs to either:
  1. Use GeoJSON building data near the depot (like route spawner)
  2. Have a much higher spatial_base constant (e.g., 50-100)
  3. Have depot-specific spawn configurations in the database
""")
