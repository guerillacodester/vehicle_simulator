#!/usr/bin/env python3
"""Check if spawn counts are realistic for route"""

import httpx

# Get route info
url = 'http://localhost:1337/api/routes?filters[documentId][$eq]=gg3pv3z19hhm117v9xth5ezq&populate=*'
r = httpx.get(url)
route = r.json()['data'][0]

print('=' * 70)
print('ROUTE CONFIGURATION & REALISM ANALYSIS')
print('=' * 70)
print()
print('Route Details:')
print(f'  Name: {route.get("name", "N/A")}')
print(f'  Description: {route.get("description", "N/A")}')
print(f'  Est. Daily Passengers: {route.get("estimated_daily_passengers", "N/A")}')
print()

# Get spawn config details
spawn_cfg = route.get('spawn_config', {})
if spawn_cfg:
    dist = spawn_cfg.get('distribution_params', [{}])[0] if spawn_cfg.get('distribution_params') else {}
    hourly_rates = spawn_cfg.get('hourly_spawn_rates', {})
    
    print('Spawn Configuration (from DB):')
    print(f'  Passengers per Building per Hour: {dist.get("passengers_per_building_per_hour")}')
    print(f'  Spawn Radius: {dist.get("spawn_radius_meters")}m')
    print(f'  Min Trip Distance: {dist.get("min_trip_distance_meters")}m')
    print()
    print('Hourly Rates (temporal multipliers):')
    for hour in range(24):
        rate = hourly_rates.get(f'hour_{hour}', hourly_rates.get(str(hour)))
        if rate:
            print(f'  Hour {hour:02d}: {rate}x')

print()
print('=' * 70)
print('REALISM ASSESSMENT')
print('=' * 70)
print()
print('Test Result: 4 passengers in 50 minutes')
print('  → ~4.8 passengers per hour at 9 AM')
print()
print('Config predicts:')
print('  5 buildings × 0.3 passengers/building/hour × 0.7 (9am rate)')
print('  = 5 × 0.3 × 0.7 = 1.05 passengers/hour')
print()
print('This is LOW - likely because:')
print('  1. Building estimate (5) is very conservative fallback')
print('  2. passengers_per_building_per_hour = 0.3 is LOW')
print('  3. Actual rural route might have 15-30+ buildings in 800m radius')
print()
print('Recommendation:')
print('  Increase passengers_per_building_per_hour to 0.5-1.0')
print('  OR improve geospatial service to find actual buildings')
