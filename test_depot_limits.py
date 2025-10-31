import requests

STRAPI_URL = "http://localhost:1337"

print("=" * 80)
print("DEPOT BUILDING DENSITY - UNLIMITED QUERY")
print("=" * 80)

# Test depots
test_depots = [
    {"name": "Cheapside (Bridgetown - Urban)", "doc_id": "oih17pz9dzkehtvhfncbtvad"},
    {"name": "Speightstown (Rural)", "doc_id": "ft3t8jc5jnzg461uod6to898"}
]

for test_depot in test_depots:
    # Get depot details
    depot_response = requests.get(
        f"{STRAPI_URL}/api/depots",
        params={
            "filters[documentId][$eq]": test_depot['doc_id'],
            "pagination[pageSize]": 1
        }
    )
    
    depot_data = depot_response.json()['data']
    if depot_data:
        depot = depot_data[0]
        lat = depot.get('latitude')
        lon = depot.get('longitude')
        
        print(f"\n{'='*80}")
        print(f"{test_depot['name']}")
        print(f"  Location: ({lat}, {lon})")
        print(f"{'='*80}")
        
        # Test different limits
        for limit in [200, 500, 1000, 5000]:
            try:
                geospatial_response = requests.get(
                    "http://localhost:6000/spatial/nearby-buildings",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "radius_meters": 800,
                        "limit": limit
                    },
                    timeout=10
                )
                
                if geospatial_response.status_code == 200:
                    buildings = geospatial_response.json()
                    building_count = len(buildings.get('buildings', []))
                    
                    # Calculate spawn rate
                    spatial_factor = building_count * 0.3
                    lambda_param = spatial_factor * 1.2 * 1.3 * (0.1667/60.0)
                    spawn_per_hour = lambda_param * 360
                    
                    print(f"  Limit={limit:<5} → {building_count:>4} buildings | "
                          f"spawn rate: ~{spawn_per_hour:.1f} pass/hr | "
                          f"lambda: {lambda_param:.4f}")
                    
                    # If we didn't hit the limit, no need to test higher
                    if building_count < limit:
                        print(f"  ✅ True count found: {building_count} buildings (didn't hit limit)")
                        break
                else:
                    print(f"  Limit={limit:<5} → ERROR: {geospatial_response.status_code}")
            except Exception as e:
                print(f"  Limit={limit:<5} → ERROR: {str(e)}")
                break

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

print("""
Based on the results above:

1. If both depots hit the limit at 200, they likely both have >200 buildings
   → Can't distinguish urban vs rural with current limit
   → Should increase API limit or use density calculation

2. If one hits limit and other doesn't, we see true density difference
   → Use that building count for spawn rate calculation

3. For production, recommend:
   - Use limit=1000 or remove limit for accurate counts
   - OR use building density calculation (buildings per km²)
   - OR query smaller radius (400m) to stay under limit
""")
