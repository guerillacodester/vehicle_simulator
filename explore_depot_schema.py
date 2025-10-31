import requests
import json

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("EXPLORING DEPOT DATABASE SCHEMA")
print("=" * 80)

# Get a sample depot with all fields
depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={
        "pagination[pageSize]": 1,
        "populate": "*"  # Get all relations
    }
)

depot_data = depots_response.json()

print("\nSample Depot Data Structure:")
print(json.dumps(depot_data, indent=2))

print("\n" + "=" * 80)
print("CHECKING ADMIN REGIONS / PARISHES")
print("=" * 80)

# Check if there's a parishes or admin-regions endpoint
for endpoint in ['parishes', 'admin-regions', 'regions', 'towns', 'cities']:
    try:
        response = requests.get(f"{STRAPI_URL}/api/{endpoint}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Found endpoint: /api/{endpoint}")
            print(f"   Count: {len(data.get('data', []))}")
            if data.get('data'):
                print(f"   Sample: {data['data'][0].get('name', 'N/A')}")
        else:
            print(f"❌ /api/{endpoint}: {response.status_code}")
    except Exception as e:
        print(f"❌ /api/{endpoint}: {str(e)}")

print("\n" + "=" * 80)
print("ALL DEPOTS WITH AVAILABLE FIELDS")
print("=" * 80)

# Get all depots
all_depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={
        "pagination[pageSize]": 100,
        "populate": "*"
    }
)

all_depots = all_depots_response.json()['data']

for depot in all_depots:
    print(f"\n📍 {depot.get('name', 'Unknown')}")
    
    # Print all available fields
    for key, value in depot.items():
        if value is not None and key not in ['id', 'documentId', 'createdAt', 'updatedAt', 'publishedAt']:
            print(f"   {key}: {value}")
