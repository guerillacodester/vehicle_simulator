import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("ALL REGIONS (TOWNS) IN DATABASE")
print("=" * 80)

# Get all regions
response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={"pagination[pageSize]": 100}
)

if response.status_code == 200:
    data = response.json()
    regions = data.get('data', [])
    
    print(f"\nTotal regions: {len(regions)}\n")
    
    for region in regions:
        print(f"📍 {region.get('name', 'Unknown')}")
        print(f"   ID: {region.get('id')}")
        print(f"   DocumentID: {region.get('documentId')}")
        
        if region.get('description'):
            print(f"   Description: {region.get('description')}")
        
        if region.get('center_latitude') and region.get('center_longitude'):
            print(f"   Center: ({region.get('center_latitude')}, {region.get('center_longitude')})")
        
        if region.get('area_sq_km'):
            print(f"   Area: {region.get('area_sq_km')} km²")
        
        if region.get('population'):
            print(f"   Population: {region.get('population'):,}")
        
        if region.get('tags'):
            print(f"   Tags: {region.get('tags')}")
        
        print()
else:
    print(f"❌ Failed to query regions: {response.status_code}")
    print(response.text)
