#!/usr/bin/env python3
"""
Enhanced Naming System
======================

When locations don't have direct names, generate descriptive names like:
"350m NE from Bridgetown Terminal"
"""

import json
import math
from typing import Dict, List, Optional, Tuple, Any


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
    """Get enhanced location name: direct name or "XmN from <nearest named entity>"."""
    
    # First check if this exact location has a name
    for entity in named_entities:
        distance = haversine_distance(lat, lon, entity['lat'], entity['lon'])
        if distance < 10:  # Within 10m, consider it the same location
            return entity['name']
    
    # Find nearest named entity
    if not named_entities:
        return f"[{lat:.6f}, {lon:.6f}]"
    
    nearest_entity = min(named_entities, 
                        key=lambda e: haversine_distance(lat, lon, e['lat'], e['lon']))
    
    distance = haversine_distance(lat, lon, nearest_entity['lat'], nearest_entity['lon'])
    bearing = calculate_bearing(nearest_entity['lat'], nearest_entity['lon'], lat, lon)
    compass = bearing_to_compass(bearing)
    
    return f"{distance:.0f}m {compass} from {nearest_entity['name']}"


def test_enhanced_naming():
    """Test the enhanced naming system."""
    print("🧪 TESTING ENHANCED NAMING SYSTEM")
    print("=" * 50)
    
    # Load all GeoJSON data
    base_path = "world/arknet_transit_simulator/passenger_modeler/data/barbados/"
    geojson_files = [
        f"{base_path}barbados_names.geojson",
        f"{base_path}barbados_highway.geojson", 
        f"{base_path}barbados_busstops.geojson",
        f"{base_path}barbados_amenities.geojson"
    ]
    
    print("📍 Loading named entities from GeoJSON files...")
    named_entities = find_all_named_entities(geojson_files)
    print(f"   Found {len(named_entities)} named entities")
    
    # Show some examples
    print(f"\n🏷️ Sample named entities:")
    for i, entity in enumerate(named_entities[:5]):
        print(f"   {i+1}. {entity['name']} at [{entity['lat']:.6f}, {entity['lon']:.6f}]")
    
    # Test some coordinates
    test_coords = [
        (13.270090, -59.642575, "Test pickup location"),
        (13.269284, -59.642648, "Test destination"),
        (13.272528, -59.641282, "Another pickup"),
        (13.106026, -59.613194, "Bridgetown area")  # Near capital
    ]
    
    print(f"\n🧭 Testing enhanced location naming:")
    for lat, lon, description in test_coords:
        enhanced_name = get_enhanced_location_name(lat, lon, named_entities)
        print(f"   {description}: {enhanced_name}")


if __name__ == "__main__":
    test_enhanced_naming()