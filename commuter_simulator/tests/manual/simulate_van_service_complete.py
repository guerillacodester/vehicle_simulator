"""
Comprehensive van service simulation with boarding AND alighting.
Tracks passengers from pickup to drop-off with realistic stop times.
"""
from datetime import datetime, timedelta
import random
import math

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
    """Exponential decay for boarding location."""
    return math.exp(-2.5 * position_fraction)

def alighting_probability(boarding_pos, alighting_pos):
    """Beta-like distribution - cluster destinations at commercial zones."""
    if alighting_pos <= boarding_pos:
        return 0.0
    
    travel_fraction = alighting_pos - boarding_pos
    
    # Favor destinations in 70-95% range (commercial/destination areas)
    if 0.7 <= alighting_pos <= 0.95:
        return travel_fraction * 2.0
    else:
        return travel_fraction * 0.5

def calculate_van_travel_time(distance_meters):
    """Calculate travel time at 30 km/h average speed."""
    avg_speed_mps = 30 * 1000 / 3600  # 30 km/h = 8.33 m/s
    return distance_meters / avg_speed_mps

# Route 1 simplified coordinates (key points along the route)
# Based on actual Route 1: Saint Lucy -> Saint Peter (13.39km)
route_coordinates = [
    (-59.6145, 13.3294),  # 0% - Origin (Saint Lucy)
    (-59.6120, 13.3280),  # ~5%
    (-59.6095, 13.3265),  # ~10%
    (-59.6070, 13.3250),  # ~15%
    (-59.6045, 13.3235),  # ~20%
    (-59.6020, 13.3220),  # ~25%
    (-59.5995, 13.3205),  # ~30%
    (-59.5970, 13.3190),  # ~35%
    (-59.5945, 13.3175),  # ~40%
    (-59.5920, 13.3160),  # ~45%
    (-59.5895, 13.3145),  # ~50%
    (-59.5870, 13.3130),  # ~55%
    (-59.5845, 13.3115),  # ~60%
    (-59.5820, 13.3100),  # ~65%
    (-59.5795, 13.3085),  # ~70%
    (-59.5770, 13.3070),  # ~75%
    (-59.5745, 13.3055),  # ~80%
    (-59.5720, 13.3040),  # ~85%
    (-59.5695, 13.3025),  # ~90%
    (-59.5670, 13.3010),  # ~95%
    (-59.5645, 13.2995),  # 100% - Destination (Saint Peter)
]

cumulative_distances = calculate_cumulative_distances(route_coordinates)
total_route_length = cumulative_distances[-1]

print("="*120)
print("VAN SERVICE SIMULATION - Route 1 with Boarding AND Alighting")
print("="*120)

print(f"\nRoute Configuration:")
print(f"  Route: Route 1 (Saint Lucy -> Saint Peter)")
print(f"  Length: {total_route_length/1000:.2f}km")
print(f"  Stops: {len(route_coordinates)} key points")

# Van configuration
VAN_CAPACITY = 16
VAN_DEPARTURE_TIME = datetime(2025, 10, 26, 7, 0)
BOARDING_TIME = 5   # seconds per passenger boarding
ALIGHTING_TIME = 3  # seconds per passenger alighting

print(f"\nVan Configuration:")
print(f"  Capacity: {VAN_CAPACITY} seats")
print(f"  Departure: {VAN_DEPARTURE_TIME.strftime('%H:%M')}")
print(f"  Speed: 30 km/h average")
print(f"  Boarding time: {BOARDING_TIME}s/passenger")
print(f"  Alighting time: {ALIGHTING_TIME}s/passenger")

# Generate passenger spawns
random.seed(42)
passengers = []
passenger_id = 1

hourly_rates = {7: 2.5, 8: 2.8}
base_spawns_per_hour = 30

for hour in [7, 8]:
    total_spawns = int(base_spawns_per_hour * hourly_rates[hour])
    
    for _ in range(total_spawns):
        # Spawn time
        minute_fraction = random.random()
        spawn_time = datetime(2025, 10, 26, hour, int(minute_fraction * 60))
        
        # Boarding location (weighted by exponential decay)
        weights = [boarding_probability(d / total_route_length) for d in cumulative_distances]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        boarding_idx = random.choices(range(len(route_coordinates)), weights=normalized_weights, k=1)[0]
        boarding_distance = cumulative_distances[boarding_idx]
        
        # Alighting location (must be after boarding)
        alight_weights = [alighting_probability(
            boarding_distance / total_route_length,
            d / total_route_length
        ) for d in cumulative_distances]
        alight_total = sum(alight_weights)
        
        if alight_total > 0:
            alight_normalized = [w / alight_total for w in alight_weights]
            alight_idx = random.choices(range(len(route_coordinates)), weights=alight_normalized, k=1)[0]
        else:
            # Fallback to end of route
            alight_idx = len(route_coordinates) - 1
        
        alight_distance = cumulative_distances[alight_idx]
        
        passengers.append({
            'id': passenger_id,
            'spawn_time': spawn_time,
            'board_idx': boarding_idx,
            'board_distance': boarding_distance,
            'alight_idx': alight_idx,
            'alight_distance': alight_distance,
            'status': 'waiting',
            'board_time': None,
            'alight_time': None,
            'wait_time': None,
            'ride_time': None
        })
        passenger_id += 1

