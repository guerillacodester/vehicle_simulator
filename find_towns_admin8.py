import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("FINDING ADMIN LEVEL 8 (TOWNS) IN REGIONS")
print("=" * 80)

# Get ALL regions first, then filter by tags
response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={"pagination[pageSize]": 500}
)

if response.status_code == 200:
    data = response.json()
    all_regions = data.get('data', [])
    
    # Filter for admin_level=8 in tags
    towns = []
    for region in all_regions:
        tags = region.get('tags', '')
        if 'admin_level=8' in str(tags) or 'admin_level:8' in str(tags):
            towns.append(region)
    
    print(f"\nTotal regions: {len(all_regions)}")
    print(f"Towns (admin_level=8): {len(towns)}\n")
    
    if towns:
        for town in sorted(towns, key=lambda x: x.get('name', '')):
            print(f"📍 {town.get('name', 'Unknown')}")
            print(f"   ID: {town.get('id')}")
            
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
        print("No towns found with admin_level=8")
        print("\nShowing sample tags from first 5 regions:")
        for region in all_regions[:5]:
            print(f"  {region.get('name')}: {region.get('tags', 'No tags')}")
else:
    print(f"❌ Failed to query regions: {response.status_code}")
    print(response.text)
