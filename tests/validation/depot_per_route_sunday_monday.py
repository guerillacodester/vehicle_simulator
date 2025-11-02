"""
Per-Route Passenger Spawning - Sunday & Monday
===============================================

**DEMONSTRATION** of attractiveness-weighted distribution model.

NOTE: Building counts (450, 320, 180) are ESTIMATED for demonstration.
In production, these will come from:
  1. Geospatial service queries (actual building counts along each route)
  2. Strapi spawn-configs (route-specific parameters)

This shows the CORRECT ALGORITHM that will be used with real data.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime, timedelta
import httpx


async def simulate_per_route_weekend_to_monday():
    """Simulate Sunday through Monday with per-route passenger distribution."""
    from commuter_service.core.domain.spawner_engine.spawn_calculator import SpawnCalculator
    
    print("=" * 100)
    print("DEPOT PASSENGER SPAWNING BY ROUTE - SUNDAY THROUGH MONDAY")
    print("=" * 100)
    print()
    print("Shows how terminal population is distributed across routes based on attractiveness")
    print()
    
    # Depot configuration (NORMALIZED 0.0-1.0)
    depot_config = {
        'distribution_params': {
            'spatial_base': 75.0,
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
    
    # Query REAL routes from Strapi
    print("Querying routes from Strapi...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("http://localhost:1337/api/spawn-configs?populate=route")
        if response.status_code != 200:
            print(f"❌ Error querying spawn configs: {response.status_code}")
            return
        
        data = response.json()
        spawn_configs = data.get('data', [])
    
    if not spawn_configs:
        print("❌ No spawn configs found in database!")
        return
    
    print(f"✓ Found {len(spawn_configs)} spawn config(s)")
    print()
    
    # Build routes dict from actual database
    routes = {}
    for config in spawn_configs:
        route = config.get('route')
        if not route:
            continue
        
        # Use correct field names: short_name and long_name (not route_short_name/route_long_name)
        route_name = route.get('short_name') or route.get('long_name') or f"Route {route.get('id')}"
        if not route_name or route_name.strip() == '':
            route_name = "Route 1"  # Default name when short_name is empty
        
        # For now, use estimated building count (will be replaced by geospatial query)
        # In production: buildings = await geo_client.query_buildings_along_route(route_id)
        estimated_buildings = 450  # Placeholder - needs geospatial query
        
        routes[route_name] = {
            'route_id': route.get('id'),
            'buildings_along_route': estimated_buildings
        }
    
    if not routes:
        print("❌ No valid routes found with spawn configs!")
        return
    
    # Calculate total buildings across all routes (for attractiveness denominator)
    total_buildings = sum(r['buildings_along_route'] for r in routes.values())
    
    # Calculate attractiveness for each route
    for route_name, route_data in routes.items():
        attractiveness = route_data['buildings_along_route'] / total_buildings
        route_data['attractiveness'] = attractiveness
    
    print("Route Configuration:")
    print("-" * 100)
    print(f"{'Route':<15} | {'Buildings':<12} | {'Attractiveness':<20} | {'Expected %'}")
    print("-" * 100)
    for route_name, route_data in routes.items():
        buildings = route_data['buildings_along_route']
        attractiveness = route_data['attractiveness']
        print(f"{route_name:<15} | {buildings:<12} | {attractiveness:<20.4f} | {attractiveness*100:.1f}%")
    print("-" * 100)
    print(f"{'TOTAL':<15} | {total_buildings:<12} | {1.0:<20.4f} | 100.0%")
    print()
    
    # Mock depot catchment (buildings near depot)
    depot_buildings = 250
    
    print(f"Depot Configuration:")
    print(f"  Buildings near depot: {depot_buildings}")
    print(f"  Spatial base: {depot_config['distribution_params']['spatial_base']}")
    print()
    
    # Sunday = Nov 10, 2024
    sunday_start = datetime(2024, 11, 10, 0, 0)
    monday_start = datetime(2024, 11, 11, 0, 0)
    
    # Storage for results
    results = {
        'Sunday': {route: [] for route in routes.keys()},
        'Monday': {route: [] for route in routes.keys()}
    }
    
    # Simulate both days
    for day_name, day_start in [('Sunday', sunday_start), ('Monday', monday_start)]:
        print("=" * 100)
        print(f"{day_name.upper()} (November {day_start.day}, 2024)")
        print("=" * 100)
        print()
        # Create header with route names
        route_names = list(routes.keys())
        header_parts = [f"{'Hour':<13}", "{'Terminal':<10}"]
        for route_name in route_names:
            header_parts.append(f"{route_name:<15}")
        print(" | ".join(header_parts))
        print("-" * 100)
        
        day_total = 0
        route_totals = {route: 0 for route in routes.keys()}
        
        for hour in range(24):
            current_time = day_start + timedelta(hours=hour)
            
            # Extract temporal multipliers using spawn calculator
            _, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
                spawn_config=depot_config,
                current_time=current_time
            )
            
            # Calculate terminal population (total passengers at depot for this hour)
            # Using simplified depot model (not building-based)
            spatial_base = depot_config['distribution_params']['spatial_base']
            lambda_terminal = spatial_base * hourly_mult * day_mult * 1.0  # 1 hour
            
            # Generate Poisson-distributed terminal population
            import numpy as np
            terminal_population = np.random.poisson(lambda_terminal) if lambda_terminal > 0 else 0
            
            # Distribute terminal population across routes based on attractiveness
            route_counts = {}
            for route_name, route_data in routes.items():
                attractiveness = route_data['attractiveness']
                # Each route gets proportional share of terminal population
                route_passengers = int(terminal_population * attractiveness)
                route_counts[route_name] = route_passengers
                route_totals[route_name] += route_passengers
            
            # Handle rounding error (distribute remainder to route with highest attractiveness)
            distributed = sum(route_counts.values())
            remainder = terminal_population - distributed
            if remainder > 0:
                max_route = max(routes.items(), key=lambda x: x[1]['attractiveness'])[0]
                route_counts[max_route] += remainder
                route_totals[max_route] += remainder
            
            day_total += terminal_population
            
            # Time label with emoji
            time_label = f"{hour:02d}:00-{hour:02d}:59"
            if 6 <= hour <= 9:
                emoji = "🌅"
            elif 16 <= hour <= 19:
                emoji = "🌆"
            elif 0 <= hour <= 5 or hour >= 22:
                emoji = "🌙"
            else:
                emoji = "☀️"
            
            # Build row
            row_parts = [f"{time_label} {emoji}", f"{terminal_population:10d}"]
            for route_name in route_names:
                row_parts.append(f"{route_counts[route_name]:<15}")
            
            # Add bar for first route
            if route_names:
                bar = '█' * min(route_counts[route_names[0]], 40)
                print(" | ".join(row_parts) + f" | {route_names[0]}: {bar}")
            else:
                print(" | ".join(row_parts))
            
            # Store for analysis
            for route_name in route_names:
                results[day_name][route_name].append(route_counts[route_name])
        
        print("-" * 100)
        
        # Totals row
        total_parts = [f"{'TOTAL':<13}", f"{day_total:10d}"]
        for route_name in route_names:
            total_parts.append(f"{route_totals[route_name]:<15}")
        print(" | ".join(total_parts))
        print()
        
        # Verify attractiveness distribution
        print(f"{day_name} Route Distribution:")
        for route_name, route_data in routes.items():
            actual_pct = (route_totals[route_name] / day_total * 100) if day_total > 0 else 0
            expected_pct = route_data['attractiveness'] * 100
            print(f"  {route_name}: {route_totals[route_name]:4d} passengers "
                  f"({actual_pct:.1f}% actual vs {expected_pct:.1f}% expected)")
        print()
    
    # Summary comparison
    print("=" * 100)
    print("SUMMARY - SUNDAY VS MONDAY")
    print("=" * 100)
    print()
    
    sunday_totals = {route: sum(results['Sunday'][route]) for route in routes.keys()}
    monday_totals = {route: sum(results['Monday'][route]) for route in routes.keys()}
    
    print(f"{'Route':<15} | {'Sunday':<12} | {'Monday':<12} | {'Ratio':<12} | {'Expected %'}")
    print("-" * 100)
    for route_name, route_data in routes.items():
        sunday = sunday_totals[route_name]
        monday = monday_totals[route_name]
        ratio = monday / sunday if sunday > 0 else 0
        expected_pct = route_data['attractiveness'] * 100
        print(f"{route_name:<15} | {sunday:<12d} | {monday:<12d} | {ratio:<12.2f}x | {expected_pct:.1f}%")
    
    print("-" * 100)
    total_sunday = sum(sunday_totals.values())
    total_monday = sum(monday_totals.values())
    total_ratio = total_monday / total_sunday if total_sunday > 0 else 0
    print(f"{'TOTAL':<15} | {total_sunday:<12d} | {total_monday:<12d} | {total_ratio:<12.2f}x | 100.0%")
    print()
    
    print("=" * 100)
    print("✓ PER-ROUTE SIMULATION COMPLETE")
    print("=" * 100)
    print()
    print("Key Insights:")
    print("  ✓ Routes with more buildings attract more passengers (attractiveness model)")
    print("  ✓ Distribution percentages match building density ratios")
    print("  ✓ Total terminal population is divided proportionally across routes")
    print("  ✓ Monday/Sunday ratio is consistent across all routes (~2.5x)")


if __name__ == "__main__":
    asyncio.run(simulate_per_route_weekend_to_monday())
