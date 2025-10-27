"""
Simulate a 16-seat van serving Route 1 spawns.
Van departs origin at 7:00 AM and picks up passengers along the route.
"""
from datetime import datetime, timedelta
import random
import math

def get_route_1_coordinates():
    """Fetch Route 1 coordinates from Strapi."""
    import requests
    
    strapi_url = "http://localhost:1337"
    route_endpoint = f"{strapi_url}/api/routes?populate=*&filters[short_name][$eq]=1"
    
    response = requests.get(route_endpoint)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch route: {response.status_code}")
    
    route_data = response.json()
    route = route_data['data'][0]
    
    # Extract coordinates from geometry
    geometry = route['geometry']
    if geometry['type'] == 'LineString':
        coordinates = geometry['coordinates']
    else:
        raise Exception(f"Unexpected geometry type: {geometry['type']}")
    
    return coordinates, route

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calculate_cumulative_distances(coordinates):
    """Calculate cumulative distance along route."""
    distances = [0.0]
    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i-1]
        lon2, lat2 = coordinates[i]
        segment_dist = haversine_distance(lat1, lon1, lat2, lon2)
        distances.append(distances[-1] + segment_dist)
    return distances

def boarding_probability(position_fraction):
    """Exponential decay probability for boarding location."""
    return math.exp(-2.5 * position_fraction)

def generate_spawn_time(hour, minute_fraction):
    """Generate spawn time for a given hour."""
    minutes = int(minute_fraction * 60)
    return datetime(2025, 10, 26, hour, minutes)

def calculate_van_travel_time(distance_meters):
    """
    Calculate van travel time based on distance.
    Assumptions:
    - Average speed: 30 km/h in urban/residential areas
    - Stop time: 10 seconds per pickup
    """
    avg_speed_mps = 30 * 1000 / 3600  # 30 km/h = 8.33 m/s
    travel_time_seconds = distance_meters / avg_speed_mps
    return travel_time_seconds

print("="*100)
print("VAN SERVICE SIMULATION - Route 1 Morning Peak (7:00-9:00 AM)")
print("="*100)

# Fetch route data
coordinates, route = get_route_1_coordinates()
cumulative_distances = calculate_cumulative_distances(coordinates)
total_route_length = cumulative_distances[-1]

print(f"\nRoute: {route['name']} (#{route['id']})")
print(f"Length: {total_route_length/1000:.2f}km")
print(f"Coordinates: {len(coordinates)} points")

# Van parameters
VAN_CAPACITY = 16
VAN_DEPARTURE_TIME = datetime(2025, 10, 26, 7, 0)  # 7:00 AM
STOP_TIME_SECONDS = 10  # Time to pick up passenger

print(f"\nVan Configuration:")
print(f"  Capacity: {VAN_CAPACITY} seats")
print(f"  Departure: {VAN_DEPARTURE_TIME.strftime('%H:%M')}")
print(f"  Average speed: 30 km/h")
print(f"  Stop time: {STOP_TIME_SECONDS}s per pickup")

# Generate spawns for 7:00-9:00 AM
print("\nGenerating spawns...")
random.seed(42)  # Reproducible results

spawns = []
spawn_id = 1

# Hourly rates from config
hourly_rates = {7: 2.5, 8: 2.8}

# Generate spawns for each hour
for hour in [7, 8]:
    hourly_rate = hourly_rates[hour]
    base_spawns_per_hour = 30  # Base for inter-parish route
    total_spawns_this_hour = int(base_spawns_per_hour * hourly_rate)
    
    for _ in range(total_spawns_this_hour):
        # Generate random minute within the hour
        minute_fraction = random.random()
        spawn_time = generate_spawn_time(hour, minute_fraction)
        
        # Calculate boarding probability weights
        weights = [boarding_probability(d / total_route_length) for d in cumulative_distances]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Select boarding position
        boarding_idx = random.choices(range(len(coordinates)), weights=normalized_weights, k=1)[0]
        boarding_distance = cumulative_distances[boarding_idx]
        boarding_position = boarding_distance / total_route_length
        lon, lat = coordinates[boarding_idx]
        
        spawns.append({
            'id': spawn_id,
            'time': spawn_time,
            'position_fraction': boarding_position,
            'distance_meters': boarding_distance,
            'lat': lat,
            'lon': lon,
            'hour': hour
        })
        spawn_id += 1

# Sort spawns by position along route
spawns_by_position = sorted(spawns, key=lambda s: s['distance_meters'])

print(f"Total spawns generated: {len(spawns)}")
print(f"  7:00 AM hour: {sum(1 for s in spawns if s['hour'] == 7)}")
print(f"  8:00 AM hour: {sum(1 for s in spawns if s['hour'] == 8)}")

# Simulate van journey
print("\n" + "="*100)
print("VAN JOURNEY SIMULATION")
print("="*100)

van_time = VAN_DEPARTURE_TIME
van_position = 0.0  # meters along route
passengers_picked_up = []
passengers_missed = []
van_full_time = None

print(f"\n{'#':<4} {'Spawn':<6} {'Pos':<6} {'Dist':<8} {'Wait':<12} {'Van':<6} {'Pickup':<8} {'Status':<15}")
print("-" * 100)

