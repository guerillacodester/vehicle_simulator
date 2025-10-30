"""
Quick manual test of GeospatialClient

Run this to verify the client works before running full pytest suite.
Requires: Geospatial API running at http://localhost:6000

Usage:
    python -m geospatial_service.tests.test_client_manual
"""

import sys
sys.path.insert(0, ".")

from geospatial_service.geospatial_client import GeospatialClient

def main():
    print("🧪 Testing GeospatialClient (Phase 1.12, Step 1)\n")
    
    # Test 1: Client initialization
    print("Test 1: Initializing client...")
    try:
        client = GeospatialClient(base_url="http://localhost:6000")
        print("✅ Client created successfully\n")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        print("   Make sure geospatial API is running: python geospatial_service/main.py")
        return
    
    # Test 2: Reverse geocoding
    print("Test 2: Reverse geocoding Bridgetown center...")
    try:
        result = client.reverse_geocode(
            latitude=13.0969,
            longitude=-59.6145
        )
        print(f"✅ Address: {result['address']}")
        print(f"   Latency: {result.get('latency_ms', 'N/A')}ms")
        if result.get('highway'):
            print(f"   Highway: {result['highway']['name']}")
        if result.get('parish'):
            print(f"   Parish: {result['parish']['name']}")
        print()
    except Exception as e:
        print(f"❌ Reverse geocode failed: {e}\n")
    
    # Test 3: Geofence check
    print("Test 3: Geofence check...")
    try:
        result = client.check_geofence(
            latitude=13.0969,
            longitude=-59.6145
        )
        if result['inside_region']:
            print(f"✅ Inside region: {result['region']['name']}")
            print(f"   Region type: {result['region']['region_type']}")
            print(f"   Latency: {result.get('latency_ms', 'N/A')}ms")
        else:
            print("⚠️ Point not in any region")
        if result['inside_landuse']:
            print(f"   Inside landuse: {result['landuse']['landuse_type']}")
        print()
    except Exception as e:
        print(f"❌ Geofence check failed: {e}\n")
    
    # Test 4: Find nearby buildings (if endpoint exists)
    print("Test 4: Finding nearby buildings...")
    try:
        result = client.find_nearby_buildings(
            latitude=13.0969,
            longitude=-59.6145,
            radius_meters=500,
            limit=10
        )
        if 'error' not in result:
            print(f"✅ Found {result['count']} buildings within 500m")
            print(f"   Latency: {result.get('latency_ms', 'N/A')}ms")
            if result['buildings']:
                print(f"   First building: {result['buildings'][0].get('name', 'Unnamed')}")
        else:
            print(f"⚠️ Endpoint not implemented yet: {result.get('error', 'Unknown')}")
        print()
    except Exception as e:
        print(f"⚠️ Endpoint not available (expected): {e}\n")
    
    # Test 5: Depot catchment area
    print("Test 5: Depot catchment area...")
    try:
        result = client.depot_catchment_area(
            depot_latitude=13.0969,
            depot_longitude=-59.6145,
            catchment_radius_meters=1500,
            limit=100
        )
        if 'error' not in result:
            print(f"✅ Found {result['count']} buildings in depot catchment")
            print(f"   Latency: {result.get('latency_ms', 'N/A')}ms")
        else:
            print(f"⚠️ Returned error: {result.get('error', 'Unknown')}")
        print()
    except Exception as e:
        print(f"❌ Depot catchment query failed: {e}\n")
    
    print("🎉 Basic client tests completed!")
    print("\n📝 Next steps:")
    print("   1. Verify all working endpoints (reverse geocode, geofence)")
    print("   2. Implement missing endpoints if needed for spawning")
    print("   3. Integrate with commuter_service spawning logic")

if __name__ == "__main__":
    main()
