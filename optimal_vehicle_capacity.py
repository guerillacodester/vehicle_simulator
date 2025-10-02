"""
Optimal Vehicle Capacity Calculator
==================================

Calculate maximum feasible vehicle count for OVH VPS with performance optimizations.
"""

import math

def calculate_optimal_vehicle_capacity():
    """Calculate optimal vehicle capacity for OVH 2-core VPS."""
    
    print("🎯 OPTIMAL VEHICLE CAPACITY ANALYSIS")
    print("=" * 50)
    
    # Hardware constraints
    available_cores = 2
    available_memory_gb = 2
    safe_cpu_utilization = 0.85  # 85% max for stability
    safe_memory_utilization = 0.80  # 80% max for stability
    
    # Memory requirements per vehicle (optimized)
    memory_per_vehicle = {
        'vehicle_driver': 2048,           # 2KB per driver
        'conductor': 1536,               # 1.5KB per conductor  
        'gps_device': 512,               # 512B per GPS device
        'engine': 256,                   # 256B per engine
        'telemetry_buffer': 4096,        # 4KB per vehicle telemetry
        'avg_passengers': 20 * 1024,     # 20 passengers × 1KB each
    }
    
    total_memory_per_vehicle = sum(memory_per_vehicle.values())
    python_overhead = 3.0  # Python object overhead
    effective_memory_per_vehicle = total_memory_per_vehicle * python_overhead
    
    # CPU requirements per vehicle (optimized)
    cpu_operations_per_vehicle_per_second = {
        'gps_updates': 0.5,              # Reduced from 1Hz to 0.5Hz
        'distance_calculations': 10,      # Reduced with spatial indexing
        'route_interpolation': 1,        # Route following
        'pickup_eligibility': 2,         # Reduced with caching
        'state_updates': 3,              # State transitions
        'api_calls': 0.05,               # Batched API calls (1 per 20 vehicles)
    }
    
    # CPU cost per operation (microseconds) - optimized
    cpu_cost_per_operation = {
        'gps_updates': 8,                # Optimized GPS updates
        'distance_calculations': 15,     # Cached calculations
        'route_interpolation': 40,       # Optimized math
        'pickup_eligibility': 60,        # Spatial indexing
        'state_updates': 4,              # Simple state changes
        'api_calls': 1500,               # Batched HTTP requests
    }
    
    # Calculate CPU microseconds per vehicle per second
    cpu_us_per_vehicle = sum(
        ops * cost for ops, cost in zip(
            cpu_operations_per_vehicle_per_second.values(),
            cpu_cost_per_operation.values()
        )
    )
    
    # Memory-based maximum
    available_memory_bytes = available_memory_gb * 1024 * 1024 * 1024 * safe_memory_utilization
    base_system_memory = 100 * 1024 * 1024  # 100MB for system overhead
    usable_memory = available_memory_bytes - base_system_memory
    
    max_vehicles_memory = int(usable_memory / effective_memory_per_vehicle)
    
    # CPU-based maximum  
    available_cpu_us = available_cores * 1_000_000 * safe_cpu_utilization  # microseconds per second
    max_vehicles_cpu = int(available_cpu_us / cpu_us_per_vehicle)
    
    # Route geometry overhead (31 routes)
    routes = 31
    memory_per_route = 22000  # 22KB per route with 88 GPS points
    total_route_memory = routes * memory_per_route * python_overhead
    
    # Adjusted memory calculation
    adjusted_usable_memory = usable_memory - total_route_memory
    max_vehicles_memory_adjusted = int(adjusted_usable_memory / effective_memory_per_vehicle)
    
    print(f"📊 RESOURCE ANALYSIS:")
    print(f"  Available CPU: {available_cores} cores × {safe_cpu_utilization*100:.0f}% = {available_cpu_us:,.0f} μs/sec")
    print(f"  Available Memory: {available_memory_gb}GB × {safe_memory_utilization*100:.0f}% = {usable_memory/1024/1024:.0f}MB")
    print(f"  Route Memory Overhead: {total_route_memory/1024/1024:.1f}MB (31 routes)")
    
    print(f"\n🚗 VEHICLE RESOURCE REQUIREMENTS:")
    print(f"  Memory per vehicle: {effective_memory_per_vehicle/1024:.1f}KB")
    print(f"  CPU per vehicle: {cpu_us_per_vehicle:.0f} μs/sec")
    
    print(f"\n🎯 MAXIMUM VEHICLE CALCULATIONS:")
    print(f"  Memory limit: {max_vehicles_memory_adjusted:,} vehicles")
    print(f"  CPU limit: {max_vehicles_cpu:,} vehicles")
    
    # Overall maximum (bottleneck)
    max_vehicles_optimal = min(max_vehicles_memory_adjusted, max_vehicles_cpu)
    
    print(f"\n🏆 OPTIMAL MAXIMUM: {max_vehicles_optimal:,} VEHICLES")
    
    # Performance at different scales
    print(f"\n📈 PERFORMANCE AT DIFFERENT SCALES:")
    vehicle_scales = [300, 600, 900, max_vehicles_optimal, 1200]
    
    for vehicles in vehicle_scales:
        memory_usage = (vehicles * effective_memory_per_vehicle + total_route_memory) / (available_memory_gb * 1024**3) * 100
        cpu_usage = (vehicles * cpu_us_per_vehicle) / (available_cores * 1_000_000) * 100
        
        status = "✅" if memory_usage < 80 and cpu_usage < 85 else "⚠️" if memory_usage < 90 and cpu_usage < 95 else "❌"
        
        print(f"  {vehicles:4d} vehicles: {memory_usage:5.1f}% RAM, {cpu_usage:5.1f}% CPU {status}")
    
    # Rush hour analysis
    print(f"\n🚦 RUSH HOUR CONSIDERATIONS:")
    rush_hour_multiplier = 1.3  # 30% more activity during rush hour
    rush_hour_cpu_usage = (max_vehicles_optimal * cpu_us_per_vehicle * rush_hour_multiplier) / (available_cores * 1_000_000) * 100
    
    print(f"  Normal load: {max_vehicles_optimal:,} vehicles at {cpu_usage:.1f}% CPU")
    print(f"  Rush hour load: {max_vehicles_optimal:,} vehicles at {rush_hour_cpu_usage:.1f}% CPU")
    
    if rush_hour_cpu_usage > 95:
        rush_hour_safe_vehicles = int(max_vehicles_optimal / rush_hour_multiplier)
        print(f"  🎯 Rush hour safe limit: {rush_hour_safe_vehicles:,} vehicles")
        return rush_hour_safe_vehicles
    
    return max_vehicles_optimal

