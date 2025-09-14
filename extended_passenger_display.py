#!/usr/bin/env python3
"""
Extended Passenger Display with Enhanced Names
==============================================

Runs for longer duration to show more passengers as they spawn over time.
Shows destination names like "350m NE from Bridgetown Terminal [13.270090, -59.642575]"
"""

import json
import math
import time
from typing import Dict, List, Any, Optional
from tabulate import tabulate
import sys
import os

# Add the project to path
sys.path.append('world')
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


def show_extended_passenger_session():
    """Show passengers over an extended time period."""
    
    print("🎯 EXTENDED PASSENGER SESSION WITH ENHANCED NAMING")
    print("=" * 70)
    
    try:
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
        
        print("\n⏱️  RUNNING EXTENDED SESSION TO COLLECT MORE PASSENGERS")
        print("=" * 70)
        print("This will run the passenger distribution demo multiple times")
        print("to collect passengers as they spawn over time...")
        
        all_passengers = {}
        passenger_counter = 0
        
        # Run multiple sessions to collect more passengers
        for session in range(1, 6):  # 5 sessions
            print(f"\n📊 SESSION {session}/5 - Collecting passengers...")
            
            # Run passenger distribution demo and capture output
            import subprocess
            import re
            
            try:
                result = subprocess.run(['python', 'demo_passenger_distribution.py'], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    output = result.stdout
                    
                    # Parse coordinates from output using regex
                    pattern = r'Route: (\w+)\s+Route Name: route \w+\s+🚶 ORIGIN: \[([-\d.]+), ([-\d.]+)\]\s+.*?\s+🎯 DESTINATION: \[([-\d.]+), ([-\d.]+)\]'
                    
                    matches = re.findall(pattern, output, re.DOTALL)
                    
                    for match in matches:
                        route_id, pickup_lon, pickup_lat, dest_lon, dest_lat = match
                        passenger_counter += 1
                        
                        passenger_id = f"PASS_{passenger_counter:03d}"
                        all_passengers[passenger_id] = {
                            'route_id': route_id,
                            'pickup_coords': [float(pickup_lon), float(pickup_lat)],
                            'destination_coords': [float(dest_lon), float(dest_lat)],
                            'session': session
                        }
                    
                    print(f"   Found {len(matches)} passengers in this session")
                    
                else:
                    print(f"   ❌ Demo failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"   ⏱️  Session {session} timed out")
            except Exception as e:
                print(f"   ❌ Error in session {session}: {e}")
            
            # Wait between sessions
            if session < 5:
                print(f"   ⏳ Waiting 15 seconds for more passengers to spawn...")
                time.sleep(15)
        
        print(f"\n📊 COLLECTED {len(all_passengers)} TOTAL PASSENGERS")
        print("=" * 70)
        
        if not all_passengers:
            print("❌ No passengers collected. Try running demo_passenger_distribution.py manually first.")
            return
        
        # Create table with enhanced names
        table_data = []
        
        for passenger_id, passenger_data in all_passengers.items():
            route_id = passenger_data.get('route_id')
            pickup_coords = passenger_data.get('pickup_coords', [])
            dest_coords = passenger_data.get('destination_coords', [])
            session = passenger_data.get('session', 0)
            
            if not pickup_coords or len(pickup_coords) < 2:
                continue
                
            if not dest_coords or len(dest_coords) < 2:
                continue
            
            pickup_lon, pickup_lat = pickup_coords[0], pickup_coords[1]
            dest_lon, dest_lat = dest_coords[0], dest_coords[1]
            
            # Calculate trip distance
            trip_distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
            
            # Get enhanced names with coordinates
            pickup_name = get_enhanced_location_name(pickup_lat, pickup_lon, named_entities)
            dest_name = get_enhanced_location_name(dest_lat, dest_lon, named_entities)
            
            # Validation
            meets_min = "✅" if trip_distance >= 350 else "❌"
            
            table_data.append([
                passenger_id,
                route_id,
                pickup_name[:45] + "..." if len(pickup_name) > 48 else pickup_name,
                dest_name[:45] + "..." if len(dest_name) > 48 else dest_name,
                f"{trip_distance:.0f}m",
                meets_min,
                f"S{session}"
            ])
        
        headers = ['ID', 'Route', 'FROM (Origin)', 'TO (Destination)', 'Dist', '✓', 'Sess']
        
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[8, 6, 48, 48, 6, 3, 4]))
        
        # Summary statistics
        distances = []
        route_counts = {}
        valid_trips = 0
        
        for passenger_data in all_passengers.values():
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
        
        print(f"\n📈 SESSION SUMMARY")
        print("=" * 30)
        print(f"🚶 Total Passengers: {len(all_passengers)}")
        print(f"✅ Valid Trips (≥350m): {valid_trips}/{len(all_passengers)} ({100*valid_trips/len(all_passengers):.1f}%)")
        
        if distances:
            print(f"📏 Distance Stats:")
            print(f"   • Average: {sum(distances)/len(distances):.0f}m")
            print(f"   • Minimum: {min(distances):.0f}m")
            print(f"   • Maximum: {max(distances):.0f}m")
        
        print(f"🚌 Route Distribution:")
        for route_id, count in sorted(route_counts.items()):
            print(f"   • Route {route_id}: {count} passengers")
        
        print(f"\n🎉 Enhanced naming system successfully shows:")
        print(f"  • Distance + direction from nearest landmarks")
        print(f"  • Precise coordinates in brackets for verification")
        print(f"  • Validation against 350m minimum distance requirement")
        
    except Exception as e:
        print(f"❌ Error in extended session: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    show_extended_passenger_session()