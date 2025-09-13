#!/usr/bin/env python3
"""
Detailed passenger distribution along routes with stop-by-stop analysis.

Shows exactly where passengers are waiting and how many stops vehicles need to make.
"""
import requests
from tabulate import tabulate
import random
import math
from collections import defaultdict


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on earth in meters."""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r


def create_route_stops(coordinates, stop_distance_meters=500):
    """Create evenly spaced stops along a route."""
    if len(coordinates) < 2:
        return []
    
    stops = []
    current_distance = 0
    stop_id = 1
    
    # Always add the first point as a stop
    stops.append({
        'stop_id': f"STOP_{stop_id:03d}",
        'lat': coordinates[0][1],  # coordinates are [lon, lat]
        'lon': coordinates[0][0],
        'distance_from_start': 0,
        'segment_index': 0
    })
    stop_id += 1
    
    # Process each segment of the route
    for i in range(1, len(coordinates)):
        prev_coord = coordinates[i-1]  # [lon, lat]
        curr_coord = coordinates[i]    # [lon, lat]
        
        segment_distance = haversine_distance(
            prev_coord[1], prev_coord[0],  # lat, lon
            curr_coord[1], curr_coord[0]   # lat, lon
        )
        
        # Check if we need to add stops in this segment
        segment_start_distance = current_distance
        while current_distance + stop_distance_meters < segment_start_distance + segment_distance:
            current_distance += stop_distance_meters
            
            # Calculate position along this segment
            progress = (current_distance - segment_start_distance) / segment_distance
            
            # Interpolate position
            stop_lat = prev_coord[1] + (curr_coord[1] - prev_coord[1]) * progress
            stop_lon = prev_coord[0] + (curr_coord[0] - prev_coord[0]) * progress
            
            stops.append({
                'stop_id': f"STOP_{stop_id:03d}",
                'lat': stop_lat,
                'lon': stop_lon,
                'distance_from_start': current_distance,
                'segment_index': i-1
            })
            stop_id += 1
        
        current_distance = segment_start_distance + segment_distance
    
    # Always add the last point as a stop
    stops.append({
        'stop_id': f"STOP_{stop_id:03d}",
        'lat': coordinates[-1][1],
        'lon': coordinates[-1][0],
        'distance_from_start': current_distance,
        'segment_index': len(coordinates)-2
    })
    
    return stops


def assign_passengers_to_stops(stops, num_passengers):
    """Assign passengers to stops with realistic distribution."""
    if not stops or num_passengers == 0:
        return []
    
    passengers = []
    
    for i in range(num_passengers):
        # Pick random pickup and dropoff stops
        pickup_stop = random.choice(stops)
        
        # Dropoff should be different from pickup
        dropoff_candidates = [s for s in stops if s['stop_id'] != pickup_stop['stop_id']]
        dropoff_stop = random.choice(dropoff_candidates) if dropoff_candidates else pickup_stop
        
        passenger = {
            'passenger_id': f"PASS_{random.randint(1000, 9999)}",
            'pickup_stop': pickup_stop['stop_id'],
            'pickup_lat': pickup_stop['lat'],
            'pickup_lon': pickup_stop['lon'],
            'dropoff_stop': dropoff_stop['stop_id'],
            'dropoff_lat': dropoff_stop['lat'],
            'dropoff_lon': dropoff_stop['lon'],
            'wait_time_min': random.randint(1, 30)
        }
        passengers.append(passenger)
    
    return passengers


def get_route_data():
    """Get route data from API."""
    API_BASE = "http://localhost:8000/api/v1"
    
    print("🚌 FETCHING ROUTE DATA FOR PASSENGER DISTRIBUTION")
    print("=" * 60)
    
    try:
        # Get routes
        response = requests.get(f"{API_BASE}/routes/public", timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to get routes: HTTP {response.status_code}")
            return {}
        
        routes = response.json()
        print(f"✅ Found {len(routes)} routes")
        
        route_data = {}
        
        for route in routes:
            route_code = route['short_name']
            print(f"\n📍 Processing Route {route_code}...")
            
            # Get route geometry
            try:
                geom_response = requests.get(f"{API_BASE}/routes/public/{route_code}/geometry", timeout=10)
                if geom_response.status_code == 200:
                    geom_data = geom_response.json()
                    if geom_data.get('geometry', {}).get('coordinates'):
                        coordinates = geom_data['geometry']['coordinates']
                        
                        # Create stops along the route (every 500m)
                        stops = create_route_stops(coordinates, stop_distance_meters=500)
                        
                        # Generate passengers for this route (random 10-50)
                        num_passengers = random.randint(10, 50)
                        passengers = assign_passengers_to_stops(stops, num_passengers)
                        
                        route_data[route_code] = {
                            'name': route.get('long_name', route_code),
                            'coordinates': coordinates,
                            'stops': stops,
                            'passengers': passengers,
                            'total_distance_km': stops[-1]['distance_from_start'] / 1000 if stops else 0
                        }
                        
                        print(f"   ✅ Created {len(stops)} stops, {len(passengers)} passengers")
                        print(f"   📏 Total route distance: {route_data[route_code]['total_distance_km']:.1f} km")
                    else:
                        print(f"   ⚠️ No geometry data for route {route_code}")
                else:
                    print(f"   ❌ Failed to get geometry: HTTP {geom_response.status_code}")
            except Exception as e:
                print(f"   ❌ Error processing route {route_code}: {e}")
        
        return route_data
        
    except Exception as e:
        print(f"❌ Failed to get route data: {e}")
        return {}


def analyze_stop_activity(route_data):
    """Analyze passenger activity at each stop."""
    
    print(f"\n🚏 DETAILED STOP-BY-STOP PASSENGER ANALYSIS")
    print("=" * 80)
    
    for route_code, data in route_data.items():
        print(f"\n📍 ROUTE {route_code}: {data['name']}")
        print("-" * 60)
        
        stops = data['stops']
        passengers = data['passengers']
        
        # Count pickup and dropoff at each stop
        stop_activity = defaultdict(lambda: {'pickups': 0, 'dropoffs': 0, 'passengers': []})
        
        for passenger in passengers:
            pickup_stop = passenger['pickup_stop']
            dropoff_stop = passenger['dropoff_stop']
            
            stop_activity[pickup_stop]['pickups'] += 1
            stop_activity[pickup_stop]['passengers'].append(f"{passenger['passenger_id']} (P)")
            
            stop_activity[dropoff_stop]['dropoffs'] += 1
            stop_activity[dropoff_stop]['passengers'].append(f"{passenger['passenger_id']} (D)")
        
        # Create table for this route
        stop_table = []
        total_pickups = 0
        total_dropoffs = 0
        active_stops = 0
        
        for stop in stops:
            stop_id = stop['stop_id']
            activity = stop_activity[stop_id]
            
            pickups = activity['pickups']
            dropoffs = activity['dropoffs']
            total_activity = pickups + dropoffs
            
            if total_activity > 0:
                active_stops += 1
            
            total_pickups += pickups
            total_dropoffs += dropoffs
            
            stop_table.append([
                stop_id,
                f"{stop['lat']:.6f}",
                f"{stop['lon']:.6f}",
                f"{stop['distance_from_start']/1000:.2f}",
                pickups,
                dropoffs,
                total_activity,
                "🚏" if total_activity > 0 else "⚪"
            ])
        
        headers = ["Stop ID", "Latitude", "Longitude", "Distance (km)", "Pickups", "Dropoffs", "Total", "Status"]
        print(tabulate(stop_table, headers=headers, tablefmt="grid"))
        
        # Route summary
        print(f"\n📊 Route {route_code} Summary:")
        print(f"   Total Stops: {len(stops)}")
        print(f"   Active Stops (with passengers): {active_stops}")
        print(f"   Vehicle Stops Required: {active_stops}")
        print(f"   Total Pickups: {total_pickups}")
        print(f"   Total Dropoffs: {total_dropoffs}")
        print(f"   Route Distance: {data['total_distance_km']:.1f} km")
        print(f"   Average Stop Spacing: {data['total_distance_km']/len(stops)*1000:.0f}m")


def analyze_vehicle_requirements(route_data):
    """Analyze vehicle requirements for each route."""
    
    print(f"\n🚐 VEHICLE STOP REQUIREMENTS ANALYSIS")
    print("=" * 80)
    
    vehicle_table = []
    
    for route_code, data in route_data.items():
        passengers = data['passengers']
        stops = data['stops']
        
        # Count active stops (stops with passenger activity)
        stop_activity = defaultdict(int)
        for passenger in passengers:
            stop_activity[passenger['pickup_stop']] += 1
            stop_activity[passenger['dropoff_stop']] += 1
        
        active_stops = len([stop for stop, activity in stop_activity.items() if activity > 0])
        
        # Calculate efficiency metrics
        total_passengers = len(passengers)
        passengers_per_stop = total_passengers / max(active_stops, 1)
        
        # Estimate trip time (assuming 2 minutes per stop + travel time)
        stop_time_minutes = active_stops * 2
        travel_time_minutes = data['total_distance_km'] * 2  # Assume 30 km/h average speed
        total_trip_time = stop_time_minutes + travel_time_minutes
        
        vehicle_table.append([
            route_code,
            data['name'],
            len(stops),
            active_stops,
            total_passengers,
            f"{passengers_per_stop:.1f}",
            f"{data['total_distance_km']:.1f}",
            f"{total_trip_time:.0f}",
            f"{60/max(total_trip_time/60, 0.1):.1f}"  # Trips per hour
        ])
    
    headers = [
        "Route", "Name", "Total Stops", "Active Stops", 
        "Passengers", "Pass/Stop", "Distance (km)", 
        "Trip Time (min)", "Trips/Hour"
    ]
    print(tabulate(vehicle_table, headers=headers, tablefmt="grid"))
    
    # Overall system summary
    total_active_stops = sum(len([stop for stop in route_data[route]['stops'] 
                                 if any(p['pickup_stop'] == stop['stop_id'] or p['dropoff_stop'] == stop['stop_id'] 
                                       for p in route_data[route]['passengers'])]) 
                            for route in route_data)
    total_passengers = sum(len(route_data[route]['passengers']) for route in route_data)
    
    print(f"\n📈 SYSTEM TOTALS:")
    print(f"   Routes: {len(route_data)}")
    print(f"   Total Active Stops: {total_active_stops}")
    print(f"   Total Passengers: {total_passengers}")
    print(f"   Average Active Stops per Route: {total_active_stops/max(len(route_data),1):.1f}")
    print(f"   Average Passengers per Route: {total_passengers/max(len(route_data),1):.1f}")


if __name__ == "__main__":
    # Get route data from API
    route_data = get_route_data()
    
    if route_data:
        # Show detailed stop-by-stop analysis
        analyze_stop_activity(route_data)
        
        # Show vehicle requirements
        analyze_vehicle_requirements(route_data)
        
        print(f"\n💡 This analysis shows:")
        print(f"   ✅ Exact stops where vehicles need to stop")
        print(f"   ✅ Number of pickups and dropoffs at each stop")
        print(f"   ✅ Total stops required per vehicle per route")
        print(f"   ✅ Estimated trip times and service frequency")
        print(f"   🚌 Use 'Active Stops' to see how many stops each vehicle makes")
    else:
        print("❌ Could not get route data from API")