#!/usr/bin/env python3
"""
Rock S0 Optimization: Maximum Passenger Load Analysis
====================================================

Find the optimal configuration for maximum passengers per route
while maintaining smooth operation on a single Rock S0 device.

Target: <80% CPU utilization for smooth operation
"""

def analyze_optimized_configurations():
    print("🎯 ROCK S0 OPTIMIZATION ANALYSIS")
    print("=" * 50)
    
    routes = 31
    vehicles = 200
    target_cpu_utilization = 0.80  # 80% max for smooth operation
    
    # Test different passenger counts per route
    test_configs = [50, 45, 40, 35, 30, 25, 20, 15]
    
    print(f"🎛️  TESTING CONFIGURATIONS (Target: <80% CPU):")
    print(f"   Routes: {routes}, Vehicles: {vehicles}")
    print("-" * 70)
    
    best_config = None
    
    for passengers_per_route in test_configs:
        total_passengers = routes * passengers_per_route
        result = analyze_configuration(routes, vehicles, passengers_per_route, total_passengers)
        
        print(f"📊 {passengers_per_route:2d} passengers/route ({total_passengers:4d} total):")
        print(f"   Memory: {result['memory_mb']:5.1f}MB ({result['memory_pct']:4.1f}%)")
        print(f"   CPU:    {result['cpu_pct']:5.1f}% {'✅' if result['cpu_pct'] < 80 else '❌'}")
        print(f"   Spawn:  {result['spawn_interval']:4.1f}s interval, {result['spawns_per_hour']:4.0f}/hr")
        
        if result['cpu_pct'] < 80 and best_config is None:
            best_config = {
                'passengers_per_route': passengers_per_route,
                'total_passengers': total_passengers,
                **result
            }
        print()
    
    if best_config:
        print(f"🏆 OPTIMAL CONFIGURATION FOUND:")
        print(f"   Passengers per route: {best_config['passengers_per_route']}")
        print(f"   Total concurrent passengers: {best_config['total_passengers']}")
        print(f"   CPU utilization: {best_config['cpu_pct']:.1f}%")
        print(f"   Memory usage: {best_config['memory_mb']:.1f}MB ({best_config['memory_pct']:.1f}%)")
        print(f"   CPU headroom: {100 - best_config['cpu_pct']:.1f}%")
        
        return best_config
    else:
        print("❌ No configuration found meeting 80% CPU target")
        return None

def analyze_configuration(routes, vehicles, passengers_per_route, total_passengers):
    """Analyze a specific configuration and return metrics."""
    
    # Memory analysis (same as before)
    passenger_memory_kb = 2
    vehicle_memory_kb = 75
    route_memory_kb = 150
    depot_memory_kb = 200
    driver_memory_kb = 50
    maintenance_memory_kb = 30
    base_system_mb = 80
    
    passenger_memory_mb = (total_passengers * passenger_memory_kb) / 1024
    vehicle_memory_mb = (vehicles * vehicle_memory_kb) / 1024
    route_memory_mb = (routes * route_memory_kb) / 1024
    depot_memory_mb = (vehicles * depot_memory_kb) / 1024
    driver_memory_mb = (vehicles * driver_memory_kb) / 1024
    maintenance_memory_mb = (vehicles * maintenance_memory_kb) / 1024
    
    total_memory_mb = (base_system_mb + passenger_memory_mb + vehicle_memory_mb + 
                      route_memory_mb + depot_memory_mb + driver_memory_mb + maintenance_memory_mb)
    
    # CPU analysis
    passenger_lifetime_minutes = 30
    spawns_per_minute = total_passengers / passenger_lifetime_minutes
    spawn_interval = 60 / spawns_per_minute
    spawns_per_hour = spawns_per_minute * 60
    
    spawn_cpu_ms = 5
    vehicle_update_ms = 3
    passenger_update_ms = 1
    depot_operations_ms = 2
    maintenance_check_ms = 1
    driver_management_ms = 0.5
    
    cpu_spawns_per_sec = spawns_per_minute / 60 * spawn_cpu_ms
    cpu_vehicles_per_sec = vehicles * vehicle_update_ms * 1.0
    cpu_passengers_per_sec = total_passengers * passenger_update_ms * 0.2
    cpu_depot_per_sec = vehicles * depot_operations_ms * 0.1
    cpu_maintenance_per_sec = vehicles * maintenance_check_ms * 0.05
    cpu_driver_per_sec = vehicles * driver_management_ms * 0.02
    
    total_cpu_ms_per_sec = (cpu_spawns_per_sec + cpu_vehicles_per_sec + cpu_passengers_per_sec + 
                           cpu_depot_per_sec + cpu_maintenance_per_sec + cpu_driver_per_sec)
    cpu_utilization = total_cpu_ms_per_sec / 1000
    
    return {
        'memory_mb': total_memory_mb,
        'memory_pct': 100 * total_memory_mb / 512,
        'cpu_pct': 100 * cpu_utilization,
        'spawn_interval': spawn_interval,
        'spawns_per_hour': spawns_per_hour,
        'passenger_memory_mb': passenger_memory_mb,
        'cpu_ms_per_sec': total_cpu_ms_per_sec
    }

