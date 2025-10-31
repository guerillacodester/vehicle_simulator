import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("QUERYING REGIONS WITH admin_level = 'TOWNS'")
print("=" * 80)

# Get ALL regions and check for admin_level field
response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={"pagination[pageSize]": 500}
)

if response.status_code == 200:
    data = response.json()
    all_regions = data.get('data', [])
    
    # Filter for admin_level = 'TOWNS' (case insensitive)
    towns = []
    for region in all_regions:
        admin_level = region.get('admin_level', '')
        if str(admin_level).upper() == 'TOWNS' or str(admin_level) == 'town':
            towns.append(region)
    
    print(f"\nTotal regions: {len(all_regions)}")
    print(f"Regions with admin_level='TOWNS': {len(towns)}\n")
    
    if towns:
        for town in sorted(towns, key=lambda x: x.get('name', '')):
            print(f"📍 {town.get('name', 'Unknown')}")
            print(f"   ID: {town.get('id')}")
            print(f"   Admin Level: {town.get('admin_level')}")
            
            if town.get('center_latitude') and town.get('center_longitude'):
                print(f"   Center: ({town.get('center_latitude')}, {town.get('center_longitude')})")
            
            if town.get('area_sq_km'):
                print(f"   Area: {town.get('area_sq_km')} km²")
            
            if town.get('population'):
                print(f"   Population: {town.get('population'):,}")
            
            print()
    else:
        print("No regions found with admin_level='TOWNS'")
        print("\nChecking what admin_level values exist:")
        admin_levels = set()
        for region in all_regions:
            admin_level = region.get('admin_level')
            if admin_level:
                admin_levels.add(str(admin_level))
        
        if admin_levels:
            print(f"Found admin_level values: {sorted(admin_levels)}")
        else:
            print("No admin_level field found in any region")
            print("\nShowing all fields from first region:")
            if all_regions:
                print(f"Fields: {list(all_regions[0].keys())}")
else:
    print(f"❌ Failed to query regions: {response.status_code}")
    print(response.text)
