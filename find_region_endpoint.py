import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("SEARCHING FOR ADMIN/REGION RELATED ENDPOINTS")
print("=" * 80)

# Try different possible endpoint names
possible_endpoints = [
    'admin-regions',
    'adminregions', 
    'regions',
    'administrative-regions',
    'parishes',
    'towns',
    'cities',
    'locations',
    'geographic-regions',
    'areas'
]

found_endpoints = []

for endpoint in possible_endpoints:
    try:
        response = requests.get(f"{STRAPI_URL}/api/{endpoint}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            count = len(data.get('data', []))
            found_endpoints.append(endpoint)
            print(f"✅ /api/{endpoint} - {count} records")
            
            # Show sample if available
            if data.get('data'):
                sample = data['data'][0]
                print(f"   Sample: {sample.get('name', sample.get('id', 'N/A'))}")
                print(f"   Fields: {list(sample.keys())}")
        elif response.status_code == 404:
            print(f"❌ /api/{endpoint} - Not Found")
        else:
            print(f"⚠️  /api/{endpoint} - Status {response.status_code}")
    except Exception as e:
        print(f"❌ /api/{endpoint} - Error: {str(e)[:50]}")

print("\n" + "=" * 80)
print("CHECKING DEPOT SCHEMA FOR REGION FIELDS")
print("=" * 80)

# Get a depot without populate to see base fields
depot_response = requests.get(
    f"{STRAPI_URL}/api/depots",
    params={"pagination[pageSize]": 1}
)

if depot_response.status_code == 200:
    depot_data = depot_response.json()
    if depot_data.get('data'):
        depot = depot_data['data'][0]
        print("\nDepot fields:")
        for key in sorted(depot.keys()):
            value = depot[key]
            if value is not None:
                print(f"  • {key}: {type(value).__name__} = {str(value)[:50]}")
