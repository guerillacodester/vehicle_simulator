"""
Create route-specific spawn configuration for Route 1 (St Lucy Rural)
Adjusts temporal rates for rural area - lower early morning demand
"""
import requests
import json

API_BASE = "http://localhost:1337/api"

# Fetch existing spawn config to use as template
response = requests.get(f"{API_BASE}/spawn-configs/2?populate=*")
if response.status_code != 200:
    print(f"Failed to fetch template: {response.status_code}")
    print("Trying to fetch by documentId...")
    response = requests.get(f"{API_BASE}/spawn-configs?populate=*")
    configs = response.json()['data']
    template = configs[0] if configs else None
    if not template:
        print("No spawn configs found!")
        exit(1)
else:
    template = response.json()['data']

print(f"Using template: {template.get('name', 'Unknown')}")
print()

# Create new spawn config for Route 1 with rural-appropriate temporal rates
route1_config = {
    "name": "Route 1 - St Lucy Rural",
    "description": "Rural spawn configuration for Route 1 (St Lucy to St Peter) - Lower early morning rates suitable for rural areas",
    "is_active": True,
    
    # Copy building weights from template
    "building_weights": template['building_weights'],
    
    # Copy POI weights from template  
    "poi_weights": template['poi_weights'],
    
    # Copy landuse weights from template
    "landuse_weights": template.get('landuse_weights', []),
    
    # ADJUSTED hourly spawn rates for rural area
    "hourly_spawn_rates": [
        {"hour": 0, "spawn_rate": 0.1},   # Midnight - very low
        {"hour": 1, "spawn_rate": 0.1},   # 1 AM - very low
        {"hour": 2, "spawn_rate": 0.1},   # 2 AM - very low
        {"hour": 3, "spawn_rate": 0.1},   # 3 AM - very low
        {"hour": 4, "spawn_rate": 0.15},  # 4 AM - minimal (was 0.3)
        {"hour": 5, "spawn_rate": 0.4},   # 5 AM - low (was 0.8, reduced for rural)
        {"hour": 6, "spawn_rate": 0.6},   # 6 AM - ADJUSTED for rural (was 1.5, now ~16 passengers)
        {"hour": 7, "spawn_rate": 1.2},   # 7 AM - moderate morning (was 2.8, reduced for rural)
        {"hour": 8, "spawn_rate": 1.8},   # 8 AM - morning peak rural (was 2.8)
        {"hour": 9, "spawn_rate": 1.2},   # 9 AM - post-peak (was 2.0, reduced)
        {"hour": 10, "spawn_rate": 1.0},  # 10 AM - mid-morning
        {"hour": 11, "spawn_rate": 1.0},  # 11 AM - late morning
        {"hour": 12, "spawn_rate": 1.2},  # 12 PM - lunch (was 1.3, adjusted up)
        {"hour": 13, "spawn_rate": 1.2},  # 1 PM - early afternoon (was 0.9, adjusted up)
        {"hour": 14, "spawn_rate": 1.0},  # 2 PM - afternoon
        {"hour": 15, "spawn_rate": 1.3},  # 3 PM - school/afternoon
        {"hour": 16, "spawn_rate": 1.5},  # 4 PM - late afternoon
        {"hour": 17, "spawn_rate": 1.8},  # 5 PM - evening peak rural (was 2.3, reduced)
        {"hour": 18, "spawn_rate": 1.2},  # 6 PM - early evening
        {"hour": 19, "spawn_rate": 0.8},  # 7 PM - evening
        {"hour": 20, "spawn_rate": 0.5},  # 8 PM - late evening
        {"hour": 21, "spawn_rate": 0.3},  # 9 PM - night
        {"hour": 22, "spawn_rate": 0.2},  # 10 PM - night
        {"hour": 23, "spawn_rate": 0.1}   # 11 PM - night
    ],
    
    # Copy day multipliers from template
    "day_multipliers": template['day_multipliers'],
    
    # Copy distribution params from template
    "distribution_params": template['distribution_params'],
    
    # Link to Route 1 (ID 14)
    "route": 14
}

# Create the spawn config
print("Creating Route 1 - St Lucy Rural spawn configuration...")
print(f"  Route ID: 14")
print(f"  Hour 6 rate: 0.6 (was 1.5)")
print(f"  Hour 7 rate: 1.2 (was 2.8)")
print(f"  Expected 6 AM spawns: ~16 passengers (was 48)")
print()

response = requests.post(
    f"{API_BASE}/spawn-configs",
    json={"data": route1_config},
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200 or response.status_code == 201:
    result = response.json()
    print(f"✅ SUCCESS! Created spawn-config ID: {result['data']['id']}")
    print(f"   Name: {result['data']['name']}")
    print()
    print("Verification:")
    print(f"  - Building weights: {len(result['data']['building_weights'])}")
    print(f"  - POI weights: {len(result['data']['poi_weights'])}")
    print(f"  - Hourly rates: {len(result['data']['hourly_spawn_rates'])}")
    print(f"  - Linked to route: {result['data'].get('route', 'N/A')}")
else:
    print(f"❌ FAILED: {response.status_code}")
    print(response.text)
