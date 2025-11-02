"""
Route Passenger Manifest Visualization
---------------------------------------

Displays passenger manifest as bar chart or detailed table.

Bar Chart: Shows hourly passenger distribution
Table: Shows detailed passenger info ordered by distance from depot

Usage:
    # Bar chart for full day
    python scripts/manifest_barchart.py --day monday --route 1 --format barchart
    
    # Table for specific time range
    python scripts/manifest_barchart.py --day monday --route 1 --format table --start-hour 7 --end-hour 9
    
    # Using specific date instead of day name
    python scripts/manifest_barchart.py --date 2024-11-04 --route 1 --format table
"""

import asyncio
import httpx
from datetime import datetime, timedelta
import argparse


MANIFEST_API_URL = "http://localhost:4000"
STRAPI_URL = "http://localhost:1337"
GEOSPATIAL_URL = "http://localhost:6000"


async def fetch_manifest(
    route_id: str = None,
    target_date: datetime = None,
    start_hour: int = 0,
    end_hour: int = 23
):
    """Fetch all passengers for a specific date and time range"""
    
    # Fetch all pages from Strapi (max 100 per page)
    all_passengers = []
    page = 1
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"📡 Fetching passengers from Strapi...")
        
        while True:
            url = f"{STRAPI_URL}/api/active-passengers?pagination[page]={page}&pagination[pageSize]=100"
            response = await client.get(url)
            
            if response.status_code != 200:
                print(f"❌ Error: API returned {response.status_code}")
                break
            
            data = response.json()
            passengers = data.get('data', [])
            
            if not passengers:
                break
            
            all_passengers.extend(passengers)
            
            # Check if there are more pages
            meta = data.get('meta', {})
            pagination = meta.get('pagination', {})
            total_pages = pagination.get('pageCount', 1)
            
            if page == 1:
                print(f"   Total pages: {total_pages}")
            
            if page >= total_pages:
                break
            
            page += 1
    
    # Filter by date, time range, and route
    filtered = []
    for p in all_passengers:
        spawn_time_str = p.get('spawned_at')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            
            # Check date match
            if target_date and spawn_time.date() != target_date.date():
                continue
            
            # Check hour range
            if spawn_time.hour < start_hour or spawn_time.hour > end_hour:
                continue
            
            # Filter by route if specified
            if route_id and p.get('route_id') != route_id:
                continue
                
            filtered.append(p)
    
    return filtered


def create_barchart(passengers, target_date: datetime, route_name: str = "All Routes"):
    """Create ASCII bar chart of hourly passenger distribution"""
    
    # Count passengers per hour
    hourly_counts = [0] * 24
    
    for p in passengers:
        spawn_time_str = p.get('spawned_at')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            hour = spawn_time.hour
            hourly_counts[hour] += 1
    
    total = sum(hourly_counts)
    max_count = max(hourly_counts) if hourly_counts else 0
    
    # Print header
    print("\n" + "=" * 80)
    print(f"PASSENGER MANIFEST - {target_date.strftime('%A, %Y-%m-%d')} - {route_name}")
    print("=" * 80)
    print(f"Total Passengers: {total}")
    print(f"Peak Hour: {hourly_counts.index(max_count):02d}:00 ({max_count} passengers)")
    print("=" * 80)
    print()
    
    # Calculate bar width (scale to 60 characters max)
    scale = 60 / max_count if max_count > 0 else 1
    
    # Print bar chart
    for hour in range(24):
        count = hourly_counts[hour]
        bar_length = int(count * scale)
        bar = "█" * bar_length
        
        # Color coding for peak hours
        if count == max_count and count > 0:
            hour_label = f"{hour:02d}:00"
            count_label = f"{count:>4}"
            print(f"{hour_label} │ {bar} {count_label} 🔥")
        elif count >= max_count * 0.7 and count > 0:
            hour_label = f"{hour:02d}:00"
            count_label = f"{count:>4}"
            print(f"{hour_label} │ {bar} {count_label} ⚡")
        elif count > 0:
            hour_label = f"{hour:02d}:00"
            count_label = f"{count:>4}"
            print(f"{hour_label} │ {bar} {count_label}")
        else:
            hour_label = f"{hour:02d}:00"
            print(f"{hour_label} │ ")
    
    print()
    print("=" * 80)
    
    # Breakdown by type
    depot_count = sum(1 for p in passengers if p.get('depot_id'))
    route_count = total - depot_count
    
    print(f"Route Passengers: {route_count} ({route_count/total*100:.1f}%)" if total > 0 else "Route Passengers: 0")
    print(f"Depot Passengers: {depot_count} ({depot_count/total*100:.1f}%)" if total > 0 else "Depot Passengers: 0")
    print("=" * 80)
    print()


