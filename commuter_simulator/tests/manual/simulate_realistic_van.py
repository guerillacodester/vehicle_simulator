"""
REALISTIC van service simulation - passengers spawn naturally throughout morning.
Van picks up whoever is waiting when it arrives at each stop.
"""
from datetime import datetime, timedelta
import random
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    R = 6371000
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
    """Beta-like distribution - destinations cluster at commercial zones."""
    if alighting_pos <= boarding_pos:
        return 0.0
    
    travel_fraction = alighting_pos - boarding_pos
    
    # Favor destinations in 70-95% range
    if 0.7 <= alighting_pos <= 0.95:
        return travel_fraction * 2.0
    else:
        return travel_fraction * 0.5

def calculate_van_travel_time(distance_meters):
    """Calculate travel time at 30 km/h."""
    avg_speed_mps = 30 * 1000 / 3600
    return distance_meters / avg_speed_mps

# Simplified Route 1 (21 key stops)
route_coordinates = [
    (-59.6145, 13.3294), (-59.6120, 13.3280), (-59.6095, 13.3265), (-59.6070, 13.3250),
    (-59.6045, 13.3235), (-59.6020, 13.3220), (-59.5995, 13.3205), (-59.5970, 13.3190),
    (-59.5945, 13.3175), (-59.5920, 13.3160), (-59.5895, 13.3145), (-59.5870, 13.3130),
    (-59.5845, 13.3115), (-59.5820, 13.3100), (-59.5795, 13.3085), (-59.5770, 13.3070),
    (-59.5745, 13.3055), (-59.5720, 13.3040), (-59.5695, 13.3025), (-59.5670, 13.3010),
    (-59.5645, 13.2995),
]

cumulative_distances = calculate_cumulative_distances(route_coordinates)
total_route_length = cumulative_distances[-1]

print("="*120)
print("REALISTIC VAN SERVICE SIMULATION - Route 1 Morning Peak")
print("="*120)

print(f"\nRoute: Route 1 (Saint Lucy -> Saint Peter)")
print(f"Length: {total_route_length/1000:.2f}km | Stops: {len(route_coordinates)}")

# Van configuration
VAN_CAPACITY = 16
VAN_DEPARTURE = datetime(2025, 10, 26, 7, 0)
BOARDING_TIME = 5   # seconds per passenger
ALIGHTING_TIME = 3  # seconds per passenger

print(f"\nVan: 16 seats | Departs 07:00 | Speed 30 km/h | Board {BOARDING_TIME}s | Alight {ALIGHTING_TIME}s")

# Generate REALISTIC passenger spawns (natural distribution throughout morning)
random.seed(42)
passengers = []
passenger_id = 1

# Morning peak: 6:00-9:00 AM (passengers arrive at stops naturally)
hourly_rates = {6: 1.5, 7: 2.5, 8: 2.8, 9: 1.8}
base_spawns = 30

print(f"\nGenerating realistic passenger demand (6:00-9:00 AM)...")

for hour in [6, 7, 8, 9]:
    total_spawns = int(base_spawns * hourly_rates.get(hour, 1.0))
    
    for _ in range(total_spawns):
        # Random spawn time within hour
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        spawn_time = datetime(2025, 10, 26, hour, minute, second)
        
        # Boarding location (exponential decay)
        weights = [boarding_probability(d / total_route_length) for d in cumulative_distances]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        board_idx = random.choices(range(len(route_coordinates)), weights=normalized_weights, k=1)[0]
        board_dist = cumulative_distances[board_idx]
        
        # Alighting location
        alight_weights = [alighting_probability(
            board_dist / total_route_length,
            d / total_route_length
        ) for d in cumulative_distances]
        alight_total = sum(alight_weights)
        
        if alight_total > 0:
            alight_normalized = [w / alight_total for w in alight_weights]
            alight_idx = random.choices(range(len(route_coordinates)), weights=alight_normalized, k=1)[0]
        else:
            alight_idx = len(route_coordinates) - 1
        
        alight_dist = cumulative_distances[alight_idx]
        
        passengers.append({
            'id': passenger_id,
            'spawn_time': spawn_time,
            'board_idx': board_idx,
            'board_dist': board_dist,
            'alight_idx': alight_idx,
            'alight_dist': alight_dist,
            'status': 'waiting',
            'board_time': None,
            'alight_time': None,
            'wait_time': None,
            'ride_time': None
        })
        passenger_id += 1

