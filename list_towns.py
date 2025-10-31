import requests
import json

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("QUERYING ADMIN REGIONS DEFINED AS 'TOWN'")
print("=" * 80)

# Get admin regions filtered by type = 'town'
response = requests.get(
    f"{STRAPI_URL}/api/admin-regions",
    params={
        "filters[type][$eq]": "town",
        "pagination[pageSize]": 100
    }
)

if response.status_code == 200:
    data = response.json()
    towns = data.get('data', [])
    
    print(f"\nFound {len(towns)} towns in admin-regions:\n")
    
    for town in towns:
        print(f"📍 {town.get('name', 'Unknown')}")
        print(f"   ID: {town.get('id')}")
        print(f"   DocumentID: {town.get('documentId')}")
        print(f"   Type: {town.get('type', 'N/A')}")
        
        # Check for other fields
        if town.get('parish'):
            print(f"   Parish: {town.get('parish')}")
        if town.get('population'):
            print(f"   Population: {town.get('population')}")
        
        print()
else:
    print(f"❌ Failed to query admin-regions: {response.status_code}")
    print(response.text)

print("=" * 80)
print("NOW CHECKING WHICH DEPOTS ARE IN THESE TOWNS")
print("=" * 80)

# Get all depots with admin_region populated
depots_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={
        "populate": "admin_region",
        "pagination[pageSize]": 100
    }
)

if depots_response.status_code == 200:
    depots_data = depots_response.json()
    depots = depots_data.get('data', [])
    
    # Group depots by town
    depots_by_town = {}
    
    for depot in depots:
        admin_region = depot.get('admin_region')
        
        if admin_region:
            town_name = admin_region.get('name', 'Unknown')
            town_type = admin_region.get('type', 'N/A')
            
            if town_type == 'town':
                if town_name not in depots_by_town:
                    depots_by_town[town_name] = []
                
                depots_by_town[town_name].append({
                    'name': depot.get('name'),
                    'lat': depot.get('latitude'),
                    'lon': depot.get('longitude')
                })
    
    if depots_by_town:
        print("\n🏘️  DEPOTS BY TOWN:")
        for town_name in sorted(depots_by_town.keys()):
            print(f"\n{town_name}:")
            for depot in depots_by_town[town_name]:
                print(f"  • {depot['name']}")
                if depot['lat'] and depot['lon']:
                    print(f"    Location: ({depot['lat']}, {depot['lon']})")
    else:
        print("\n⚠️  No depots found linked to towns")
        print("   Depots might not have admin_region relation populated")
else:
    print(f"❌ Failed to query depots: {depots_response.status_code}")
