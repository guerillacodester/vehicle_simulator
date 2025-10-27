"""
Commuter Spawn Test Script
===========================

Generates passengers for a route at a specific date/time.
- Cleans passenger database table first
- Generates passengers using Poisson plugin
- Outputs all passengers ordered by distance from route start
"""

import asyncio
import logging
import sys
from datetime import datetime
import math

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


async def main():
    print("="*120)
    print("COMMUTER SPAWN TEST - Generate Passengers for Route")
    print("="*120)
    
    # Configuration
    ROUTE_ID = "gg3pv3z19hhm117v9xth5ezq"  # Route 1
    SPAWN_TIME = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # 9:00 AM
    SPAWN_WINDOW_MINUTES = 60  # 1 hour
    
    print(f"\nConfiguration:")
    print(f"  Route: {ROUTE_ID}")
    print(f"  Spawn Time: {SPAWN_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Spawn Window: {SPAWN_WINDOW_MINUTES} minutes")
    
    # Import dependencies
    from commuter_simulator.infrastructure.database import StrapiApiClient, PassengerRepository
    from commuter_simulator.core.domain.plugins.poisson_plugin import PoissonGeoJSONPlugin
    from commuter_simulator.core.domain.spawning_plugin import PluginConfig, PluginType, SpawnContext
    import httpx
    
    # Initialize services
    print("\n[STEP 1/5] Initializing services...")
    api_client = StrapiApiClient("http://localhost:1337")
    await api_client.connect()
    
    passenger_repo = PassengerRepository(
        strapi_url="http://localhost:1337",
        logger=logger
    )
    await passenger_repo.connect()
    
    print("OK - Services initialized")
    
    # Clean passenger database FIRST
    print("\n[STEP 2/5] Cleaning passenger database...")
    async with httpx.AsyncClient() as client:
        # Get all active passengers for this route
        response = await client.get(
            "http://localhost:1337/api/active-passengers",
            params={
                "filters[route_id][$eq]": ROUTE_ID,
                "pagination[pageSize]": 1000
            }
        )
        existing_passengers = response.json().get('data', [])
        
        # Delete each one
        deleted_count = 0
        for p in existing_passengers:
            delete_response = await client.delete(
                f"http://localhost:1337/api/active-passengers/{p['id']}"
            )
            if delete_response.status_code in (200, 204):
                deleted_count += 1
        
        print(f"OK - Deleted {deleted_count} existing passengers from database")
    
    # Initialize Poisson plugin
    print("\n[STEP 3/5] Initializing Poisson plugin...")
    plugin_config = PluginConfig(
        plugin_name="poisson_geojson",
        plugin_type=PluginType.STATISTICAL,
        country_code="BB",
        spawn_rate_multiplier=1.0,
        temporal_adjustment=True,
        use_spatial_cache=False,
        custom_params={
            'strapi_url': 'http://localhost:1337/api',
            'geo_url': 'http://localhost:8001'
        }
    )
    
    poisson_plugin = PoissonGeoJSONPlugin(
        config=plugin_config,
        api_client=api_client,
        passenger_repository=passenger_repo,
        logger=logger
    )
    
    await poisson_plugin.initialize()
    print("OK - Poisson plugin ready")
    
    # Generate passengers (saves to database)
    print(f"\n[STEP 4/5] Generating passengers for {SPAWN_TIME.strftime('%H:%M:%S')}...")
    spawn_requests = await poisson_plugin.generate_spawn_requests(
        current_time=SPAWN_TIME,
        time_window_minutes=SPAWN_WINDOW_MINUTES,
        context=SpawnContext.ROUTE,
        route_id=ROUTE_ID
    )
    
    print(f"OK - Generated {len(spawn_requests)} passengers (saved to database)")
    
    # Get route geometry for ordering passengers
    print("\n[STEP 5/5] Loading route geometry and passenger positions...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8001/spatial/route-geometry/{ROUTE_ID}")
        route_geom = response.json()
    
    route_coords = route_geom['coordinates']  # List of [lat, lon]
    
    # Calculate cumulative distances along route
    cumulative_distances = [0.0]
    for i in range(1, len(route_coords)):
        lat1, lon1 = route_coords[i-1]
        lat2, lon2 = route_coords[i]
        segment_dist = haversine_distance(lat1, lon1, lat2, lon2)
        cumulative_distances.append(cumulative_distances[-1] + segment_dist)
    
    # Query all passengers from database
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:1337/api/active-passengers",
            params={
                "filters[route_id][$eq]": ROUTE_ID,
                "filters[status][$eq]": "WAITING",
                "pagination[pageSize]": 1000
            }
        )
        all_passengers_data = response.json()
    
    all_passengers = []
    for p in all_passengers_data.get('data', []):
        attrs = p.get('attributes', {})
        all_passengers.append({
            'id': p.get('id'),
            'passenger_id': attrs.get('passenger_id'),
            'latitude': attrs.get('latitude'),
            'longitude': attrs.get('longitude'),
            'destination_lat': attrs.get('destination_lat'),
            'destination_lon': attrs.get('destination_lon'),
            'destination_name': attrs.get('destination_name'),
            'spawned_at': attrs.get('spawned_at')
        })
    
    # Calculate route position for each passenger
    for passenger in all_passengers:
        min_dist = float('inf')
        nearest_idx = 0
        
        for i, (lat, lon) in enumerate(route_coords):
            dist = haversine_distance(passenger['latitude'], passenger['longitude'], lat, lon)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        passenger['route_position'] = cumulative_distances[nearest_idx]
        passenger['nearest_route_idx'] = nearest_idx
        passenger['distance_to_route'] = min_dist
    
    # Sort passengers by route position (distance from start)
    all_passengers.sort(key=lambda p: p['route_position'])
    
    # Output results
    print("\n" + "="*120)
    print(f"PASSENGERS GENERATED - Ordered by Route Position ({len(all_passengers)} total)")
    print("="*120)
    
    if all_passengers:
        print(f"\n{'Seq':<5} {'Passenger ID':<15} {'Spawned At':<20} {'Route Pos (m)':<14} {'Board Lat':<11} {'Board Lon':<12} {'Alight Lat':<11} {'Alight Lon':<12} {'Distance (m)':<12}")
        print("-" * 120)
        
        for idx, p in enumerate(all_passengers, 1):
            board_to_alight_dist = haversine_distance(
                p['latitude'], p['longitude'],
                p['destination_lat'], p['destination_lon']
            )
            
            spawn_time = datetime.fromisoformat(p['spawned_at'].replace('Z', '+00:00'))
            
            print(
                f"{idx:<5} "
                f"{p['passenger_id']:<15} "
                f"{spawn_time.strftime('%Y-%m-%d %H:%M:%S'):<20} "
                f"{p['route_position']:<14.1f} "
                f"{p['latitude']:<11.6f} "
                f"{p['longitude']:<12.6f} "
                f"{p['destination_lat']:<11.6f} "
                f"{p['destination_lon']:<12.6f} "
                f"{board_to_alight_dist:<12.1f}"
            )
    else:
        print("\nNo passengers generated")
    
    # Cleanup
    print("\n[CLEANUP] Disconnecting...")
    await passenger_repo.disconnect()
    await api_client.close()
    
    print("\n" + "="*120)
    print("COMMUTER SPAWN COMPLETE")
    print("="*120)


if __name__ == "__main__":
    asyncio.run(main())