# Sort by boarding position for processing
passengers_by_position = sorted(passengers, key=lambda p: p['board_dist'])

total = len(passengers)
by_hour = {h: sum(1 for p in passengers if p['spawn_time'].hour == h) for h in [6, 7, 8, 9]}
print(f"Generated {total} passengers: 6AM={by_hour[6]} | 7AM={by_hour[7]} | 8AM={by_hour[8]} | 9AM={by_hour[9]}")

# Simulate van journey
print("\n" + "="*120)
print("VAN JOURNEY SIMULATION (Stops with Activity)")
print("="*120)

van_time = VAN_DEPARTURE
van_position = 0.0
passengers_onboard = []
passengers_picked_up = []
passengers_missed = []
stops = []

print(f"\n{'Stop':<5} {'Pos':<7} {'Dist':<9} {'Arrive':<9} {'Waiting':<8} {'Alight':<7} {'Board':<7} {'Miss':<6} {'Onboard':<8} {'Depart':<9} {'Stop Time':<10}")
print("-" * 120)

for stop_idx in range(len(route_coordinates)):
    stop_dist = cumulative_distances[stop_idx]
    
    # Travel to stop
    distance_to_travel = stop_dist - van_position
    if distance_to_travel > 0:
        travel_time = calculate_van_travel_time(distance_to_travel)
        van_time += timedelta(seconds=travel_time)
        van_position = stop_dist
    
    # Who's alighting here?
    alighting = [p for p in passengers_onboard if p['alight_idx'] == stop_idx]
    
    # Who's waiting here (spawned before van arrived)?
    waiting = [p for p in passengers_by_position 
               if p['board_idx'] == stop_idx 
               and p['status'] == 'waiting'
               and p['spawn_time'] <= van_time]
    
    # How many can board after people alight?
    seats_available = VAN_CAPACITY - (len(passengers_onboard) - len(alighting))
    boarding = waiting[:seats_available]
    missed = waiting[seats_available:]
    
    # Only record stops with activity
    if alighting or boarding or missed:
        arrival_time = van_time
        
        # Process alighting (they get off first)
        for p in alighting:
            p['alight_time'] = van_time
            p['ride_time'] = (van_time - p['board_time']).total_seconds()
            p['status'] = 'completed'
            passengers_onboard.remove(p)
        
        van_time += timedelta(seconds=len(alighting) * ALIGHTING_TIME)
        
        # Process boarding
        for p in boarding:
            p['board_time'] = van_time
            p['wait_time'] = (van_time - p['spawn_time']).total_seconds()
            p['status'] = 'onboard'
            passengers_onboard.append(p)
            passengers_picked_up.append(p)
        
        van_time += timedelta(seconds=len(boarding) * BOARDING_TIME)
        
        # Mark missed passengers
        for p in missed:
            p['status'] = 'missed_full'
            passengers_missed.append(p)
        
        stop_time = (van_time - arrival_time).total_seconds()
        
        print(f"{stop_idx:<5} {stop_dist/total_route_length*100:>6.1f}% {stop_dist:>8.0f}m "
              f"{arrival_time.strftime('%H:%M:%S'):<9} {len(waiting):<8} "
              f"{len(alighting):<7} {len(boarding):<7} {len(missed):<6} "
              f"{len(passengers_onboard):<8} {van_time.strftime('%H:%M:%S'):<9} {stop_time:.0f}s")
        
        stops.append({
            'idx': stop_idx,
            'waiting': len(waiting),
            'alighting': len(alighting),
            'boarding': len(boarding),
            'missed': len(missed),
            'onboard': len(passengers_onboard)
        })

# Count passengers who spawned after van passed their stop
missed_spawned_late = [p for p in passengers if p['status'] == 'waiting']

