from datetime import datetime, timedelta

VAN_START = datetime(2025, 10, 26, 7, 0, 0)
ROUTE_LENGTH_KM = 1.31
VAN_SPEED_KMH = 30

def van_arrival_time(position_pct):
    distance_km = ROUTE_LENGTH_KM * position_pct
    travel_time_min = (distance_km / VAN_SPEED_KMH) * 60
    return VAN_START + timedelta(minutes=travel_time_min)

# All 21 passengers from simulation
passengers = [
    (1, '06:01:06', 0.021), (2, '06:02:48', 0.938), (3, '06:03:34', 0.971),
    (4, '06:04:08', 0.021), (5, '06:21:31', 0.021), (6, '06:23:20', 0.971),
    (7, '06:26:49', 0.652), (8, '06:27:29', 0.021), (9, '06:27:45', 0.386),
    (10, '06:32:43', 0.652), (11, '06:35:43', 0.021), (12, '06:35:46', 0.836),
    (13, '06:38:27', 0.971), (14, '06:40:30', 0.021), (15, '06:41:07', 0.021),
    (16, '06:41:50', 0.971), (17, '06:45:52', 0.021), (18, '06:48:34', 0.716),
    (19, '06:52:07', 0.021), (20, '06:52:33', 0.021), (21, '06:58:59', 0.938),
]

print('PICKUP FEASIBILITY CHECK - All 21 Passengers')
print('=' * 100)
print(f'Van departs: 07:00:00')
print(f'Route: {ROUTE_LENGTH_KM}km @ {VAN_SPEED_KMH}km/h')
print('')
print(f'{"ID":<4} {"Spawn Time":<12} {"Position":<10} {"Van Arrives":<12} {"Wait (min)":<12} {"Feasible?"}')
print('-' * 100)

feasible_count = 0
for pid, spawn_str, position in passengers:
    spawn_time = datetime.strptime(f'2025-10-26 {spawn_str}', '%Y-%m-%d %H:%M:%S')
    van_arrives = van_arrival_time(position)
    wait_minutes = (van_arrives - spawn_time).total_seconds() / 60
    
    if wait_minutes >= 0:
        feasible = 'YES'
        feasible_count += 1
    else:
        feasible = 'NO (van already passed!)'
    
    print(f'{pid:<4} {spawn_str:<12} {position*100:>8.1f}% {van_arrives.strftime("%H:%M:%S"):<12} {wait_minutes:>10.1f} {feasible}')

print('')
print(f'RESULT: {feasible_count}/{len(passengers)} passengers spawned before van arrived')
print(f'100% pickup rate is {"REALISTIC" if feasible_count == len(passengers) else "UNREALISTIC"}')
