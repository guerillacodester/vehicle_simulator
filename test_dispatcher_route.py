"""
Test script to verify dispatcher can fetch route geometry from Strapi API.
This tests the updated get_route_info method that uses the new /api/routes/{route_code}/geometry endpoint.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from arknet_transit_simulator.core.dispatcher import FastApiStrategy


async def test_dispatcher_route_fetch():
    """Test that dispatcher can fetch route geometry from Strapi."""
    
    # Initialize strategy with Strapi URL
    strapi_url = "http://localhost:1337"
    strategy = FastApiStrategy(api_base_url=strapi_url)
    
    print(f"\n{'='*60}")
    print(f"Testing Dispatcher Route Fetch")
    print(f"{'='*60}")
    print(f"Strapi URL: {strapi_url}")
    print(f"Endpoint: /api/routes/1/geometry")
    print(f"{'='*60}\n")
    
    try:
        # Initialize session
        await strategy.initialize()
        print("✅ Initialized HTTP session")
        
        # Test connection
        connected = await strategy.test_connection()
        if not connected:
            print("❌ Failed to connect to Strapi")
            return False
        print("✅ Connected to Strapi API")
        
        # Fetch route info for route "1"
        print("\n📡 Fetching route geometry for route '1'...")
        route_info = await strategy.get_route_info("1")
        
        if route_info:
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS: Route Loaded")
            print(f"{'='*60}")
            print(f"Route ID: {route_info.route_id}")
            print(f"Route Name: {route_info.route_name}")
            print(f"Route Type: {route_info.route_type}")
            print(f"Coordinate Count: {route_info.coordinate_count}")
            print(f"Distance (km): {route_info.distance_km:.6f}")
            print(f"{'='*60}")
            
            # Verify geometry structure
            if route_info.geometry:
                coords = route_info.geometry.get('coordinates', [])
                if coords:
                    first = coords[0]
                    last = coords[-1]
                    print(f"\n🗺️  Route Path:")
                    print(f"   Start: [{first[0]:.6f}, {first[1]:.6f}]")
                    print(f"   End:   [{last[0]:.6f}, {last[1]:.6f}]")
                    print(f"   Total coordinates: {len(coords)}")
                
                # Validation
                print(f"\n✅ Validation:")
                if route_info.coordinate_count == 415:
                    print(f"   ✅ Coordinate count matches expected (415)")
                else:
                    print(f"   ⚠️  Coordinate count: {route_info.coordinate_count} (expected 415)")
                
                if 13.3 < route_info.distance_km < 13.5:
                    print(f"   ✅ Distance in expected range (13.3-13.5 km)")
                else:
                    print(f"   ⚠️  Distance: {route_info.distance_km:.3f} km (expected ~13.4 km)")
            
            return True
        else:
            print("❌ Failed to fetch route info")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await strategy.close()
        print("\n✅ Closed HTTP session")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Dispatcher Route Geometry Test")
    print("="*60)
    print("This script tests the updated dispatcher to verify it can")
    print("fetch route geometry from the new Strapi endpoint:")
    print("  GET /api/routes/:routeName/geometry")
    print("="*60 + "\n")
    
    # Check if Strapi is running
    print("⚠️  Ensure Strapi is running on http://localhost:1337")
    print("   Start it with: cd arknet_fleet_manager/arknet-fleet-api && npm run develop\n")
    
    # Run test
    success = asyncio.run(test_dispatcher_route_fetch())
    
    if success:
        print("\n" + "="*60)
        print("✅ TEST PASSED: Dispatcher successfully uses new Strapi endpoint!")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ TEST FAILED: Check logs above for details")
        print("="*60 + "\n")
        sys.exit(1)
