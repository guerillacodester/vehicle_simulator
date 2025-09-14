#!/usr/bin/env python3
"""
Rock S0 Performance Analysis for Transit System
===============================================

Analyze feasibility of:
- 150 spawns/hour across 31 routes  
- 100 vehicles active simultaneously
- Rock S0 hardware constraints (512MB RAM, ARM Cortex-A55)
"""

def analyze_spawn_requirements():
    print("🚌 TRANSIT SYSTEM PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Target requirements
    routes = 31
    vehicles = 100
    spawns_per_hour = 150
    
    print(f"📋 TARGET REQUIREMENTS:")
    print(f"   • Routes: {routes}")
    print(f"   • Active vehicles: {vehicles}")
    print(f"   • Passenger spawns: {spawns_per_hour}/hour")
    
    # Calculate spawn intervals
    seconds_per_hour = 3600
    spawn_interval = seconds_per_hour / spawns_per_hour
    spawns_per_minute = spawns_per_hour / 60
    spawns_per_route_hour = spawns_per_hour / routes
    spawns_per_route_minute = spawns_per_route_hour / 60
    
    print(f"\n⏱️  SPAWN TIMING ANALYSIS:")
    print(f"   • Spawn interval: {spawn_interval:.1f} seconds")
    print(f"   • Spawns per minute: {spawns_per_minute:.1f}")
    print(f"   • Spawns per route/hour: {spawns_per_route_hour:.1f}")
    print(f"   • Spawns per route/minute: {spawns_per_route_minute:.2f}")
    
    # Memory analysis
    passenger_memory_kb = 2  # Estimated per passenger
    vehicle_memory_kb = 50   # Estimated per vehicle  
    route_memory_kb = 100    # Estimated per route
    base_system_mb = 50      # OS + Python + framework
    
    # Calculate concurrent passengers (30min timeout)
    passenger_lifetime_minutes = 30
    concurrent_passengers = spawns_per_minute * passenger_lifetime_minutes
    
    passenger_memory_mb = (concurrent_passengers * passenger_memory_kb) / 1024
    vehicle_memory_mb = (vehicles * vehicle_memory_kb) / 1024
    route_memory_mb = (routes * route_memory_kb) / 1024
    total_memory_mb = base_system_mb + passenger_memory_mb + vehicle_memory_mb + route_memory_mb
    
    print(f"\n💾 MEMORY ANALYSIS (Rock S0: 512MB RAM):")
    print(f"   • Concurrent passengers: {concurrent_passengers:.0f}")
    print(f"   • Passenger memory: {passenger_memory_mb:.1f}MB")
    print(f"   • Vehicle memory: {vehicle_memory_mb:.1f}MB") 
    print(f"   • Route memory: {route_memory_mb:.1f}MB")
    print(f"   • Base system: {base_system_mb}MB")
    print(f"   • TOTAL ESTIMATED: {total_memory_mb:.1f}MB")
    print(f"   • Available: 512MB")
    print(f"   • Utilization: {100 * total_memory_mb / 512:.1f}%")
    
    # CPU analysis  
    spawn_cpu_ms = 5      # CPU time per spawn
    vehicle_update_ms = 2 # CPU time per vehicle update (1Hz)
    passenger_update_ms = 1 # CPU time per passenger update (0.2Hz)
    
    cpu_spawns_per_sec = spawns_per_minute / 60 * spawn_cpu_ms
    cpu_vehicles_per_sec = vehicles * vehicle_update_ms 
    cpu_passengers_per_sec = concurrent_passengers * passenger_update_ms * 0.2
    total_cpu_ms_per_sec = cpu_spawns_per_sec + cpu_vehicles_per_sec + cpu_passengers_per_sec
    cpu_utilization = total_cpu_ms_per_sec / 1000
    
    print(f"\n🔥 CPU ANALYSIS (Rock S0: ARM Cortex-A55):")
    print(f"   • Spawn processing: {cpu_spawns_per_sec:.1f}ms/sec")
    print(f"   • Vehicle updates: {cpu_vehicles_per_sec:.1f}ms/sec")
    print(f"   • Passenger updates: {cpu_passengers_per_sec:.1f}ms/sec")
    print(f"   • TOTAL CPU LOAD: {total_cpu_ms_per_sec:.1f}ms/sec")
    print(f"   • CPU utilization: {100 * cpu_utilization:.1f}%")
    
    # Storage analysis
    passenger_storage_kb = 1
    route_geometry_mb = 2
    logs_per_hour_mb = 10
    total_storage_mb = (concurrent_passengers * passenger_storage_kb / 1024 + 
                       routes * route_geometry_mb + logs_per_hour_mb)
    
    print(f"\n💿 STORAGE ANALYSIS:")
    print(f"   • Passenger data: {concurrent_passengers * passenger_storage_kb / 1024:.1f}MB")
    print(f"   • Route geometry: {routes * route_geometry_mb:.1f}MB")
    print(f"   • Logs/hour: {logs_per_hour_mb}MB")
    print(f"   • TOTAL STORAGE: {total_storage_mb:.1f}MB")
    
    # Network analysis
    gps_updates_per_sec = vehicles * 1  # 1Hz GPS
    passenger_events_per_sec = spawns_per_minute / 60 * 2  # spawn + pickup events
    api_calls_per_sec = gps_updates_per_sec + passenger_events_per_sec
    bandwidth_kbps = api_calls_per_sec * 0.5  # 0.5KB per API call
    
    print(f"\n🌐 NETWORK ANALYSIS:")
    print(f"   • GPS updates: {gps_updates_per_sec}/sec")
    print(f"   • Passenger events: {passenger_events_per_sec:.1f}/sec")
    print(f"   • Total API calls: {api_calls_per_sec:.1f}/sec")
    print(f"   • Bandwidth needed: {bandwidth_kbps:.1f}Kbps")
    
    # Feasibility assessment
    memory_ok = total_memory_mb < 400  # Leave 112MB headroom
    cpu_ok = cpu_utilization < 0.7     # Max 70% CPU
    storage_ok = total_storage_mb < 1000  # Reasonable storage
    network_ok = bandwidth_kbps < 100    # Reasonable bandwidth
    
    print(f"\n🎯 FEASIBILITY ASSESSMENT:")
    print(f"   Memory (< 400MB): {'✅ PASS' if memory_ok else '❌ FAIL'} ({total_memory_mb:.1f}MB)")
    print(f"   CPU (< 70%): {'✅ PASS' if cpu_ok else '❌ FAIL'} ({100 * cpu_utilization:.1f}%)")
    print(f"   Storage: {'✅ PASS' if storage_ok else '❌ FAIL'} ({total_storage_mb:.1f}MB)")
    print(f"   Network: {'✅ PASS' if network_ok else '❌ FAIL'} ({bandwidth_kbps:.1f}Kbps)")
    
    overall_feasible = memory_ok and cpu_ok and storage_ok and network_ok
    
    print(f"\n🏆 OVERALL VERDICT: {'✅ FEASIBLE' if overall_feasible else '❌ NOT FEASIBLE'}")
    
    if overall_feasible:
        print(f"\n📊 RECOMMENDED CONFIGURATION:")
        print(f"   spawn_interval_seconds = {spawn_interval:.1f}")
        print(f"   max_concurrent_spawns = {int(concurrent_passengers / routes)}")
        print(f"   memory_limit_mb = {int(total_memory_mb / routes)}")
        print(f"   passenger_timeout_minutes = 30")
        print(f"   cleanup_interval_seconds = 30")
    else:
        print(f"\n⚠️  OPTIMIZATION RECOMMENDATIONS:")
        if not memory_ok:
            print(f"   • Reduce passenger timeout to 20 minutes")
            print(f"   • Reduce max_passengers_per_route to 30")
        if not cpu_ok:
            print(f"   • Increase spawn_interval to {spawn_interval * 1.5:.1f}s")
            print(f"   • Reduce vehicle update frequency to 0.5Hz")

def calculate_config_for_rock_s0():
    """Calculate optimal configuration for Rock S0 constraints."""
    print(f"\n🔧 OPTIMAL ROCK S0 CONFIGURATION")
    print("=" * 50)
    
    # Rock S0 constraints
    max_memory_mb = 400  # Leave 112MB headroom from 512MB
    max_cpu_percent = 70
    
    # Target 150 spawns/hour but optimize for constraints
    target_spawns_hour = 150
    routes = 31
    
    # Calculate based on memory constraint
    base_memory = 50 + (routes * 0.1) + (100 * 0.05)  # Base + routes + vehicles
    available_for_passengers = max_memory_mb - base_memory
    
    passenger_memory_mb = 0.002  # 2KB per passenger
    max_concurrent_passengers = available_for_passengers / passenger_memory_mb
    
    # With 30min timeout, max spawns = concurrent / 30
    max_spawns_per_minute = max_concurrent_passengers / 30
    max_spawns_per_hour = max_spawns_per_minute * 60
    
    print(f"Memory-constrained max spawns/hour: {max_spawns_per_hour:.0f}")
    
    if max_spawns_per_hour >= target_spawns_hour:
        recommended_spawns = target_spawns_hour
        spawn_interval = 3600 / recommended_spawns
        print(f"✅ Target {target_spawns_hour} spawns/hour is achievable!")
    else:
        recommended_spawns = int(max_spawns_per_hour)
        spawn_interval = 3600 / recommended_spawns
        print(f"⚠️  Recommend {recommended_spawns} spawns/hour (memory limited)")
    
    concurrent_passengers = recommended_spawns / 60 * 30
    passengers_per_route = concurrent_passengers / routes
    
    print(f"\n📋 RECOMMENDED CONFIG VALUES:")
    print(f"   spawn_interval_seconds = {spawn_interval:.1f}")
    print(f"   max_concurrent_spawns = {int(passengers_per_route * 3)}")  # 3 routes active
    print(f"   max_passengers_per_route = {int(passengers_per_route)}")
    print(f"   memory_limit_mb = {int(available_for_passengers / routes)}")
    print(f"   passenger_timeout_minutes = 30")
    
    return spawn_interval, int(passengers_per_route * 3), int(passengers_per_route)

if __name__ == "__main__":
    analyze_spawn_requirements()
    spawn_interval, max_spawns, max_per_route = calculate_config_for_rock_s0()