async def reverse_geocode(lat: float, lon: float) -> str:
    """Get address from coordinates using geospatial service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{GEOSPATIAL_URL}/reverse-geocode?lat={lat}&lon={lon}")
            if response.status_code == 200:
                data = response.json()
                return data.get('address', 'N/A')
    except:
        pass
    return 'N/A'


async def create_table(passengers, target_date: datetime, route_name: str = "All Routes"):
    """Create detailed table of passengers ordered by distance from depot"""
    
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance in km between two coordinates"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    # Get depot info once for all route passengers
    depot_cache = {}
    
    async def get_depot_coords(route_id):
        if route_id in depot_cache:
            return depot_cache[route_id]
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{GEOSPATIAL_URL}/routes/by-document-id/{route_id}/depot")
                if response.status_code == 200:
                    depot_info = response.json().get('depot', {})
                    coords = (depot_info.get('latitude'), depot_info.get('longitude'))
                    depot_cache[route_id] = coords
                    return coords
        except:
            pass
        return (None, None)
    
    # Fetch all depot coords in parallel
    print(f"🗺️  Fetching depot coordinates...")
    route_ids = list(set(p.get('route_id') for p in passengers if p.get('route_id')))
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [get_depot_coords(rid) for rid in route_ids]
        await asyncio.gather(*tasks)
    
    # Batch reverse geocode - collect all unique coordinates first
    print(f"🗺️  Reverse geocoding {len(passengers)} passengers (batched)...")
    
    unique_coords = set()
    for p in passengers:
        start_lat = p.get('latitude')
        start_lon = p.get('longitude')
        dest_lat = p.get('destination_lat')
        dest_lon = p.get('destination_lon')
        
        if start_lat and start_lon:
            unique_coords.add((start_lat, start_lon))
        if dest_lat and dest_lon:
            unique_coords.add((dest_lat, dest_lon))
    
    print(f"   {len(unique_coords)} unique locations to geocode...")
    
    # Reverse geocode all unique coordinates in parallel with semaphore to control concurrency
    address_cache = {}
    
    # Shared client for all requests (much faster than creating new clients)
    async with httpx.AsyncClient(timeout=10.0) as shared_client:
        async def geocode_coord(lat, lon, semaphore):
            async with semaphore:  # Limit concurrent requests
                try:
                    response = await shared_client.get(f"{GEOSPATIAL_URL}/geocode/reverse?lat={lat}&lon={lon}")
                    if response.status_code == 200:
                        data = response.json()
                        return ((lat, lon), data.get('address', 'N/A'))
                except:
                    pass
                return ((lat, lon), 'N/A')
        
        # Process all coordinates in parallel with max 100 concurrent requests
        semaphore = asyncio.Semaphore(100)
        coords_list = list(unique_coords)
        
        print(f"   Geocoding all {len(coords_list)} locations in parallel...")
        tasks = [geocode_coord(lat, lon, semaphore) for lat, lon in coords_list]
        results = await asyncio.gather(*tasks)
        
        for coords, address in results:
            address_cache[coords] = address
        
        print(f"   ✅ Geocoded {len(coords_list)} locations!")
    
    # Enrich passenger data with calculated distances and addresses
    enriched_passengers = []
    
    for idx, p in enumerate(passengers, 1):
        start_lat = p.get('latitude')
        start_lon = p.get('longitude')
        dest_lat = p.get('destination_lat')
        dest_lon = p.get('destination_lon')
        
        # Get depot coordinates
        route_id = p.get('route_id')
        depot_lat, depot_lon = depot_cache.get(route_id, (None, None)) if route_id else (None, None)
        
        # Get addresses from cache
        start_addr = address_cache.get((start_lat, start_lon), 'N/A') if start_lat and start_lon else 'N/A'
        dest_addr = address_cache.get((dest_lat, dest_lon), 'N/A') if dest_lat and dest_lon else 'N/A'
        
        # Calculate commute distance (start to destination)
        commute_distance = 0.0
        if all([start_lat, start_lon, dest_lat, dest_lon]):
            commute_distance = haversine_distance(start_lat, start_lon, dest_lat, dest_lon)
        
        # Calculate distance from depot to start location
        depot_distance = 0.0
        if all([depot_lat, depot_lon, start_lat, start_lon]):
            depot_distance = haversine_distance(depot_lat, depot_lon, start_lat, start_lon)
        
        enriched_passengers.append({
            'index': idx,
            'passenger': p,
            'start_address': start_addr,
            'dest_address': dest_addr,
            'commute_distance': commute_distance,
            'depot_distance': depot_distance
        })
    
    # Sort by depot_distance (ascending)
    enriched_passengers.sort(key=lambda x: x['depot_distance'])
    
    # Calculate route total distance from passenger coordinates
    route_total_distance = None
    if enriched_passengers:
        # Get all unique coordinates from passengers
        all_coords = []
        for item in enriched_passengers:
            p = item['passenger']
            lat = p.get('latitude')
            lon = p.get('longitude')
            if lat and lon:
                all_coords.append((lat, lon))
        
        # Sort by distance from depot to get route order
        if all_coords and len(all_coords) > 1:
            # Calculate total by summing all segment distances
            total_distance = 0.0
            for i in range(len(all_coords) - 1):
                lat1, lon1 = all_coords[i]
                lat2, lon2 = all_coords[i + 1]
                total_distance += haversine_distance(lat1, lon1, lat2, lon2)
            route_total_distance = total_distance
    
    # Print header
    print("\n" + "=" * 140)
    print(f"PASSENGER MANIFEST TABLE - {target_date.strftime('%A, %Y-%m-%d')} - {route_name}")
    print("=" * 140)
    print(f"Total Passengers: {len(passengers)}")
    print("=" * 140)
    print()
    
    # Table header
    print(f"{'#':>4} | {'Spawn Time':^19} | {'Start Location':^30} | {'Dest Location':^30} | {'Commute':>8} | {'From Depot':>11}")
    print("-" * 140)
    
    # Table rows
    for item in enriched_passengers:
        idx = item['index']
        p = item['passenger']
        commute_dist = item['commute_distance']
        depot_dist = item['depot_distance']
        start_addr = item['start_address']
        dest_addr = item['dest_address']
        
        spawn_time_str = p.get('spawned_at', '')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            spawn_display = spawn_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            spawn_display = 'N/A'
        
        # Truncate addresses to fit
        start_addr_short = start_addr[:28]
        dest_addr_short = dest_addr[:28]
        
        print(f"{idx:>4} | {spawn_display:^19} | {start_addr_short:<30} | {dest_addr_short:<30} | {commute_dist:>6.2f}km | {depot_dist:>9.2f}km")
    
    print()
    print("=" * 140)
    
    # Summary statistics
    depot_count = sum(1 for p in passengers if p.get('depot_id'))
    route_count = len(passengers) - depot_count
    avg_commute = sum(item['commute_distance'] for item in enriched_passengers) / len(enriched_passengers) if enriched_passengers else 0
    avg_depot_dist = sum(item['depot_distance'] for item in enriched_passengers) / len(enriched_passengers) if enriched_passengers else 0
    
    print(f"Route Passengers: {route_count} | Depot Passengers: {depot_count}")
    print(f"Average Commute Distance: {avg_commute:.2f}km")
    print(f"Average Distance from Depot: {avg_depot_dist:.2f}km")
    
    if route_total_distance is not None:
        print(f"Total Route Distance: {route_total_distance:.2f}km")
    
    print("=" * 140)
    print()


async def main():
    parser = argparse.ArgumentParser(
        description="Display passenger manifest as bar chart or detailed table"
    )
    
    parser.add_argument(
        '--day',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        help='Day of week to display (alternative to --date)'
    )
    
    parser.add_argument(
        '--date',
        help='Specific date to display (YYYY-MM-DD format, alternative to --day)'
    )
    
    parser.add_argument(
        '--route',
        default=None,
        help='Route short_name (e.g., "1")'
    )
    
    parser.add_argument(
        '--format',
        choices=['barchart', 'table'],
        default='barchart',
        help='Output format: barchart (hourly distribution) or table (detailed list)'
    )
    
    parser.add_argument(
        '--start-hour',
        type=int,
        default=0,
        help='Start hour (0-23, default: 0)'
    )
    
    parser.add_argument(
        '--end-hour',
        type=int,
        default=23,
        help='End hour (0-23, default: 23)'
    )
    
    args = parser.parse_args()
    
    # Validate that either --day or --date is provided
    if not args.day and not args.date:
        parser.error("Either --day or --date must be specified")
    
    if args.day and args.date:
        parser.error("Cannot specify both --day and --date")
    
    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ ERROR: Invalid date format '{args.date}'. Use YYYY-MM-DD")
            return
    else:
        # Map day name to a fixed base week
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        base_date = datetime(2024, 11, 4)  # Monday, Nov 4, 2024
        day_offset = day_map[args.day.lower()]
        target_date = base_date + timedelta(days=day_offset)
    
    # If route specified, fetch route ID
    route_id = None
    route_name = "All Routes"
    
    if args.route:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{STRAPI_URL}/api/routes")
            routes = response.json().get('data', [])
            
            for r in routes:
                if r.get('short_name') == args.route:
                    route_id = r.get('documentId')
                    route_name = f"Route {args.route}"
                    break
            
            if not route_id:
                print(f"❌ Route '{args.route}' not found!")
                return
    
    # Fetch and display
    passengers = await fetch_manifest(
        route_id=route_id,
        target_date=target_date,
        start_hour=args.start_hour,
        end_hour=args.end_hour
    )
    
    if not passengers:
        print(f"❌ No passengers found for {target_date.strftime('%A, %Y-%m-%d')} ({args.start_hour:02d}:00-{args.end_hour:02d}:00)")
        return
    
    if args.format == 'barchart':
        create_barchart(passengers, target_date, route_name)
    else:
        await create_table(passengers, target_date, route_name)


if __name__ == "__main__":
    asyncio.run(main())
