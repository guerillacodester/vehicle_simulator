#!/usr/bin/env python3
"""
Route Passenger Distribution Generator with Time Smearing
Fetches route from public API and generates Poisson-distributed passengers along the route
with stops no less than 150m apart, including time-smeared passenger distribution
"""

import requests
import json
import math
import sys
import argparse
import configparser
from collections import defaultdict
from datetime import datetime, timedelta
import random
import numpy as np

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great    print(f"\n📊 ROUTE SUMMARY")
    print("=" * 80)
    print(f"Route: {summary['route_info']['short_name']} - {summary['route_info']['long_name']}")
    print(f"Total Stops: {summary['route_info']['total_stops']}")
    print(f"Total Distance: {summary['route_info']['total_distance_meters']:.0f}m ({summary['route_info']['total_distance_meters']/1000:.1f}km)")
    print(f"Start Hour: {args.start_hour}:00")
    print(f"Walking Distance: {summary['route_info']['walking_distance_meters']}m (from config.ini)")
    print(f"Base Capacity: {summary['route_totals']['total_base_capacity']:,}")
    print(f"Statistical Capacity: {summary['route_totals']['total_statistical_capacity']:,}")
    print(f"Total Passengers Generated: {summary['route_totals']['total_passenger_count']:,}")
    print(f"Passenger Sources: {summary['route_totals']['total_passenger_sources']:,}")stance between two points on Earth in meters"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def fetch_route_data(route_id, dispatcher=None):
    """Fetch route data and geometry using GTFS protocol: routes -> route-shapes -> shapes tables"""
    import requests
    try:
        print(f"📡 Fetching Route {route_id} from Strapi API using GTFS protocol...")
        
        # Get the base URL from the dispatcher's api strategy
        base_url = 'http://localhost:1337'
        if dispatcher:
            base_url = getattr(dispatcher.api_strategy, 'api_base_url', 'http://localhost:1337')
        
        # Step 1: Get route data from routes table
        print(f"🔍 Step 1: Fetching route data from routes table...")
        route_url = f"{base_url}/api/routes"
        params = {'filters[short_name][$eq]': route_id}
        response = requests.get(route_url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch routes: HTTP {response.status_code}")
            return None, None
            
        routes_data = response.json()
        routes = routes_data.get('data', [])
        
        if not routes:
            print(f"❌ Route {route_id} not found in routes table")
            return None, None
        
        route = routes[0]
        route_data = {
            'short_name': route.get('short_name'),
            'long_name': route.get('long_name'), 
            'route_type': 'bus',
            'route_id': route.get('route_id', route.get('short_name'))
        }
        
        # Step 2: Get shape_id from route-shapes table
        print(f"🔍 Step 2: Fetching shape_id from route-shapes table...")
        route_shapes_url = f"{base_url}/api/route-shapes"
        params = {'filters[route_id][$eq]': route_id, 'filters[is_default][$eq]': True}
        response = requests.get(route_shapes_url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch route-shapes: HTTP {response.status_code}")
            return None, None
            
        route_shapes_data = response.json()
        route_shapes = route_shapes_data.get('data', [])
        
        if not route_shapes:
            print(f"❌ No shape found for route {route_id} in route-shapes table")
            return None, None
            
        shape_id = route_shapes[0].get('shape_id')
        print(f"✅ Found shape_id: {shape_id}")
        
        # Step 3: Get GPS coordinates from shapes table
        print(f"🔍 Step 3: Fetching GPS coordinates from shapes table...")
        shapes_url = f"{base_url}/api/shapes"
        params = {'filters[shape_id][$eq]': shape_id, 'sort': 'shape_pt_sequence:asc'}
        response = requests.get(shapes_url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch shapes: HTTP {response.status_code}")
            return None, None
            
        shapes_data = response.json()
        shapes = shapes_data.get('data', [])
        
        if not shapes:
            print(f"❌ No GPS coordinates found for shape_id {shape_id}")
            return None, None
        
        # Convert shapes to GeoJSON format
        coordinates = []
        for shape in shapes:
            lon = shape.get('shape_pt_lon')
            lat = shape.get('shape_pt_lat')
            if lon is not None and lat is not None:
                coordinates.append([lon, lat])
        
        geometry_data = {
            'type': 'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': coordinates
                }
            }]
        }
        
        print(f"✅ Successfully fetched Route {route_id} data via GTFS protocol")
        print(f"   Short Name: {route_data.get('short_name')}")
        print(f"   Long Name: {route_data.get('long_name')}")
        print(f"   Route Type: {route_data.get('route_type')}")
        print(f"   GPS Coordinates: {len(coordinates)} points")
        
        return route_data, geometry_data
        
    except Exception as e:
        print(f"❌ Error fetching route data: {e}")
        return None, None

