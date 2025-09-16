#!/usr/bin/env python3
"""
Display Passenger Distribution During Service Run
================================================

This script starts a passenger service and immediately queries its distribution.
"""

import asyncio
import json
from datetime import datetime
from tabulate import tabulate

from world.arknet_transit_simulator.core.dispatcher import Dispatcher
from world.arknet_transit_simulator.core.passenger_service_factory import PassengerServiceFactory


async def demo_passenger_distribution():
    """Start passenger service and show distribution."""
    
    print("🚀 Starting Passenger Distribution Demo")
    print("=" * 50)
    
    # Initialize dispatcher
    dispatcher = Dispatcher(api_base_url="http://localhost:8000")
    
    try:
        # Connect to Fleet Manager API
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Create passenger service factory
        factory = PassengerServiceFactory()
        factory.set_dispatcher(dispatcher)
        
        # Get route IDs from current vehicle assignments
        vehicle_assignments = await dispatcher.get_vehicle_assignments()
        if not vehicle_assignments:
            print("⚠️  No vehicle assignments found")
            return
        
        route_ids = list(set(v.route_id for v in vehicle_assignments if v.route_id))
        print(f"📍 Found routes: {route_ids}")
        
        # Create passenger service
        print("🚶 Creating passenger service...")
        success = await factory.create_passenger_service(route_ids)
        
        if not success:
            print("❌ Failed to create passenger service")
            return
        
        print("✅ Passenger service created successfully!")
        
        # Let it run for a few seconds to generate passengers
        print("⏱️  Waiting for passengers to spawn (5 seconds)...")
        await asyncio.sleep(5)
        
        # Get service status
        status = await factory.get_service_status()
        print(f"\n📊 Service Status:")
        print(f"   • Routes: {status.get('active_routes', [])}")
        print(f"   • Active Passengers: {status.get('passengers', 0)}")
        print(f"   • Total Spawned: {status.get('stats', {}).get('total_spawned', 0)}")
        print(f"   • Memory Usage: {status.get('memory_usage_mb', 0):.2f} MB")
        
        # Display passenger distribution
        if factory.passenger_service and hasattr(factory.passenger_service, 'active_passengers'):
            passengers = factory.passenger_service.active_passengers
            
            print(f"\n🚶 Active Passengers: {len(passengers)}")
            
            if passengers:
                # Build distribution table
                distribution_data = []
                route_summary = {}
                
                for passenger_id, passenger_data in passengers.items():
                    route_id = passenger_data.get('route_id', 'Unknown')
                    
                    # Get coordinates from the actual data structure
                    pickup_coords = passenger_data.get('pickup_coords', [])
                    dest_coords = passenger_data.get('destination_coords', [])
                    
                    # Extract origin coordinates
                    if pickup_coords and len(pickup_coords) >= 2:
                        origin_lon, origin_lat = pickup_coords[0], pickup_coords[1]
                        origin_str = f"{origin_lat:.6f}, {origin_lon:.6f}"
                    else:
                        origin_str = "No coordinates"
                    
                    # Extract destination coordinates  
                    if dest_coords and len(dest_coords) >= 2:
                        dest_lon, dest_lat = dest_coords[0], dest_coords[1]
                        dest_str = f"{dest_lat:.6f}, {dest_lon:.6f}"
                    else:
                        dest_str = "No coordinates"
                    
                    status = passenger_data.get('status', 'waiting')
                    spawn_time = passenger_data.get('spawn_time', 'N/A')
                    
                    distribution_data.append([
                        passenger_id[:12] + "...",
                        route_id,
                        origin_str,
                        dest_str,
                        status,
                        str(spawn_time)[:19] if spawn_time != 'N/A' else 'N/A'
                    ])
                    
                    # Count by route
                    if route_id not in route_summary:
                        route_summary[route_id] = 0
                    route_summary[route_id] += 1
                
                # Display passenger table
                print(f"\n📍 Passenger Distribution Table:")
                headers = ["Passenger ID", "Route", "Origin (Lat, Lon)", "Destination (Lat, Lon)", "Status", "Spawn Time"]
                print(tabulate(distribution_data, headers=headers, tablefmt="grid", maxcolwidths=[10, 8, 20, 20, 10, 19]))
                
                # Display summary by route
                print(f"\n🗺️  Distribution Summary:")
                summary_data = [[f"Route {route}", count] for route, count in route_summary.items()]
                print(tabulate(summary_data, headers=["Route", "Passengers"], tablefmt="simple"))
                
                # Show detailed coordinate analysis
                print(f"\n🎯 Detailed Coordinate Analysis:")
                for i, (passenger_id, passenger_data) in enumerate(passengers.items()):
                    print(f"\n--- Passenger {i+1}: {passenger_id} ---")
                    route_id = passenger_data.get('route_id', 'Unknown')
                    pickup_coords = passenger_data.get('pickup_coords', [])
                    dest_coords = passenger_data.get('destination_coords', [])
                    
                    print(f"  Route: {route_id}")
                    print(f"  Route Name: {passenger_data.get('route_name', 'N/A')}")
                    
                    if pickup_coords and len(pickup_coords) >= 2:
                        print(f"  🚶 ORIGIN: [{pickup_coords[0]:.6f}, {pickup_coords[1]:.6f}]")
                        print(f"    (Longitude: {pickup_coords[0]:.6f}, Latitude: {pickup_coords[1]:.6f})")
                    else:
                        print(f"  🚶 ORIGIN: NO COORDINATES FOUND")
                    
                    if dest_coords and len(dest_coords) >= 2:
                        print(f"  🎯 DESTINATION: [{dest_coords[0]:.6f}, {dest_coords[1]:.6f}]") 
                        print(f"    (Longitude: {dest_coords[0]:.6f}, Latitude: {dest_coords[1]:.6f})")
                    else:
                        print(f"  🎯 DESTINATION: NO COORDINATES FOUND")
                    
                    print(f"  Status: {passenger_data.get('status', 'N/A')}")
                    print(f"  Using Route Geometry: {passenger_data.get('using_route_geometry', 'N/A')}")
                    print(f"  Spawn Time: {passenger_data.get('spawn_time', 'N/A')}")
                
                # Show raw data structure for verification
                if passengers:
                    sample_id, sample_data = next(iter(passengers.items()))
                    print(f"\n🔍 Raw Data Structure (First Passenger):")
                    print(f"Passenger ID: {sample_id}")
                    for key, value in sample_data.items():
                        print(f"  {key}: {value}")
            
            else:
                print("   No passengers currently active (they may spawn shortly)")
        
        # Let service run a bit longer to see more passengers
        print(f"\n⏱️  Continuing service for 5 more seconds...")
        await asyncio.sleep(5)
        
        # Final status check
        final_status = await factory.get_service_status() 
        print(f"\n📈 Final Status:")
        print(f"   • Total Spawned: {final_status.get('stats', {}).get('total_spawned', 0)}")
        print(f"   • Active Now: {final_status.get('passengers', 0)}")
        
    except Exception as e:
        print(f"❌ Error in passenger distribution demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if dispatcher.session:
            await dispatcher.session.close()


if __name__ == "__main__":
    asyncio.run(demo_passenger_distribution())