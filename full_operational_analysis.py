#!/usr/bin/env python3
"""
Operational Vehicle Capacity Analysis
====================================

Analyze how many vehicles can actually operate simultaneously when
all systems are online: conductors, drivers, engines, dispatcher,
depot management, maintenance, telemetry, etc.
"""

def analyze_operational_constraints():
    print("🚌 OPERATIONAL VEHICLE CAPACITY ANALYSIS")
    print("=" * 50)
    
    # Rock S0 constraints
    total_memory_mb = 512
    total_cpu_cores = 1  # Single core ARM Cortex-A55
    target_cpu_utilization = 0.75  # 75% max for stable operation
    
    print(f"🔧 ROCK S0 HARDWARE CONSTRAINTS:")
    print(f"   Memory: {total_memory_mb}MB")
    print(f"   CPU: Single ARM Cortex-A55 core")
    print(f"   Target CPU utilization: {target_cpu_utilization*100}%")
    print()
    
    # Test different vehicle counts
    vehicle_counts = [50, 75, 100, 125, 150, 175, 200, 225, 250]
    routes = 31
    passengers_per_route_per_hour = 150
    
    print(f"📊 TESTING VEHICLE COUNTS (with all systems online):")
    print(f"   Routes: {routes}")
    print(f"   Passenger load: {passengers_per_route_per_hour}/route/hour")
    print("-" * 80)
    print("Vehicles | Memory | CPU  | Conductors | Drivers | Engines | Dispatcher | Status")
    print("-" * 80)
    
    max_feasible_vehicles = 0
    
    for vehicle_count in vehicle_counts:
        result = analyze_full_system_load(vehicle_count, routes, passengers_per_route_per_hour)
        
        status = "✅ GOOD" if result['feasible'] and result['cpu_pct'] < 60 else \
                 "⚠️  OK" if result['feasible'] else "❌ OVERLOAD"
        
        print(f"{vehicle_count:8d} | {result['memory_mb']:5.1f}MB | {result['cpu_pct']:4.1f}% | "
              f"{result['conductors']:9d} | {result['drivers']:7d} | {result['engines']:7d} | "
              f"{result['dispatchers']:9d} | {status}")
        
        if result['feasible'] and result['cpu_pct'] < target_cpu_utilization * 100:
            max_feasible_vehicles = vehicle_count
    
    print("-" * 80)
    print(f"🏆 MAXIMUM OPERATIONAL VEHICLES: {max_feasible_vehicles}")
    
    return max_feasible_vehicles