def convert_geometry_to_lat_lng(geometry_data):
    """Convert GTFS geometry from [lng, lat] to (lat, lng) format"""
    # Handle new GTFS FeatureCollection format
    if geometry_data.get('type') == 'FeatureCollection':
        features = geometry_data.get('features', [])
        if features:
            geometry = features[0].get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            geometry_type = geometry.get('type')
        else:
            coordinates = []
            geometry_type = None
    else:
        # Handle legacy format
        geometry = geometry_data.get('geometry', {})
        coordinates = geometry.get('coordinates', [])
        geometry_type = geometry.get('type')
    
    if geometry_type != 'LineString':
        print(f"⚠️  Expected LineString geometry, got {geometry_type}")
        return []
    
    # API returns [longitude, latitude], we need (latitude, longitude)
    route_points = [(coord[1], coord[0]) for coord in coordinates]
    
    print(f"🗺️  Route Geometry:")
    print(f"   Coordinate Points: {len(route_points)}")
    if route_points:
        print(f"   Start: ({route_points[0][0]:.6f}, {route_points[0][1]:.6f})")
        print(f"   End: ({route_points[-1][0]:.6f}, {route_points[-1][1]:.6f})")
    
    return route_points

def generate_stops_with_spacing(route_points, min_distance_meters=150):
    """Generate stops along the route with minimum distance spacing and calculate distances"""
    if not route_points:
        return []
    
    stops = [{'coordinates': route_points[0], 'cumulative_distance': 0.0}]  # Start with first point
    cumulative_distance = 0.0
    
    for point in route_points[1:]:
        # Check distance from the last added stop
        last_stop = stops[-1]['coordinates']
        distance = haversine_distance(last_stop[0], last_stop[1], point[0], point[1])
        
        if distance >= min_distance_meters:
            cumulative_distance += distance
            stops.append({
                'coordinates': point,
                'distance_from_previous': distance,
                'cumulative_distance': cumulative_distance
            })
    
    # Always include the last point if it's not already included
    if stops[-1]['coordinates'] != route_points[-1]:
        last_stop = stops[-1]['coordinates']
        final_distance = haversine_distance(last_stop[0], last_stop[1], route_points[-1][0], route_points[-1][1])
        cumulative_distance += final_distance
        stops.append({
            'coordinates': route_points[-1],
            'distance_from_previous': final_distance,
            'cumulative_distance': cumulative_distance
        })
    
    # Add distance from previous for the first stop
    if len(stops) > 1:
        stops[0]['distance_from_previous'] = 0.0
    
    print(f"🚏 Generated {len(stops)} stops from {len(route_points)} route points")
    print(f"   Minimum spacing: {min_distance_meters}m")
    print(f"   Total route length: {cumulative_distance:.1f}m")
    
    return stops

def load_config():
    """Load configuration settings from config.ini"""
    config = configparser.ConfigParser()
    config_path = 'config.ini'
    
    try:
        config.read(config_path)
        walking_distance = config.getint('processing', 'walking_distance_meters', fallback=150)
        demand_multiplier = config.getfloat('processing', 'passenger_demand_multiplier', fallback=0.4)
        print(f"📐 Walking distance from config: {walking_distance}m")
        print(f"🔧 Passenger demand multiplier from config: {demand_multiplier}")
        return {
            'walking_distance_meters': walking_distance,
            'passenger_demand_multiplier': demand_multiplier
        }
    except Exception as e:
        print(f"⚠️  Warning: Could not load config.ini ({e}), using defaults")
        return {
            'walking_distance_meters': 150,
            'passenger_demand_multiplier': 0.4
        }

