#!/usr/bin/env python3
"""
CORRECTED Comprehensive Passenger Validation
============================================

This validates passengers using the ACTUAL passenger modeler system:
1. Uses priority naming system (names priority 1, highway priority 2)
2. Uses all GeoJSON files as configured in config.ini
3. Uses correct walking distance from config.ini (80m)
4. Shows proper location names based on priority system
5. Accounts for minimum trip distance logic
"""

import json
import asyncio
import math
from typing import List, Dict, Any, Tuple
from tabulate import tabulate
import configparser
from pathlib import Path

# Import the actual dispatcher
import sys
sys.path.append('world/arknet_transit_simulator')
from core.dispatcher import Dispatcher


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371000  # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) * math.sin(delta_phi / 2) +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2))
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


def load_passenger_modeler_config() -> configparser.ConfigParser:
    """Load the actual passenger modeler config.ini"""
    config = configparser.ConfigParser()
    config_path = "world/arknet_transit_simulator/passenger_modeler/config.ini"
    try:
        config.read(config_path)
        return config
    except Exception as e:
        print(f"❌ Error loading config.ini: {e}")
        return None


def get_location_name_with_priority(lat: float, lon: float, all_datasets: Dict[str, Dict], 
                                  naming_priorities: Dict[str, int], max_distance: float = 80) -> str:
    """Get location name using the priority system from passenger modeler config."""
    
    # Find closest named locations by priority
    priority_matches = {}
    
    for dataset_name, priority in naming_priorities.items():
        if dataset_name not in all_datasets:
            continue
            
        dataset = all_datasets[dataset_name]
        if not dataset or 'features' not in dataset:
            continue
            
        closest_distance = float('inf')
        closest_name = None
        
        for feature in dataset['features']:
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Point':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    feature_lon, feature_lat = coords[0], coords[1]
                    distance = haversine_distance(lat, lon, feature_lat, feature_lon)
                    
                    if distance <= max_distance and distance < closest_distance:
                        name = properties.get('name')
                        if name:  # Only consider features with actual names
                            closest_distance = distance
                            closest_name = name
        
        if closest_name:
            priority_matches[priority] = {
                'name': closest_name,
                'distance': closest_distance,
                'dataset': dataset_name
            }
    
    # Return the highest priority match
    if priority_matches:
        highest_priority = min(priority_matches.keys())
        match = priority_matches[highest_priority]
        return f"{match['name']} ({match['distance']:.0f}m from {match['dataset']})"
    
    return "Unknown Location"


