"""
Visual dashboard for depot-centric passenger system monitoring.

Provides real-time table displays of:
- Passenger counts at each depot
- Passenger distribution along routes
- Vehicle positions and passenger loads
- System performance metrics
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from tabulate import tabulate
import os

from world.arknet_transit_simulator.models.depot_passenger_coordinator import setup_depot_passenger_system


class PassengerDashboard:
    """Real-time dashboard for monitoring passenger distribution."""
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def clear_screen(self):
        """Clear terminal screen for updated display."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_depot_passenger_table(self) -> str:
        """Generate table showing passenger counts at each depot."""
        passenger_manager = self.coordinator.passenger_manager
        
        depot_data = []
        total_passengers = 0
        
        for depot_id, depot_pool in passenger_manager.depot_pools.items():
            # Count passengers by route at this depot
            route_counts = {}
            for passenger in depot_pool.waiting_passengers:
                route_id = passenger.journey.route_id
                route_counts[route_id] = route_counts.get(route_id, 0) + 1
            
            depot_total = len(depot_pool.waiting_passengers)
            total_passengers += depot_total
            
            # Build route breakdown string
            route_breakdown = ", ".join([f"{route}: {count}" for route, count in route_counts.items()]) if route_counts else "None"
            
            depot_data.append([
                depot_id,
                f"{depot_pool.depot_lat:.4f}",
                f"{depot_pool.depot_lon:.4f}",
                depot_total,
                f"{depot_pool.max_pool_size}",
                f"{(depot_total/depot_pool.max_pool_size)*100:.1f}%",
                route_breakdown
            ])
        
        headers = ["Depot ID", "Latitude", "Longitude", "Waiting", "Capacity", "Usage", "Routes"]
        table = tabulate(depot_data, headers=headers, tablefmt="grid")
        
        return f"""
DEPOT PASSENGER COUNTS
{'='*80}
{table}

Total Passengers at Depots: {total_passengers}
"""
    
    def get_route_passenger_table(self) -> str:
        """Generate table showing passenger distribution along routes."""
        passenger_manager = self.coordinator.passenger_manager
        
        # Collect passenger data by route
        route_passenger_data = {}
        
        for depot_pool in passenger_manager.depot_pools.values():
            for passenger in depot_pool.waiting_passengers:
                route_id = passenger.journey.route_id
                
                if route_id not in route_passenger_data:
                    route_passenger_data[route_id] = {
                        'waiting_at_depots': 0,
                        'pickup_locations': [],
                        'destination_locations': []
                    }
                
                route_passenger_data[route_id]['waiting_at_depots'] += 1
                route_passenger_data[route_id]['pickup_locations'].append(
                    (passenger.journey.pickup_lat, passenger.journey.pickup_lon)
                )
                route_passenger_data[route_id]['destination_locations'].append(
                    (passenger.journey.destination_lat, passenger.journey.destination_lon)
                )
        
        route_data = []
        total_route_passengers = 0
        
        for route_id, data in route_passenger_data.items():
            waiting_passengers = data['waiting_at_depots']
            total_route_passengers += waiting_passengers
            
            # Calculate route coverage (simplified)
            unique_pickups = len(set(data['pickup_locations']))
            unique_destinations = len(set(data['destination_locations']))
            
            route_length = len(passenger_manager.route_polylines.get(route_id, []))
            coverage_percent = (unique_pickups / max(route_length, 1)) * 100 if route_length > 0 else 0
            
            route_data.append([
                route_id,
                waiting_passengers,
                unique_pickups,
                unique_destinations,
                route_length,
                f"{coverage_percent:.1f}%"
            ])
        
        headers = ["Route ID", "Waiting", "Pickup Points", "Destinations", "Route Length", "Coverage"]
        table = tabulate(route_data, headers=headers, tablefmt="grid")
        
        return f"""
ROUTE PASSENGER DISTRIBUTION
{'='*80}
{table}

Total Passengers on Routes: {total_route_passengers}
"""
    
    def get_vehicle_status_table(self) -> str:
        """Generate table showing vehicle positions and passenger status."""
        passenger_manager = self.coordinator.passenger_manager
        integration_service = self.coordinator.integration_service
        
        vehicle_data = []
        
        for vehicle_id, tracker in passenger_manager.vehicle_trackers.items():
            # Check if vehicle is at depot
            at_depot = None
            if integration_service:
                at_depot = integration_service.vehicles_at_depots.get(vehicle_id)
            
            # Get route progress
            route_points = passenger_manager.route_polylines.get(tracker.route_id, [])
            progress_percent = (tracker.route_segment_index / max(len(route_points), 1)) * 100 if route_points else 0
            
            direction_str = "Forward" if tracker.direction == 1 else "Reverse"
            depot_status = at_depot if at_depot else "In Transit"
            
            vehicle_data.append([
                vehicle_id,
                tracker.route_id,
                f"{tracker.current_lat:.4f}",
                f"{tracker.current_lon:.4f}",
                f"{progress_percent:.1f}%",
                direction_str,
                depot_status,
                tracker.last_update.strftime("%H:%M:%S")
            ])
        
        headers = ["Vehicle ID", "Route", "Latitude", "Longitude", "Progress", "Direction", "Status", "Last Update"]
        table = tabulate(vehicle_data, headers=headers, tablefmt="grid")
        
        return f"""
VEHICLE STATUS
{'='*80}
{table}

Active Vehicles: {len(vehicle_data)}
"""
    
    def get_system_performance_table(self) -> str:
        """Generate table showing system performance metrics."""
        stats = self.coordinator.get_system_stats()
        passenger_stats = stats['passenger_stats']
        integration_stats = stats['integration_stats']
        
        performance_data = [
            ["System Uptime", f"{stats['uptime_seconds']:.1f} seconds"],
            ["Active Vehicles", passenger_stats['active_vehicles']],
            ["Depot Pools", passenger_stats['depot_pools']],
            ["Total Waiting Passengers", passenger_stats['total_waiting_passengers']],
            ["Passengers Generated", passenger_stats['passengers_generated']],
            ["Passengers Matched", passenger_stats['passengers_matched']],
            ["Passengers Boarded", passenger_stats['passengers_boarded']],
            ["Telemetry Packets Processed", integration_stats['telemetry_packets_processed']],
            ["Position Updates", integration_stats['position_updates_processed']],
            ["Boarding Events", integration_stats['boarding_events']],
            ["Performance Warnings", integration_stats['performance_warnings']],
            ["Vehicles at Depots", integration_stats['vehicles_at_depots']],
            ["Object Pool Size", passenger_stats['object_pool_size']],
            ["Generation Interval", f"{stats['config']['generation_interval']}s"],
            ["Max Passengers/Depot", stats['config']['max_passengers_per_depot']]
        ]
        
        table = tabulate(performance_data, headers=["Metric", "Value"], tablefmt="grid")
        
        return f"""
SYSTEM PERFORMANCE
{'='*80}
{table}
"""
    
    def display_full_dashboard(self):
        """Display complete dashboard with all tables."""
        self.clear_screen()
        
        print("🚌 DEPOT-CENTRIC PASSENGER SYSTEM DASHBOARD")
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Display all tables
        print(self.get_depot_passenger_table())
        print(self.get_route_passenger_table())
        print(self.get_vehicle_status_table())
        print(self.get_system_performance_table())
        
        print("💡 Press Ctrl+C to stop monitoring")