def load_statistical_passenger_model():
    """Load the generated statistical passenger model"""
    global statistical_model, named_locations
    
    try:
        with open('models/generated/barbados_v4_statistical.json', 'r', encoding='utf-8') as f:
            statistical_model = json.load(f)
        
        print("✅ Loaded statistical passenger model")
        
        # Extract all named locations with coordinates, prioritizing true landmarks
        named_locations = {}
        
        # Extract locations from each category
        for category in ['bus_stops', 'amenities', 'streets', 'places']:
            category_data = statistical_model.get(category, {})
            for location_id, location_info in category_data.items():
                # Get the name from stop_name field
                stop_name = location_info.get('stop_name', '')
                
                # Skip if no proper name or if it's a generic auto-generated name
                if (stop_name and 
                    not stop_name.startswith(('AME_', 'BUS_', 'STR_', 'PLC_')) and
                    stop_name != location_id):
                    
                    # Filter out positional descriptions - we want actual landmark names
                    # Skip names that contain distance/direction patterns
                    positional_patterns = [
                        'of ', 'm N', 'm S', 'm E', 'm W', 'NE', 'NW', 'SE', 'SW',
                        'NNE', 'NNW', 'SSE', 'SSW', 'ENE', 'ESE', 'WNW', 'WSW'
                    ]
                    is_positional = any(pattern in stop_name for pattern in positional_patterns)
                    
                    if not is_positional:
                        # Get coordinates from latitude/longitude fields
                        lat = location_info.get('latitude')
                        lon = location_info.get('longitude')
                        
                        if lat is not None and lon is not None:
                            named_locations[stop_name] = {
                                'coordinates': [lon, lat],  # [longitude, latitude] format
                                'category': category,
                                'location_id': location_id
                            }
        
        print(f"   Total locations in model: {sum(len(statistical_model.get(cat, {})) for cat in ['bus_stops', 'amenities', 'streets', 'places'])}")
        print(f"   Bus stops: {len(statistical_model.get('bus_stops', {}))}")
        print(f"   Amenities: {len(statistical_model.get('amenities', {}))}")
        print(f"   Streets: {len(statistical_model.get('streets', {}))}")
        print(f"   Places: {len(statistical_model.get('places', {}))}")
        print(f"   Named locations: {len(named_locations)}")
        
        return True
        
    except FileNotFoundError:
        print("❌ Statistical passenger model not found")
        print("   Run consolidated_passenger_modeler.py first to generate the model")
        return None
    except Exception as e:
        print(f"❌ Error loading passenger model: {e}")
        return None

def find_nearby_passenger_locations(stop_lat, stop_lng, passenger_locations, walking_distance_meters):
    """Find passenger generation locations within walking distance of a stop"""
    nearby = []
    
    for location in passenger_locations:
        loc_lat = location.get('latitude')
        loc_lng = location.get('longitude')
        
        if loc_lat is None or loc_lng is None:
            continue
            
        distance = haversine_distance(stop_lat, stop_lng, loc_lat, loc_lng)
        if distance <= walking_distance_meters:
            location_copy = location.copy()
            location_copy['distance_to_stop'] = distance
            nearby.append(location_copy)
    
    # Sort by distance (closest first)
    nearby.sort(key=lambda x: x['distance_to_stop'])
    
    # Limit to maximum number of contributing locations (prevents excessive aggregation)
    MAX_CONTRIBUTING_LOCATIONS = 8  # Reasonable limit for bus stop catchment area
    if len(nearby) > MAX_CONTRIBUTING_LOCATIONS:
        nearby = nearby[:MAX_CONTRIBUTING_LOCATIONS]
        
    return nearby

def get_cardinal_direction(lat1, lon1, lat2, lon2):
    """Calculate cardinal direction from point 1 to point 2"""
    # Calculate the bearing from point 1 to point 2
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360  # Normalize to 0-360
    
    # Convert bearing to cardinal direction
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(bearing / 22.5) % 16
    return directions[index]

