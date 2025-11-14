#!/usr/bin/env python3
"""
Validate projected depot spawn rates for realism.
Calculate expected passengers per hour based on building counts.
"""

import requests
import json

# Depot data from previous analysis
depots = [
    {"name": "Constitution River Terminal", "lat": 13.102403, "lon": -59.612742, "town": "Bridgetown"},
    {"name": "Cheapside Terminal", "lat": 13.097306, "lon": -59.620117, "town": "Bridgetown"},
    {"name": "Princess Alice Terminal", "lat": 13.086972, "lon": -59.615194, "town": "Bridgetown"},
    {"name": "Speightstown Bus Terminal", "lat": 13.250128, "lon": -59.639525, "town": "Speightstown"},
    {"name": "Granville Williams Terminal", "lat": 13.100147, "lon": -59.607353, "town": "Bridgetown"},
]

# Spawn parameters (from commuter_behavior_config.json)
PASSENGERS_PER_BUILDING_PER_HOUR = 0.3  # Default from route spawner
SPAWN_RADIUS = 800  # meters
TIME_WINDOW = 5  # minutes per spawn cycle
HOURLY_RATE = 1.0  # Default
DAY_MULTIPLIER = 1.0  # Default for weekday

# Calculation window
CYCLES_PER_HOUR = 60 / TIME_WINDOW  # 12 cycles per hour

print("=" * 80)
print("DEPOT SPAWN RATE VALIDATION")
print("=" * 80)
print(f"\nParameters:")
print(f"  - Passengers per building per hour: {PASSENGERS_PER_BUILDING_PER_HOUR}")
print(f"  - Search radius: {SPAWN_RADIUS}m")
print(f"  - Spawn cycle: {TIME_WINDOW} minutes ({CYCLES_PER_HOUR} cycles/hour)")
print(f"  - Hourly rate multiplier: {HOURLY_RATE}")
print(f"  - Day multiplier: {DAY_MULTIPLIER}")
print()

total_passengers_per_hour = 0

for depot in depots:
    print(f"\n{depot['name']} ({depot['town']})")
    print("-" * 80)
    
    # Query buildings
    url = f"http://localhost:6000/spatial/nearby-buildings"
    params = {
        "lat": depot["lat"],
        "lon": depot["lon"],
        "radius_meters": SPAWN_RADIUS,
        "limit": 5000
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        building_count = len(data.get('buildings', []))
    except Exception as e:
        print(f"  ERROR querying buildings: {e}")
        continue
    
    # Calculate lambda for one spawn cycle
    spatial_factor = building_count * PASSENGERS_PER_BUILDING_PER_HOUR
    time_fraction = TIME_WINDOW / 60.0  # Convert minutes to hours
    lambda_per_cycle = spatial_factor * HOURLY_RATE * DAY_MULTIPLIER * time_fraction
    
    # Expected passengers per hour (average from Poisson)
    passengers_per_hour = lambda_per_cycle * CYCLES_PER_HOUR
    
    print(f"  Buildings within {SPAWN_RADIUS}m: {building_count}")
    print(f"  Spatial factor: {building_count} × {PASSENGERS_PER_BUILDING_PER_HOUR} = {spatial_factor:.1f}")
    print(f"  Lambda per cycle: {spatial_factor:.1f} × {time_fraction:.4f}h = {lambda_per_cycle:.4f}")
    print(f"  Expected passengers/hour: {lambda_per_cycle:.4f} × {CYCLES_PER_HOUR} = {passengers_per_hour:.1f}")
    
    total_passengers_per_hour += passengers_per_hour
    
    # Realism check
    print(f"\n  REALISM CHECK:")
    print(f"    - Per building per hour: {passengers_per_hour / building_count if building_count > 0 else 0:.4f}")
    print(f"    - Per minute: {passengers_per_hour / 60:.2f}")
    print(f"    - Per cycle ({TIME_WINDOW}min): {passengers_per_hour / CYCLES_PER_HOUR:.2f}")

print("\n" + "=" * 80)
print("SYSTEM TOTALS")
print("=" * 80)
print(f"Total passengers spawned per hour across all {len(depots)} depots: {total_passengers_per_hour:.1f}")
print(f"Average per depot: {total_passengers_per_hour / len(depots):.1f} passengers/hour")

print("\n" + "=" * 80)
print("SCALING ANALYSIS")
print("=" * 80)
print("\nIf these rates seem too high, consider scaling options:")
print("1. Reduce passengers_per_building_per_hour (currently 0.3)")
print("   - Try 0.1: would reduce to ~1/3")
print("   - Try 0.05: would reduce to ~1/6")
print("   - Try 0.01: would reduce to ~1/30")
print("\n2. Increase spawn cycle time window (currently 5 minutes)")
print("   - Try 10 minutes: would reduce by half")
print("   - Try 15 minutes: would reduce to 1/3")
print("\n3. Add time-of-day multipliers")
print("   - Peak hours (7-9am, 4-6pm): 1.5x")
print("   - Normal hours: 1.0x")
print("   - Off-peak hours: 0.3x")
print("   - Night hours: 0.1x")

# Calculate with scaled parameters
print("\n" + "=" * 80)
print("SCALED SCENARIOS")
print("=" * 80)

scaling_factors = [
    ("Current (0.3 pass/bldg/hr)", 0.3),
    ("Conservative (0.1 pass/bldg/hr)", 0.1),
    ("Very Conservative (0.05 pass/bldg/hr)", 0.05),
    ("Minimal (0.01 pass/bldg/hr)", 0.01),
]

for scenario_name, pass_per_bldg in scaling_factors:
    # Using Constitution River as example (highest building count)
    example_buildings = 2992
    spatial_factor = example_buildings * pass_per_bldg
    time_fraction = TIME_WINDOW / 60.0
    lambda_per_cycle = spatial_factor * HOURLY_RATE * DAY_MULTIPLIER * time_fraction
    passengers_per_hour = lambda_per_cycle * CYCLES_PER_HOUR
    
    print(f"\n{scenario_name}:")
    print(f"  Constitution River: {passengers_per_hour:.1f} pass/hr ({passengers_per_hour/60:.2f} pass/min)")
    print(f"  System total (5 depots): ~{passengers_per_hour * 5:.0f} pass/hr")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("\nFor a realistic simulation of Barbados transit:")
print("  - Population of Barbados: ~287,000")
print("  - Assume 10% use public transit: ~28,700 people")
print("  - Spread over 12 hours: ~2,400 passengers/hour system-wide")
print("  - With 5 depots: ~480 passengers/hour per depot on average")
print("\nSuggested scaling: passengers_per_building_per_hour = 0.05 to 0.1")
print("This would give 200-400 passengers/hour per major depot")