# Sort by boarding position
passengers_by_board = sorted(passengers, key=lambda p: p['board_distance'])

print(f"\nGenerated {len(passengers)} passenger spawns")
print(f"  7:00 AM: {sum(1 for p in passengers if p['spawn_time'].hour == 7)}")
print(f"  8:00 AM: {sum(1 for p in passengers if p['spawn_time'].hour == 8)}")

# Simulate van journey
print("\n" + "="*120)
print("VAN JOURNEY - Stop-by-Stop Simulation")
print("="*120)

van_time = VAN_DEPARTURE_TIME
van_position = 0.0
passengers_onboard = []
passengers_picked_up = []
passengers_missed = []

# Track all stops
stops = []

# Process each position along route
for position_idx in range(len(route_coordinates)):
    stop_position = cumulative_distances[position_idx]
    
    # Travel to this position
    distance_to_travel = stop_position - van_position
    if distance_to_travel > 0:
        travel_time = calculate_van_travel_time(distance_to_travel)
        van_time += timedelta(seconds=travel_time)
        van_position = stop_position
    
    # Check for alighting passengers
    alighting_here = [p for p in passengers_onboard if p['alight_idx'] == position_idx]
    
    # Check for boarding passengers
    boarding_here = [p for p in passengers_by_board 
                     if p['board_idx'] == position_idx 
                     and p['status'] == 'waiting'
                     and p['spawn_time'] <= van_time
                     and len(passengers_onboard) - len(alighting_here) + len([p for p in passengers_by_board 
                        if p['board_idx'] == position_idx 
                        and p['status'] == 'waiting'
                        and p['spawn_time'] <= van_time
                        and passengers_by_board.index(p) <= passengers_by_board.index(p)]) <= VAN_CAPACITY]
    
    # Recalculate boarding considering capacity after alighting
    boarding_candidates = [p for p in passengers_by_board 
                          if p['board_idx'] == position_idx 
                          and p['status'] == 'waiting'
                          and p['spawn_time'] <= van_time]
    
    seats_after_alight = VAN_CAPACITY - (len(passengers_onboard) - len(alighting_here))
    boarding_here = boarding_candidates[:seats_after_alight]
    missed_here = boarding_candidates[seats_after_alight:]
    
    # Only create stop if there's activity
    if alighting_here or boarding_here or missed_here:
        stop_info = {
            'idx': position_idx,
            'distance': stop_position,
            'position_pct': stop_position / total_route_length * 100,
            'arrival_time': van_time,
            'alighting': len(alighting_here),
            'boarding': len(boarding_here),
            'missed': len(missed_here),
            'onboard_after': 0,
            'departure_time': van_time
        }
        
        # Process alighting
        alight_time_total = 0
        for passenger in alighting_here:
            passenger['alight_time'] = van_time
            passenger['ride_time'] = (van_time - passenger['board_time']).total_seconds()
            passenger['status'] = 'completed'
            passengers_onboard.remove(passenger)
            alight_time_total += ALIGHTING_TIME
        
        van_time += timedelta(seconds=alight_time_total)
        
        # Process boarding
        board_time_total = 0
        for passenger in boarding_here:
            passenger['board_time'] = van_time
            passenger['wait_time'] = (van_time - passenger['spawn_time']).total_seconds()
            passenger['status'] = 'onboard'
            passengers_onboard.append(passenger)
            passengers_picked_up.append(passenger)
            board_time_total += BOARDING_TIME
        
        van_time += timedelta(seconds=board_time_total)
        
        # Process missed passengers
        for passenger in missed_here:
            passenger['status'] = 'missed'
            passengers_missed.append(passenger)
        
        stop_info['onboard_after'] = len(passengers_onboard)
        stop_info['departure_time'] = van_time
        stops.append(stop_info)

# Display stop-by-stop breakdown
print(f"\n{'Stop':<5} {'Pos':<6} {'Dist':<8} {'Arrive':<8} {'Alight':<7} {'Board':<7} {'Missed':<7} {'Onboard':<8} {'Depart':<8} {'Stop Time':<10}")
print("-" * 120)

for stop in stops:
    stop_duration = (stop['departure_time'] - stop['arrival_time']).total_seconds()
    
    print(f"{stop['idx']:<5} {stop['position_pct']:>5.1f}% {stop['distance']:>7.0f}m "
          f"{stop['arrival_time'].strftime('%H:%M:%S'):<8} "
          f"{stop['alighting']:<7} {stop['boarding']:<7} {stop['missed']:<7} "
          f"{stop['onboard_after']:<8} {stop['departure_time'].strftime('%H:%M:%S'):<8} "
          f"{stop_duration:.0f}s")