def generate_stop_name(stop_index, stop_coords, nearby_locations, total_stops):
    """Generate clean, simple names for stops based on nearby locations"""
    global named_locations
    
    if not named_locations:
        # Fallback naming if no named locations available
        if stop_index == 0:
            return "Route Start"
        elif stop_index == total_stops - 1:
            return "Route End" 
        else:
            return f"Stop {stop_index + 1}"
    
    # Calculate distances to all named locations
    stop_lat, stop_lon = stop_coords
    
    closest_name = None
    min_distance = float('inf')
    closest_coords = None
    
    for name, location_info in named_locations.items():
        loc_coords = location_info['coordinates']  # [longitude, latitude]
        distance = haversine_distance(stop_lat, stop_lon, loc_coords[1], loc_coords[0])
        
        if distance < min_distance:
            min_distance = distance
            closest_name = name
            closest_coords = loc_coords
    
    if closest_name:
        # Simple naming logic: if close enough, use the actual location name
        if min_distance <= 50:  # Close enough - use the actual name directly
            return closest_name
        elif min_distance < 2000:  # Within reasonable distance - show direction
            direction = get_cardinal_direction(stop_lat, stop_lon, closest_coords[1], closest_coords[0])
            distance_str = f"{int(min_distance)}m" if min_distance < 1000 else f"{min_distance/1000:.1f}km"
            return f"{distance_str} {direction} of {closest_name}"
    
    # Fallback naming
    if stop_index == 0:
        return "Route Start"
    elif stop_index == total_stops - 1:
        return "Route End" 
    else:
        return f"Stop {stop_index + 1}"

def apply_time_smearing(base_passengers, start_hour, smear_hours=1):
    """Apply time smearing to passenger distribution (from start_hour to start_hour+1)"""
    if base_passengers == 0:
        return []
    
    # Generate passengers distributed over the next hour
    time_distributed_passengers = []
    
    for _ in range(base_passengers):
        # Random time within the hour window
        time_offset_minutes = random.uniform(0, smear_hours * 60)
        passenger_time = start_hour + (time_offset_minutes / 60)
        
        # Ensure time stays within 24-hour format
        if passenger_time >= 24:
            passenger_time -= 24
            
        time_distributed_passengers.append(passenger_time)
    
    return sorted(time_distributed_passengers)

def get_hourly_multiplier(location, hour):
    """Get the hourly multiplier for a specific location and hour"""
    hourly_patterns = location.get('hourly_patterns', {})
    if not hourly_patterns:
        return 1.0
    
    # Get the multiplier for the specific hour
    hour_str = str(int(hour))  # Convert to string key
    return hourly_patterns.get(hour_str, 1.0)

