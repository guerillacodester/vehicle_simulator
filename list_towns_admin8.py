import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("QUERYING ADMIN LEVEL 8 (TOWNS)")
print("=" * 80)

# Get regions filtered by admin_level = 8
response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={
        "filters[tags][$contains]": "admin_level=8",
        "pagination[pageSize]": 200
    }
)

if response.status_code == 200:
    data = response.json()
    towns = data.get('data', [])
    
    print(f"\nTotal towns (admin_level=8): {len(towns)}\n")
    
    for town in sorted(towns, key=lambda x: x.get('name', '')):
        print(f"📍 {town.get('name', 'Unknown')}")
        print(f"   ID: {town.get('id')}")
        print(f"   DocumentID: {town.get('documentId')}")
        
        if town.get('center_latitude') and town.get('center_longitude'):
            print(f"   Center: ({town.get('center_latitude')}, {town.get('center_longitude')})")
        
        if town.get('area_sq_km'):
            print(f"   Area: {town.get('area_sq_km')} km²")
        
        if town.get('population'):
            print(f"   Population: {town.get('population'):,}")
        
        if town.get('tags'):
            print(f"   Tags: {town.get('tags')}")
        
        print()
else:
    print(f"❌ Failed to query regions: {response.status_code}")
    print(response.text)