def calculate_deployment_scenarios():
    """Calculate different deployment scenarios and their vehicle capacity."""
    
    print(f"\n🏗️ DEPLOYMENT SCENARIO COMPARISON:")
    print("=" * 50)
    
    scenarios = [
        {
            'name': 'Current VPS (Unoptimized)',
            'cores': 2,
            'memory_gb': 2,
            'gps_frequency': 1.0,
            'spatial_indexing': False,
            'caching': False,
            'cost_factor': 1.0
        },
        {
            'name': 'Current VPS (Optimized)',
            'cores': 2,
            'memory_gb': 2,
            'gps_frequency': 0.5,
            'spatial_indexing': True,
            'caching': True,
            'cost_factor': 1.0
        },
        {
            'name': 'OVH VPS-SSD-3',
            'cores': 4,
            'memory_gb': 8,
            'gps_frequency': 1.0,
            'spatial_indexing': True,
            'caching': True,
            'cost_factor': 2.5
        },
        {
            'name': 'OVH VPS-SSD-4',
            'cores': 8,
            'memory_gb': 16,
            'gps_frequency': 1.0,
            'spatial_indexing': True,
            'caching': True,
            'cost_factor': 4.0
        }
    ]
    
    for scenario in scenarios:
        # Calculate CPU capacity with optimizations
        base_cpu_per_vehicle = 141.0  # microseconds from original analysis
        
        optimizations = 1.0
        if scenario['gps_frequency'] == 0.5:
            optimizations *= 0.88  # 12% reduction
        if scenario['spatial_indexing']:
            optimizations *= 0.60  # 40% reduction  
        if scenario['caching']:
            optimizations *= 0.75  # 25% reduction
            
        optimized_cpu_per_vehicle = base_cpu_per_vehicle * optimizations
        
        available_cpu = scenario['cores'] * 100 * 0.85  # 85% safe utilization
        max_vehicles_cpu = int(available_cpu / (optimized_cpu_per_vehicle / 100))
        
        # Memory capacity (simplified)
        available_memory_mb = scenario['memory_gb'] * 1024 * 0.80  # 80% safe utilization
        memory_per_vehicle_mb = 0.138  # From previous analysis
        max_vehicles_memory = int((available_memory_mb - 100) / memory_per_vehicle_mb)  # 100MB system overhead
        
        max_vehicles = min(max_vehicles_cpu, max_vehicles_memory)
        
        print(f"  {scenario['name']:20s}: {max_vehicles:4d} vehicles (Cost: {scenario['cost_factor']:.1f}x)")
    
    return scenarios

if __name__ == "__main__":
    optimal_vehicles = calculate_optimal_vehicle_capacity()
    calculate_deployment_scenarios()
    
    print(f"\n🎯 EXECUTIVE SUMMARY:")
    print(f"  Optimal vehicle count: {optimal_vehicles:,} vehicles")
    print(f"  Target capacity (1,200): {'✅ ACHIEVABLE' if optimal_vehicles >= 1200 else '❌ REQUIRES UPGRADE'}")
    
    if optimal_vehicles < 1200:
        deficit = 1200 - optimal_vehicles
        print(f"  Capacity deficit: {deficit:,} vehicles ({deficit/1200*100:.1f}%)")
        print(f"  Recommended: Upgrade VPS or implement vehicle sharding")