def generate_passengers_for_stop(stop_info, stop_index, passenger_model, start_hour, total_stops, walking_distance_meters, demand_multiplier=0.4):
    """Generate passengers for a specific stop using the statistical model with time smearing"""
    global statistical_model
    stop_coords = stop_info['coordinates']
    
    # Build the passenger locations list from the statistical model
    passenger_locations = []
    for category in ['bus_stops', 'amenities', 'streets', 'places']:
        category_data = statistical_model.get(category, {})
        for location_id, location_info in category_data.items():
            lat = location_info.get('latitude')
            lon = location_info.get('longitude')
            if lat is not None and lon is not None:
                passenger_locations.append({
                    'id': location_id,
                    'category': category,
                    'coordinates': [lon, lat],
                    'latitude': lat,
                    'longitude': lon,
                    'stop_name': location_info.get('stop_name', location_id),
                    'passenger_capacity': location_info.get('passenger_capacity', 0),
                    'base_capacity': location_info.get('base_capacity', 0),
                    'hourly_patterns': location_info.get('hourly_patterns', {}),
                    'daily_patterns': location_info.get('daily_patterns', {}),
                    'amenity_weights': location_info.get('amenity_weights', {})
                })
    
    # Find nearby passenger generation locations within walking distance
    nearby_locations = find_nearby_passenger_locations(
        stop_coords[0], stop_coords[1], passenger_locations, walking_distance_meters
    )
    
    total_capacity = 0
    total_statistical_capacity = 0
    location_types = defaultdict(int)
    
    # Generate stop name
    stop_name = generate_stop_name(stop_index, stop_coords, nearby_locations, total_stops)
    
    stop_passengers = {
        'stop_id': stop_index,
        'stop_name': stop_name,
        'coordinates': stop_coords,
        'distance_from_previous': stop_info.get('distance_from_previous', 0.0),
        'cumulative_distance': stop_info.get('cumulative_distance', 0.0),
        'nearby_locations': len(nearby_locations),
        'passenger_sources': []
    }
    
    for location in nearby_locations:
        # Fix: Use the correct key names from the statistical model
        capacity = location.get('passenger_capacity', 0)  # Fixed key name
        statistical_capacity = location.get('passenger_capacity', capacity)  # Use same real data
        location_type = location.get('category', location.get('type', 'unknown'))
        
        # Note: All locations in the statistical model have passenger_capacity > 0
        # No fallback logic needed - the statistical model generation is complete
        
        # Apply distance decay weighting (closer locations contribute more)
        distance = location.get('distance_to_stop', 0)
        distance_weight = max(0.3, 1.0 - (distance / walking_distance_meters))  # 30-100% weight based on distance
        
        # Apply hourly multiplier based on the time
        hourly_multiplier = get_hourly_multiplier(location, start_hour)
        time_adjusted_capacity = int(statistical_capacity * hourly_multiplier * distance_weight)
        
        total_capacity += capacity if capacity > 0 else statistical_capacity
        total_statistical_capacity += time_adjusted_capacity
        location_types[location_type] += 1
            
        stop_passengers['passenger_sources'].append({
            'location_name': location.get('name', 'Unnamed'),
            'type': location_type,
            'distance': location['distance_to_stop'],
            'distance_weight': distance_weight,
            'base_capacity': capacity,
            'statistical_capacity': statistical_capacity,
            'hourly_multiplier': hourly_multiplier,
            'time_adjusted_capacity': time_adjusted_capacity,
            'hourly_patterns': location.get('hourly_patterns', {}),
            'daily_patterns': location.get('daily_patterns', {}),
            'amenity_weights': location.get('amenity_weights', {})
        })
    
    # Apply GLOBAL passenger demand reduction to match real-world ridership
    total_statistical_capacity = int(total_statistical_capacity * demand_multiplier)
    
    # Ensure minimum passenger distribution to prevent clustering (every 3rd stop gets at least 1 passenger)
    MIN_PASSENGERS_PER_STOP = 1 if (stop_index % 3 == 0 or total_statistical_capacity == 0) else 0
    if total_statistical_capacity == 0 and MIN_PASSENGERS_PER_STOP > 0:
        total_statistical_capacity = MIN_PASSENGERS_PER_STOP
        print(f"   🎯 Stop {stop_index}: Added minimum {MIN_PASSENGERS_PER_STOP} passenger (anti-clustering)")
    
    # Apply realistic maximum capacity limit per stop (prevent extreme outliers)
    MAX_PASSENGERS_PER_STOP_PER_HOUR = 12  # Reasonable limit for busy urban stops
    if total_statistical_capacity > MAX_PASSENGERS_PER_STOP_PER_HOUR:
        print(f"   ⚠️  Stop {stop_index}: Capping {total_statistical_capacity} → {MAX_PASSENGERS_PER_STOP_PER_HOUR} passengers/hour")
        total_statistical_capacity = MAX_PASSENGERS_PER_STOP_PER_HOUR
    
    # Apply time smearing to passenger distribution
    time_distributed_passengers = apply_time_smearing(total_statistical_capacity, start_hour)
    
    # Calculate time period for this stop (1 hour window)
    smear_hours = 1
    end_hour = start_hour + smear_hours
    if end_hour >= 24:
        end_hour -= 24
    
    time_period = {
        'start_time': start_hour,
        'end_time': end_hour,
        'smear_window_hours': smear_hours
    }
    
    stop_passengers.update({
        'total_base_capacity': total_capacity,
        'total_statistical_capacity': total_statistical_capacity,
        'time_distributed_passengers': time_distributed_passengers,
        'passenger_count': len(time_distributed_passengers),
        'location_type_breakdown': dict(location_types),
        'time_period': time_period
    })
    
    return stop_passengers

