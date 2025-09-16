#!/usr/bin/env python3
"""
Query Passenger Distribution Table
=================================

Quick utility to query the running passenger service and display
the current passenger distribution table for testing purposes.
"""

import asyncio
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from tabulate import tabulate

# Add the project to path
sys.path.append('.')
from world.arknet_transit_simulator.core.passenger_service_factory import PassengerServiceFactory
from world.arknet_transit_simulator.core.dispatcher import Dispatcher


async def get_passenger_distribution():
    """Query the passenger service and display distribution table."""
    
    print("🔍 Querying Passenger Distribution...")
    print("=" * 50)
    
    # Initialize dispatcher to connect to Fleet Manager API
    dispatcher = Dispatcher(api_base_url="http://localhost:8000")
    
    try:
        # Initialize connection
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Create passenger service factory
        factory = PassengerServiceFactory(dispatcher)
        
        # Get current service status
        if not factory.passenger_service:
            print("⚠️  No active passenger service found")
            return
        
        # Get service status
        status = await factory.get_service_status()
        print(f"\n📊 Passenger Service Status:")
        print(f"   • Active Routes: {status.get('active_routes', [])}")
        print(f"   • Active Passengers: {status.get('passengers', 0)}")
        print(f"   • Memory Usage: {status.get('memory_usage_mb', 0):.2f} MB")
        print(f"   • Service Running: {status.get('is_running', False)}")
        
        # Get passenger details
        if factory.passenger_service and hasattr(factory.passenger_service, 'active_passengers'):
            passengers = factory.passenger_service.active_passengers
            
            if not passengers:
                print("\n🚶 No active passengers currently in the system")
                return
            
            # Build distribution table
            distribution_data = []
            location_summary = {}
            
            for passenger_id, passenger_data in passengers.items():
                # Extract location info
                lat = passenger_data.get('lat', 'N/A')
                lon = passenger_data.get('lon', 'N/A')
                route_id = passenger_data.get('route_id', 'N/A')
                spawn_time = passenger_data.get('spawn_time', 'N/A')
                status = passenger_data.get('status', 'waiting')
                
                # Add to table data
                distribution_data.append([
                    passenger_id[:8] + "...",  # Truncate ID for readability
                    route_id,
                    f"{lat:.6f}" if isinstance(lat, (int, float)) else str(lat),
                    f"{lon:.6f}" if isinstance(lon, (int, float)) else str(lon),
                    status,
                    spawn_time
                ])
                
                # Build location summary
                location_key = f"Route {route_id}"
                if location_key not in location_summary:
                    location_summary[location_key] = 0
                location_summary[location_key] += 1
            
            # Display passenger distribution table
            print(f"\n📍 Passenger Distribution Table ({len(passengers)} passengers):")
            headers = ["Passenger ID", "Route", "Latitude", "Longitude", "Status", "Spawn Time"]
            print(tabulate(distribution_data, headers=headers, tablefmt="grid"))
            
            # Display location summary
            print(f"\n🗺️  Location Summary:")
            summary_data = [[location, count] for location, count in location_summary.items()]
            print(tabulate(summary_data, headers=["Location", "Passenger Count"], tablefmt="simple"))
            
        else:
            print("⚠️  Unable to access passenger data structure")
            
    except Exception as e:
        print(f"❌ Error querying passenger distribution: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if dispatcher.session:
            await dispatcher.session.close()


if __name__ == "__main__":
    asyncio.run(get_passenger_distribution())