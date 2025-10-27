import requests
import json

# Get spawn-config 11 with populated components
r = requests.get('http://localhost:1337/api/spawn-configs?filters[name][$eq]=Route 1 - St Lucy Rural&populate[building_weights]=*&populate[poi_weights]=*&populate[landuse_weights]=*&populate[hourly_spawn_rates]=*&populate[day_multipliers]=*&populate[distribution_params]=*')

print(f"Status: {r.status_code}\n")

if r.status_code == 200:
    data = r.json()
    if data.get('data') and len(data['data']) > 0:
        config = data['data'][0]
        print(f"Config: {config.get('name')}")
        print(f"ID: {config.get('id')}")
        print(f"documentId: {config.get('documentId')}")
        print(f"\nComponent counts:")
        print(f"  building_weights: {len(config.get('building_weights', []))}")
        print(f"  poi_weights: {len(config.get('poi_weights', []))}")
        print(f"  landuse_weights: {len(config.get('landuse_weights', []))}")
        print(f"  hourly_spawn_rates: {len(config.get('hourly_spawn_rates', []))}")
        print(f"  day_multipliers: {len(config.get('day_multipliers', []))}")
        print(f"  distribution_params: {len(config.get('distribution_params', []))}")
        
        print(f"\nday_multipliers content:")
        for dm in config.get('day_multipliers', []):
            print(f"  {dm}")
        
        print(f"\npoi_weights content:")
        for pw in config.get('poi_weights', []):
            print(f"  {pw}")
    else:
        print("No data found")
        print(json.dumps(data, indent=2))
else:
    print(f"Error: {r.text}")
