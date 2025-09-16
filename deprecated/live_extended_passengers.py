#!/usr/bin/env python3
"""
Live Extended Passenger Display
===============================

Runs the passenger service for an extended time to show more passengers
as they spawn, with enhanced destination names.
"""

import asyncio
import json
import math
import time
from typing import Dict, List, Any, Optional
from tabulate import tabulate
import sys
import os

# Add the project to path
sys.path.append('world')
sys.path.append('world/fleet_manager') 
sys.path.append('world/arknet_transit_simulator')


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in meters."""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the bearing from point 1 to point 2 in degrees."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
    
    bearing = math.atan2(y, x)
    bearing_degrees = math.degrees(bearing)
    
    # Normalize to 0-360 degrees
    return (bearing_degrees + 360) % 360


def bearing_to_compass(bearing: float) -> str:
    """Convert bearing in degrees to compass direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    
    # Each direction covers 22.5 degrees (360/16)
    index = int((bearing + 11.25) / 22.5) % 16
    return directions[index]


def load_geojson_data(filepath: str) -> Dict[str, Any]:
    """Load GeoJSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return {}


def extract_name_from_properties(properties: Dict) -> Optional[str]:
    """Extract name using priority system: names > highway > stop_name."""
    # Priority 1: names field
    if properties.get('names'):
        return properties['names']
    
    # Priority 2: highway field  
    if properties.get('highway'):
        return properties['highway']
        
    # Priority 3: stop_name field
    if properties.get('stop_name'):
        return properties['stop_name']
        
    return None


def find_all_named_entities(geojson_files: List[str]) -> List[Dict]:
    """Load all named entities from multiple GeoJSON files."""
    named_entities = []
    
    for filepath in geojson_files:
        data = load_geojson_data(filepath)
        if not data or 'features' not in data:
            continue
            
        for feature in data['features']:
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Point':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    name = extract_name_from_properties(properties)
                    if name:  # Only include entities with names
                        named_entities.append({
                            'name': name,
                            'lat': coords[1],
                            'lon': coords[0],
                            'properties': properties
                        })
    
    return named_entities


def get_enhanced_location_name(lat: float, lon: float, named_entities: List[Dict]) -> str:
    """Get enhanced location name: direct name or "XmN from <nearest named entity> [lat, lon]"."""
    
    coord_suffix = f" [{lat:.6f}, {lon:.6f}]"
    
    # First check if this exact location has a name
    for entity in named_entities:
        distance = haversine_distance(lat, lon, entity['lat'], entity['lon'])
        if distance < 10:  # Within 10m, consider it the same location
            return f"{entity['name']}{coord_suffix}"
    
    # Find nearest named entity
    if not named_entities:
        return f"Unknown Location{coord_suffix}"
    
    nearest_entity = min(named_entities, 
                        key=lambda e: haversine_distance(lat, lon, e['lat'], e['lon']))
    
    distance = haversine_distance(lat, lon, nearest_entity['lat'], nearest_entity['lon'])
    bearing = calculate_bearing(nearest_entity['lat'], nearest_entity['lon'], lat, lon)
    compass = bearing_to_compass(bearing)
    
    return f"{distance:.0f}m {compass} from {nearest_entity['name']}{coord_suffix}"


async def run_extended_passenger_session():
    """Run passenger service for extended time to collect more passengers."""
    
    print("🎯 LIVE EXTENDED PASSENGER SESSION")
    print("=" * 60)
    
    try:
        # Load named entities
        print("📍 Loading named entities from GeoJSON files...")
        base_path = "world/arknet_transit_simulator/passenger_modeler/data/barbados/"
        geojson_files = [
            f"{base_path}barbados_names.geojson",
            f"{base_path}barbados_highway.geojson", 
            f"{base_path}barbados_busstops.geojson",
            f"{base_path}barbados_amenities.geojson"
        ]
        
        named_entities = find_all_named_entities(geojson_files)
        print(f"   Found {len(named_entities)} named entities")
        
        # Import here to avoid module issues
        from fleet_manager.services.route_dispatcher import Dispatcher
        from arknet_transit_simulator.passenger_modeler.passenger_service import DynamicPassengerService
        
        print("\n🚀 Starting extended passenger collection...")
        print("📊 This will run for 2 minutes, checking every 20 seconds")
        print("   (Passengers spawn every 10 seconds by default)")
        
        # Initialize dispatcher
        dispatcher = Dispatcher(api_base_url="http://localhost:8000")
        
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Create passenger service
        passenger_service = DynamicPassengerService(['1B', '1', '1A'], max_memory_mb=10, dispatcher=dispatcher)
        
        all_collected_passengers = {}
        collection_times = []
        
        # Run for 2 minutes, checking every 20 seconds
        total_duration = 120  # 2 minutes
        check_interval = 20   # 20 seconds
        checks = total_duration // check_interval
        
        print(f"\n⏱️  Running {checks} checks over {total_duration} seconds...")
        
        for check in range(1, checks + 1):
            print(f"\n📊 CHECK {check}/{checks} - After {check * check_interval} seconds")
            
            # Get current passengers
            try:
                current_passengers = passenger_service.active_passengers
                collection_times.append(time.time())
                
                print(f"   🚶 Found {len(current_passengers)} active passengers")
                
                # Add new passengers to collection
                for passenger_id, passenger_data in current_passengers.items():
                    if passenger_id not in all_collected_passengers:
                        all_collected_passengers[passenger_id] = {
                            **passenger_data,
                            'collection_check': check,
                            'collection_time': check * check_interval
                        }
                        print(f"   ➕ New passenger: {passenger_id[:12]}...")
                
                print(f"   📈 Total collected so far: {len(all_collected_passengers)}")
                
                # Wait for next check (except on last iteration)
                if check < checks:
                    print(f"   ⏳ Waiting {check_interval} seconds for next check...")
                    await asyncio.sleep(check_interval)
                    
            except Exception as e:
                print(f"   ❌ Error in check {check}: {e}")
        
        print(f"\n🎯 COLLECTION COMPLETE - FINAL RESULTS")
        print("=" * 60)
        
        if not all_collected_passengers:
            print("❌ No passengers collected during the session")
            return
        
        # Create enhanced table
        table_data = []
        
        for i, (passenger_id, passenger_data) in enumerate(all_collected_passengers.items(), 1):
            route_id = passenger_data.get('route_id', 'Unknown')
            pickup_coords = passenger_data.get('pickup_coords', [])
            dest_coords = passenger_data.get('destination_coords', [])
            collection_check = passenger_data.get('collection_check', 0)
            collection_time = passenger_data.get('collection_time', 0)
            
            if not pickup_coords or len(pickup_coords) < 2:
                continue
                
            if not dest_coords or len(dest_coords) < 2:
                continue
            
            pickup_lon, pickup_lat = pickup_coords[0], pickup_coords[1]
            dest_lon, dest_lat = dest_coords[0], dest_coords[1]
            
            # Calculate trip distance
            trip_distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
            
            # Get enhanced names
            pickup_name = get_enhanced_location_name(pickup_lat, pickup_lon, named_entities)
            dest_name = get_enhanced_location_name(dest_lat, dest_lon, named_entities)
            
            # Validation
            meets_min = "✅" if trip_distance >= 350 else "❌"
            
            table_data.append([
                f"P{i:02d}",
                route_id,
                pickup_name[:40] + "..." if len(pickup_name) > 43 else pickup_name,
                dest_name[:40] + "..." if len(dest_name) > 43 else dest_name,
                f"{trip_distance:.0f}m",
                meets_min,
                f"@{collection_time}s"
            ])
        
        headers = ['#', 'Route', 'FROM (Origin)', 'TO (Destination)', 'Dist', '✓', 'Time']
        
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[4, 6, 43, 43, 6, 3, 8]))
        
        # Statistics
        distances = []
        route_counts = {}
        valid_trips = 0
        
        for passenger_data in all_collected_passengers.values():
            pickup_coords = passenger_data.get('pickup_coords', [])
            dest_coords = passenger_data.get('destination_coords', [])
            route_id = passenger_data.get('route_id')
            
            if len(pickup_coords) >= 2 and len(dest_coords) >= 2:
                pickup_lon, pickup_lat = pickup_coords[0], pickup_coords[1]
                dest_lon, dest_lat = dest_coords[0], dest_coords[1]
                distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
                distances.append(distance)
                
                if distance >= 350:
                    valid_trips += 1
                    
                route_counts[route_id] = route_counts.get(route_id, 0) + 1
        
        print(f"\n📈 EXTENDED SESSION SUMMARY")
        print("=" * 40)
        print(f"⏱️  Session Duration: {total_duration} seconds ({checks} checks)")
        print(f"🚶 Total Passengers Collected: {len(all_collected_passengers)}")
        print(f"✅ Valid Trips (≥350m): {valid_trips}/{len(all_collected_passengers)} ({100*valid_trips/len(all_collected_passengers):.1f}%)")
        
        if distances:
            print(f"📏 Distance Statistics:")
            print(f"   • Average: {sum(distances)/len(distances):.0f}m")
            print(f"   • Minimum: {min(distances):.0f}m")
            print(f"   • Maximum: {max(distances):.0f}m")
        
        print(f"🚌 Route Distribution:")
        for route_id, count in sorted(route_counts.items()):
            print(f"   • Route {route_id}: {count} passengers")
        
        print(f"\n🎉 Enhanced naming system shows destinations with:")
        print(f"  • Distance + compass direction from nearest landmarks")
        print(f"  • Precise coordinates [lat, lon] in brackets")
        print(f"  • All trips validated against 350m minimum requirement")
        
    except Exception as e:
        print(f"❌ Error in extended session: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            if 'dispatcher' in locals() and hasattr(dispatcher, 'session') and dispatcher.session:
                await dispatcher.session.close()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(run_extended_passenger_session())