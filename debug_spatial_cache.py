"""
Debug script to test spatial zone loading in isolation
"""

import asyncio
import logging
from commuter_service.strapi_api_client import StrapiApiClient
from commuter_service.simple_spatial_cache import SimpleSpatialZoneCache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

async def test_zone_loading():
    """Test zone loading with timing"""
    import time
    
    # Connect to API
    print("=" * 80)
    print("SPATIAL ZONE CACHE DEBUG TEST")
    print("=" * 80)
    
    api_client = StrapiApiClient("http://localhost:1337")
    await api_client.connect()
    
    # Get a sample route
    print("\n1. Loading routes...")
    start = time.time()
    routes = await api_client.get_all_routes()
    print(f"   ✅ Loaded {len(routes)} routes in {time.time() - start:.2f}s")
    
    if not routes:
        print("   ❌ No routes found!")
        return
    
    # Extract route coordinates
    route = routes[0]
    print(f"\n2. Using route: {route.short_name} ({route.coordinate_count} points)")
    route_coords = route.geometry_coordinates
    
    # Create spatial cache
    print("\n3. Creating spatial cache...")
    cache = SimpleSpatialZoneCache(
        api_client=api_client,
        country_id=29,  # Barbados
        buffer_km=5.0
    )
    
    # Initialize and load zones
    print("\n4. Loading zones with spatial filtering...")
    start = time.time()
    
    try:
        await cache.initialize_for_route(
            route_coordinates=route_coords[:10],  # Use only first 10 points for testing
            depot_locations=[]
        )
        elapsed = time.time() - start
        
        stats = cache.get_stats()
        print(f"\n   ✅ Zone loading complete in {elapsed:.2f}s")
        print(f"   📊 Population zones: {stats['population_zones']}")
        print(f"   📊 Amenity zones: {stats['amenity_zones']}")
        print(f"   📊 Buffer: ±{stats['buffer_km']}km")
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    await api_client.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_zone_loading())
