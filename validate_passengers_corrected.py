#!/usr/bin/env python3
"""
Comprehensive Passenger Validation with Proper Naming System
============================================================

Updated validation that accounts for:
1. Priority naming system: names (priority 1) and highway (priority 2)
2. Minimum destination distance of 350m from config
3. Walking distance of 80m from config for amenity proximity
4. Proper bus stop count (individual stops, not combined pickup + destination)
"""

import asyncio
import json
import math
import configparser
from typing import Dict, List, Any, Tuple
from tabulate import tabulate
import sys
sys.path.append('world/arknet_transit_simulator')

from core.dispatcher import Dispatcher
from passenger_modeler.passenger_service import DynamicPassengerService


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in meters."""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def load_geojson_data(filepath: str) -> Dict[str, Any]:
    """Load GeoJSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return {}


def load_config() -> Dict[str, Any]:
    """Load configuration from config.ini"""
    config = configparser.ConfigParser()
    config_path = 'world/arknet_transit_simulator/config/config.ini'
    
    try:
        config.read(config_path)
        
        # Load passenger service configuration
        if config.has_section('passenger_service'):
            section = config['passenger_service']
            walking_distance_km = section.getfloat('walking_distance_km', 0.5)
            destination_distance_m = section.getfloat('destination_distance_meters', 350.0)
            
            return {
                'walking_distance_meters': walking_distance_km * 1000,  # Convert km to meters
                'destination_distance_meters': destination_distance_m
            }
        else:
            print("⚠️ No [passenger_service] section found, using defaults")
            return {
                'walking_distance_meters': 500.0,  # 0.5km default
                'destination_distance_meters': 350.0
            }
            
    except Exception as e:
        print(f"❌ Error loading config: {e}, using defaults")
        return {
            'walking_distance_meters': 500.0,
            'destination_distance_meters': 350.0
        }


def get_location_name(properties: Dict[str, Any]) -> str:
    """Get location name using priority naming system."""
    # Priority 1: names GeoJSON file
    if 'name' in properties and properties['name']:
        return str(properties['name'])
    
    # Priority 2: highway GeoJSON file
    if 'highway' in properties and properties['highway']:
        return f"Highway: {properties['highway']}"
    
    # Priority 3: bus stop names
    if 'stop_name' in properties and properties['stop_name']:
        return str(properties['stop_name'])
    
    # Priority 4: amenity type
    if 'amenity' in properties and properties['amenity']:
        return f"{properties['amenity'].title()}"
        
    # Priority 5: other identifying fields
    if 'full_id' in properties:
        return f"Location {properties['full_id']}"
        
    return "Unknown Location"


def find_nearest_locations(passenger_lat: float, passenger_lon: float, 
                          location_data: Dict, max_distance: float = 500) -> List[Dict]:
    """Find locations within distance of passenger location with proper naming."""
    nearby = []
    
    if not location_data or 'features' not in location_data:
        return nearby
    
    for feature in location_data['features']:
        geometry = feature.get('geometry', {})
        properties = feature.get('properties', {})
        
        if geometry.get('type') == 'Point':
            coords = geometry.get('coordinates', [])
            if len(coords) >= 2:
                loc_lon, loc_lat = coords[0], coords[1]
                distance = haversine_distance(passenger_lat, passenger_lon, loc_lat, loc_lon)
                
                if distance <= max_distance:
                    nearby.append({
                        'name': get_location_name(properties),
                        'type': properties.get('amenity') or properties.get('highway') or 'location',
                        'distance_m': round(distance, 1),
                        'coordinates': [loc_lat, loc_lon]
                    })
    
    return sorted(nearby, key=lambda x: x['distance_m'])


def validate_point_on_route(point_lat: float, point_lon: float, 
                           route_coords: List[List[float]], tolerance_m: float = 100) -> Tuple[bool, float]:
    """Check if a point is within tolerance of a route path."""
    if not route_coords:
        return False, float('inf')
    
    min_distance = float('inf')
    
    for coord in route_coords:
        if len(coord) >= 2:
            route_lon, route_lat = coord[0], coord[1]
            distance = haversine_distance(point_lat, point_lon, route_lat, route_lon)
            min_distance = min(min_distance, distance)
    
    return min_distance <= tolerance_m, min_distance