def generate_route_passenger_summary(route_data, stops, passenger_model, start_hour, walking_distance_meters, demand_multiplier=0.4):
    """Generate comprehensive passenger summary for the entire route with time smearing"""
    
    route_id = route_data.get('short_name', 'Unknown')
    print(f"\n🚀 GENERATING PASSENGER DISTRIBUTION FOR ROUTE {route_id}")
    print("=" * 80)
    
    total_route_distance = stops[-1]['cumulative_distance'] if stops else 0
    
    route_summary = {
        'route_info': {
            'short_name': route_data.get('short_name'),
            'long_name': route_data.get('long_name'),
            'route_type': route_data.get('route_type'),
            'total_stops': len(stops),
            'total_distance_meters': total_route_distance,
            'start_hour': start_hour,
            'walking_distance_meters': walking_distance_meters,
            'generation_date': datetime.now().isoformat()
        },
        'stops': [],
        'route_totals': {
            'total_base_capacity': 0,
            'total_statistical_capacity': 0,
            'total_passenger_count': 0,
            'total_passenger_sources': 0,
            'location_type_totals': defaultdict(int)
        }
    }
    
    # Generate passengers for each stop
    for i, stop_info in enumerate(stops):
        print(f"Processing stop {i+1}/{len(stops)}...", end=" ")
        
        stop_passengers = generate_passengers_for_stop(stop_info, i, passenger_model, start_hour, len(stops), walking_distance_meters, demand_multiplier)
        route_summary['stops'].append(stop_passengers)
        
        # Update route totals
        route_summary['route_totals']['total_base_capacity'] += stop_passengers['total_base_capacity']
        route_summary['route_totals']['total_statistical_capacity'] += stop_passengers['total_statistical_capacity']
        route_summary['route_totals']['total_passenger_count'] += stop_passengers['passenger_count']
        route_summary['route_totals']['total_passenger_sources'] += stop_passengers['nearby_locations']
        
        for loc_type, count in stop_passengers['location_type_breakdown'].items():
            route_summary['route_totals']['location_type_totals'][loc_type] += count
        
        print(f"✅ {stop_passengers['passenger_count']} passengers")
    
    # Convert defaultdict to regular dict for JSON serialization
    route_summary['route_totals']['location_type_totals'] = dict(route_summary['route_totals']['location_type_totals'])
    
    return route_summary

