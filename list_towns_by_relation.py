import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("QUERYING REGIONS WITH admin_level RELATION POPULATED")
print("=" * 80)

# Get regions with admin_level relation populated
response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={
        "populate": "admin_level",
        "pagination[pageSize]": 500
    }
)

if response.status_code == 200:
    data = response.json()
    all_regions = data.get('data', [])
    
    # Filter for admin_level = 'TOWNS'
    towns = []
    for region in all_regions:
        admin_level = region.get('admin_level')
        if admin_level:
            level_name = admin_level.get('name', '').upper()
            if level_name == 'TOWNS' or level_name == 'TOWN':
                towns.append(region)
    
    print(f"\nTotal regions: {len(all_regions)}")
    print(f"Regions with admin_level='TOWNS': {len(towns)}\n")
    
    if towns:
        for town in sorted(towns, key=lambda x: x.get('name', '')):
            print(f"📍 {town.get('name', 'Unknown')}")
            print(f"   ID: {town.get('id')}")
            print(f"   DocumentID: {town.get('documentId')}")
            
            admin_level = town.get('admin_level', {})
            if admin_level:
                print(f"   Admin Level: {admin_level.get('name')} (ID: {admin_level.get('id')})")
            
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
        admin_levels = {}
        for region in all_regions:
            admin_level = region.get('admin_level')
            if admin_level:
                level_name = admin_level.get('name', 'Unknown')
                if level_name not in admin_levels:
                    admin_levels[level_name] = 0
                admin_levels[level_name] += 1
        
        if admin_levels:
            print("\nAdmin levels found:")
            for level, count in sorted(admin_levels.items()):
                print(f"  {level}: {count} regions")
        else:
            print("No admin_level relations found")
else:
    print(f"❌ Failed to query regions: {response.status_code}")
    print(response.text)
