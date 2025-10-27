"""
Quick test of reverse geocoding address lookup
"""

import sys
sys.path.insert(0, ".")

from infrastructure.geospatial.client import GeospatialClient

def test_address_lookup():
    """Test reverse geocoding to see what address data we get"""
    
    print("=" * 70)
    print("REVERSE GEOCODE ADDRESS LOOKUP TEST")
    print("=" * 70)
    
    client = GeospatialClient()
    
    # Test locations in Barbados
    test_locations = [
        (13.0969, -59.6145, "Bridgetown Center"),
        (13.0806, -59.5905, "Airport Area"),
        (13.1853, -59.5431, "North of Island"),
    ]
    
    for lat, lon, description in test_locations:
        print(f"\n[TEST] {description}")
        print(f"Coordinates: ({lat}, {lon})")
        print("-" * 70)
        
        try:
            result = client.reverse_geocode(lat, lon)
            
            print(f"Full API Response:")
            print(f"  Keys returned: {list(result.keys())}")
            print(f"")
            
            # Check all possible address fields
            if 'address' in result:
                print(f"  address: {result['address']}")
            
            if 'display_name' in result:
                print(f"  display_name: {result['display_name']}")
            
            if 'formatted_address' in result:
                print(f"  formatted_address: {result['formatted_address']}")
            
            if 'parish' in result:
                print(f"  parish: {result['parish']}")
            
            if 'highway' in result:
                print(f"  highway: {result['highway']}")
            
            if 'latency_ms' in result:
                print(f"  latency_ms: {result['latency_ms']}")
            
            # Print raw response for debugging
            print(f"\nRaw response (first 500 chars):")
            print(f"  {str(result)[:500]}")
            
        except Exception as e:
            print(f"[ERROR] {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_address_lookup()
