"""
Vehicle Simulation Test Script
===============================

Simulates a vehicle driving along a route, picking up passengers from database.
- Takes departure time and route as arguments
- Picks up passengers encountered along route
- Deletes picked-up passengers from database
- Reports passenger wait times
- Leaves missed passengers in database

Usage:
    python test_vehicle_simulation.py --route ROUTE_ID --depart "09:05:00" [--speed 30]
    
Example:
    python test_vehicle_simulation.py --route gg3pv3z19hhm117v9xth5ezq --depart "09:05:00" --speed 30
"""

import asyncio
import argparse
from datetime import datetime, timedelta, timezone
import math
import httpx
import time  # Add time for delay

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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Vehicle simulation - pickup passengers from database')
    parser.add_argument('--route', type=str, default='gg3pv3z19hhm117v9xth5ezq', 
                        help='Route document ID (default: Route 1)')
    parser.add_argument('--depart', type=str, required=True,
                        help='Departure time in HH:MM:SS format (e.g., 09:05:00)')
    parser.add_argument('--speed', type=float, default=30.0,
                        help='Vehicle speed in km/h (default: 30)')
    parser.add_argument('--pickup-radius', type=float, default=100.0,
                        help='Pickup radius in meters (default: 100)')
    
    args = parser.parse_args()
    
    # Parse departure time (use UTC for consistency)
    try:
        time_parts = args.depart.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
        # Create timezone-aware UTC datetime
        DEPART_TIME = datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=second, microsecond=0)
    except Exception as e:
        print(f"ERROR: Invalid departure time format '{args.depart}'. Use HH:MM:SS (e.g., 09:05:00)")
        return
    
    ROUTE_ID = args.route
    VAN_SPEED_KMH = args.speed
    PICKUP_RADIUS_METERS = args.pickup_radius
    
    print("="*120)
    print("VEHICLE SIMULATION - Passenger Pickup")
    print("="*120)
    
    print(f"\nConfiguration:")
    print(f"  Route: {ROUTE_ID}")
    print(f"  Departure Time: {DEPART_TIME.strftime('%H:%M:%S')}")
    print(f"  Vehicle Speed: {VAN_SPEED_KMH} km/h")
    print(f"  Pickup Radius: {PICKUP_RADIUS_METERS}m")
    
    # Get route geometry
    print("\n[STEP 1/3] Loading route geometry...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8001/spatial/route-geometry/{ROUTE_ID}")
            response.raise_for_status()
            route_geom = response.json()
        except Exception as e:
            print(f"ERROR: Failed to load route geometry: {e}")
            return
    
    route_coords = route_geom['coordinates']  # List of [lat, lon]
    total_distance = route_geom['total_distance_meters']
    
    print(f"OK - Route has {len(route_coords)} points, total distance: {total_distance:.1f}m")
    
    # Calculate cumulative distances along route
    cumulative_distances = [0.0]
    for i in range(1, len(route_coords)):
        lat1, lon1 = route_coords[i-1]
        lat2, lon2 = route_coords[i]
        segment_dist = haversine_distance(lat1, lon1, lat2, lon2)
        cumulative_distances.append(cumulative_distances[-1] + segment_dist)
    
    # Query all passengers for this route
    print("\n[STEP 2/3] Loading passengers from database...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:1337/api/active-passengers",
                params={
                    "filters[route_id][$eq]": ROUTE_ID,
                    "filters[status][$eq]": "WAITING",
                    "pagination[pageSize]": 1000
                }
            )
            all_passengers_data = response.json()
        except Exception as e:
            print(f"ERROR: Failed to load passengers: {e}")
            return
    
    all_passengers = []
    for p in all_passengers_data.get('data', []):
        # Handle both Strapi v4 (attributes) and v5 (flat) formats
        attrs = p.get('attributes', p)
        all_passengers.append({
            'id': p.get('id'),
            'documentId': p.get('documentId'),  # Store documentId as well
            'passenger_id': attrs.get('passenger_id'),
            'latitude': attrs.get('latitude'),
            'longitude': attrs.get('longitude'),
            'destination_lat': attrs.get('destination_lat'),
            'destination_lon': attrs.get('destination_lon'),
            'destination_name': attrs.get('destination_name'),
            'spawned_at': attrs.get('spawned_at')
        })
    
    print(f"OK - Found {len(all_passengers)} waiting passengers in database")
    
    if len(all_passengers) == 0:
        print("\nNo passengers to pick up. Run test_commuter_spawn.py first to generate passengers.")
        return
    
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
    
    # Sort passengers by route position
    all_passengers.sort(key=lambda p: p['route_position'])
    
    # Simulate vehicle journey
    print(f"\n[STEP 3/3] Simulating vehicle journey (departs {DEPART_TIME.strftime('%H:%M:%S')})...")
    
    van_speed_mps = (VAN_SPEED_KMH * 1000) / 3600  # Convert to meters per second
    picked_up_passengers = []
    missed_passengers = []
    
    current_distance = 0.0
    current_time = DEPART_TIME
    
    for passenger in all_passengers:
        # Vehicle travels to passenger position
        distance_to_passenger = passenger['route_position'] - current_distance
        
        if distance_to_passenger > 0:
            travel_time_seconds = distance_to_passenger / van_speed_mps
            current_time += timedelta(seconds=travel_time_seconds)
            current_distance = passenger['route_position']
        
        # Check if passenger spawned before vehicle arrived AND is within pickup radius
        passenger_spawn_time = datetime.fromisoformat(passenger['spawned_at'].replace('Z', '+00:00'))
        
        if passenger_spawn_time < current_time and passenger['distance_to_route'] <= PICKUP_RADIUS_METERS:
            # PICKUP!
            wait_time_seconds = (current_time - passenger_spawn_time).total_seconds()
            picked_up_passengers.append({
                **passenger,
                'spawn_time': passenger_spawn_time,
                'pickup_time': current_time,
                'wait_time_seconds': wait_time_seconds
            })
            
            # Remove from database (use documentId for Strapi v5)
            async with httpx.AsyncClient() as client:
                try:
                    delete_url = f"http://localhost:1337/api/active-passengers/{passenger['documentId']}"
                    delete_response = await client.delete(delete_url)
                    if delete_response.status_code in (200, 204):
                        print(f"[OK] Deleted passenger {passenger['passenger_id']}")
                    else:
                        print(f"[WARNING] Delete returned status {delete_response.status_code} for {passenger['passenger_id']}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete passenger {passenger['passenger_id']}: {e}")
        else:
            # MISSED!
            reason = 'not_spawned_yet' if passenger_spawn_time >= current_time else 'too_far_from_route'
            missed_passengers.append({
                **passenger,
                'reason': reason,
                'vehicle_arrival_time': current_time
            })
    
    print(f"OK - Vehicle journey complete")
    print(f"  Picked up: {len(picked_up_passengers)} passengers (deleted from database)")
    print(f"  Missed: {len(missed_passengers)} passengers (left in database)")
    
    # Get total route distance
    total_route_distance = cumulative_distances[-1] if cumulative_distances else 0
    
    # Output results
    print("\n" + "="*150)
    print("PICKED-UP PASSENGERS REPORT")
    print("="*150)
    
    if picked_up_passengers:
        print(f"\n{'Seq':<5} {'Passenger ID':<15} {'Spawn Time':<12} {'Pickup Time':<12} {'Wait (min)':<12} {'Dist fr Start (m)':<18} {'Dist fr End (m)':<16}")
        print("-" * 150)
        
        total_wait_seconds = 0
        for idx, p in enumerate(picked_up_passengers, 1):
            dist_from_start = p['route_position']
            dist_from_end = total_route_distance - p['route_position']
            wait_minutes = p['wait_time_seconds'] / 60.0
            total_wait_seconds += p['wait_time_seconds']
            
            print(
                f"{idx:<5} "
                f"{p['passenger_id']:<15} "
                f"{p['spawn_time'].strftime('%H:%M:%S'):<12} "
                f"{p['pickup_time'].strftime('%H:%M:%S'):<12} "
                f"{wait_minutes:<12.1f} "
                f"{dist_from_start:<18.1f} "
                f"{dist_from_end:<16.1f}"
            )
        
        # Summary statistics
        avg_wait_minutes = total_wait_seconds / len(picked_up_passengers) / 60.0
        print(f"\nSummary: {len(picked_up_passengers)} passengers picked up")
        print(f"  Total Wait Time: {total_wait_seconds/60.0:.1f} minutes ({total_wait_seconds} seconds)")
        print(f"  Average Wait: {avg_wait_minutes:.1f} minutes")
    else:
        print("\nNo passengers picked up")
    
    if missed_passengers:
        print(f"\n\nMISSED PASSENGERS ({len(missed_passengers)}) - LEFT IN DATABASE:")
        print(f"{'Seq':<5} {'Passenger ID':<15} {'Spawn Time':<12} {'Vehicle Time':<12} {'Reason':<25} {'Dist fr Start (m)':<18} {'Dist fr End (m)':<16}")
        print("-" * 150)
        for idx, p in enumerate(missed_passengers, 1):
            dist_from_start = p['route_position']
            dist_from_end = total_route_distance - p['route_position']
            spawn_time = datetime.fromisoformat(p['spawned_at'].replace('Z', '+00:00'))
            
            print(
                f"{idx:<5} "
                f"{p['passenger_id']:<15} "
                f"{spawn_time.strftime('%H:%M:%S'):<12} "
                f"{p['vehicle_arrival_time'].strftime('%H:%M:%S'):<12} "
                f"{p['reason']:<25} "
                f"{dist_from_start:<18.1f} "
                f"{dist_from_end:<16.1f}"
            )
    
    # Summary statistics
    if picked_up_passengers:
        total_wait_time = sum(p['wait_time_seconds'] for p in picked_up_passengers)
        avg_wait_time = total_wait_time / len(picked_up_passengers)
        
        print(f"\n" + "="*150)
        print("PICKUP SUMMARY")
        print("="*150)
        print(f"Total Passengers Picked Up: {len(picked_up_passengers)}")
        print(f"Total Wait Time (all passengers): {total_wait_time:.0f} seconds ({total_wait_time/60:.1f} minutes)")
        print(f"Average Wait Time per Passenger: {avg_wait_time:.0f} seconds ({avg_wait_time/60:.1f} minutes)")
    
    print("\n" + "="*120)
    print("VEHICLE SIMULATION COMPLETE")
    print("="*120)


if __name__ == "__main__":
    asyncio.run(main())
