"""
Hourly Passenger Spawning - Sunday & Monday
============================================

Shows actual passenger counts spawned per hour for a 48-hour period.
Uses realistic depot configuration for a small Caribbean town.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime, timedelta


async def simulate_weekend_to_monday():
    """Simulate Sunday through Monday with hourly passenger counts."""
    from commuter_service.core.domain.spawner_engine.depot_spawner import DepotSpawner
    from unittest.mock import MagicMock
    
    print("=" * 80)
    print("DEPOT PASSENGER SPAWNING - SUNDAY THROUGH MONDAY")
    print("=" * 80)
    print()
    print("Simulating 48 hours of passenger spawning (Sunday 00:00 → Monday 23:59)")
    print("Configuration: Realistic small-town Caribbean depot")
    print()
    
    # Setup depot with realistic config
    mock_reservoir = MagicMock()
    
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="speightstown_depot",
        depot_location=(13.238, -59.642),
        available_routes=["1", "2", "3"]
    )
    
    # REALISTIC config for small town depot (~800 passengers/day average)
    # NORMALIZED: hourly_rates are 0.0-1.0 (peak 8 AM = 1.0)
    spawn_config = {
        'distribution_params': {
            'spatial_base': 75.0,  # Increased to compensate for normalized rates (was 30.0)
            'hourly_rates': {
                '0': 0.08,  '1': 0.06,  '2': 0.04,  '3': 0.04,  '4': 0.12,  '5': 0.32,
                '6': 0.60,  '7': 0.80,  '8': 1.00,  '9': 0.80,  '10': 0.48, '11': 0.40,
                '12': 0.40, '13': 0.36, '14': 0.32, '15': 0.36, '16': 0.60, '17': 0.92,
                '18': 0.80, '19': 0.48, '20': 0.32, '21': 0.20, '22': 0.12, '23': 0.08
            },
            'day_multipliers': {
                '0': 1.2,  # Monday
                '6': 0.5   # Sunday
            }
        }
    }
    
    print("Configuration:")
    print(f"  Spatial Base: {spawn_config['distribution_params']['spatial_base']}")
    print(f"  Sunday Multiplier: {spawn_config['distribution_params']['day_multipliers']['6']}")
    print(f"  Monday Multiplier: {spawn_config['distribution_params']['day_multipliers']['0']}")
    print()
    
    # Sunday = Nov 10, 2024
    sunday_start = datetime(2024, 11, 10, 0, 0)
    
    sunday_total = 0
    monday_total = 0
    
    # Print header
    print("=" * 80)
    print("SUNDAY (November 10, 2024)")
    print("=" * 80)
    print()
    print("Hour        | Passengers | Bar Chart")
    print("-" * 80)
    
    sunday_counts = []
    
    for hour in range(24):
        current_time = sunday_start + timedelta(hours=hour)
        
        # Spawn for this 1-hour period
        spawn_count = await spawner._calculate_spawn_count(
            spawn_config=spawn_config,
            current_time=current_time,
            time_window_minutes=60  # 1 hour
        )
        
        sunday_counts.append(spawn_count)
        sunday_total += spawn_count
        
        # Create bar
        bar = '█' * spawn_count
        
        # Time period label
        time_label = f"{hour:02d}:00-{hour:02d}:59"
        
        # Add emoji for time of day
        if 6 <= hour <= 9:
            emoji = "🌅"
        elif 16 <= hour <= 19:
            emoji = "🌆"
        elif 0 <= hour <= 5 or hour >= 22:
            emoji = "🌙"
        else:
            emoji = "☀️"
        
        print(f"{time_label} {emoji} | {spawn_count:10d} | {bar}")
    
    print("-" * 80)
    print(f"SUNDAY TOTAL: {sunday_total} passengers")
    print()
    
    # Monday
    monday_start = datetime(2024, 11, 11, 0, 0)
    
    print("=" * 80)
    print("MONDAY (November 11, 2024)")
    print("=" * 80)
    print()
    print("Hour        | Passengers | Bar Chart")
    print("-" * 80)
    
    monday_counts = []
    
    for hour in range(24):
        current_time = monday_start + timedelta(hours=hour)
        
        # Spawn for this 1-hour period
        spawn_count = await spawner._calculate_spawn_count(
            spawn_config=spawn_config,
            current_time=current_time,
            time_window_minutes=60  # 1 hour
        )
        
        monday_counts.append(spawn_count)
        monday_total += spawn_count
        
        # Create bar
        bar = '█' * spawn_count
        
        # Time period label
        time_label = f"{hour:02d}:00-{hour:02d}:59"
        
        # Add emoji for time of day
        if 6 <= hour <= 9:
            emoji = "🌅"
        elif 16 <= hour <= 19:
            emoji = "🌆"
        elif 0 <= hour <= 5 or hour >= 22:
            emoji = "🌙"
        else:
            emoji = "☀️"
        
        print(f"{time_label} {emoji} | {spawn_count:10d} | {bar}")
    
    print("-" * 80)
    print(f"MONDAY TOTAL: {monday_total} passengers")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Sunday Total:  {sunday_total:4d} passengers")
    print(f"Monday Total:  {monday_total:4d} passengers")
    print(f"48-Hour Total: {sunday_total + monday_total:4d} passengers")
    print()
    print(f"Sunday Average: {sunday_total/24:.1f} passengers/hour")
    print(f"Monday Average: {monday_total/24:.1f} passengers/hour")
    print()
    print(f"Monday/Sunday Ratio: {monday_total/sunday_total if sunday_total > 0 else 0:.2f}x")
    print()
    
    # Peak hours
    sunday_peak_hour = sunday_counts.index(max(sunday_counts))
    monday_peak_hour = monday_counts.index(max(monday_counts))
    
    print(f"Sunday Peak Hour: {sunday_peak_hour:02d}:00 ({sunday_counts[sunday_peak_hour]} passengers)")
    print(f"Monday Peak Hour: {monday_peak_hour:02d}:00 ({monday_counts[monday_peak_hour]} passengers)")
    print()
    
    # Expected lambda calculations
    print("=" * 80)
    print("EXPECTED VALUES (Theoretical) - NORMALIZED RATES")
    print("=" * 80)
    print()
    
    spatial_base = 75.0  # Updated to match normalized config
    hourly_rates = spawn_config['distribution_params']['hourly_rates']
    
    print("Normalized Configuration:")
    print(f"  spatial_base = {spatial_base} (increased to compensate)")
    print(f"  hourly_rates = 0.0 to 1.0 (peak 8 AM = 1.0, night 3 AM = 0.04)")
    print(f"  Formula: λ = spatial_base × hourly_rate × day_mult × hours")
    print()
    print("Example calculations for peak hours:")
    print()
    
    # Sunday 8 AM
    sunday_hourly = float(hourly_rates.get('8', 1.0))
    sunday_mult = 0.5
    sunday_lambda = spatial_base * sunday_hourly * sunday_mult * 1.0  # 1 hour
    print(f"Sunday 8 AM:")
    print(f"  λ = {spatial_base} × {sunday_hourly} × {sunday_mult} × 1h = {sunday_lambda:.1f}")
    print(f"  Actual spawned: {sunday_counts[8]} (Poisson variance is normal)")
    print()
    
    # Monday 8 AM
    monday_hourly = float(hourly_rates.get('8', 1.0))
    monday_mult = 1.2
    monday_lambda = spatial_base * monday_hourly * monday_mult * 1.0  # 1 hour
    print(f"Monday 8 AM:")
    print(f"  λ = {spatial_base} × {monday_hourly} × {monday_mult} × 1h = {monday_lambda:.1f}")
    print(f"  Actual spawned: {monday_counts[8]} (Poisson variance is normal)")
    print()
    
    # Show normalization benefit
    print("Normalization Benefits:")
    print("  ✓ Hourly rates are percentages (0% - 100% of peak)")
    print("  ✓ 8 AM = 1.0 (100% peak activity)")
    print("  ✓ 5 PM = 0.92 (92% of peak)")
    print("  ✓ 3 AM = 0.04 (4% of peak)")
    print()
    
    print("=" * 80)
    print("✓ SIMULATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(simulate_weekend_to_monday())