def analyze_full_system_load(vehicles, routes, passengers_per_hour):
    """Analyze complete system load with all operational components."""
    
    # Calculate concurrent passengers
    avg_journey_minutes = 25
    concurrent_per_route = passengers_per_hour * (avg_journey_minutes / 60)
    total_concurrent_passengers = routes * concurrent_per_route
    
    # Operational staff requirements
    conductors = vehicles  # 1 conductor per vehicle
    drivers = vehicles     # 1 driver per vehicle  
    engines = vehicles     # 1 engine per vehicle
    dispatchers = max(1, routes // 5)  # 1 dispatcher per 5 routes
    depot_managers = max(1, vehicles // 50)  # 1 depot manager per 50 vehicles
    maintenance_staff = max(1, vehicles // 25)  # 1 maintenance per 25 vehicles
    
    # Memory analysis (enhanced for full operations)
    base_system_mb = 80
    passenger_memory_kb = 2
    vehicle_memory_kb = 85      # Enhanced: GPS + telemetry + conductor + driver + engine
    conductor_memory_kb = 25    # Conductor state, passenger management
    driver_memory_kb = 20       # Driver state, route navigation
    engine_memory_kb = 15       # Engine telemetry, fuel, maintenance
    dispatcher_memory_kb = 200  # Route coordination, vehicle assignment
    depot_memory_kb = 150       # Per depot manager
    maintenance_memory_kb = 100 # Per maintenance staff
    route_memory_kb = 150
    
    passenger_memory_mb = (total_concurrent_passengers * passenger_memory_kb) / 1024
    vehicle_memory_mb = (vehicles * vehicle_memory_kb) / 1024
    conductor_memory_mb = (conductors * conductor_memory_kb) / 1024
    driver_memory_mb = (drivers * driver_memory_kb) / 1024
    engine_memory_mb = (engines * engine_memory_kb) / 1024
    dispatcher_memory_mb = (dispatchers * dispatcher_memory_kb) / 1024
    depot_memory_mb = (depot_managers * depot_memory_kb) / 1024
    maintenance_memory_mb = (maintenance_staff * maintenance_memory_kb) / 1024
    route_memory_mb = (routes * route_memory_kb) / 1024
    
    total_memory_mb = (base_system_mb + passenger_memory_mb + vehicle_memory_mb + 
                      conductor_memory_mb + driver_memory_mb + engine_memory_mb +
                      dispatcher_memory_mb + depot_memory_mb + maintenance_memory_mb + route_memory_mb)
    
    # CPU analysis (enhanced for full operations)
    spawn_cpu_ms = 5
    vehicle_gps_ms = 3          # GPS processing per vehicle
    conductor_cpu_ms = 4        # Passenger management, boarding/alighting
    driver_cpu_ms = 2           # Route navigation, decision making
    engine_cpu_ms = 1.5         # Engine monitoring, fuel calculation
    dispatcher_cpu_ms = 15      # Route coordination, vehicle assignment
    depot_cpu_ms = 3            # Depot operations per vehicle
    maintenance_cpu_ms = 2      # Maintenance checks per vehicle
    passenger_update_ms = 1     # Passenger position updates
    
    # Operations per second
    gps_hz = 0.5               # Every 2 seconds (optimized)
    conductor_hz = 0.2         # Conductor operations
    driver_hz = 0.33           # Driver decision frequency
    engine_hz = 0.1            # Engine monitoring
    dispatcher_hz = 0.05       # Dispatcher coordination
    depot_hz = 0.08            # Depot operations
    maintenance_hz = 0.02      # Maintenance checks
    passenger_hz = 0.1         # Passenger updates
    
    spawns_per_minute = total_concurrent_passengers / 25  # 25 minute passenger lifetime
    cpu_spawns_per_sec = spawns_per_minute / 60 * spawn_cpu_ms
    cpu_gps_per_sec = vehicles * vehicle_gps_ms * gps_hz
    cpu_conductors_per_sec = conductors * conductor_cpu_ms * conductor_hz
    cpu_drivers_per_sec = drivers * driver_cpu_ms * driver_hz
    cpu_engines_per_sec = engines * engine_cpu_ms * engine_hz
    cpu_dispatchers_per_sec = dispatchers * dispatcher_cpu_ms * dispatcher_hz
    cpu_depot_per_sec = vehicles * depot_cpu_ms * depot_hz
    cpu_maintenance_per_sec = vehicles * maintenance_cpu_ms * maintenance_hz
    cpu_passengers_per_sec = total_concurrent_passengers * passenger_update_ms * passenger_hz
    
    total_cpu_ms_per_sec = (cpu_spawns_per_sec + cpu_gps_per_sec + cpu_conductors_per_sec +
                           cpu_drivers_per_sec + cpu_engines_per_sec + cpu_dispatchers_per_sec +
                           cpu_depot_per_sec + cpu_maintenance_per_sec + cpu_passengers_per_sec)
    
    cpu_utilization_pct = 100 * total_cpu_ms_per_sec / 1000
    
    # Feasibility check
    memory_ok = total_memory_mb < 480  # Leave 32MB headroom
    cpu_ok = cpu_utilization_pct < 90  # 90% max for full operations
    
    return {
        'vehicles': vehicles,
        'conductors': conductors,
        'drivers': drivers,
        'engines': engines,
        'dispatchers': dispatchers,
        'depot_managers': depot_managers,
        'maintenance_staff': maintenance_staff,
        'memory_mb': total_memory_mb,
        'memory_pct': 100 * total_memory_mb / 512,
        'cpu_pct': cpu_utilization_pct,
        'cpu_ms_per_sec': total_cpu_ms_per_sec,
        'feasible': memory_ok and cpu_ok,
        'concurrent_passengers': total_concurrent_passengers
    }

def analyze_system_breakdown(max_vehicles):
    """Analyze the system breakdown for maximum operational vehicles."""
    print(f"\n🔍 DETAILED SYSTEM BREAKDOWN ({max_vehicles} VEHICLES)")
    print("=" * 55)
    
    routes = 31
    passengers_per_hour = 150
    result = analyze_full_system_load(max_vehicles, routes, passengers_per_hour)
    
    print(f"📋 OPERATIONAL STAFF:")
    print(f"   Conductors: {result['conductors']} (1 per vehicle)")
    print(f"   Drivers: {result['drivers']} (1 per vehicle)")
    print(f"   Engines: {result['engines']} (1 per vehicle)")
    print(f"   Dispatchers: {result['dispatchers']} (1 per {routes//result['dispatchers']} routes)")
    print(f"   Depot managers: {result['depot_managers']} (1 per {max_vehicles//result['depot_managers']} vehicles)")
    print(f"   Maintenance staff: {result['maintenance_staff']} (1 per {max_vehicles//result['maintenance_staff']} vehicles)")
    
    print(f"\n💾 MEMORY ALLOCATION:")
    print(f"   Total usage: {result['memory_mb']:.1f}MB ({result['memory_pct']:.1f}%)")
    print(f"   Available headroom: {512 - result['memory_mb']:.1f}MB")
    
    print(f"\n🔥 CPU ALLOCATION:")
    print(f"   Total usage: {result['cpu_pct']:.1f}%")
    print(f"   Available headroom: {100 - result['cpu_pct']:.1f}%")
    
    print(f"\n🚌 PASSENGER CAPACITY:")
    print(f"   Concurrent passengers: {result['concurrent_passengers']:.0f}")
    print(f"   Hourly throughput: {routes * passengers_per_hour:,} passengers/hour")
    print(f"   Daily capacity: ~{routes * passengers_per_hour * 16:,} passengers/day")

def recommend_operational_configuration(max_vehicles):
    """Recommend configuration for maximum operational capacity."""
    print(f"\n🎯 RECOMMENDED OPERATIONAL CONFIGURATION")
    print("=" * 50)
    
    routes = 31
    result = analyze_full_system_load(max_vehicles, routes, 150)
    
    print(f"# Full operational capacity: {max_vehicles} vehicles")
    print(f"# All systems online: conductors, drivers, engines, dispatcher, depot")
    print(f"# CPU: {result['cpu_pct']:.1f}%, Memory: {result['memory_pct']:.1f}%")
    print()
    print("[simulation]")
    print("tick_time = 1.0")
    print("standalone_mode = true")
    print(f"max_operational_vehicles = {max_vehicles}")
    print()
    print("[operational_staff]")
    print(f"conductors_per_vehicle = 1")
    print(f"drivers_per_vehicle = 1") 
    print(f"dispatchers_total = {result['dispatchers']}")
    print(f"depot_managers_total = {result['depot_managers']}")
    print(f"maintenance_staff_total = {result['maintenance_staff']}")
    print()
    print("[vehicle_telemetry]")
    print("gps_update_interval_seconds = 2.0")
    print("conductor_update_interval_seconds = 5.0")
    print("driver_update_interval_seconds = 3.0")
    print("engine_telemetry_interval_seconds = 10.0")
    print()
    print("[dispatcher]")
    print(f"coordination_interval_seconds = 20.0")
    print(f"vehicle_assignment_interval_seconds = 30.0")
    print(f"route_optimization_interval_seconds = 300.0")
    print()
    print("[depot_simulation]")
    print("enable_full_simulation = true")
    print(f"max_vehicles = {max_vehicles}")
    print("enable_conductor_management = true")
    print("enable_driver_scheduling = true")
    print("enable_engine_monitoring = true")
    print("enable_dispatcher_coordination = true")

if __name__ == "__main__":
    max_vehicles = analyze_operational_constraints()
    if max_vehicles > 0:
        analyze_system_breakdown(max_vehicles)
        recommend_operational_configuration(max_vehicles)
    else:
        print("❌ No feasible operational configuration found")