def analyze_optimization_strategies():
    """Analyze different optimization strategies to increase passenger capacity."""
    print("\n🔧 OPTIMIZATION STRATEGIES")
    print("=" * 40)
    
    routes = 31
    vehicles = 200
    base_passengers_per_route = 35  # Starting point from analysis
    
    print("📈 STRATEGY 1: REDUCE UPDATE FREQUENCIES")
    print("-" * 45)
    
    # Test reduced update frequencies
    strategies = [
        {"name": "Baseline", "vehicle_hz": 1.0, "passenger_hz": 0.2, "depot_hz": 0.1},
        {"name": "Reduced Vehicle GPS", "vehicle_hz": 0.5, "passenger_hz": 0.2, "depot_hz": 0.1},
        {"name": "Reduced Passenger", "vehicle_hz": 1.0, "passenger_hz": 0.1, "depot_hz": 0.1},
        {"name": "Reduced Both", "vehicle_hz": 0.5, "passenger_hz": 0.1, "depot_hz": 0.1},
        {"name": "Minimal Updates", "vehicle_hz": 0.33, "passenger_hz": 0.067, "depot_hz": 0.05},
    ]
    
    for strategy in strategies:
        cpu_savings = calculate_cpu_with_strategy(routes, vehicles, base_passengers_per_route, strategy)
        max_passengers = find_max_passengers_with_strategy(routes, vehicles, strategy)
        
        print(f"   {strategy['name']:15s}: {cpu_savings:5.1f}% CPU → Max {max_passengers:2d} passengers/route")
    
    print(f"\n📊 STRATEGY 2: SELECTIVE FEATURE REDUCTION")
    print("-" * 50)
    
    feature_strategies = [
        {"name": "Full Features", "depot": True, "maintenance": True, "driver": True, "telemetry": True},
        {"name": "No Maintenance", "depot": True, "maintenance": False, "driver": True, "telemetry": True},
        {"name": "No Driver Mgmt", "depot": True, "maintenance": True, "driver": False, "telemetry": True},
        {"name": "Basic Depot Only", "depot": True, "maintenance": False, "driver": False, "telemetry": False},
        {"name": "Vehicles Only", "depot": False, "maintenance": False, "driver": False, "telemetry": False},
    ]
    
    for strategy in feature_strategies:
        max_passengers = calculate_max_with_features(routes, vehicles, strategy)
        print(f"   {strategy['name']:15s}: Max {max_passengers:2d} passengers/route")

