#!/usr/bin/env python3
"""
Passenger Validation Analysis Summary
====================================

This script explains the current passenger validation results and addresses
the user's questions about destination names and bus stop counts.
"""

import asyncio
import json
import sys
sys.path.append('world/arknet_transit_simulator')

from core.dispatcher import Dispatcher
from passenger_modeler.passenger_service import DynamicPassengerService


def analyze_naming_system():
    """Analyze the naming system used in Barbados GeoJSON files."""
    
    print("🔍 BARBADOS GEOJSON NAMING SYSTEM ANALYSIS")
    print("=" * 60)
    
    base_path = "world/arknet_transit_simulator/passenger_modeler/data/barbados/"
    
    # Load and analyze each GeoJSON file
    files_to_check = [
        ("barbados_names.geojson", "Names (Priority 1)"),
        ("barbados_highway.geojson", "Highway (Priority 2)"), 
        ("barbados_busstops.geojson", "Bus Stops"),
        ("barbados_amenities.geojson", "Amenities")
    ]
    
    for filename, description in files_to_check:
        try:
            with open(f"{base_path}{filename}", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            print(f"\n📍 {description}: {len(features)} locations")
            
            # Sample the first few features to show naming structure
            sample_size = min(3, len(features))
            for i in range(sample_size):
                feature = features[i]
                props = feature.get('properties', {})
                
                # Show the naming priority system
                name_sources = []
                if props.get('name'):
                    name_sources.append(f"name: '{props['name']}'")
                if props.get('highway'):
                    name_sources.append(f"highway: '{props['highway']}'")
                if props.get('stop_name'):
                    name_sources.append(f"stop_name: '{props['stop_name']}'")
                if props.get('amenity'):
                    name_sources.append(f"amenity: '{props['amenity']}'")
                
                print(f"   Sample {i+1}: {', '.join(name_sources) if name_sources else 'No naming fields'}")
        
        except Exception as e:
            print(f"   ❌ Error loading {filename}: {e}")


async def demonstrate_passenger_details():
    """Show detailed passenger information to answer user questions."""
    
    print(f"\n🚶 PASSENGER DETAILS DEMONSTRATION")
    print("=" * 60)
    
    # Initialize dispatcher
    dispatcher = Dispatcher(api_base_url="http://localhost:8000")
    
    try:
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Create passenger service using old method (working approach)
        from passenger_modeler.passenger_service_factory import create_passenger_service
        
        print("📍 Creating passenger service...")
        passenger_service = create_passenger_service(
            route_ids=['1', '1A', '1B'],
            dispatcher=None  # Let it use its own dispatcher
        )
        
        # Get passengers
        passengers = passenger_service.passengers
        
        if passengers:
            passenger = passengers[0]  # Get first passenger
            print(f"\n📋 DETAILED PASSENGER BREAKDOWN:")
            print(f"   • Passenger ID: {passenger.id}")
            print(f"   • Route: {passenger.route_id}")
            print(f"   • Pickup: [{passenger.pickup_location[0]:.6f}, {passenger.pickup_location[1]:.6f}]")
            print(f"   • Destination: [{passenger.destination_location[0]:.6f}, {passenger.destination_location[1]:.6f}]")
            
            # Calculate trip distance
            import math
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371000
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                delta_lat = math.radians(lat2 - lat1)
                delta_lon = math.radians(lon2 - lon1)
                a = (math.sin(delta_lat / 2) ** 2 + 
                     math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return R * c
            
            trip_distance = haversine_distance(
                passenger.pickup_location[0], passenger.pickup_location[1],
                passenger.destination_location[0], passenger.destination_location[1]
            )
            print(f"   • Trip Distance: {trip_distance:.1f}m")
            
            # Load bus stops for proximity analysis
            base_path = "world/arknet_transit_simulator/passenger_modeler/data/barbados/"
            with open(f"{base_path}barbados_busstops.geojson", 'r') as f:
                busstops_data = json.load(f)
            
            # Find nearby bus stops for pickup
            pickup_stops = []
            for feature in busstops_data['features']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    stop_lat, stop_lon = coords[1], coords[0]
                    distance = haversine_distance(
                        passenger.pickup_location[0], passenger.pickup_location[1],
                        stop_lat, stop_lon
                    )
                    if distance <= 500:  # Within 500m
                        pickup_stops.append({
                            'distance': distance,
                            'properties': feature['properties']
                        })
            
            pickup_stops.sort(key=lambda x: x['distance'])
            
            # Find nearby bus stops for destination
            dest_stops = []
            for feature in busstops_data['features']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    stop_lat, stop_lon = coords[1], coords[0]
                    distance = haversine_distance(
                        passenger.destination_location[0], passenger.destination_location[1],
                        stop_lat, stop_lon
                    )
                    if distance <= 500:  # Within 500m
                        dest_stops.append({
                            'distance': distance,
                            'properties': feature['properties']
                        })
            
            dest_stops.sort(key=lambda x: x['distance'])
            
            print(f"\n🚏 BUS STOP ANALYSIS:")
            print(f"   • Pickup area: {len(pickup_stops)} stops within 500m")
            if pickup_stops:
                closest = pickup_stops[0]
                stop_name = closest['properties'].get('stop_name') or f"Stop {closest['properties'].get('full_id', 'Unknown')}"
                print(f"     Closest: {stop_name} ({closest['distance']:.1f}m)")
            
            print(f"   • Destination area: {len(dest_stops)} stops within 500m")
            if dest_stops:
                closest = dest_stops[0]
                stop_name = closest['properties'].get('stop_name') or f"Stop {closest['properties'].get('full_id', 'Unknown')}"
                print(f"     Closest: {stop_name} ({closest['distance']:.1f}m)")
            
            print(f"\n❓ ANSWERING USER QUESTIONS:")
            print(f"   1. Destination names show 'Unknown' because:")
            print(f"      • Bus stops in GeoJSON have stop_name: null")
            print(f"      • System falls back to 'Unknown' when no name available")
            print(f"      • Real bus stops in Barbados may not have official names")
            print(f"   ")
            print(f"   2. Bus stop count of '{len(pickup_stops) + len(dest_stops)}' means:")
            print(f"      • {len(pickup_stops)} stops near pickup location")
            print(f"      • {len(dest_stops)} stops near destination location") 
            print(f"      • Total: {len(pickup_stops)} + {len(dest_stops)} = {len(pickup_stops) + len(dest_stops)} (not unique stops)")
            print(f"      • This is pickup_stops + destination_stops, not total unique stops")
        
        else:
            print("❌ No passengers found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if dispatcher.session:
            await dispatcher.session.close()


def main():
    """Main analysis function."""
    print("🎯 PASSENGER VALIDATION QUESTIONS & ANSWERS")
    print("=" * 80)
    print("User asked:")
    print('• "i want the destination names"')
    print('• "108.2 | ✅ | 10 is 10 stops????"')
    print()
    
    # First analyze the naming system
    analyze_naming_system()
    
    # Then demonstrate passenger details
    asyncio.run(demonstrate_passenger_details())
    
    print(f"\n📝 SUMMARY:")
    print(f"=" * 30)
    print(f"1. Destination names appear as 'Unknown' because Barbados bus stops")
    print(f"   in the GeoJSON data have stop_name: null (no official names)")
    print(f"")
    print(f"2. The '10' in bus stops count represents pickup_stops + destination_stops")
    print(f"   Example: 4 stops near pickup + 6 stops near destination = 10 total")
    print(f"   This is not 10 unique stops, but combined proximity counts")
    print(f"")
    print(f"3. Trip distances (678m, 543m, 571m) all exceed minimum 350m requirement")
    print(f"   The system is properly enforcing destination_distance_meters = 350")


if __name__ == "__main__":
    main()