# Summary statistics
print("\n" + "="*120)
print("SUMMARY STATISTICS")
print("="*120)

print(f"\nTotal passengers: {len(passengers)}")
print(f"  Picked up: {len(passengers_picked_up)} ({len(passengers_picked_up)/len(passengers)*100:.1f}%)")
print(f"  Missed: {len(passengers_missed)} ({len(passengers_missed)/len(passengers)*100:.1f}%)")
print(f"  Completed journey: {sum(1 for p in passengers if p['status'] == 'completed')}")

# Missed passengers breakdown
spawned_late = sum(1 for p in passengers if p['status'] == 'waiting' 
                   and passengers_by_board.index(p) >= len([p2 for p2 in passengers_by_board if p2['board_idx'] <= p['board_idx']]))
missed_full = len(passengers_missed)

print(f"\nMissed passengers:")
print(f"  Van full: {missed_full}")
print(f"  Spawned after van passed: {len(passengers) - len(passengers_picked_up) - missed_full}")

if passengers_picked_up:
    avg_wait = sum(p['wait_time'] for p in passengers_picked_up) / len(passengers_picked_up) / 60
    max_wait = max(p['wait_time'] for p in passengers_picked_up) / 60
    min_wait = min(p['wait_time'] for p in passengers_picked_up) / 60
    
    print(f"\nWait times (passengers picked up):")
    print(f"  Average: {avg_wait:.1f} minutes")
    print(f"  Maximum: {max_wait:.1f} minutes")
    print(f"  Minimum: {min_wait:.1f} minutes")

completed = [p for p in passengers if p['status'] == 'completed']
if completed:
    avg_ride = sum(p['ride_time'] for p in completed) / len(completed) / 60
    max_ride = max(p['ride_time'] for p in completed) / 60
    min_ride = min(p['ride_time'] for p in completed) / 60
    
    print(f"\nRide times (completed journeys):")
    print(f"  Average: {avg_ride:.1f} minutes")
    print(f"  Maximum: {max_ride:.1f} minutes")
    print(f"  Minimum: {min_ride:.1f} minutes")

print(f"\nVan journey:")
print(f"  Departure: {VAN_DEPARTURE_TIME.strftime('%H:%M:%S')}")
print(f"  Arrival at terminus: {van_time.strftime('%H:%M:%S')}")
print(f"  Total journey time: {(van_time - VAN_DEPARTURE_TIME).total_seconds() / 60:.1f} minutes")
print(f"  Number of stops: {len(stops)}")

# Detailed passenger list
print("\n" + "="*120)
print("DETAILED PASSENGER BREAKDOWN (First 40)")
print("="*120)

print(f"\n{'ID':<4} {'Spawn':<8} {'Board':<6} {'Alight':<6} {'Wait':<10} {'Pickup':<8} {'Drop':<8} {'Ride':<10} {'Status':<12}")
print("-" * 120)

for i, p in enumerate(passengers_picked_up[:40]):
    spawn_str = p['spawn_time'].strftime('%H:%M')
    board_pct = p['board_distance'] / total_route_length * 100
    alight_pct = p['alight_distance'] / total_route_length * 100
    wait_str = f"{p['wait_time']/60:.1f} min" if p['wait_time'] else "---"
    pickup_str = p['board_time'].strftime('%H:%M:%S') if p['board_time'] else "---"
    drop_str = p['alight_time'].strftime('%H:%M:%S') if p['alight_time'] else "onboard"
    ride_str = f"{p['ride_time']/60:.1f} min" if p['ride_time'] else "---"
    status = p['status']
    
    print(f"{p['id']:<4} {spawn_str:<8} {board_pct:>5.1f}% {alight_pct:>5.1f}% "
          f"{wait_str:<10} {pickup_str:<8} {drop_str:<8} {ride_str:<10} {status:<12}")

print("\n" + "="*120)
print("OPERATIONAL INSIGHTS")
print("="*120)

pickup_rate = len(passengers_picked_up) / len(passengers) * 100
print(f"\nService coverage: {pickup_rate:.1f}% of passengers served")

if pickup_rate < 50:
    print("⚠️  CRITICAL: Less than half of demand served")
    print("   → Deploy additional vehicles immediately")
elif pickup_rate < 80:
    print("⚠️  MODERATE: Significant unmet demand")
    print("   → Consider adding a follow-up van 10-15 minutes later")
else:
    print("✓ GOOD: Most demand served adequately")

print(f"\nTotal stops made: {len(stops)}")
print(f"  Average passengers per stop: {sum(s['boarding'] + s['alighting'] for s in stops) / len(stops):.1f}")
print(f"  Maximum onboard at once: {max(s['onboard_after'] for s in stops)}")

if missed_full > 0:
    print(f"\n🚐 {missed_full} passengers couldn't board (van full)")
    print("   → Indicates need for higher capacity or more frequent service")