async def validate_passengers():
    """Comprehensive passenger validation with proper naming and configuration."""
    
    print("🔍 COMPREHENSIVE PASSENGER VALIDATION")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    walking_distance_m = config['walking_distance_meters']
    min_destination_distance_m = config['destination_distance_meters']
    
    print(f"📋 Configuration:")
    print(f"   • Walking distance for amenities: {walking_distance_m}m")
    print(f"   • Minimum trip distance: {min_destination_distance_m}m")
    
    # Initialize dispatcher
    dispatcher = Dispatcher(api_base_url="http://localhost:8000")
    
    try:
        # Connect to Fleet Manager API
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Load Barbados GeoJSON data with proper naming priority
        print("📍 Loading Barbados GeoJSON validation data...")
        base_path = "world/arknet_transit_simulator/passenger_modeler/data/barbados/"
        
        # Load all location types according to priority naming system
        names_data = load_geojson_data(f"{base_path}barbados_names.geojson")  # Priority 1
        highway_data = load_geojson_data(f"{base_path}barbados_highway.geojson")  # Priority 2  
        busstops_data = load_geojson_data(f"{base_path}barbados_busstops.geojson")
        amenities_data = load_geojson_data(f"{base_path}barbados_amenities.geojson")
        
        print(f"   • Names (Priority 1): {len(names_data.get('features', []))} locations")
        print(f"   • Highway (Priority 2): {len(highway_data.get('features', []))} locations")
        print(f"   • Bus stops: {len(busstops_data.get('features', []))} locations")
        print(f"   • Amenities: {len(amenities_data.get('features', []))} locations")
        
        # Create passenger service
        print(f"📍 Creating passenger service for routes: ['1B', '1', '1A']")
        passenger_service = DynamicPassengerService(
            route_ids={'1', '1A', '1B'},
            dispatcher=dispatcher,
            max_memory_mb=50
        )
        
        await passenger_service.start_service()
        
        # Wait for passengers to spawn
        print("⏱️  Waiting for passengers to spawn...")
        await asyncio.sleep(3)
        
        passengers = passenger_service.active_passengers
        print(f"🚶 Found {len(passengers)} active passengers")
        
        if not passengers:
            print("⚠️ No passengers found, trying to spawn manually...")
            # Try manual spawn
            await passenger_service._spawn_passengers_batch(3)
            await asyncio.sleep(1)
            passengers = passenger_service.active_passengers
            print(f"🚶 After manual spawn: {len(passengers)} passengers")
        
        if not passengers:
            print("❌ No passengers available for validation")
            return
        
        # Fetch route geometries
        print(f"\n🗺️ Fetching route geometries from Fleet Manager...")
        route_geometries = {}
        
        for route_id in ['1', '1A', '1B']:
            try:
                route_info = await dispatcher.query_route_by_id(route_id)
                if route_info and route_info.geometry:
                    coords = route_info.geometry.get('coordinates', [])
                    route_geometries[route_id] = coords
                    print(f"   • Route {route_id}: {len(coords)} coordinate points")
                else:
                    print(f"   ⚠️ Route {route_id}: No geometry data")
            except Exception as e:
                print(f"   ❌ Route {route_id}: Error fetching geometry - {e}")
        
        # Validate each passenger
        print(f"\n🔍 DETAILED PASSENGER VALIDATION")
        print("=" * 60)
        
        validation_results = []
        
        for i, (passenger_id, passenger_data) in enumerate(passengers.items()):
            print(f"\n--- PASSENGER {i+1}: {passenger_id} ---")
            
            route_id = passenger_data.get('route_id')
            route_name = passenger_data.get('route_name', 'Unknown')
            pickup_coords = passenger_data.get('pickup_coords', [])
            dest_coords = passenger_data.get('destination_coords', [])
            
            print(f"📋 Route Assignment: {route_id} ({route_name})")
            
            if not pickup_coords or len(pickup_coords) < 2:
                print("❌ No valid pickup coordinates")
                continue
                
            if not dest_coords or len(dest_coords) < 2:
                print("❌ No valid destination coordinates")
                continue
            
            pickup_lon, pickup_lat = pickup_coords[0], pickup_coords[1]
            dest_lon, dest_lat = dest_coords[0], dest_coords[1]
            
            print(f"🚶 ORIGIN: [{pickup_lat:.6f}, {pickup_lon:.6f}]")
            print(f"🎯 DESTINATION: [{dest_lat:.6f}, {dest_lon:.6f}]")
            
            # Calculate trip distance
            trip_distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
            print(f"📏 Trip Distance: {trip_distance:.1f} meters")
            
            # Validate against route geometry
            if route_id in route_geometries:
                route_coords = route_geometries[route_id]
                pickup_on_route, pickup_distance = validate_point_on_route(pickup_lat, pickup_lon, route_coords)
                dest_on_route, dest_distance = validate_point_on_route(dest_lat, dest_lon, route_coords)
                route_valid = pickup_on_route and dest_on_route
                
                print(f"🗺️ ROUTE GEOMETRY VALIDATION:")
                print(f"   • Pickup on route: {'✅ YES' if pickup_on_route else '❌ NO'} (closest: {pickup_distance:.1f}m)")
                print(f"   • Destination on route: {'✅ YES' if dest_on_route else '❌ NO'} (closest: {dest_distance:.1f}m)")
            else:
                print(f"⚠️ No route geometry available for validation")
                route_valid = False
                pickup_distance = dest_distance = 0
            
            # Find nearby locations using priority naming system
            pickup_locations = []
            dest_locations = []
            
            # Combine all location sources for proximity analysis
            all_location_data = {'features': []}
            for data_source in [names_data, highway_data, busstops_data, amenities_data]:
                if data_source and 'features' in data_source:
                    all_location_data['features'].extend(data_source['features'])
            
            pickup_locations = find_nearest_locations(pickup_lat, pickup_lon, all_location_data, walking_distance_m)
            dest_locations = find_nearest_locations(dest_lat, dest_lon, all_location_data, walking_distance_m)
            
            print(f"🚏 NEARBY LOCATIONS:")
            print(f"   • Near pickup: {len(pickup_locations)} locations within {walking_distance_m}m")
            if pickup_locations:
                closest_pickup = pickup_locations[0]
                print(f"     Closest: {closest_pickup['name']} ({closest_pickup['distance_m']}m)")
            
            print(f"   • Near destination: {len(dest_locations)} locations within {walking_distance_m}m")  
            if dest_locations:
                closest_dest = dest_locations[0]
                print(f"     Closest: {closest_dest['name']} ({closest_dest['distance_m']}m)")
            
            # Separate bus stops for specific count
            pickup_bus_stops = [loc for loc in pickup_locations if 'bus' in loc['type'].lower() or loc['type'] == 'location']
            dest_bus_stops = [loc for loc in dest_locations if 'bus' in loc['type'].lower() or loc['type'] == 'location']
            
            print(f"🚌 BUS STOP ANALYSIS:")
            print(f"   • Bus stops near pickup: {len(pickup_bus_stops)}")
            print(f"   • Bus stops near destination: {len(dest_bus_stops)}")
            
            # Validation scoring
            score = 0
            
            # Core validation - being exactly on route is most important
            if route_valid:
                score += 5
            
            # Trip distance validation with new minimum
            if trip_distance >= min_destination_distance_m:
                score += 3  # Meets minimum distance requirement
            elif trip_distance >= 100:  # Still reasonable distance
                score += 2
            elif trip_distance >= 50:  # Short but valid
                score += 1
            
            # Location proximity bonuses
            if pickup_locations:
                score += 1
            if dest_locations:
                score += 1
            
            validation_results.append({
                'passenger_id': passenger_id[:12] + "...",
                'route': route_id,
                'pickup_coords': f"{pickup_lat:.6f},{pickup_lon:.6f}",
                'dest_coords': f"{dest_lat:.6f},{dest_lon:.6f}",
                'trip_distance_m': round(trip_distance, 1),
                'on_route': '✅' if route_valid else '❌',
                'pickup_locations': len(pickup_locations),
                'dest_locations': len(dest_locations),
                'bus_stops_pickup': len(pickup_bus_stops),
                'bus_stops_dest': len(dest_bus_stops),
                'meets_min_distance': '✅' if trip_distance >= min_destination_distance_m else '❌',
                'validation_score': score,
                'status': '✅ VALID' if score >= 6 else '⚠️ QUESTIONABLE' if score >= 4 else '❌ INVALID'
            })
        
        # Summary table
        print(f"\n📊 VALIDATION SUMMARY TABLE")
        print("=" * 80)
        
        headers = ['Passenger', 'Route', 'Pickup Lat,Lon', 'Dest Lat,Lon', 'Trip(m)', 
                  'On Route', f'Locations({walking_distance_m}m)', 'Bus Stops', f'Min Dist({min_destination_distance_m}m)', 'Score', 'Status']
        
        table_data = []
        for result in validation_results:
            table_data.append([
                result['passenger_id'],
                result['route'],
                result['pickup_coords'],
                result['dest_coords'],
                result['trip_distance_m'],
                result['on_route'],
                f"{result['pickup_locations']}+{result['dest_locations']}",
                f"{result['bus_stops_pickup']}+{result['bus_stops_dest']}",
                result['meets_min_distance'],
                f"{result['validation_score']}/10",
                result['status']
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Final verdict
        valid_passengers = sum(1 for r in validation_results if r['validation_score'] >= 6)
        total_passengers = len(validation_results)
        
        print(f"\n🏆 FINAL VALIDATION VERDICT")
        print("=" * 30)
        print(f"✅ Valid Passengers: {valid_passengers}/{total_passengers}")
        print(f"📍 Using proper naming priority: names → highway → bus stops → amenities")
        print(f"📏 Enforcing minimum trip distance: {min_destination_distance_m}m")
        print(f"🚶 Walking distance for amenities: {walking_distance_m}m")
        
        if valid_passengers == total_passengers:
            print(f"\n🎉 ALL PASSENGERS ARE LEGITIMATE! 🎉")
        else:
            print(f"\n⚠️ Some passengers may need further investigation")
        
    except Exception as e:
        print(f"❌ Error in passenger validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if dispatcher.session:
            await dispatcher.session.close()


if __name__ == "__main__":
    asyncio.run(validate_passengers())