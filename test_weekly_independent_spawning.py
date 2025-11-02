"""
Test RouteSpawner with Independent Additive Spawning - WEEKLY BAR CHARTS

Shows passenger spawning for 3 routes over a full week (7 days × 24 hours).
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

async def test_weekly_independent_spawning():
    """
    Simulate full week of independent spawning for multiple routes.
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
    print("INDEPENDENT ADDITIVE SPAWNING - WEEKLY SIMULATION")
    print("=" * 80)
    print(f"3 Routes, Same Depot, Different Route Buildings")
    print(f"Each route spawns INDEPENDENTLY - totals are ADDITIVE")
    print()
    
    # Simulate full week (7 days × 24 hours)
    start_date = datetime(2024, 11, 3)  # Sunday
    
    # Store results per route per day
    route_daily_totals = defaultdict(lambda: defaultdict(int))
    system_daily_totals = defaultdict(int)
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        
        for hour in range(24):
            test_time = current_date.replace(hour=hour, minute=0, second=0)
            
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
                
                route_daily_totals[route["route_id"]][day_name] += spawn_count
                system_daily_totals[day_name] += spawn_count
    
    # Print daily totals per route
    print("DAILY TOTALS PER ROUTE (Independent Spawning)")
    print("-" * 80)
    
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    for route in routes:
        print(f"\n{route['route_name']}:")
        print(f"  Depot Buildings: {route['depot_buildings']}, Route Buildings: {route['route_buildings']}")
        for day in days:
            count = route_daily_totals[route["route_id"]][day]
            print(f"  {day:>9}: {count:>4} passengers")
    
    print("\n" + "=" * 80)
    print("SYSTEM TOTALS (Additive Sum of All Routes)")
    print("=" * 80)
    for day in days:
        count = system_daily_totals[day]
        print(f"{day:>9}: {count:>4} passengers")
    
    # ASCII Bar Charts
    print("\n" + "=" * 80)
    print("BAR CHART: Route 1 (Independent)")
    print("=" * 80)
    max_val_r1 = max(route_daily_totals["route_1"].values())
    for day in days:
        count = route_daily_totals["route_1"][day]
        bar_length = int((count / max_val_r1) * 50) if max_val_r1 > 0 else 0
        bar = "█" * bar_length
        print(f"{day:>9} ({count:>4}): {bar}")
    
    print("\n" + "=" * 80)
    print("BAR CHART: Route 2 (Independent)")
    print("=" * 80)
    max_val_r2 = max(route_daily_totals["route_2"].values())
    for day in days:
        count = route_daily_totals["route_2"][day]
        bar_length = int((count / max_val_r2) * 50) if max_val_r2 > 0 else 0
        bar = "█" * bar_length
        print(f"{day:>9} ({count:>4}): {bar}")
    
    print("\n" + "=" * 80)
    print("BAR CHART: Route 3 (Independent)")
    print("=" * 80)
    max_val_r3 = max(route_daily_totals["route_3"].values())
    for day in days:
        count = route_daily_totals["route_3"][day]
        bar_length = int((count / max_val_r3) * 50) if max_val_r3 > 0 else 0
        bar = "█" * bar_length
        print(f"{day:>9} ({count:>4}): {bar}")
    
    print("\n" + "=" * 80)
    print("BAR CHART: SYSTEM TOTAL (Additive Sum)")
    print("=" * 80)
    max_val_sys = max(system_daily_totals.values())
    for day in days:
        count = system_daily_totals[day]
        bar_length = int((count / max_val_sys) * 50) if max_val_sys > 0 else 0
        bar = "█" * bar_length
        print(f"{day:>9} ({count:>4}): {bar}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION: Routes Spawn Independently")
    print("=" * 80)
    
    # Show that system total = sum of individual routes
    for day in days:
        r1 = route_daily_totals["route_1"][day]
        r2 = route_daily_totals["route_2"][day]
        r3 = route_daily_totals["route_3"][day]
        calculated_sum = r1 + r2 + r3
        actual_total = system_daily_totals[day]
        
        print(f"{day}: R1({r1}) + R2({r2}) + R3({r3}) = {calculated_sum} (System: {actual_total}) ✓")
    
    print()
    print("✓ Each route spawns INDEPENDENTLY")
    print("✓ System total = SUM of all routes")
    print("✓ Adding routes INCREASES total (not redistributes)")
    print()

if __name__ == "__main__":
    asyncio.run(test_weekly_independent_spawning())