for spawn in spawns_by_position:
    spawn_id = spawn['id']
    spawn_time = spawn['time']
    spawn_position = spawn['distance_meters']
    
    # Calculate van travel time to this position
    distance_to_travel = spawn_position - van_position
    
    if distance_to_travel < 0:
        # Van already passed this point
        passengers_missed.append({
            'spawn': spawn,
            'reason': 'Van already passed',
            'van_time': van_time.strftime('%H:%M:%S')
        })
        continue
    
    travel_time = calculate_van_travel_time(distance_to_travel)
    van_arrival_time = van_time + timedelta(seconds=travel_time)
    
    # Check if passenger spawned before van arrives
    if spawn_time > van_arrival_time:
        # Passenger spawns AFTER van passes - MISSED
        wait_time = "N/A"
        passengers_missed.append({
            'spawn': spawn,
            'reason': f'Spawned after van passed ({spawn_time.strftime("%H:%M:%S")} > {van_arrival_time.strftime("%H:%M:%S")})',
            'van_time': van_arrival_time.strftime('%H:%M:%S')
        })
        status = "MISSED (late)"
        van_arrival = van_arrival_time.strftime('%H:%M')
        pickup_time = "---"
    else:
        # Passenger waiting when van arrives
        wait_seconds = (van_arrival_time - spawn_time).total_seconds()
        wait_minutes = wait_seconds / 60
        
        if len(passengers_picked_up) < VAN_CAPACITY:
            # Van has space - PICKUP
            passengers_picked_up.append({
                'spawn': spawn,
                'wait_time_seconds': wait_seconds,
                'pickup_time': van_arrival_time
            })
            
            # Update van state
            van_time = van_arrival_time + timedelta(seconds=STOP_TIME_SECONDS)
            van_position = spawn_position
            
            if len(passengers_picked_up) == VAN_CAPACITY:
                van_full_time = van_time
            
            wait_time = f"{wait_minutes:.1f} min"
            status = f"PICKED UP ({len(passengers_picked_up)}/{VAN_CAPACITY})"
            van_arrival = van_arrival_time.strftime('%H:%M')
            pickup_time = van_arrival_time.strftime('%H:%M:%S')
        else:
            # Van is full - MISSED
            passengers_missed.append({
                'spawn': spawn,
                'reason': f'Van full (capacity {VAN_CAPACITY})',
                'van_time': van_arrival_time.strftime('%H:%M:%S')
            })
            wait_time = f"{wait_minutes:.1f} min"
            status = "MISSED (full)"
            van_arrival = van_arrival_time.strftime('%H:%M')
            pickup_time = "---"
    
    print(f"{spawn_id:<4} {spawn_time.strftime('%H:%M'):<6} {spawn['position_fraction']*100:>5.1f}% "
          f"{spawn['distance_meters']:>7.0f}m {wait_time:<12} {van_arrival:<6} {pickup_time:<8} {status:<15}")

# Summary statistics
print("\n" + "="*100)
print("SUMMARY STATISTICS")
print("="*100)

print(f"\nTotal spawns: {len(spawns)}")
print(f"  Passengers picked up: {len(passengers_picked_up)} ({len(passengers_picked_up)/len(spawns)*100:.1f}%)")
print(f"  Passengers missed: {len(passengers_missed)} ({len(passengers_missed)/len(spawns)*100:.1f}%)")

if passengers_picked_up:
    avg_wait = sum(p['wait_time_seconds'] for p in passengers_picked_up) / len(passengers_picked_up) / 60
    max_wait = max(p['wait_time_seconds'] for p in passengers_picked_up) / 60
    min_wait = min(p['wait_time_seconds'] for p in passengers_picked_up) / 60
    
    print(f"\nWait time statistics (picked up passengers):")
    print(f"  Average wait: {avg_wait:.1f} minutes")
    print(f"  Maximum wait: {max_wait:.1f} minutes")
    print(f"  Minimum wait: {min_wait:.1f} minutes")

if van_full_time:
    print(f"\nVan reached capacity at: {van_full_time.strftime('%H:%M:%S')}")
    distance_when_full = passengers_picked_up[VAN_CAPACITY-1]['spawn']['distance_meters']
    print(f"  Position when full: {distance_when_full/total_route_length*100:.1f}% ({distance_when_full:.0f}m)")

print(f"\nMissed passengers breakdown:")
missed_late_spawn = sum(1 for p in passengers_missed if 'late' in p['reason'])
missed_full = sum(1 for p in passengers_missed if 'full' in p['reason'])
missed_passed = sum(1 for p in passengers_missed if 'passed' in p['reason'])

print(f"  Spawned too late: {missed_late_spawn}")
print(f"  Van already full: {missed_full}")
print(f"  Van already passed: {missed_passed}")

print("\n" + "="*100)
print("OPERATIONAL INSIGHTS")
print("="*100)

pickup_rate = len(passengers_picked_up) / len(spawns) * 100
print(f"\nPickup rate: {pickup_rate:.1f}%")

if pickup_rate < 50:
    print("⚠️  LOW: Less than half of passengers picked up")
    print("   Recommendation: Increase service frequency or vehicle capacity")
elif pickup_rate < 80:
    print("⚠️  MODERATE: Some passengers missing service")
    print("   Recommendation: Consider adding another van 15-30 minutes later")
else:
    print("✓ GOOD: Most passengers served")

if missed_late_spawn > 0:
    print(f"\n⏰ {missed_late_spawn} passengers spawned after van passed their location")
    print("   These passengers need a later departure time to be served")

if missed_full > 0:
    print(f"\n🚐 {missed_full} passengers missed because van was full")
    print("   Van reached capacity and couldn't pick up remaining passengers")
    print("   Recommendation: Deploy second van or increase capacity")
