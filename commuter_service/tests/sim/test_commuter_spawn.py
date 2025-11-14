"""
Commuter Spawn Test Script
===========================

Generates passengers for a route at a specific date/time or time range.

Usage - Single Time Mode:
  python test_commuter_spawn.py [route_id] [day_of_week] [spawn_time]
  route_id: Strapi route document ID (default: gg3pv3z19hhm117v9xth5ezq)
  day_of_week: Day name (Monday, Tuesday, ..., Sunday) or 'today' (default: today)
  spawn_time: Time as HH:MM:SS (default: 09:00:00)

Usage - Time Range Mode:
  python test_commuter_spawn.py [route_id] [day_of_week] --time-range START_TIME END_TIME --interval MINUTES
  route_id: Strapi route document ID (default: gg3pv3z19hhm117v9xth5ezq)
  day_of_week: Day name (Monday, Tuesday, ..., Sunday) or 'today' (default: today)
  --time-range: Start and end times as HH:MM:SS (e.g., 09:00:00 17:00:00)
  --interval: Interval in minutes between spawns (default: 10)

Examples - Single Time:
  python test_commuter_spawn.py
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq today 14:30:00
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq Monday 09:00:00

Examples - Time Range:
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq Monday --time-range 09:00:00 09:50:00 --interval 10
  python test_commuter_spawn.py --time-range 08:00:00 17:00:00 --interval 60
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq Friday --time-range 06:00:00 22:00:00 --interval 30

Output:
- Passengers ordered by increasing distance from route start point
- Shows boarding location, alighting location, and travel distance
"""

import asyncio
import logging
import sys
import argparse
from datetime import datetime, timedelta
import math

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


DAYS_OF_WEEK = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6
}


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
    # Add project root to path so imports work from anywhere
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate commuter spawns for a route on a specific day/time or time range",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples - Single Time:
  python test_commuter_spawn.py
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq today 14:30:00
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq Monday 09:00:00

