#!/usr/bin/env python3
"""
Enhanced Passenger Validation with Named Destinations
=====================================================

Shows passenger origins and destinations with enhanced names like:
"90m N from Six Men's [13.270090, -59.642575]"
"""

import asyncio
import json
import math
import sys
from typing import Dict, List, Any, Tuple, Optional
from tabulate import tabulate

# Add the project to path
sys.path.append('world')
sys.path.append('world/fleet_manager') 
sys.path.append('world/arknet_transit_simulator')

from arknet_transit_simulator.passenger_modeler.passenger_service import PassengerService


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


def get_enhanced_location_name(lat: float, lon: float, named_entities: List[Dict], include_coords: bool = True) -> str:
    """Get enhanced location name: direct name or "XmN from <nearest named entity> [lat, lon]"."""
    
    coord_suffix = f" [{lat:.6f}, {lon:.6f}]" if include_coords else ""
    
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


async def enhanced_passenger_validation():
    """Enhanced passenger validation with named destinations."""
    
    print("🎯 ENHANCED PASSENGER VALIDATION WITH NAMED DESTINATIONS")
    print("=" * 65)
    
    # Initialize dispatcher
    dispatcher = Dispatcher(api_base_url="http://localhost:8000")
    
    try:
        # Connect to Fleet Manager API
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Load all named entities from GeoJSON files
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
        
        # Create passenger service
        print("📍 Creating passenger service for routes: ['1B', '1', '1A']")
        passenger_service = PassengerService(['1B', '1', '1A'], dispatcher)
        
        # Wait for passengers to spawn
        print("⏱️  Waiting for passengers to spawn...")
        await asyncio.sleep(2)
        
        passengers = passenger_service.get_passengers()
        print(f"🚶 Found {len(passengers)} active passengers")
        
        if not passengers:
            print("❌ No passengers found")
            return
        
        # Get route geometries
        print(f"\n🗺️ Fetching route geometries from Fleet Manager...")
        route_geometries = {}
        for route_id in ['1B', '1', '1A']:
            try:
                route_info = await dispatcher.get_route_info(route_id)
                if route_info and hasattr(route_info, 'geometry'):
                    coords = route_info.geometry.get('coordinates', [])
                    route_geometries[route_id] = coords
                    print(f"   • Route {route_id}: {len(coords)} coordinate points")
                else:
                    print(f"   ⚠️ Route {route_id}: No geometry data")
            except Exception as e:
                print(f"   ❌ Route {route_id}: Error fetching geometry - {e}")
        
        # Create validation table
        print(f"\n📊 PASSENGER DESTINATIONS WITH ENHANCED NAMING")
        print("=" * 65)
        
        table_data = []
        
        for i, (passenger_id, passenger_data) in enumerate(passengers.items()):
            route_id = passenger_data.get('route_id')
            pickup_coords = passenger_data.get('pickup_coords', [])
            dest_coords = passenger_data.get('destination_coords', [])
            
            if not pickup_coords or len(pickup_coords) < 2:
                continue
                
            if not dest_coords or len(dest_coords) < 2:
                continue
            
            pickup_lon, pickup_lat = pickup_coords[0], pickup_coords[1]
            dest_lon, dest_lat = dest_coords[0], dest_coords[1]
            
            # Calculate trip distance
            trip_distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
            
            # Get enhanced names with coordinates
            pickup_name = get_enhanced_location_name(pickup_lat, pickup_lon, named_entities, True)
            dest_name = get_enhanced_location_name(dest_lat, dest_lon, named_entities, True)
            
            # Validate route geometry
            route_valid = "❌"
            if route_id in route_geometries:
                pickup_on_route, pickup_dist = validate_point_on_route(
                    pickup_lat, pickup_lon, route_geometries[route_id]
                )
                dest_on_route, dest_dist = validate_point_on_route(
                    dest_lat, dest_lon, route_geometries[route_id]
                )
                if pickup_on_route and dest_on_route:
                    route_valid = "✅"
            
            table_data.append([
                f"PASS_{i+1}",
                route_id,
                pickup_name,
                dest_name,
                f"{trip_distance:.0f}m",
                route_valid
            ])
        
        headers = ['Passenger', 'Route', 'Origin (Pickup)', 'Destination (Drop-off)', 'Distance', 'Valid']
        
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[12, 6, 40, 40, 8, 6]))
        
        print(f"\n🎉 Enhanced naming system shows:")
        print(f"  • Exact location names when available")
        print(f"  • Distance/direction from nearest landmark when not")
        print(f"  • Precise coordinates in brackets for verification")
        print(f"  • All passengers validated against real route geometry")
        
    except Exception as e:
        print(f"❌ Error in enhanced validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if dispatcher.session:
            await dispatcher.session.close()


if __name__ == "__main__":
    asyncio.run(enhanced_passenger_validation())