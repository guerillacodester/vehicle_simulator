"""Quick script to check end-to-end terminal trips"""
import httpx
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

def find_closest_stop(lat, lon, coords):
    """Find closest stop index to given lat/lon using Haversine"""
    min_dist = float('inf')
    closest_idx = -1
    
    for idx, (stop_lon, stop_lat) in enumerate(coords):
        R = 6371000  # Earth radius in meters
        dlat = radians(lat - stop_lat)
        dlon = radians(lon - stop_lon)
        a = sin(dlat/2)**2 + cos(radians(stop_lat)) * cos(radians(lat)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        dist = R * c
        
        if dist < min_dist:
            min_dist = dist
            closest_idx = idx
    
    return closest_idx

# Fetch all active passengers
response = httpx.get(
    'http://localhost:1337/api/active-passengers',
    params={'pagination[pageSize]': 100}
)

data = response.json()
all_passengers = data.get('data', [])

# Filter for hour 17 on 2024-11-04
passengers = []
for p in all_passengers:
    spawn_time_str = p.get('spawned_at')
    if spawn_time_str:
        spawn_time = datetime.fromisoformat(spawn_time_str.replace('Z', '+00:00'))
        if spawn_time.hour == 17 and spawn_time.date().isoformat() == '2024-11-04':
            passengers.append(p)

print(f'Total passengers in hour 17: {len(passengers)}\n')

if not passengers:
    print('⚠️  No passengers found for verification')
    exit(0)

# Get route geometry
route_geom = httpx.get('http://localhost:6000/spatial/route-geometry/gg3pv3z19hhm117v9xth5ezq').json()
coords = route_geom['coordinates']
num_stops = len(coords)

print(f'Route has {num_stops} stops')
print(f'Terminals: Stop 0 at ({coords[0][1]:.6f}, {coords[0][0]:.6f})')
print(f'           Stop {num_stops-1} at ({coords[-1][1]:.6f}, {coords[-1][0]:.6f})\n')

# Calculate boarding/alighting indices and find terminal trips
terminal_trips = []
for p in passengers:
    board_idx = find_closest_stop(p['latitude'], p['longitude'], coords)
    alight_idx = find_closest_stop(p['destination_lat'], p['destination_lon'], coords)
    
    p['_board_idx'] = board_idx
    p['_alight_idx'] = alight_idx
    
    # Terminal-to-terminal: both at terminals and different
    if board_idx in [0, num_stops-1] and alight_idx in [0, num_stops-1] and board_idx != alight_idx:
        terminal_trips.append(p)

# Report results
print(f'📊 RESULTS:')
print(f'   Total passengers: {len(passengers)}')
print(f'   Terminal-to-terminal trips: {len(terminal_trips)} ({len(terminal_trips)/len(passengers)*100:.1f}%)')
print(f'   Expected rate: ~5% (end_to_end_probability = 0.05)\n')

if terminal_trips:
    print('✅ End-to-end terminal trips found:')
    for i, p in enumerate(terminal_trips, 1):
        direction = "Forward" if p['_board_idx'] == 0 else "Reverse"
        print(f"   {i}. {p['passenger_id'][:20]}... | Board: Stop {p['_board_idx']} → Alight: Stop {p['_alight_idx']} ({direction})")
else:
    print('⚠️  No terminal-to-terminal trips found.')
    print('   With 5% probability and 33 passengers, expected ~1-2 trips.')
    print('   This could be due to:')
    print('   - Random chance (5% is low)')
    print('   - Code not executing the end-to-end logic')
    print('   - Distance validation rejecting terminal trips')
    
    print('\n📋 Sample trip distributions:')
    board_counts = {}
    for p in passengers:
        idx = p['_board_idx']
        board_counts[idx] = board_counts.get(idx, 0) + 1
    
    terminal_boards = board_counts.get(0, 0) + board_counts.get(num_stops-1, 0)
    print(f'   Boarding at terminals: {terminal_boards} passengers')
    print(f'   Boarding at stop 0: {board_counts.get(0, 0)}')
    print(f'   Boarding at stop {num_stops-1}: {board_counts.get(num_stops-1, 0)}')