Examples - Time Range:
  python test_commuter_spawn.py gg3pv3z19hhm117v9xth5ezq Monday --time-range 09:00:00 09:50:00 --interval 10
  python test_commuter_spawn.py --time-range 08:00:00 17:00:00 --interval 60
        """
    )
    parser.add_argument(
        'route_id',
        nargs='?',
        default='gg3pv3z19hhm117v9xth5ezq',
        help='Strapi route document ID (default: gg3pv3z19hhm117v9xth5ezq)'
    )
    parser.add_argument(
        'day_of_week',
        nargs='?',
        default='today',
        help='Day of week: Monday, Tuesday, ..., Sunday or "today" (default: today)'
    )
    parser.add_argument(
        'spawn_time',
        nargs='?',
        default=None,
        help='Spawn time as HH:MM:SS (default: 09:00:00 in single-time mode)'
    )
    parser.add_argument(
        '--time-range',
        nargs=2,
        metavar=('START_TIME', 'END_TIME'),
        help='Time range for spawns: START_TIME END_TIME as HH:MM:SS'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Interval in minutes between spawns in range mode (default: 10)'
    )
    
    args = parser.parse_args()
    ROUTE_ID = args.route_id
    day_str = args.day_of_week.lower()
    
    # Determine mode: range or single time
    time_range_mode = args.time_range is not None
    
    # Parse day of week
    if day_str == 'today':
        spawn_date = datetime.now().date()
    elif day_str in DAYS_OF_WEEK:
        # Find the next occurrence of this day of week (or today if today is that day)
        target_day = DAYS_OF_WEEK[day_str]
        today = datetime.now().date()
        current_day = today.weekday()
        days_ahead = target_day - current_day
        if days_ahead < 0:  # Target day already happened this week
            days_ahead += 7
        spawn_date = today + timedelta(days=days_ahead)
    else:
        print(f"ERROR: Invalid day. Use 'today' or day name (Monday, Tuesday, ..., Sunday)")
        sys.exit(1)
    
    # Parse spawn times based on mode
    if time_range_mode:
        # Range mode
        try:
            start_time_obj = datetime.strptime(args.time_range[0], '%H:%M:%S').time()
            end_time_obj = datetime.strptime(args.time_range[1], '%H:%M:%S').time()
            start_datetime = datetime.combine(spawn_date, start_time_obj)
            end_datetime = datetime.combine(spawn_date, end_time_obj)
            
            # Generate time points at specified intervals
            spawn_times = []
            current = start_datetime
            while current <= end_datetime:
                spawn_times.append(current)
                current += timedelta(minutes=args.interval)
            
            if not spawn_times:
                print(f"ERROR: No spawn times generated. Check time range and interval.")
                sys.exit(1)
        except ValueError:
            print(f"ERROR: Invalid time range format. Use HH:MM:SS for both start and end times")
            sys.exit(1)
    else:
        # Single time mode
        time_str = args.spawn_time if args.spawn_time else '09:00:00'
        try:
            time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
            spawn_times = [datetime.combine(spawn_date, time_obj)]
        except ValueError:
            print(f"ERROR: Invalid spawn time format. Use HH:MM:SS")
            sys.exit(1)
    
    SPAWN_WINDOW_MINUTES = 60  # 1 hour
    
    print("="*120)
    print("COMMUTER SPAWN TEST - Generate Passengers for Route")
    print("="*120)
    
    print(f"\nConfiguration:")
    print(f"  Route: {ROUTE_ID}")
    print(f"  Day: {spawn_date.strftime('%A')} ({spawn_date})")
    if time_range_mode:
        print(f"  Time Range: {spawn_times[0].strftime('%H:%M:%S')} - {spawn_times[-1].strftime('%H:%M:%S')}")
        print(f"  Interval: {args.interval} minutes")
        print(f"  Total Time Points: {len(spawn_times)}")
    else:
        print(f"  Spawn Time: {spawn_times[0].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Spawn Window: {SPAWN_WINDOW_MINUTES} minutes")
    
    # Import dependencies
    from commuter_service.infrastructure.database import StrapiApiClient, PassengerRepository
    from commuter_service.core.domain.plugins.poisson_plugin import PoissonGeoJSONPlugin
    from commuter_service.core.domain.spawning_plugin import PluginConfig, PluginType, SpawnContext
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
    
    # Clean passenger database FIRST - Delete ALL passengers (not just this route)
    print("\n[STEP 2/5] Cleaning passenger database...")
    async with httpx.AsyncClient() as client:
        # Get ALL active passengers
        response = await client.get(
            "http://localhost:1337/api/active-passengers",
            params={
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
            'geo_url': 'http://localhost:6000'
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
    
    # Generate passengers for all spawn times
    print(f"\n[STEP 4/5] Generating passengers...")
    total_spawn_requests = 0
    for spawn_time in spawn_times:
        spawn_requests = await poisson_plugin.generate_spawn_requests(
            current_time=spawn_time,
            time_window_minutes=SPAWN_WINDOW_MINUTES,
            context=SpawnContext.ROUTE,
            route_id=ROUTE_ID
        )
        total_spawn_requests += len(spawn_requests)
        print(f"  {spawn_time.strftime('%H:%M:%S')}: Generated {len(spawn_requests)} passengers")
    
    print(f"OK - Generated {total_spawn_requests} total passengers (saved to database)")
    
    # Get route geometry for ordering passengers
    print("\n[STEP 5/5] Loading route geometry and passenger positions...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:6000/spatial/route-geometry/{ROUTE_ID}")
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
    for idx, p in enumerate(all_passengers_data.get('data', []), 1):
        # Handle both nested (attributes) and flat Strapi responses
        attrs = p.get('attributes', p)
        
        all_passengers.append({
            'id': p.get('id'),
            'spawn_sequence': idx,  # Track original insertion order
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
        # Skip if no boarding location
        if not passenger['latitude'] or not passenger['longitude']:
            passenger['route_position'] = 0
            passenger['nearest_route_idx'] = 0
            passenger['distance_to_route'] = float('inf')
            continue
        
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
    
    # Output results - group by spawn time if in range mode
    print("\n" + "="*120)
    if time_range_mode:
        print(f"PASSENGERS GENERATED - Time Range Mode ({len(all_passengers)} total)")
    else:
        print(f"PASSENGERS GENERATED - Ordered by Route Position (Nearest to Furthest) ({len(all_passengers)} total)")
    print("="*120)
    
    if all_passengers:
        if time_range_mode:
            # Group by spawn time
            by_spawn_time = {}
            for p in all_passengers:
                spawn_time_str = "N/A"
                if p['spawned_at']:
                    try:
                        spawn_time = datetime.fromisoformat(p['spawned_at'].replace('Z', '+00:00'))
                        spawn_time_str = spawn_time.strftime('%H:%M:%S')
                    except:
                        spawn_time_str = "ERROR"
                if spawn_time_str not in by_spawn_time:
                    by_spawn_time[spawn_time_str] = []
                by_spawn_time[spawn_time_str].append(p)
            
            # Print for each spawn time
            for spawn_time_str in sorted(by_spawn_time.keys()):
                passengers_at_time = by_spawn_time[spawn_time_str]
                print(f"\n{'-'*120}")
                print(f"Spawn Time: {spawn_time_str} ({len(passengers_at_time)} passengers)")
                print(f"{'-'*120}")
                print(f"{'Seq':<5} {'Spawn#':<8} {'Passenger ID':<15} {'Route Pos (m)':<14} {'Board Lat':<11} {'Board Lon':<12} {'Alight Lat':<11} {'Alight Lon':<12} {'Distance (m)':<12}")
                print("-" * 120)
                
                for idx, p in enumerate(passengers_at_time, 1):
                    # Skip passengers with None passenger_id
                    if not p['passenger_id']:
                        continue
                    
                    # Handle missing coordinates
                    if p['latitude'] is None or p['longitude'] is None:
                        board_to_alight_dist = 0
                        lat_str = "N/A"
                        lon_str = "N/A"
                        dest_lat_str = "N/A" if p['destination_lat'] is None else f"{p['destination_lat']:.6f}"
                        dest_lon_str = "N/A" if p['destination_lon'] is None else f"{p['destination_lon']:.6f}"
                    else:
                        if p['destination_lat'] is not None and p['destination_lon'] is not None:
                            board_to_alight_dist = haversine_distance(
                                p['latitude'], p['longitude'],
                                p['destination_lat'], p['destination_lon']
                            )
                        else:
                            board_to_alight_dist = 0
                        lat_str = f"{p['latitude']:.6f}"
                        lon_str = f"{p['longitude']:.6f}"
                        dest_lat_str = f"{p['destination_lat']:.6f}" if p['destination_lat'] is not None else "N/A"
                        dest_lon_str = f"{p['destination_lon']:.6f}" if p['destination_lon'] is not None else "N/A"
                    
                    print(
                        f"{idx:<5} "
                        f"{p['spawn_sequence']:<8} "
                        f"{p['passenger_id']:<15} "
                        f"{p['route_position']:<14.1f} "
                        f"{lat_str:<11} "
                        f"{lon_str:<12} "
                        f"{dest_lat_str:<11} "
                        f"{dest_lon_str:<12} "
                        f"{board_to_alight_dist:<12.1f}"
                    )
        else:
            # Single time mode - original output format
            print(f"\n{'Seq':<5} {'Spawn#':<8} {'Passenger ID':<15} {'Spawned At':<20} {'Route Pos (m)':<14} {'Board Lat':<11} {'Board Lon':<12} {'Alight Lat':<11} {'Alight Lon':<12} {'Distance (m)':<12}")
            print("-" * 140)
            
            for idx, p in enumerate(all_passengers, 1):
                # Skip passengers with None passenger_id
                if not p['passenger_id']:
                    continue
                
                # Handle missing coordinates
                if p['latitude'] is None or p['longitude'] is None:
                    board_to_alight_dist = 0
                    lat_str = "N/A"
                    lon_str = "N/A"
                    dest_lat_str = "N/A" if p['destination_lat'] is None else f"{p['destination_lat']:.6f}"
                    dest_lon_str = "N/A" if p['destination_lon'] is None else f"{p['destination_lon']:.6f}"
                else:
                    if p['destination_lat'] is not None and p['destination_lon'] is not None:
                        board_to_alight_dist = haversine_distance(
                            p['latitude'], p['longitude'],
                            p['destination_lat'], p['destination_lon']
                        )
                    else:
                        board_to_alight_dist = 0
                    lat_str = f"{p['latitude']:.6f}"
                    lon_str = f"{p['longitude']:.6f}"
                    dest_lat_str = f"{p['destination_lat']:.6f}" if p['destination_lat'] is not None else "N/A"
                    dest_lon_str = f"{p['destination_lon']:.6f}" if p['destination_lon'] is not None else "N/A"
                
                spawn_time_str = "N/A"
                if p['spawned_at']:
                    try:
                        spawn_time = datetime.fromisoformat(p['spawned_at'].replace('Z', '+00:00'))
                        spawn_time_str = spawn_time.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        spawn_time_str = "ERROR"
                
                print(
                    f"{idx:<5} "
                    f"{p['spawn_sequence']:<8} "
                    f"{p['passenger_id']:<15} "
                    f"{spawn_time_str:<20} "
                    f"{p['route_position']:<14.1f} "
                    f"{lat_str:<11} "
                    f"{lon_str:<12} "
                    f"{dest_lat_str:<11} "
                    f"{dest_lon_str:<12} "
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
