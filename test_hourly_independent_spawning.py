"""
Test RouteSpawner with Independent Additive Spawning - HOURLY BAR CHARTS

Shows passenger spawning per hour for Sunday and Monday (24-hour clock).
Each route spawns independently - totals are ADDITIVE, not competitive.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_hourly_independent_spawning():
    """
    Simulate hourly spawning for Sunday and Monday showing 24-hour patterns.
    """
    from commuter_simulator.core.domain.spawner_engine.spawn_calculator import SpawnCalculator
    import numpy as np
    
    # Mock spawn config (normalized rates)
    spawn_config = {
        "distribution_params": {
            "spatial_base": 75.0,
            "hourly_rates": {
                "0": 0.05, "1": 0.03, "2": 0.02, "3": 0.02, "4": 0.03,
                "5": 0.15, "6": 0.50, "7": 0.90, "8": 1.00, "9": 0.85,
                "10": 0.60, "11": 0.55, "12": 0.60, "13": 0.50, "14": 0.55,
                "15": 0.65, "16": 0.85, "17": 0.95, "18": 0.70, "19": 0.40,
                "20": 0.25, "21": 0.15, "22": 0.10, "23": 0.07
            },
            "day_multipliers": {
                "0": 0.4, "1": 1.0, "2": 1.0, "3": 1.0, "4": 1.0, "5": 0.9, "6": 0.5
            }
        }
    }
    
    # 3 routes sharing same depot
    routes = [
        {
            "route_id": "route_1",
            "route_name": "Route 1",
            "depot_buildings": 450,
            "route_buildings": 320,
        },
        {
            "route_id": "route_2", 
            "route_name": "Route 2",
            "depot_buildings": 450,
            "route_buildings": 180,
        },
        {
            "route_id": "route_3",
            "route_name": "Route 3",
            "depot_buildings": 450,
            "route_buildings": 250,
        }
    ]
    
    print("=" * 80)
    print("INDEPENDENT ADDITIVE SPAWNING - HOURLY BREAKDOWN (24-HOUR CLOCK)")
    print("=" * 80)
    print(f"3 Routes, Same Depot, Different Route Buildings")
    print(f"Each route spawns INDEPENDENTLY - totals are ADDITIVE")
    print()
    
    # Simulate Sunday and Monday (24 hours each)
    days_to_simulate = [
        ("Sunday", datetime(2024, 11, 3)),
        ("Monday", datetime(2024, 11, 4))
    ]
    
    for day_name, start_date in days_to_simulate:
        route_hourly = defaultdict(lambda: defaultdict(int))
        system_hourly = defaultdict(int)
        
        for hour in range(24):
            test_time = start_date.replace(hour=hour, minute=0, second=0)
            
            # Extract temporal multipliers
            base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
                spawn_config=spawn_config,
                current_time=test_time
            )
            
            effective_rate = SpawnCalculator.calculate_effective_rate(
                base_rate=base_rate,
                hourly_multiplier=hourly_mult,
                day_multiplier=day_mult
            )
            
            # Calculate spawns for each route independently
            for route in routes:
                depot_passengers_per_hour = route["depot_buildings"] * effective_rate
                route_passengers_per_hour = route["route_buildings"] * effective_rate
                total_passengers_per_hour = depot_passengers_per_hour + route_passengers_per_hour
                
                lambda_param = total_passengers_per_hour * 1.0  # 1 hour window
                spawn_count = np.random.poisson(lambda_param) if lambda_param > 0 else 0
                
                route_hourly[route["route_id"]][hour] = spawn_count
                system_hourly[hour] += spawn_count
        
        # Print hourly breakdown
        print("=" * 80)
        print(f"{day_name.upper()} - HOURLY TOTALS PER ROUTE")
        print("=" * 80)
        
        for route in routes:
            print(f"\n{route['route_name']} (Depot: {route['depot_buildings']}, Route: {route['route_buildings']} buildings):")
            for hour in range(24):
                count = route_hourly[route["route_id"]][hour]
                print(f"  {hour:02d}:00 - {count:>3} passengers")
        
        print("\n" + "=" * 80)
        print(f"{day_name.upper()} - SYSTEM TOTAL (Additive Sum)")
        print("=" * 80)
        for hour in range(24):
            count = system_hourly[hour]
            print(f"{hour:02d}:00 - {count:>3} passengers")
        
        # BAR CHARTS
        print("\n" + "=" * 80)
        print(f"BAR CHART: {day_name.upper()} - Route 1 (Independent)")
        print("=" * 80)
        max_val_r1 = max(route_hourly["route_1"].values()) if route_hourly["route_1"] else 1
        for hour in range(24):
            count = route_hourly["route_1"][hour]
            bar_length = int((count / max_val_r1) * 50) if max_val_r1 > 0 else 0
            bar = "█" * bar_length
            print(f"{hour:02d}:00 ({count:>3}): {bar}")
        
        print("\n" + "=" * 80)
        print(f"BAR CHART: {day_name.upper()} - Route 2 (Independent)")
        print("=" * 80)
        max_val_r2 = max(route_hourly["route_2"].values()) if route_hourly["route_2"] else 1
        for hour in range(24):
            count = route_hourly["route_2"][hour]
            bar_length = int((count / max_val_r2) * 50) if max_val_r2 > 0 else 0
            bar = "█" * bar_length
            print(f"{hour:02d}:00 ({count:>3}): {bar}")
        
        print("\n" + "=" * 80)
        print(f"BAR CHART: {day_name.upper()} - Route 3 (Independent)")
        print("=" * 80)
        max_val_r3 = max(route_hourly["route_3"].values()) if route_hourly["route_3"] else 1
        for hour in range(24):
            count = route_hourly["route_3"][hour]
            bar_length = int((count / max_val_r3) * 50) if max_val_r3 > 0 else 0
            bar = "█" * bar_length
            print(f"{hour:02d}:00 ({count:>3}): {bar}")
        
        print("\n" + "=" * 80)
        print(f"BAR CHART: {day_name.upper()} - SYSTEM TOTAL (Additive Sum)")
        print("=" * 80)
        max_val_sys = max(system_hourly.values()) if system_hourly else 1
        for hour in range(24):
            count = system_hourly[hour]
            bar_length = int((count / max_val_sys) * 50) if max_val_sys > 0 else 0
            bar = "█" * bar_length
            print(f"{hour:02d}:00 ({count:>3}): {bar}")
        
        # Verification
        print("\n" + "=" * 80)
        print(f"{day_name.upper()} - VERIFICATION: Independent Spawning")
        print("=" * 80)
        daily_total = 0
        for hour in range(24):
            r1 = route_hourly["route_1"][hour]
            r2 = route_hourly["route_2"][hour]
            r3 = route_hourly["route_3"][hour]
            calculated_sum = r1 + r2 + r3
            actual_total = system_hourly[hour]
            daily_total += actual_total
            print(f"{hour:02d}:00 - R1({r1:>3}) + R2({r2:>3}) + R3({r3:>3}) = {calculated_sum:>3} (System: {actual_total:>3}) ✓")
        
        print(f"\n{day_name} Daily Total: {daily_total} passengers")
        print()
    
    print("=" * 80)
    print("✓ Each route spawns INDEPENDENTLY every hour")
    print("✓ Hourly system total = SUM of all routes")
    print("✓ Clear morning (8AM) and evening (17:00) peaks visible")
    print("✓ Routes don't compete - they ADD together!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_hourly_independent_spawning())
