"""
Example usage of the high-performance depot-centric passenger system.

This example demonstrates how to set up and use the optimized passenger generation
system for large-scale vehicle simulations (1200+ vehicles).
"""
import asyncio
import logging
from datetime import datetime

from world.vehicle_simulator.models.depot_passenger_coordinator import setup_depot_passenger_system


async def example_depot_passenger_simulation():
    """
    Example of setting up depot-centric passenger simulation for multiple depots and routes.
    """
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚌 Setting up Depot-Centric Passenger System Example")
    print("=" * 60)
    
    # Step 1: Define depot locations (where passengers wait for vehicles)
    depots = [
        {
            'depot_id': 'central_depot',
            'lat': 37.7749,  # San Francisco coordinates
            'lon': -122.4194,
            'boarding_radius': 0.001  # ~100m radius for boarding detection
        },
        {
            'depot_id': 'north_depot', 
            'lat': 37.7849,
            'lon': -122.4094,
            'boarding_radius': 0.001
        },
        {
            'depot_id': 'south_depot',
            'lat': 37.7649, 
            'lon': -122.4294,
            'boarding_radius': 0.001
        }
    ]
    
    # Step 2: Define route polylines (actual paths vehicles follow)
    routes = {
        'route_1': [
            (37.7749, -122.4194),  # Start at central depot
            (37.7759, -122.4184),
            (37.7769, -122.4174),
            (37.7779, -122.4164),
            (37.7789, -122.4154),  # Continue north
            (37.7799, -122.4144),
            (37.7809, -122.4134),
            (37.7819, -122.4124),
            (37.7829, -122.4114),
            (37.7839, -122.4104),
            (37.7849, -122.4094)   # End at north depot
        ],
        'route_2': [
            (37.7749, -122.4194),  # Start at central depot
            (37.7739, -122.4204),
            (37.7729, -122.4214),
            (37.7719, -122.4224),
            (37.7709, -122.4234),  # Continue south
            (37.7699, -122.4244),
            (37.7689, -122.4254),
            (37.7679, -122.4264),
            (37.7669, -122.4274),
            (37.7659, -122.4284),
            (37.7649, -122.4294)   # End at south depot
        ]
    }
    
    # Step 3: Set up the passenger system
    # Choose performance mode based on your hardware:
    # - 'ultra_low_resource': For constrained hardware (< 4GB RAM)
    # - 'standard': For typical hardware (4-8GB RAM) 
    # - 'high_performance': For powerful hardware (8+ GB RAM)
    
    print("⚙️  Initializing system with standard performance mode...")
    coordinator = await setup_depot_passenger_system(
        depots=depots,
        routes=routes, 
        performance_mode='standard'
    )
    
    # Step 4: Register vehicles for tracking
    print("🚐 Registering vehicles...")
    
    # Register vehicles on route_1 (going north)
    for i in range(10):
        vehicle_id = f"vehicle_north_{i}"
        # Start vehicles at different points along route_1
        start_point = routes['route_1'][i % len(routes['route_1'])]
        coordinator.register_vehicle(vehicle_id, 'route_1', start_point[0], start_point[1])
    
    # Register vehicles on route_2 (going south)  
    for i in range(10):
        vehicle_id = f"vehicle_south_{i}"
        # Start vehicles at different points along route_2
        start_point = routes['route_2'][i % len(routes['route_2'])]
        coordinator.register_vehicle(vehicle_id, 'route_2', start_point[0], start_point[1])
    
    print(f"✅ Registered 20 vehicles on 2 routes")
    
    # Step 5: Run simulation and monitor performance
    print("🔄 Running passenger simulation...")
    print("   - Passengers generate at depots every ~45 seconds")
    print("   - Vehicles track along routes and pick up matching passengers")
    print("   - System optimized for minimal CPU and memory usage")
    print()
    
    # Run for 3 minutes, showing stats every 30 seconds
    for minute in range(3):
        for interval in range(2):  # 2 intervals of 30 seconds each
            await asyncio.sleep(30)
            
            stats = coordinator.get_system_stats()
            passenger_stats = stats['passenger_stats']
            integration_stats = stats['integration_stats']
            
            print(f"📊 T+{(minute*2 + interval + 1)*30}s Stats:")
            print(f"   Passengers Generated: {passenger_stats['passengers_generated']}")
            print(f"   Passengers Waiting: {passenger_stats['total_waiting_passengers']}")
            print(f"   Passengers Matched: {passenger_stats['passengers_matched']}")
            print(f"   Telemetry Packets: {integration_stats['telemetry_packets_processed']}")
            print(f"   Vehicles at Depots: {integration_stats['vehicles_at_depots']}")
            print()
    
    # Step 6: Get final performance summary
    final_stats = coordinator.get_system_stats()
    print("📈 Final Performance Summary:")
    print(f"   Total Runtime: {final_stats['uptime_seconds']:.1f} seconds")
    print(f"   Active Vehicles: {final_stats['passenger_stats']['active_vehicles']}")
    print(f"   Total Passengers Generated: {final_stats['passenger_stats']['passengers_generated']}")
    print(f"   Memory Efficiency: {final_stats['passenger_stats']['object_pool_size']} objects pooled")
    print()
    
    # Step 7: Clean shutdown
    print("🛑 Shutting down system...")
    await coordinator.stop()
    
    print("✅ Example completed successfully!")
    print()
    print("💡 Key Features Demonstrated:")
    print("   ✓ Depot-centric passenger generation")
    print("   ✓ Vehicle position tracking along routes")
    print("   ✓ Directional passenger matching")
    print("   ✓ Efficient memory and CPU usage")
    print("   ✓ Real-time performance monitoring")
    print("   ✓ Scalable architecture for 1200+ vehicles")


async def example_high_load_simulation():
    """
    Example of high-load simulation with many vehicles.
    """
    print("\n🚀 High-Load Simulation Example (100 vehicles)")
    print("=" * 50)
    
    # Simplified setup for high load
    depots = [
        {'depot_id': f'depot_{i}', 'lat': 37.77 + (i * 0.01), 'lon': -122.42 + (i * 0.01)}
        for i in range(5)  # 5 depots
    ]
    
    routes = {
        f'route_{i}': [
            (37.77 + (i * 0.005) + (j * 0.001), -122.42 + (i * 0.005) + (j * 0.001))
            for j in range(20)  # 20 points per route
        ]
        for i in range(3)  # 3 routes
    }
    
    # Use high-performance mode for better handling of load
    coordinator = await setup_depot_passenger_system(
        depots=depots,
        routes=routes,
        performance_mode='high_performance'
    )
    
    # Register 100 vehicles
    print("📝 Registering 100 vehicles...")
    for i in range(100):
        route_id = f'route_{i % 3}'
        lat = 37.77 + ((i % 20) * 0.001)
        lon = -122.42 + ((i % 20) * 0.001)
        coordinator.register_vehicle(f'vehicle_{i}', route_id, lat, lon)
    
    # Run for 2 minutes
    print("⏱️  Running 2-minute high-load test...")
    await asyncio.sleep(120)
    
    stats = coordinator.get_system_stats()
    print(f"📊 High-Load Results:")
    print(f"   Vehicles: {stats['passenger_stats']['active_vehicles']}")
    print(f"   Passengers: {stats['passenger_stats']['total_waiting_passengers']}")
    print(f"   Performance: {stats['integration_stats']['performance_warnings']} warnings")
    
    await coordinator.stop()
    print("✅ High-load test completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(example_depot_passenger_simulation())
    asyncio.run(example_high_load_simulation())