def find_nearby_locations(passenger_lat: float, passenger_lon: float, 
                         all_datasets: Dict[str, Dict], max_distance: float = 80) -> List[Dict]:
    """Find all nearby locations from all datasets."""
    nearby = []
    
    for dataset_name, dataset in all_datasets.items():
        if not dataset or 'features' not in dataset:
            continue
            
        for feature in dataset['features']:
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Point':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    feature_lon, feature_lat = coords[0], coords[1]
                    distance = haversine_distance(passenger_lat, passenger_lon, feature_lat, feature_lon)
                    
                    if distance <= max_distance:
                        name = properties.get('name') or properties.get('stop_name') or properties.get('amenity') or f"{dataset_name}_feature"
                        nearby.append({
                            'name': name,
                            'dataset': dataset_name,
                            'distance_m': round(distance, 1),
                            'coordinates': [feature_lat, feature_lon]
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


async def validate_passengers_correct():
    """Comprehensive passenger validation using the actual passenger modeler configuration."""
    
    print("🔍 CORRECTED COMPREHENSIVE PASSENGER VALIDATION")
    print("=" * 60)
    
    # Load passenger modeler config
    config = load_passenger_modeler_config()
    if not config:
        print("❌ Failed to load passenger modeler config")
        return
    
    # Parse naming priorities
    naming_priorities = {}
    for key, value in config['naming_priority'].items():
        if key.startswith('priority_'):
            priority_num = int(key.split('_')[1])
            naming_priorities[value] = priority_num
    
    # Get walking distance from config
    walking_distance_m = config.getint('processing', 'walking_distance_meters', fallback=80)
    
    print(f"📋 Using Passenger Modeler Configuration:")
    print(f"   • Walking distance: {walking_distance_m}m")
    print(f"   • Naming priorities: {naming_priorities}")
    
    # Initialize dispatcher
    dispatcher = Dispatcher(api_base_url="http://localhost:8000")
    
    try:
        # Connect to Fleet Manager API
        if not await dispatcher.initialize():
            print("❌ Failed to connect to Fleet Manager API")
            return
        
        print("✅ Connected to Fleet Manager API")
        
        # Load ALL GeoJSON data files from config
        print("📍 Loading all GeoJSON validation data from config...")
        base_path = "world/arknet_transit_simulator/passenger_modeler/"
        
        all_datasets = {}
        total_features = 0
        
        for dataset_name, file_path in config['data'].items():
            if file_path:  # Only load non-empty paths
                full_path = base_path + file_path
                dataset = load_geojson_data(full_path)
                if dataset and 'features' in dataset:
                    all_datasets[dataset_name] = dataset
                    feature_count = len(dataset['features'])
                    total_features += feature_count
                    print(f"   • {dataset_name}: {feature_count} features")
        
        print(f"   • Total features loaded: {total_features}")
        
        # Create passenger service for testing
        print("📍 Creating passenger service for routes: ['1B', '1', '1A']")
        from passenger_modeler.passenger_service import create_passenger_service
        
        service = await create_passenger_service(['1B', '1', '1A'], max_memory_mb=5)
        if not service:
            print("❌ Failed to create passenger service")
            return
        
        # Start service and wait for passengers
        await service.start_service()
        print("⏱️  Waiting for passengers to spawn...")
        await asyncio.sleep(3)
        
        passengers = service.get_active_passengers()
        print(f"🚶 Found {len(passengers)} active passengers")
        
        if not passengers:
            print("⚠️ No passengers found. Service may need more time to initialize.")
            await service.stop_service()
            return
        
        # Get route geometries
        print(f"\n🗺️ Fetching route geometries from Fleet Manager...")
        route_geometries = {}
        unique_routes = set(p.get('route_id') for p in passengers.values())
        
        for route_id in unique_routes:
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
            
            # Validate route geometry
            if route_id in route_geometries:
                coords = route_geometries[route_id]
                pickup_on_route, pickup_distance = validate_point_on_route(pickup_lat, pickup_lon, coords)
                dest_on_route, dest_distance = validate_point_on_route(dest_lat, dest_lon, coords)
                
                print(f"🗺️ ROUTE GEOMETRY VALIDATION:")
                print(f"   • Pickup on route: {'✅ YES' if pickup_on_route else '❌ NO'} (closest: {pickup_distance:.1f}m)")
                print(f"   • Destination on route: {'✅ YES' if dest_on_route else '❌ NO'} (closest: {dest_distance:.1f}m)")
                
                route_valid = pickup_on_route and dest_on_route
            else:
                print(f"⚠️ No route geometry available for validation")
                route_valid = False
                pickup_distance = dest_distance = 0
            
            # Get named locations using priority system
            pickup_name = get_location_name_with_priority(pickup_lat, pickup_lon, all_datasets, naming_priorities, walking_distance_m)
            dest_name = get_location_name_with_priority(dest_lat, dest_lon, all_datasets, naming_priorities, walking_distance_m)
            
            print(f"🏷️ PRIORITY NAMING:")
            print(f"   • Pickup location: {pickup_name}")
            print(f"   • Destination location: {dest_name}")
            
            # Find nearby features from all datasets
            pickup_nearby = find_nearby_locations(pickup_lat, pickup_lon, all_datasets, walking_distance_m)
            dest_nearby = find_nearby_locations(dest_lat, dest_lon, all_datasets, walking_distance_m)
            
            print(f"🗺️ NEARBY FEATURES (within {walking_distance_m}m):")
            print(f"   • Near pickup: {len(pickup_nearby)} features")
            if pickup_nearby:
                for feature in pickup_nearby[:3]:  # Show top 3
                    print(f"     - {feature['name']} ({feature['dataset']}, {feature['distance_m']}m)")
            
            print(f"   • Near destination: {len(dest_nearby)} features")
            if dest_nearby:
                for feature in dest_nearby[:3]:  # Show top 3
                    print(f"     - {feature['name']} ({feature['dataset']}, {feature['distance_m']}m)")
            
            # Validation scoring
            score = 0
            
            # Core validation - being exactly on route is most important
            if route_valid:
                score += 5
            
            # Named location proximity
            if pickup_name != "Unknown Location":
                score += 2
            if dest_name != "Unknown Location":
                score += 2
            
            # Feature proximity
            if pickup_nearby:
                score += 0.5
            if dest_nearby:
                score += 0.5
            
            # Trip distance validation (minimum from config is walking_distance_meters)
            if trip_distance >= walking_distance_m:
                score += 1
            elif trip_distance >= walking_distance_m / 2:  # Half minimum is acceptable
                score += 0.5
                
            validation_results.append({
                'passenger_id': passenger_id[:12] + "...",
                'route': route_id,
                'pickup_coords': f"{pickup_lat:.6f},{pickup_lon:.6f}",
                'dest_coords': f"{dest_lat:.6f},{dest_lon:.6f}",
                'pickup_name': pickup_name.split('(')[0].strip(),  # Just the name part
                'dest_name': dest_name.split('(')[0].strip(),      # Just the name part
                'trip_distance_m': round(trip_distance, 1),
                'on_route': '✅' if route_valid else '❌',
                'nearby_features': len(pickup_nearby) + len(dest_nearby),
                'validation_score': round(score, 1),
                'status': '✅ VALID' if score >= 5 else '⚠️ QUESTIONABLE' if score >= 3 else '❌ INVALID'
            })
        
        # Summary table
        print(f"\n📊 CORRECTED VALIDATION SUMMARY TABLE")
        print("=" * 80)
        
        headers = ['Passenger', 'Route', 'Pickup Location', 'Dest Location', 'Trip(m)', 
                  'On Route', 'Features', 'Score', 'Status']
        
        table_data = []
        for result in validation_results:
            table_data.append([
                result['passenger_id'],
                result['route'],
                result['pickup_name'],
                result['dest_name'],
                result['trip_distance_m'],
                result['on_route'],
                result['nearby_features'],
                f"{result['validation_score']}/10",
                result['status']
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Final verdict
        valid_passengers = sum(1 for r in validation_results if r['validation_score'] >= 5)
        total_passengers = len(validation_results)
        
        print(f"\n🏆 CORRECTED VALIDATION VERDICT")
        print("=" * 40)
        print(f"✅ Valid Passengers: {valid_passengers}/{total_passengers}")
        print(f"📍 Using actual passenger modeler configuration")
        print(f"🏷️ Names resolved using priority system: {naming_priorities}")
        print(f"📏 Walking distance: {walking_distance_m}m (from config.ini)")
        print(f"🗺️ Total validation features: {total_features}")
        
        if valid_passengers == total_passengers:
            print(f"\n🎉 ALL PASSENGERS VALIDATED WITH CORRECT SYSTEM! 🎉")
        else:
            print(f"\n⚠️ Some passengers may need further investigation")
        
        # Stop the service
        await service.stop_service()
        
    except Exception as e:
        print(f"❌ Error in passenger validation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if dispatcher.session:
            await dispatcher.session.close()


if __name__ == "__main__":
    asyncio.run(validate_passengers_correct())