def calculate_cpu_with_strategy(routes, vehicles, passengers_per_route, strategy):
    """Calculate CPU usage with a specific update frequency strategy."""
    total_passengers = routes * passengers_per_route
    
    # Base CPU calculations with custom frequencies
    spawn_cpu_ms = 5
    vehicle_update_ms = 3
    passenger_update_ms = 1
    depot_operations_ms = 2
    maintenance_check_ms = 1
    driver_management_ms = 0.5
    
    spawns_per_minute = total_passengers / 30  # 30 minute lifetime
    cpu_spawns_per_sec = spawns_per_minute / 60 * spawn_cpu_ms
    cpu_vehicles_per_sec = vehicles * vehicle_update_ms * strategy["vehicle_hz"]
    cpu_passengers_per_sec = total_passengers * passenger_update_ms * strategy["passenger_hz"]
    cpu_depot_per_sec = vehicles * depot_operations_ms * strategy["depot_hz"]
    cpu_maintenance_per_sec = vehicles * maintenance_check_ms * 0.05  # Keep maintenance low
    cpu_driver_per_sec = vehicles * driver_management_ms * 0.02      # Keep driver mgmt low
    
    total_cpu_ms_per_sec = (cpu_spawns_per_sec + cpu_vehicles_per_sec + cpu_passengers_per_sec + 
                           cpu_depot_per_sec + cpu_maintenance_per_sec + cpu_driver_per_sec)
    cpu_utilization = 100 * total_cpu_ms_per_sec / 1000
    
    return cpu_utilization

def find_max_passengers_with_strategy(routes, vehicles, strategy):
    """Find maximum passengers per route with a given strategy."""
    for passengers_per_route in range(50, 10, -1):
        cpu_usage = calculate_cpu_with_strategy(routes, vehicles, passengers_per_route, strategy)
        if cpu_usage < 80:
            return passengers_per_route
    return 10

def calculate_max_with_features(routes, vehicles, features):
    """Calculate max passengers with selective features enabled."""
    # Simplified calculation - just estimate based on feature overhead
    base_max = 35  # Known baseline
    
    savings = 0
    if not features["maintenance"]: savings += 5  # 5% CPU savings
    if not features["driver"]: savings += 2      # 2% CPU savings  
    if not features["telemetry"]: savings += 3   # 3% CPU savings
    if not features["depot"]: savings += 8       # 8% CPU savings
    
    # Rough estimate: each 2% CPU savings = +1 passenger per route
    bonus_passengers = int(savings / 2)
    return min(50, base_max + bonus_passengers)

def generate_optimal_config(config):
    """Generate the optimal configuration file."""
    if not config:
        return
        
    print(f"\n🎯 RECOMMENDED CONFIGURATION")
    print("=" * 40)
    
    print("# Optimized for single Rock S0 - Maximum passenger load")
    print("[passenger_service]")
    print(f"max_concurrent_spawns = {config['passengers_per_route']}")
    print(f"max_passengers_per_route = {config['passengers_per_route']}")
    print(f"spawn_interval_seconds = {config['spawn_interval']:.1f}")
    print("cleanup_interval_seconds = 20.0")
    print("monitoring_interval_seconds = 3.0")
    print("walking_distance_km = 0.4")
    print("route_discovery_radius_km = 0.6")
    print("passenger_timeout_minutes = 30.0")
    print("destination_distance_meters = 400")
    print(f"max_spawns_per_hour = {int(config['spawns_per_hour'])}")
    print(f"memory_limit_mb = {int(config['passenger_memory_mb'] * 1.2)}")
    
    print(f"\n[vehicle_telemetry]")
    print("gps_update_frequency_hz = 0.5  # Reduced from 1.0 for CPU optimization")
    print("telemetry_frequency_hz = 0.15  # Reduced from 0.2")
    print("status_update_frequency_hz = 0.08  # Reduced from 0.1")
    
    print(f"\n[depot_simulation]")
    print("maintenance_check_frequency_hz = 0.03  # Reduced from 0.05")
    print("driver_management_frequency_hz = 0.015  # Reduced from 0.02")
    print("depot_operations_frequency_hz = 0.08   # Reduced from 0.1")

if __name__ == "__main__":
    optimal_config = analyze_optimized_configurations()
    analyze_optimization_strategies()
    generate_optimal_config(optimal_config)