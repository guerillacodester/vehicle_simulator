"""
Route Passenger Manifest - Bar Chart Visualization
---------------------------------------------------

Displays hourly passenger distribution as a bar chart.

Usage:
    python scripts/manifest_barchart.py
    python scripts/manifest_barchart.py --day monday
    python scripts/manifest_barchart.py --day monday --route 1
"""

import asyncio
import httpx
from datetime import datetime
import argparse


MANIFEST_API_URL = "http://localhost:4000"
STRAPI_URL = "http://localhost:1337"


async def fetch_manifest(
    route_id: str = None,
    day_of_week: str = "monday"
):
    """Fetch all passengers for a specific day"""
    
    # Map day name to weekday number (0=Monday, 6=Sunday)
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    target_weekday = day_map[day_of_week.lower()]
    
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
            
            print(f"   Fetched page {page}/{total_pages} ({len(passengers)} passengers)")
            
            if page >= total_pages:
                break
            
            page += 1
    
    # Filter by day of week and route
    filtered = []
    for p in all_passengers:
        spawn_time_str = p.get('spawned_at')
        if spawn_time_str:
            spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
            if spawn_time.weekday() == target_weekday:
                # Filter by route if specified
                if route_id and p.get('route_id') != route_id:
                    continue
                filtered.append(p)
    
    return filtered


def create_barchart(passengers, day_name: str, route_name: str = "All Routes"):
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
    print(f"PASSENGER MANIFEST - {day_name.upper()} - {route_name}")
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


async def main():
    parser = argparse.ArgumentParser(
        description="Display passenger manifest as bar chart"
    )
    
    parser.add_argument(
        '--day',
        default='monday',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        help='Day of week to display'
    )
    
    parser.add_argument(
        '--route',
        default=None,
        help='Route short_name (e.g., "1")'
    )
    
    args = parser.parse_args()
    
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
    passengers = await fetch_manifest(route_id=route_id, day_of_week=args.day)
    
    if not passengers:
        print(f"❌ No passengers found for {args.day}")
        return
    
    create_barchart(passengers, args.day, route_name)


if __name__ == "__main__":
    asyncio.run(main())
