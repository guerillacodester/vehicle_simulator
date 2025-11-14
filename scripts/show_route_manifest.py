"""
Route Passenger Manifest Table
-------------------------------

Queries the manifest API and displays route passengers in a table:
- Commuter index
- Start address
- Stop address  
- Commute distance
- Distance from route start

Ordered by ascending distance from route start.
Async implementation for fast data fetching.

Usage:
    python scripts/show_route_manifest.py
    python scripts/show_route_manifest.py --route ROUTE_1
    python scripts/show_route_manifest.py --day monday --start-hour 7 --end-hour 9
    python scripts/show_route_manifest.py --day friday --start-hour 16 --end-hour 18
    python scripts/show_route_manifest.py --limit 100
"""

import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import argparse


COMMUTER_commuter_service_url = "http://localhost:4000"
STRAPI_URL = "http://localhost:1337"


async def fetch_and_filter_manifest(
    route_id: Optional[str] = None,
    day_of_week: str = "monday",
    start_hour: int = 7,
    end_hour: int = 9,
    limit: int = 2000
) -> List[Dict]:
    """
    Fetch enriched manifest from API and filter by day/time locally.
    
    The manifest API provides all the enrichment (addresses, route positions),
    so we fetch that and then filter the results.
    """
    # Map day name to weekday number (0=Monday, 6=Sunday)
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    target_weekday = day_map.get(day_of_week.lower(), 0)
    
    # Fetch enriched manifest
    params = {"limit": limit}
    
    # If no route specified, use the actual route ID from database
    # The manifest API needs a route_id to calculate route positions properly
    if not route_id:
        route_id = "gg3pv3z19hhm117v9xth5ezq"  # Default route ID from database
    
    params["route"] = route_id
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{COMMUTER_commuter_service_url}/api/manifest",
                params=params
            )
            
            if response.status_code != 200:
                print(f"❌ Error fetching manifest: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return []
            
            manifest = response.json()
            passengers = manifest.get("passengers", [])
            print(f"   📊 Manifest API returned {len(passengers)} total passengers")
        except Exception as e:
            print(f"❌ Error connecting to manifest API: {e}")
            print(f"   Make sure manifest API is running on {COMMUTER_commuter_service_url}")
            return []
    
    # Filter by day of week and time range
    filtered = []
    route_passenger_count = 0
    for p in passengers:
        # Check if route passenger
        if p.get("route_position_m") is None:
            continue
        
        route_passenger_count += 1
        
        spawned_at = p.get("spawned_at")
        if not spawned_at:
            continue
        
        # Parse datetime
        try:
            dt = datetime.fromisoformat(spawned_at.replace("Z", "+00:00"))
        except:
            continue
        
        # Check day of week
        if dt.weekday() != target_weekday:
            continue
        
        # Check hour range (inclusive start, exclusive end)
        hour = dt.hour
        if hour < start_hour or hour >= end_hour:
            continue
        
        filtered.append(p)
    
    print(f"   📊 Found {route_passenger_count} route passengers (out of {len(passengers)} total)")
    print(f"   📊 Filtered to {len(filtered)} passengers for {day_of_week.capitalize()} {start_hour:02d}:00-{end_hour:02d}:00")
    
    return filtered


def format_address(address: Optional[str], max_length: int = 40) -> str:
    """Format address for table display"""
    if not address:
        return "N/A"
    
    if len(address) <= max_length:
        return address
    
    return address[:max_length - 3] + "..."


def display_manifest_table(passengers: List[Dict], day_of_week: str, start_hour: int, end_hour: int):
    """Display manifest in a formatted table"""
    
    if not passengers:
        print("❌ No passengers in manifest")
        return
    
    # Filter for route passengers only (those with route_position_m)
    route_passengers = [
        p for p in passengers 
        if p.get("route_position_m") is not None
    ]
    
    if not route_passengers:
        print("❌ No route passengers found")
        return
    
    # Sort by route position (ascending) - distance from depot/route start
    route_passengers.sort(key=lambda p: p.get("route_position_m", 0))
    
    print()
    print("=" * 180)
    print(f"ROUTE PASSENGER MANIFEST - {day_of_week.upper()} {start_hour:02d}:00-{end_hour:02d}:00 - {len(route_passengers)} passengers")
    print("=" * 180)
    print()
    
    # Table header
    print(f"{'#':<5} {'Spawn Time':<17} {'From Depot (km)':<16} {'Start Address':<42} {'Stop Address':<42} {'Commute (km)':<12}")
    print("-" * 180)
    
    # Table rows
    for idx, passenger in enumerate(route_passengers, 1):
        passenger_id = passenger.get("passenger_id", "N/A")
        
        # Distance from depot (route start position) - convert to km
        distance_from_depot_m = passenger.get("route_position_m", 0)
        distance_from_depot_km = distance_from_depot_m / 1000.0
        
        start_address = format_address(passenger.get("start_address"), 40)
        stop_address = format_address(passenger.get("stop_address"), 40)
        
        # Commute distance (how far passenger travels)
        commute_distance_km = passenger.get("travel_distance_km", 0)
        
        # Format spawn time with minutes
        spawned_at = passenger.get("spawned_at", "")
        if spawned_at:
            try:
                dt = datetime.fromisoformat(spawned_at.replace("Z", "+00:00"))
                spawn_time = dt.strftime("%m-%d %H:%M")
            except:
                spawn_time = spawned_at[:16]
        else:
            spawn_time = "N/A"
        
        print(
            f"{idx:<5} "
            f"{spawn_time:<17} "
            f"{distance_from_depot_km:<16.2f} "
            f"{start_address:<42} "
            f"{stop_address:<42} "
            f"{commute_distance_km:<12.2f}"
        )
    
    print("-" * 180)
    print(f"Total: {len(route_passengers)} route passengers (ordered by distance from depot)")
    print()
    
    # Summary statistics
    positions = [p.get("route_position_m", 0) for p in route_passengers]
    distances = [p.get("travel_distance_km", 0) for p in route_passengers]
    
    print("SUMMARY STATISTICS")
    print("-" * 50)
    print(f"Time window: {day_of_week.capitalize()} {start_hour:02d}:00-{end_hour:02d}:00")
    
    if positions:
        min_pos_km = min(positions) / 1000.0
        max_pos_km = max(positions) / 1000.0
        print(f"Pickup locations: {min_pos_km:.2f} km to {max_pos_km:.2f} km from depot")
        print(f"Route coverage distance: {max_pos_km:.2f} km")
    
    if distances:
        print(f"Average commute distance: {sum(distances) / len(distances):.2f} km")
        print(f"Min commute distance: {min(distances):.2f} km")
        print(f"Max commute distance: {max(distances):.2f} km")
    
    # Get total route length from first passenger (should all have same route)
    if route_passengers:
        # Note: We'd need to query the route geometry to get actual total route length
        # For now, use the max pickup position as an approximation
        print(f"\nNote: Route length shown is based on furthest passenger pickup location ({max_pos_km:.2f} km)")
    print()


async def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Display route passenger manifest table filtered by day and time"
    )
    parser.add_argument(
        "--route",
        type=str,
        default=None,
        help="Filter by route ID (e.g., ROUTE_1)"
    )
    parser.add_argument(
        "--day",
        type=str,
        default="monday",
        choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        help="Day of week (default: monday)"
    )
    parser.add_argument(
        "--start-hour",
        type=int,
        default=7,
        help="Start hour (0-23, default: 7 for morning peak)"
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=9,
        help="End hour (0-23, default: 9 for morning peak)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of passengers to fetch (default: 1000)"
    )
    
    args = parser.parse_args()
    
    print("=" * 180)
    print("ROUTE PASSENGER MANIFEST")
    print("=" * 180)
    
    if args.route:
        print(f"Route: {args.route}")
    else:
        print("Route: All routes")
    
    print(f"Day: {args.day.capitalize()}")
    print(f"Time window: {args.start_hour:02d}:00 - {args.end_hour:02d}:00")
    print(f"Limit: {args.limit}")
    print()
    
    # Fetch passengers filtered by day and time
    print("Fetching and filtering manifest...")
    passengers = await fetch_and_filter_manifest(
        route_id=args.route,
        day_of_week=args.day,
        start_hour=args.start_hour,
        end_hour=args.end_hour,
        limit=args.limit
    )
    
    print(f"✅ Found {len(passengers)} passengers matching criteria")
    
    if not passengers:
        print("❌ No passengers found for this time window")
        return
    
    # Display table (passengers are already enriched from manifest API)
    display_manifest_table(passengers, args.day, args.start_hour, args.end_hour)


if __name__ == "__main__":
    asyncio.run(main())
