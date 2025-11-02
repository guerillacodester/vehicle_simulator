"""
24-Hour Depot Spawner Analysis - Full Week Simulation
======================================================

Simulates depot passenger spawning for a full week (7 days × 24 hours)
and displays results as bar charts showing passenger counts by hour.

Uses default depot configuration with realistic temporal patterns.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import statistics


async def simulate_depot_week():
    """Simulate depot spawning for a full week with 1-hour bins."""
    from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
    from unittest.mock import MagicMock
    
    print("=" * 80)
    print("DEPOT SPAWNER - FULL WEEK SIMULATION")
    print("=" * 80)
    print()
    print("Simulating 7 days × 24 hours = 168 hours of depot passenger spawning")
    print("Each hour simulated 10 times to get average passenger counts")
    print()
    
    # Setup depot with REALISTIC config for a small Caribbean town depot
    mock_reservoir = MagicMock()
    
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="main_depot",
        depot_location=(13.238, -59.642),
        available_routes=["1", "2", "3"]
    )
    
    # Use REALISTIC config (adjusted spatial_base for small town depot)
    # Targeting ~800 passengers/day (~33/hour average)
    spawn_config = {
        'distribution_params': {
            'spatial_base': 30.0,  # Increased from 2.0 to 30.0 for realistic volume
            'hourly_rates': {
                '0': 0.2, '1': 0.15, '2': 0.1, '3': 0.1, '4': 0.3, '5': 0.8,
                '6': 1.5, '7': 2.0, '8': 2.5, '9': 2.0, '10': 1.2, '11': 1.0,
                '12': 1.0, '13': 0.9, '14': 0.8, '15': 0.9, '16': 1.5, '17': 2.3,
                '18': 2.0, '19': 1.2, '20': 0.8, '21': 0.5, '22': 0.3, '23': 0.2
            },
            'day_multipliers': {
                '0': 1.2,  # Monday
                '1': 1.1,  # Tuesday
                '2': 1.1,  # Wednesday
                '3': 1.1,  # Thursday
                '4': 1.3,  # Friday (busiest)
                '5': 0.7,  # Saturday
                '6': 0.5   # Sunday (quietest)
            }
        }
    }
    
    print("Depot Configuration:")
    dist_params = spawn_config.get('distribution_params', {})
    print(f"  Spatial base: {dist_params.get('spatial_base', 2.0)}")
    print(f"  Hourly rates: {len(dist_params.get('hourly_rates', {}))} hours defined")
    print(f"  Day multipliers: {len(dist_params.get('day_multipliers', {}))} days defined")
    print()
    
    # Simulate full week starting Monday
    start_date = datetime(2024, 11, 4, 0, 0)  # Monday, November 4, 2024, midnight
    
    # Store results: day_name -> [24 hourly averages]
    week_data = {
        'Monday': [],
        'Tuesday': [],
        'Wednesday': [],
        'Thursday': [],
        'Friday': [],
        'Saturday': [],
        'Sunday': []
    }
    
    day_names = list(week_data.keys())
    
    print("Simulating...")
    print()
    
    for day_offset in range(7):
        day_name = day_names[day_offset]
        print(f"  {day_name}...", end='', flush=True)
        
        hourly_averages = []
        
        for hour in range(24):
            current_time = start_date + timedelta(days=day_offset, hours=hour)
            
            # Run 10 trials per hour to get average
            trials = []
            for _ in range(10):
                spawn_count = await spawner._calculate_spawn_count(
                    spawn_config=spawn_config,
                    current_time=current_time,
                    time_window_minutes=60  # 1-hour bin
                )
                trials.append(spawn_count)
            
            avg = statistics.mean(trials)
            hourly_averages.append(avg)
        
        week_data[day_name] = hourly_averages
        print(f" ✓ (Total: {sum(hourly_averages):.0f} passengers)")
    
    print()
    return week_data, spawn_config


def print_bar_chart(week_data: Dict[str, List[float]]):
    """Print ASCII bar chart of passenger counts by day and hour."""
    
    print("=" * 80)
    print("PASSENGER SPAWN COUNTS - FULL WEEK")
    print("=" * 80)
    print()
    
    # Daily totals
    print("DAILY TOTALS:")
    print()
    
    max_daily_total = 0
    daily_totals = {}
    
    for day_name, hourly_counts in week_data.items():
        total = sum(hourly_counts)
        daily_totals[day_name] = total
        max_daily_total = max(max_daily_total, total)
    
    for day_name, total in daily_totals.items():
        bar_length = int((total / max_daily_total) * 50) if max_daily_total > 0 else 0
        bar = '█' * bar_length
        print(f"  {day_name:9s}: {bar} {total:6.0f} passengers")
    
    print()
    print("=" * 80)
    print("HOURLY BREAKDOWN BY DAY")
    print("=" * 80)
    print()
    
    # Hourly breakdown for each day
    for day_name, hourly_counts in week_data.items():
        print(f"{day_name.upper()}")
        print("-" * 80)
        
        max_count = max(hourly_counts) if hourly_counts else 1
        
        for hour, count in enumerate(hourly_counts):
            bar_length = int((count / max_count) * 40) if max_count > 0 else 0
            bar = '█' * bar_length
            
            # Color code by time of day
            if 6 <= hour <= 9:
                label = "🌅 MORNING PEAK"
            elif 16 <= hour <= 19:
                label = "🌆 EVENING PEAK"
            elif 0 <= hour <= 5 or hour >= 22:
                label = "🌙 NIGHT"
            else:
                label = "☀️  DAY"
            
            print(f"  {hour:02d}:00 {bar:40s} {count:5.1f} {label}")
        
        print()
    
    print("=" * 80)
    print("PEAK HOURS ANALYSIS")
    print("=" * 80)
    print()
    
    # Find peak hours across the week
    all_hours = []
    for day_name, hourly_counts in week_data.items():
        for hour, count in enumerate(hourly_counts):
            all_hours.append((day_name, hour, count))
    
    # Sort by count descending
    all_hours.sort(key=lambda x: x[2], reverse=True)
    
    print("Top 10 Peak Hours:")
    print()
    for i, (day, hour, count) in enumerate(all_hours[:10], 1):
        print(f"  {i:2d}. {day:9s} {hour:02d}:00 - {count:5.1f} passengers")
    
    print()
    
    print("Bottom 10 Slowest Hours:")
    print()
    for i, (day, hour, count) in enumerate(all_hours[-10:], 1):
        print(f"  {i:2d}. {day:9s} {hour:02d}:00 - {count:5.1f} passengers")
    
    print()


def print_summary_statistics(week_data: Dict[str, List[float]], spawn_config: Dict):
    """Print summary statistics."""
    
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    # Calculate totals
    grand_total = sum(sum(hours) for hours in week_data.values())
    daily_totals = {day: sum(hours) for day, hours in week_data.items()}
    
    print(f"Weekly Total: {grand_total:.0f} passengers")
    print(f"Daily Average: {grand_total/7:.0f} passengers/day")
    print(f"Hourly Average: {grand_total/168:.1f} passengers/hour")
    print()
    
    # Weekday vs Weekend
    weekday_total = sum(daily_totals[day] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    weekend_total = sum(daily_totals[day] for day in ['Saturday', 'Sunday'])
    
    print(f"Weekday Total (Mon-Fri): {weekday_total:.0f} passengers ({weekday_total/grand_total*100:.1f}%)")
    print(f"Weekend Total (Sat-Sun): {weekend_total:.0f} passengers ({weekend_total/grand_total*100:.1f}%)")
    print(f"Weekday/Weekend Ratio: {weekday_total/weekend_total if weekend_total > 0 else 0:.2f}x")
    print()
    
    # Peak hours (6-9 AM and 4-7 PM)
    morning_peak_total = 0
    evening_peak_total = 0
    off_peak_total = 0
    
    for day_name, hourly_counts in week_data.items():
        for hour, count in enumerate(hourly_counts):
            if 6 <= hour <= 9:
                morning_peak_total += count
            elif 16 <= hour <= 19:
                evening_peak_total += count
            else:
                off_peak_total += count
    
    print(f"Morning Peak (6-9 AM): {morning_peak_total:.0f} passengers ({morning_peak_total/grand_total*100:.1f}%)")
    print(f"Evening Peak (4-7 PM): {evening_peak_total:.0f} passengers ({evening_peak_total/grand_total*100:.1f}%)")
    print(f"Off-Peak Hours: {off_peak_total:.0f} passengers ({off_peak_total/grand_total*100:.1f}%)")
    print()
    
    # Configuration used
    print("Configuration Used:")
    dist_params = spawn_config.get('distribution_params', {})
    print(f"  Spatial Base: {dist_params.get('spatial_base', 2.0)}")
    print(f"  Hourly Rates: {dist_params.get('hourly_rates', {})}")
    print(f"  Day Multipliers: {dist_params.get('day_multipliers', {})}")
    print()


async def main():
    """Run full week simulation and display results."""
    
    # Run simulation
    week_data, spawn_config = await simulate_depot_week()
    
    # Display results
    print_bar_chart(week_data)
    print_summary_statistics(week_data, spawn_config)
    
    print("=" * 80)
    print("✓ SIMULATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