def print_passenger_summary(route_summary):
    """Print a comprehensive passenger summary table"""
    
    print("\n" + "="*100)
    print("🚌 ROUTE 1 PASSENGER DISTRIBUTION SUMMARY")
    print("="*100)
    
    route_info = route_summary['route_info']
    route_totals = route_summary['route_totals']
    
    print(f"Route: {route_info['short_name']} - {route_info['long_name']}")
    print(f"Type: {route_info['route_type']} | Stops: {route_info['total_stops']} | Generated: {route_info['generation_date'][:19]}")
    print()
    
    # Overall statistics
    print("📊 ROUTE TOTALS")
    print("-" * 100)
    print(f"{'Metric':<30} {'Value':<15} {'Details':<50}")
    print("-" * 100)
    print(f"{'Total Stops':<30} {route_info['total_stops']:<15} Stops with minimum 150m spacing")
    print(f"{'Passenger Sources':<30} {route_totals['total_passenger_sources']:<15} Nearby locations generating passengers")
    print(f"{'Base Capacity':<30} {route_totals['total_base_capacity']:,<15} Simple multiplier-based calculation")
    print(f"{'Statistical Capacity':<30} {route_totals['total_statistical_capacity']:,<15} Poisson distribution-enhanced capacity")
    
    enhancement = route_totals['total_statistical_capacity'] - route_totals['total_base_capacity']
    enhancement_pct = (enhancement / route_totals['total_base_capacity'] * 100) if route_totals['total_base_capacity'] > 0 else 0
    enhancement_str = f"{enhancement:+,}"
    print(f"{'Enhancement':<30} {enhancement_str:<15} {enhancement_pct:+.1f}% statistical modeling impact")
    
    avg_per_stop = route_totals['total_statistical_capacity'] / route_info['total_stops'] if route_info['total_stops'] > 0 else 0
    print(f"{'Avg Passengers/Stop':<30} {avg_per_stop:.1f}<15 Mean statistical capacity per stop")
    print()
    
    # Location type breakdown
    print("📍 PASSENGER SOURCES BY TYPE")
    print("-" * 100)
    print(f"{'Location Type':<15} {'Count':<10} {'Percentage':<12} {'Description':<50}")
    print("-" * 100)
    
    total_sources = route_totals['total_passenger_sources']
    for loc_type, count in sorted(route_totals['location_type_totals'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_sources * 100) if total_sources > 0 else 0
        print(f"{loc_type:<15} {count:<10} {pct:<12.1f}% Locations of this type near stops")
    
    print()
    
    # Top 10 stops by passenger capacity
    print("🚏 TOP 10 STOPS BY PASSENGER CAPACITY")
    print("-" * 100)
    print(f"{'Stop #':<8} {'Coordinates':<25} {'Statistical Cap':<15} {'Sources':<10} {'Top Types':<30}")
    print("-" * 100)
    
    sorted_stops = sorted(route_summary['stops'], key=lambda x: x['total_statistical_capacity'], reverse=True)[:10]
    
    for stop in sorted_stops:
        coords = f"({stop['coordinates'][0]:.5f}, {stop['coordinates'][1]:.5f})"
        top_types = ", ".join([f"{t}({c})" for t, c in sorted(stop['location_type_breakdown'].items(), key=lambda x: x[1], reverse=True)[:3]])
        
        print(f"{stop['stop_id']+1:<8} {coords:<25} {stop['total_statistical_capacity']:<15,} {stop['nearby_locations']:<10} {top_types:<30}")
    
    print()
    print("="*100)
    print("✅ ROUTE 1 PASSENGER DISTRIBUTION ANALYSIS COMPLETE")
    print("="*100)

def print_stop_details(stops, summary):
    """Print detailed stop information with proper timed passenger grid"""
    
    # First, print basic stop information
    print(f"\n🚏 STOP INFORMATION")
    print("=" * 120)
    print(f"{'#':<3} {'Stop Name':<40} {'Location':<25} {'Dist':<6} {'Pass':<5}")
    print("-" * 120)
    
    for i, (stop_info, stop_data) in enumerate(zip(stops, summary['stops'])):
        name = stop_data['stop_name']
        if len(name) > 40:
            name = name[:37] + "..."
        
        location = f"({stop_info['coordinates'][0]:.6f}, {stop_info['coordinates'][1]:.6f})"
        distance = f"{stop_info['cumulative_distance']:.0f}m"
        passengers = stop_data['passenger_count']
        
        print(f"{i+1:<3} {name:<40} {location:<25} {distance:<6} {passengers:<5}")
    
    # Now create a detailed passenger time grid clustered in 5-minute intervals
    print(f"\n⏰ PASSENGER ARRIVAL TIME GRID (5-Minute Intervals)")
    print("=" * 120)
    
    # Collect passenger times and cluster them into 5-minute intervals
    all_time_slots = set()
    stop_time_data = {}
    
    for i, (stop_info, stop_data) in enumerate(zip(stops, summary['stops'])):
        passenger_times = stop_data.get('time_distributed_passengers', [])
        time_counts = {}
        
        for time in passenger_times:
            hours = int(time)
            minutes = int((time - hours) * 60)
            # Round down to nearest 5-minute interval
            interval_minutes = (minutes // 5) * 5
            time_key = f"{hours:02d}:{interval_minutes:02d}"
            all_time_slots.add(time_key)
            time_counts[time_key] = time_counts.get(time_key, 0) + 1
        
        stop_time_data[i] = time_counts
    
    if all_time_slots:
        # Sort time slots
        sorted_times = sorted(all_time_slots)
        
        # Print header with time slots
        header = f"{'Stop':<35}"
        for time_slot in sorted_times:
            header += f"{time_slot:<6}"
        header += f"{'Total':<6}"
        print(header)
        print("-" * len(header))
        
        # Print each stop's passenger distribution
        for i, (stop_info, stop_data) in enumerate(zip(stops, summary['stops'])):
            stop_name = stop_data['stop_name']
            if len(stop_name) > 34:
                stop_name = stop_name[:31] + "..."
            
            row = f"{stop_name:<35}"
            total_passengers = 0
            
            for time_slot in sorted_times:
                count = stop_time_data[i].get(time_slot, 0)
                total_passengers += count
                if count > 0:
                    row += f"{count:<6}"
                else:
                    row += f"{'·':<6}"  # Use dot for zero
            
            row += f"{total_passengers:<6}"
            print(row)
        
        # Print totals row
        totals_row = f"{'TOTALS':<35}"
        grand_total = 0
        for time_slot in sorted_times:
            time_total = sum(stop_time_data[i].get(time_slot, 0) for i in range(len(stops)))
            grand_total += time_total
            totals_row += f"{time_total:<6}"
        totals_row += f"{grand_total:<6}"
        print("-" * len(header))
        print(totals_row)
    else:
        print("No passengers generated for any stops.")
    
    print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate passenger distribution for a specific route')
    parser.add_argument('route_id', help='Route ID to generate passengers for (e.g., "1")')
    parser.add_argument('start_hour', type=float, help='Starting hour for passenger time smearing (e.g., 8.0 for 8:00 AM)')
    
    args = parser.parse_args()
    
    print(f"🚌 Route {args.route_id} Passenger Distribution Generator")
    print(f"⏰ Start Hour: {args.start_hour}:00")
    
    # Load configuration
    config = load_config()
    walking_distance_meters = config['walking_distance_meters']
    passenger_demand_multiplier = config['passenger_demand_multiplier']
    
    print("Loading statistical passenger model...")
    
    # Load the passenger model
    passenger_model = load_statistical_passenger_model()
    if not passenger_model:
        print("❌ Could not load passenger model")
        return
    
    # Fetch route data
    print(f"📍 Fetching route {args.route_id} data from API...")
    route_data, geometry_data = fetch_route_data(args.route_id)
    if not route_data or not geometry_data:
        print("❌ Failed to fetch route data")
        return
    
    # Convert geometry to coordinate points
    route_points = convert_geometry_to_lat_lng(geometry_data)
    if not route_points:
        print("❌ No valid route geometry found")
        return
    
    # Generate stops along the route
    print("🎯 Generating stops with Poisson distribution...")
    stops = generate_stops_with_spacing(route_points)
    print(f"Generated {len(stops)} stops with minimum 150m spacing")
    
    # Generate passenger summary
    summary = generate_route_passenger_summary(route_data, stops, passenger_model, args.start_hour, walking_distance_meters, passenger_demand_multiplier)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"route_{args.route_id}_passenger_distribution_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print detailed stop listing
    print_stop_details(stops, summary)
    
    print(f"\n� ROUTE SUMMARY")
    print("=" * 80)
    print(f"Route: {summary['route_info']['short_name']} - {summary['route_info']['long_name']}")
    print(f"Total Stops: {summary['route_info']['total_stops']}")
    print(f"Total Distance: {summary['route_info']['total_distance_meters']:.0f}m ({summary['route_info']['total_distance_meters']/1000:.1f}km)")
    print(f"Start Hour: {args.start_hour}:00")
    print(f"🔧 Passenger Demand Multiplier: {passenger_demand_multiplier} ({int((1-passenger_demand_multiplier)*100)}% reduction for realistic ridership)")
    print(f"🚶 Walking Distance: {summary['route_info']['walking_distance_meters']}m")
    print(f"Base Capacity: {summary['route_totals']['total_base_capacity']:,}")
    print(f"Statistical Capacity: {summary['route_totals']['total_statistical_capacity']:,}")
    print(f"Total Passengers Generated: {summary['route_totals']['total_passenger_count']:,}")
    print(f"Passenger Sources: {summary['route_totals']['total_passenger_sources']:,}")
    print(f"\nLocation Type Breakdown:")
    for loc_type, count in summary['route_totals']['location_type_totals'].items():
        print(f"  {loc_type}: {count}")
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main()