import requests
import json

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("EXAMINING ALL REGIONS - FULL DATA")
print("=" * 80)

# Get ALL regions with all fields
response = requests.get(
    f"{STRAPI_URL}/api/regions",
    params={"pagination[pageSize]": 500}
)

if response.status_code == 200:
    data = response.json()
    all_regions = data.get('data', [])
    
    print(f"\nTotal regions: {len(all_regions)}\n")
    
    for region in all_regions:
        print(f"{'='*80}")
        print(f"REGION: {region.get('name', 'Unknown')}")
        print(f"{'='*80}")
        print(json.dumps(region, indent=2))
        print()
else:
    print(f"❌ Failed to query regions: {response.status_code}")
    print(response.text)