async def run_passenger_monitoring_demo():
    """
    Run a live demonstration of the passenger monitoring dashboard.
    """
    print("🚀 Starting Depot Passenger System with Live Monitoring")
    print("=" * 60)
    
    # Set up system with sample data
    depots = [
        {
            'depot_id': 'central_depot',
            'lat': 37.7749,
            'lon': -122.4194,
            'boarding_radius': 0.001
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
    
    routes = {
        'route_1': [
            (37.7749, -122.4194), (37.7759, -122.4184), (37.7769, -122.4174),
            (37.7779, -122.4164), (37.7789, -122.4154), (37.7799, -122.4144),
            (37.7809, -122.4134), (37.7819, -122.4124), (37.7829, -122.4114),
            (37.7839, -122.4104), (37.7849, -122.4094)
        ],
        'route_2': [
            (37.7749, -122.4194), (37.7739, -122.4204), (37.7729, -122.4214),
            (37.7719, -122.4224), (37.7709, -122.4234), (37.7699, -122.4244),
            (37.7689, -122.4254), (37.7679, -122.4264), (37.7669, -122.4274),
            (37.7659, -122.4284), (37.7649, -122.4294)
        ],
        'route_3': [
            (37.7749, -122.4194), (37.7759, -122.4204), (37.7769, -122.4214),
            (37.7779, -122.4224), (37.7789, -122.4234), (37.7799, -122.4244)
        ]
    }
    
    # Initialize system
    coordinator = await setup_depot_passenger_system(
        depots=depots,
        routes=routes,
        performance_mode='standard'
    )
    
    # Register sample vehicles
    print("📝 Registering sample vehicles...")
    vehicle_routes = [
        ('vehicle_n1', 'route_1', 37.7749, -122.4194),
        ('vehicle_n2', 'route_1', 37.7779, -122.4164),
        ('vehicle_n3', 'route_1', 37.7809, -122.4134),
        ('vehicle_s1', 'route_2', 37.7749, -122.4194),
        ('vehicle_s2', 'route_2', 37.7719, -122.4224),
        ('vehicle_s3', 'route_2', 37.7689, -122.4254),
        ('vehicle_c1', 'route_3', 37.7749, -122.4194),
        ('vehicle_c2', 'route_3', 37.7769, -122.4214)
    ]
    
    for vehicle_id, route_id, lat, lon in vehicle_routes:
        coordinator.register_vehicle(vehicle_id, route_id, lat, lon)
    
    # Create dashboard
    dashboard = PassengerDashboard(coordinator)
    
    try:
        print("⏳ Waiting 30 seconds for passenger generation...")
        await asyncio.sleep(30)  # Wait for some passengers to generate
        
        # Display dashboard updates every 10 seconds
        print("📊 Starting live dashboard (updates every 10 seconds)...")
        
        for update_cycle in range(18):  # Run for 3 minutes (18 * 10 seconds)
            dashboard.display_full_dashboard()
            
            if update_cycle < 17:  # Don't sleep after last update
                await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")
    
    finally:
        await coordinator.stop()
        print("✅ System shutdown complete")


async def show_static_passenger_tables():
    """
    Show a static snapshot of passenger tables for quick viewing.
    """
    print("📊 STATIC PASSENGER COUNT TABLES")
    print("=" * 50)
    
    # Quick setup
    depots = [
        {'depot_id': 'depot_A', 'lat': 37.7749, 'lon': -122.4194},
        {'depot_id': 'depot_B', 'lat': 37.7849, 'lon': -122.4094},
        {'depot_id': 'depot_C', 'lat': 37.7649, 'lon': -122.4294}
    ]
    
    routes = {
        'route_1': [(37.77 + i*0.001, -122.42 + i*0.001) for i in range(20)],
        'route_2': [(37.76 + i*0.001, -122.43 + i*0.001) for i in range(15)],
        'route_3': [(37.78 + i*0.001, -122.41 + i*0.001) for i in range(10)]
    }
    
    coordinator = await setup_depot_passenger_system(depots, routes, 'standard')
    
    # Register a few vehicles
    coordinator.register_vehicle('v1', 'route_1', 37.7749, -122.4194)
    coordinator.register_vehicle('v2', 'route_2', 37.7649, -122.4294)
    coordinator.register_vehicle('v3', 'route_3', 37.7849, -122.4094)
    
    # Wait for passenger generation  
    print("⏳ Generating passengers...")
    await asyncio.sleep(50)  # Wait for passenger generation
    
    # Show tables
    dashboard = PassengerDashboard(coordinator)
    
    print(dashboard.get_depot_passenger_table())
    print(dashboard.get_route_passenger_table())
    print(dashboard.get_vehicle_status_table())
    print(dashboard.get_system_performance_table())
    
    await coordinator.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--static":
        # Show static tables
        asyncio.run(show_static_passenger_tables())
    else:
        # Run live monitoring demo
        asyncio.run(run_passenger_monitoring_demo())