print("\n" + "="*120)
print("SUMMARY STATISTICS")
print("="*120)

print(f"\nTotal passengers (6:00-9:00 AM): {total}")
print(f"  Picked up: {len(passengers_picked_up)} ({len(passengers_picked_up)/total*100:.1f}%)")
print(f"  Missed (van full): {len(passengers_missed)} ({len(passengers_missed)/total*100:.1f}%)")
print(f"  Spawned after van passed: {len(missed_spawned_late)} ({len(missed_spawned_late)/total*100:.1f}%)")
print(f"  Completed journey: {sum(1 for p in passengers if p['status'] == 'completed')}")

if passengers_picked_up:
    wait_times = [p['wait_time']/60 for p in passengers_picked_up]
    print(f"\nWait times (picked up passengers):")
    print(f"  Average: {sum(wait_times)/len(wait_times):.1f} min")
    print(f"  Range: {min(wait_times):.1f} - {max(wait_times):.1f} min")

completed = [p for p in passengers if p['status'] == 'completed']
if completed:
    ride_times = [p['ride_time']/60 for p in completed]
    print(f"\nRide times (completed trips):")
    print(f"  Average: {sum(ride_times)/len(ride_times):.1f} min")
    print(f"  Range: {min(ride_times):.1f} - {max(ride_times):.1f} min")

journey_time = (van_time - VAN_DEPARTURE).total_seconds() / 60
print(f"\nVan journey:")
print(f"  {VAN_DEPARTURE.strftime('%H:%M:%S')} -> {van_time.strftime('%H:%M:%S')} ({journey_time:.1f} minutes)")
print(f"  Stops with activity: {len(stops)}")
print(f"  Max occupancy: {max(s['onboard'] for s in stops)} passengers")

# Detailed passenger table
print("\n" + "="*120)
print(f"PASSENGER DETAILS (First 50 of {len(passengers_picked_up)} picked up)")
print("="*120)

print(f"\n{'ID':<5} {'Spawn':<9} {'Board':<7} {'Alight':<7} {'Wait':<11} {'Boarded':<9} {'Alighted':<9} {'Ride':<11} {'Status':<12}")
print("-" * 120)

for p in passengers_picked_up[:50]:
    spawn = p['spawn_time'].strftime('%H:%M:%S')
    board_pct = f"{p['board_dist']/total_route_length*100:.1f}%"
    alight_pct = f"{p['alight_dist']/total_route_length*100:.1f}%"
    wait = f"{p['wait_time']/60:.1f} min"
    boarded = p['board_time'].strftime('%H:%M:%S')
    alighted = p['alight_time'].strftime('%H:%M:%S') if p['alight_time'] else "onboard"
    ride = f"{p['ride_time']/60:.1f} min" if p['ride_time'] else "---"
    status = p['status']
    
    print(f"{p['id']:<5} {spawn:<9} {board_pct:<7} {alight_pct:<7} {wait:<11} {boarded:<9} {alighted:<9} {ride:<11} {status:<12}")

print("\n" + "="*120)
print("INSIGHTS")
print("="*120)

coverage = len(passengers_picked_up) / total * 100
print(f"\nService coverage: {coverage:.1f}%")

if coverage >= 80:
    print("✓ EXCELLENT: Van serving most morning demand")
elif coverage >= 50:
    print("⚠️  MODERATE: Significant demand unmet - consider:")
    print("   - Deploy second van at 7:15 or 7:30")
    print("   - Increase frequency during peak hours")
else:
    print("⚠️  POOR: Most passengers not served - need:")
    print("   - Multiple vans (every 15-20 minutes)")
    print("   - Higher capacity vehicles")

if len(passengers_missed) > 0:
    print(f"\n🚐 {len(passengers_missed)} passengers couldn't board (van full)")
    print("   This represents unmet demand at specific stops")

if len(missed_spawned_late) > 0:
    print(f"\n⏰ {len(missed_spawned_late)} passengers arrived after van passed")
    print("   These need later departure times (follow-up services)")
