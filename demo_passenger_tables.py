#!/usr/bin/env python3
"""
Simple passenger count demonstration with real data.

Shows passenger counts at depots and along routes using actual route data.
"""
import asyncio
import logging
from datetime import datetime
from tabulate import tabulate

from world.vehicle_simulator.models.depot_passenger_manager import DepotPassengerManager
from world.vehicle_simulator.models.people import PeopleSimulatorConfig
from world.vehicle_simulator.models.people_models.poisson import PoissonDistributionModel


async def demonstrate_passenger_tables():
    """Show passenger count tables with actual passenger generation."""
    
    print("🚌 PASSENGER COUNT DEMONSTRATION")
    print("=" * 50)
    
    # Configure logging to reduce noise
    logging.basicConfig(level=logging.WARNING)
    
    # Set up passenger manager
    config = PeopleSimulatorConfig()
    passenger_manager = DepotPassengerManager(config)
    
    # Create test depots
    depots = [
        {'depot_id': 'central_depot', 'lat': 37.7749, 'lon': -122.4194},
        {'depot_id': 'north_depot', 'lat': 37.7849, 'lon': -122.4094},
        {'depot_id': 'south_depot', 'lat': 37.7649, 'lon': -122.4294}
    ]
    
    await passenger_manager.initialize_depots(depots)
    
    # Load route data from actual API
    import requests
    routes = {}
    try:
        # Get actual route geometry from API
        api_response = requests.get("http://localhost:8000/api/v1/routes/public/1/geometry", timeout=10)
        if api_response.status_code == 200:
            route_data = api_response.json()
            coordinates = route_data['geometry']['coordinates']
            # Convert from [lon, lat] to (lat, lon)
            routes['1'] = [(coord[1], coord[0]) for coord in coordinates]
            print(f"✅ Loaded route 1 with {len(coordinates)} coordinates from API")
        else:
            print(f"⚠️ Could not load route 1 from API: HTTP {api_response.status_code}")
    except Exception as e:
        print(f"⚠️ Error loading route from API: {e}")
        # Fallback to dummy data
        routes = {
            '1': [(13.319443, -59.636900), (13.318181, -59.638242), (13.316750, -59.640525)]
        }
    
    await passenger_manager.load_route_polylines(routes)
    
    # Create distribution model with higher generation rate for demo
    distribution_model = PoissonDistributionModel(
        config=config,
        base_lambda=50.0,  # High rate for quick demo
        peak_multiplier=2.0
    )
    
    # Register some vehicles on actual route
    if '1' in routes and routes['1']:
        route_points = routes['1']
        passenger_manager.register_vehicle('vehicle_1', '1', route_points[0][0], route_points[0][1])
        if len(route_points) > 20:
            passenger_manager.register_vehicle('vehicle_2', '1', route_points[20][0], route_points[20][1])
        if len(route_points) > 40:
            passenger_manager.register_vehicle('vehicle_3', '1', route_points[40][0], route_points[40][1])
    else:
        # Fallback positions
        passenger_manager.register_vehicle('vehicle_1', '1', 13.319443, -59.636900)
        passenger_manager.register_vehicle('vehicle_2', '1', 13.318181, -59.638242)
        passenger_manager.register_vehicle('vehicle_3', '1', 13.316750, -59.640525)
    
    print("⏳ Generating passengers (this may take a moment)...")
    
    # Generate passengers multiple times to build up numbers
    current_time = datetime.now().replace(hour=8, minute=30)  # Peak time
    
    # Use the actual available routes from API
    available_routes = ['1']  # Routes that work with current API mapping
    
    for i in range(5):  # Generate 5 times
        print(f"   Generation cycle {i+1}/5...")
        # Generate passengers for each available route
        for route_id in available_routes:
            try:
                passengers = await distribution_model.generate_passengers([route_id], current_time, 60)
                if passengers:
                    # Add passengers to random depot
                    import random
                    depot_id = random.choice(list(passenger_manager.depot_pools.keys()))
                    depot_pool = passenger_manager.depot_pools[depot_id]
                    for passenger in passengers:
                        depot_pool.add_passenger(passenger)
                    print(f"     Added {len(passengers)} passengers for route {route_id} at {depot_id}")
            except Exception as e:
                print(f"     Error generating for route {route_id}: {e}")
        
        await asyncio.sleep(2)  # Brief pause between generations
    
    # Display depot passenger table
    print("\n📊 DEPOT PASSENGER COUNTS")
    print("=" * 60)
    
    depot_data = []
    total_passengers = 0
    
    for depot_id, depot_pool in passenger_manager.depot_pools.items():
        # Count passengers by route
        route_counts = {}
        for passenger in depot_pool.waiting_passengers:
            route_id = passenger.journey.route_id
            route_counts[route_id] = route_counts.get(route_id, 0) + 1
        
        depot_total = len(depot_pool.waiting_passengers)
        total_passengers += depot_total
        
        route_breakdown = ", ".join([f"{route}: {count}" for route, count in route_counts.items()]) if route_counts else "None"
        
        depot_data.append([
            depot_id,
            f"{depot_pool.depot_lat:.4f}",
            f"{depot_pool.depot_lon:.4f}",
            depot_total,
            depot_pool.max_pool_size,
            f"{(depot_total/depot_pool.max_pool_size)*100:.1f}%",
            route_breakdown
        ])
    
    headers = ["Depot ID", "Latitude", "Longitude", "Waiting", "Capacity", "Usage", "Route Breakdown"]
    print(tabulate(depot_data, headers=headers, tablefmt="grid"))
    print(f"\nTotal Passengers at All Depots: {total_passengers}")
    
    # Display route passenger distribution
    print(f"\n📍 ROUTE PASSENGER DISTRIBUTION")
    print("=" * 60)
    
    route_data = []
    
    # Analyze passenger distribution along route 1
    route1_passengers = []
    pickup_points = []
    destination_points = []
    
    for depot_pool in passenger_manager.depot_pools.values():
        for passenger in depot_pool.waiting_passengers:
            if passenger.journey.route_id == '1':
                route1_passengers.append(passenger)
                pickup_points.append((passenger.journey.pickup_lat, passenger.journey.pickup_lon))
                destination_points.append((passenger.journey.destination_lat, passenger.journey.destination_lon))
    
    # Segment the route into sections and count passengers
    route_points = routes.get('1', [])
    section_size = len(route_points) // 5  # Divide route into 5 sections
    
    for i in range(5):
        start_idx = i * section_size
        end_idx = min((i + 1) * section_size, len(route_points))
        
        section_start = route_points[start_idx]
        section_end = route_points[end_idx - 1] if end_idx > start_idx else section_start
        
        # Count passengers with pickups in this section
        passengers_in_section = 0
        for pickup_lat, pickup_lon in pickup_points:
            # Simple proximity check
            if (section_start[0] <= pickup_lat <= section_end[0] or section_end[0] <= pickup_lat <= section_start[0]):
                passengers_in_section += 1
        
        route_data.append([
            f"Section {i+1}",
            f"{section_start[0]:.4f}, {section_start[1]:.4f}",
            f"{section_end[0]:.4f}, {section_end[1]:.4f}",
            passengers_in_section,
            f"{(passengers_in_section/max(len(pickup_points),1))*100:.1f}%" if pickup_points else "0%"
        ])
    
    headers = ["Route Section", "Start Point", "End Point", "Passengers", "% of Total"]
    print(tabulate(route_data, headers=headers, tablefmt="grid"))
    
    # Display vehicle status
    print(f"\n🚐 VEHICLE STATUS")
    print("=" * 60)
    
    vehicle_data = []
    for vehicle_id, tracker in passenger_manager.vehicle_trackers.items():
        route_points = passenger_manager.route_polylines.get(tracker.route_id, [])
        progress = (tracker.route_segment_index / max(len(route_points), 1)) * 100 if route_points else 0
        
        # Check how many passengers this vehicle could pick up
        potential_passengers = 0
        for depot_pool in passenger_manager.depot_pools.values():
            potential_passengers += len(passenger_manager.get_passengers_for_vehicle(
                vehicle_id, depot_pool.depot_id, max_passengers=10
            ))
        
        vehicle_data.append([
            vehicle_id,
            tracker.route_id,
            f"{tracker.current_lat:.4f}",
            f"{tracker.current_lon:.4f}",
            f"{progress:.1f}%",
            "Forward" if tracker.direction == 1 else "Reverse",
            potential_passengers
        ])
    
    headers = ["Vehicle ID", "Route", "Latitude", "Longitude", "Progress", "Direction", "Available Passengers"]
    print(tabulate(vehicle_data, headers=headers, tablefmt="grid"))
    
    # Performance summary
    stats = passenger_manager.get_performance_stats()
    
    print(f"\n📈 SYSTEM SUMMARY")
    print("=" * 60)
    
    summary_data = [
        ["Total Depots", len(passenger_manager.depot_pools)],
        ["Total Routes", len(passenger_manager.route_polylines)],
        ["Active Vehicles", stats['active_vehicles']],
        ["Total Passengers Generated", stats['passengers_generated']],
        ["Total Waiting at Depots", stats['total_waiting_passengers']],
        ["Passengers Matched to Vehicles", stats['passengers_matched']],
        ["Memory Pool Size", stats['object_pool_size']],
        ["Average Passengers per Depot", f"{stats['avg_passengers_per_depot']:.1f}"]
    ]
    
    print(tabulate(summary_data, headers=["Metric", "Value"], tablefmt="grid"))
    
    print(f"\n✅ Demonstration complete!")
    print(f"💡 The system successfully generated {total_passengers} passengers across {len(depots)} depots")
    print(f"🚐 {len(passenger_manager.vehicle_trackers)} vehicles are ready to pick up passengers")


if __name__ == "__main__":
    asyncio.run(demonstrate_passenger_tables())