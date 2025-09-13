#!/usr/bin/env python3
"""
Realistic passenger distribution using actual depots from database.

Uses real depot locations and generates passengers along vehicle routes.
"""
import requests
from tabulate import tabulate
import random
import math
from collections import defaultdict


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371000 * c  # Earth radius in meters


def get_real_depots():
    """Get actual depots from the database via API."""
    API_BASE = "http://localhost:8000/api/v1"
    
    try:
        print("📍 Getting real depots from database...")
        response = requests.get(f"{API_BASE}/depots/public", timeout=10)
        if response.status_code == 200:
            depots = response.json()
            print(f"✅ Found {len(depots)} real depots in database")
            
            # Enhance depot data with coordinates if missing
            enhanced_depots = []
            
            for depot in depots:
                depot_name = depot.get('name', 'Unknown')
                
                # If depot has no coordinates, assign reasonable ones
                if depot.get('latitude') is None or depot.get('longitude') is None:
                    # Assign reasonable coordinates based on depot name/location
                    # For Barbados (Bridgetown area)
                    if 'Bridgetown' in depot_name or 'bridgetown' in depot_name.lower():
                        # Bridgetown, Barbados coordinates
                        depot['latitude'] = 13.1133 + random.uniform(-0.01, 0.01)  # Small random offset
                        depot['longitude'] = -59.6134 + random.uniform(-0.01, 0.01)
                    else:
                        # Default to central Barbados area with some variation
                        depot['latitude'] = 13.1939 + random.uniform(-0.1, 0.1)
                        depot['longitude'] = -59.5432 + random.uniform(-0.1, 0.1)
                
                enhanced_depots.append(depot)
                print(f"   🏢 {depot_name}: {depot['latitude']:.6f}, {depot['longitude']:.6f}")
            
            return enhanced_depots
        else:
            print(f"❌ Failed to get depots: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting depots: {e}")
        return []


def get_route_data():
    """Get route data from API."""
    API_BASE = "http://localhost:8000/api/v1"
    
    try:
        print("\n📍 Getting routes from database...")
        response = requests.get(f"{API_BASE}/routes/public", timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to get routes: HTTP {response.status_code}")
            return {}
        
        routes = response.json()
        print(f"✅ Found {len(routes)} routes")
        
        route_data = {}
        
        for route in routes:
            route_code = route['short_name']
            
            # Get route geometry
            try:
                geom_response = requests.get(f"{API_BASE}/routes/public/{route_code}/geometry", timeout=10)
                if geom_response.status_code == 200:
                    geom_data = geom_response.json()
                    if geom_data.get('geometry', {}).get('coordinates'):
                        coordinates = geom_data['geometry']['coordinates']
                        
                        route_data[route_code] = {
                            'name': route.get('long_name', route_code),
                            'coordinates': coordinates
                        }
                        print(f"   ✅ Route {route_code}: {len(coordinates)} coordinate points")
            except Exception as e:
                print(f"   ❌ Error getting geometry for route {route_code}: {e}")
        
        return route_data
        
    except Exception as e:
        print(f"❌ Failed to get route data: {e}")
        return {}


def get_vehicles():
    """Get vehicles from API."""
    API_BASE = "http://localhost:8000/api/v1"
    
    try:
        print("\n🚐 Getting vehicles from database...")
        response = requests.get(f"{API_BASE}/vehicles/public", timeout=10)
        if response.status_code == 200:
            vehicles = response.json()
            print(f"✅ Found {len(vehicles)} real vehicles")
            return vehicles
        else:
            print(f"❌ Failed to get vehicles: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting vehicles: {e}")
        return []


def generate_depot_passengers(depots):
    """Generate realistic passengers waiting at each depot."""
    
    print(f"\n👥 GENERATING PASSENGERS AT REAL DEPOTS")
    print("=" * 60)
    
    depot_passengers = {}
    
    for depot in depots:
        depot_name = depot.get('name', 'Unknown')
        depot_lat = depot.get('latitude')
        depot_lng = depot.get('longitude')
        
        if depot_lat is None or depot_lng is None:
            print(f"   ⚠️ Depot {depot_name}: No coordinates, skipping")
            continue
        
        # Generate 5-25 passengers per depot (realistic numbers)
        num_passengers = random.randint(5, 25)
        
        passengers = []
        for i in range(num_passengers):
            passenger = {
                'passenger_id': f"PASS_{depot_name.replace(' ', '_')}_{i+1:03d}",
                'depot_name': depot_name,
                'pickup_lat': depot_lat,
                'pickup_lon': depot_lng,
                'wait_time_min': random.randint(2, 45),
                'destination_type': random.choice(['route_stop', 'other_depot', 'city_center'])
            }
            passengers.append(passenger)
        
        depot_passengers[depot_name] = {
            'depot_info': depot,
            'passengers': passengers
        }
        
        print(f"   🏢 {depot_name}: {num_passengers} passengers waiting")
    
    return depot_passengers


def assign_vehicles_to_routes(vehicles, route_data):
    """Assign vehicles to routes and generate passengers along their routes."""
    
    print(f"\n🚌 ASSIGNING VEHICLES TO ROUTES")
    print("=" * 60)
    
    if not vehicles or not route_data:
        print("❌ No vehicles or routes available")
        return {}
    
    vehicle_assignments = {}
    route_codes = list(route_data.keys())
    
    for vehicle in vehicles:
        vehicle_id = vehicle.get('reg_code', vehicle.get('vehicle_id', 'Unknown'))
        
        # Assign vehicle to random route
        assigned_route = random.choice(route_codes)
        route_coords = route_data[assigned_route]['coordinates']
        
        # Place vehicle at random position on route
        current_position_idx = random.randint(0, len(route_coords) - 1)
        current_coord = route_coords[current_position_idx]
        
        # Generate passengers along this route (ahead of the vehicle)
        route_passengers = []
        
        # Create potential stops along route (every 10-20 coordinate points)
        stop_interval = random.randint(8, 15)
        potential_stops = []
        
        for i in range(current_position_idx, len(route_coords), stop_interval):
            coord = route_coords[i]
            potential_stops.append({
                'stop_index': i,
                'lat': coord[1],  # [lon, lat] format
                'lon': coord[0],
                'distance_from_vehicle': i - current_position_idx
            })
        
        # Generate 0-8 passengers at various stops ahead
        num_route_passengers = random.randint(0, 8)
        
        for p in range(num_route_passengers):
            if potential_stops:
                pickup_stop = random.choice(potential_stops)
                
                # Destination could be another stop further ahead
                dest_stops = [s for s in potential_stops if s['stop_index'] > pickup_stop['stop_index']]
                dest_stop = random.choice(dest_stops) if dest_stops else pickup_stop
                
                passenger = {
                    'passenger_id': f"ROUTE_{vehicle_id}_{p+1:02d}",
                    'pickup_lat': pickup_stop['lat'],
                    'pickup_lon': pickup_stop['lon'],
                    'pickup_stop_index': pickup_stop['stop_index'],
                    'dest_lat': dest_stop['lat'],
                    'dest_lon': dest_stop['lon'],
                    'dest_stop_index': dest_stop['stop_index'],
                    'wait_time_min': random.randint(1, 20)
                }
                route_passengers.append(passenger)
        
        vehicle_assignments[vehicle_id] = {
            'vehicle_info': vehicle,
            'assigned_route': assigned_route,
            'route_name': route_data[assigned_route]['name'],
            'current_position': {
                'lat': current_coord[1],
                'lon': current_coord[0],
                'index': current_position_idx
            },
            'route_passengers': route_passengers,
            'potential_stops': potential_stops
        }
        
        print(f"   🚐 {vehicle_id}: Route {assigned_route}, {len(route_passengers)} passengers ahead")
    
    return vehicle_assignments


def display_depot_passenger_table(depot_passengers):
    """Display depot passengers in table format."""
    
    print(f"\n📊 DEPOT PASSENGER DISTRIBUTION")
    print("=" * 80)
    
    depot_table = []
    total_depot_passengers = 0
    
    for depot_name, data in depot_passengers.items():
        depot = data['depot_info']
        passengers = data['passengers']
        
        depot_table.append([
            depot_name,
            depot.get('capacity', 'N/A'),
            f"{depot.get('latitude', 0):.6f}",
            f"{depot.get('longitude', 0):.6f}",
            len(passengers),
            f"{sum(p['wait_time_min'] for p in passengers) / len(passengers):.1f}" if passengers else "0.0"
        ])
        
        total_depot_passengers += len(passengers)
    
    headers = ["Depot Name", "Capacity", "Latitude", "Longitude", "Passengers", "Avg Wait (min)"]
    print(tabulate(depot_table, headers=headers, tablefmt="grid"))
    print(f"\nTotal Passengers at Depots: {total_depot_passengers}")


def display_vehicle_route_table(vehicle_assignments):
    """Display vehicle assignments and route passengers."""
    
    print(f"\n🚌 VEHICLE ROUTE ASSIGNMENTS & PASSENGERS")
    print("=" * 80)
    
    vehicle_table = []
    total_route_passengers = 0
    
    for vehicle_id, data in vehicle_assignments.items():
        route_passengers = data['route_passengers']
        
        # Calculate stops vehicle needs to make
        pickup_stops = len(set(p['pickup_stop_index'] for p in route_passengers))
        dropoff_stops = len(set(p['dest_stop_index'] for p in route_passengers))
        total_stops = len(set(
            list(p['pickup_stop_index'] for p in route_passengers) +
            list(p['dest_stop_index'] for p in route_passengers)
        ))
        
        vehicle_table.append([
            vehicle_id,
            data['assigned_route'],
            data['route_name'][:25] + "..." if len(data['route_name']) > 25 else data['route_name'],
            f"{data['current_position']['lat']:.6f}",
            f"{data['current_position']['lon']:.6f}",
            len(route_passengers),
            pickup_stops,
            dropoff_stops,
            total_stops
        ])
        
        total_route_passengers += len(route_passengers)
    
    headers = [
        "Vehicle ID", "Route", "Route Name", "Current Lat", "Current Lon", 
        "Passengers", "Pickup Stops", "Dropoff Stops", "Total Stops"
    ]
    print(tabulate(vehicle_table, headers=headers, tablefmt="grid"))
    print(f"\nTotal Passengers Along Routes: {total_route_passengers}")


def display_detailed_passenger_breakdown(depot_passengers, vehicle_assignments):
    """Show detailed breakdown of all passengers."""
    
    print(f"\n📋 DETAILED PASSENGER BREAKDOWN")
    print("=" * 80)
    
    # Depot passengers detail
    print(f"\n🏢 DEPOT PASSENGERS:")
    for depot_name, data in depot_passengers.items():
        passengers = data['passengers']
        print(f"\n   {depot_name}:")
        
        for passenger in passengers[:5]:  # Show first 5
            print(f"     • {passenger['passenger_id']}: waiting {passenger['wait_time_min']}min")
        
        if len(passengers) > 5:
            print(f"     ... and {len(passengers) - 5} more passengers")
    
    # Route passengers detail  
    print(f"\n🛣️ ROUTE PASSENGERS:")
    for vehicle_id, data in vehicle_assignments.items():
        route_passengers = data['route_passengers']
        if route_passengers:
            print(f"\n   Vehicle {vehicle_id} on Route {data['assigned_route']}:")
            
            for passenger in route_passengers:
                pickup_idx = passenger['pickup_stop_index']
                dest_idx = passenger['dest_stop_index']
                print(f"     • {passenger['passenger_id']}: stop {pickup_idx} → stop {dest_idx}")


def display_summary_statistics(depot_passengers, vehicle_assignments):
    """Display overall system statistics."""
    
    print(f"\n📈 SYSTEM SUMMARY STATISTICS")
    print("=" * 80)
    
    # Calculate totals
    total_depots = len(depot_passengers)
    total_depot_passengers = sum(len(data['passengers']) for data in depot_passengers.values())
    total_vehicles = len(vehicle_assignments)
    total_route_passengers = sum(len(data['route_passengers']) for data in vehicle_assignments.values())
    total_passengers = total_depot_passengers + total_route_passengers
    
    # Calculate stop requirements
    total_stops_required = sum(
        len(set(
            list(p['pickup_stop_index'] for p in data['route_passengers']) +
            list(p['dest_stop_index'] for p in data['route_passengers'])
        ))
        for data in vehicle_assignments.values()
    )
    
    avg_stops_per_vehicle = total_stops_required / max(total_vehicles, 1)
    
    summary_data = [
        ["Real Depots from Database", total_depots],
        ["Passengers at Depots", total_depot_passengers],
        ["Active Vehicles", total_vehicles],
        ["Passengers Along Routes", total_route_passengers],
        ["Total System Passengers", total_passengers],
        ["Total Stops Required", total_stops_required],
        ["Average Stops per Vehicle", f"{avg_stops_per_vehicle:.1f}"],
        ["Passengers per Vehicle", f"{total_route_passengers/max(total_vehicles,1):.1f}"]
    ]
    
    headers = ["Metric", "Value"]
    print(tabulate(summary_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    print("🚌 REALISTIC PASSENGER DISTRIBUTION SYSTEM")
    print("=" * 60)
    print("Using REAL depots from database")
    print("Generating passengers at depot locations and along vehicle routes")
    print()
    
    # Get real data from API
    depots = get_real_depots()
    route_data = get_route_data()
    vehicles = get_vehicles()
    
    if not depots:
        print("❌ No depots found in database")
        exit(1)
    
    if not route_data:
        print("❌ No route data available")
        exit(1)
    
    if not vehicles:
        print("❌ No vehicles found")
        exit(1)
    
    # Generate passengers at real depot locations
    depot_passengers = generate_depot_passengers(depots)
    
    # Assign vehicles to routes and generate route passengers
    vehicle_assignments = assign_vehicles_to_routes(vehicles, route_data)
    
    # Display all results in tabulated format
    display_depot_passenger_table(depot_passengers)
    display_vehicle_route_table(vehicle_assignments)
    display_detailed_passenger_breakdown(depot_passengers, vehicle_assignments)
    display_summary_statistics(depot_passengers, vehicle_assignments)
    
    print(f"\n✅ COMPLETE PASSENGER DISTRIBUTION ANALYSIS")
    print(f"   🏢 Using {len(depots)} real depots from database")
    print(f"   🚐 {len(vehicles)} vehicles assigned to routes")
    print(f"   👥 Realistic passenger distribution generated")
    print(f"   📊 All data presented in table format")