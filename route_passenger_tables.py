#!/usr/bin/env python3
"""
Route-centric passenger table showing passengers per route in columns.

Each route gets its own column with all passengers in that route.
"""
import requests
from tabulate import tabulate
import random
import math
from collections import defaultdict


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371000 * c  # Earth radius in meters


def get_api_data():
    """Get data from API endpoints."""
    API_BASE = "http://localhost:8000/api/v1"
    
    print("🚌 FETCHING DATA FROM API")
    print("=" * 50)
    
    # Get depots
    try:
        response = requests.get(f"{API_BASE}/depots/public", timeout=10)
        depots = response.json() if response.status_code == 200 else []
        print(f"✅ Found {len(depots)} depots")
    except:
        depots = []
        print("❌ Failed to get depots")
    
    # Get routes
    try:
        response = requests.get(f"{API_BASE}/routes/public", timeout=10)
        routes_data = response.json() if response.status_code == 200 else []
        print(f"✅ Found {len(routes_data)} routes")
        
        # Get route geometry
        routes = {}
        for route in routes_data:
            route_code = route['short_name']
            try:
                geom_response = requests.get(f"{API_BASE}/routes/public/{route_code}/geometry", timeout=10)
                if geom_response.status_code == 200:
                    geom_data = geom_response.json()
                    if geom_data.get('geometry', {}).get('coordinates'):
                        routes[route_code] = {
                            'name': route.get('long_name', route_code),
                            'coordinates': geom_data['geometry']['coordinates']
                        }
                        print(f"   ✅ Route {route_code}: {len(routes[route_code]['coordinates'])} points")
            except:
                pass
    except:
        routes = {}
        print("❌ Failed to get routes")
    
    # Get vehicles
    try:
        response = requests.get(f"{API_BASE}/vehicles/public", timeout=10)
        vehicles = response.json() if response.status_code == 200 else []
        print(f"✅ Found {len(vehicles)} vehicles")
    except:
        vehicles = []
        print("❌ Failed to get vehicles")
    
    return depots, routes, vehicles


def enhance_depots_with_coordinates(depots):
    """Add coordinates to depots that don't have them."""
    enhanced_depots = []
    
    for depot in depots:
        depot_name = depot.get('name', 'Unknown')
        
        if depot.get('latitude') is None or depot.get('longitude') is None:
            # Assign reasonable coordinates for Barbados
            if 'Bridgetown' in depot_name or 'bridgetown' in depot_name.lower():
                depot['latitude'] = 13.1133 + random.uniform(-0.01, 0.01)
                depot['longitude'] = -59.6134 + random.uniform(-0.01, 0.01)
            else:
                depot['latitude'] = 13.1939 + random.uniform(-0.1, 0.1)
                depot['longitude'] = -59.5432 + random.uniform(-0.1, 0.1)
        
        enhanced_depots.append(depot)
    
    return enhanced_depots


def create_route_passengers(routes, vehicles, depots):
    """Create passengers organized by route."""
    print(f"\n👥 GENERATING PASSENGERS BY ROUTE")
    print("=" * 50)
    
    route_passengers = {}
    route_vehicles = defaultdict(list)
    
    # Assign vehicles to routes
    for vehicle in vehicles:
        vehicle_id = vehicle.get('reg_code', vehicle.get('vehicle_id', 'Unknown'))
        assigned_route = random.choice(list(routes.keys()))
        route_vehicles[assigned_route].append(vehicle_id)
    
    # Generate passengers for each route
    for route_code, route_data in routes.items():
        route_name = route_data['name']
        coordinates = route_data['coordinates']
        assigned_vehicles = route_vehicles[route_code]
        
        print(f"\n📍 Route {route_code} ({route_name})")
        print(f"   Vehicles: {', '.join(assigned_vehicles)}")
        
        passengers = []
        
        # Generate depot passengers for this route
        for depot in depots:
            depot_name = depot.get('name', 'Unknown')
            
            # Generate 15-35 passengers per depot per route (much more generous)
            # This means each depot generates passengers for each route separately
            base_passengers = random.randint(15, 35)
            
            # Add peak hour bonus (simulate rush hour traffic)
            peak_bonus = random.randint(5, 15)  # Extra passengers during peak times
            num_depot_passengers = base_passengers + peak_bonus
            
            for i in range(num_depot_passengers):
                # Random destination along the route
                dest_coord = random.choice(coordinates)
                
                passenger = {
                    'id': f"DEPOT_{depot_name.replace(' ', '_')}_{i+1:02d}",
                    'type': 'depot_pickup',
                    'origin': depot_name,
                    'origin_lat': depot.get('latitude'),
                    'origin_lon': depot.get('longitude'),
                    'dest_lat': dest_coord[1],  # [lon, lat] format
                    'dest_lon': dest_coord[0],
                    'wait_time': random.randint(5, 30),
                    'vehicle': random.choice(assigned_vehicles) if assigned_vehicles else 'N/A'
                }
                passengers.append(passenger)
        
        # Generate route passengers (people waiting at stops along the route)
        num_route_stops = len(coordinates) // 12  # Stop every ~12 coordinate points (more stops)
        
        for stop_idx in range(0, len(coordinates), 12):
            if stop_idx >= len(coordinates):
                break
            
            stop_coord = coordinates[stop_idx]
            
            # Generate 2-12 passengers at this stop (much more generous)
            base_stop_passengers = random.randint(2, 12)
            
            # Add random busy stop bonus for popular stops
            if random.random() < 0.3:  # 30% chance of busy stop
                busy_bonus = random.randint(3, 8)
                num_stop_passengers = base_stop_passengers + busy_bonus
            else:
                num_stop_passengers = base_stop_passengers
            
            for i in range(num_stop_passengers):
                # Destination is further along the route (longer trips)
                dest_idx = min(stop_idx + random.randint(12, 80), len(coordinates) - 1)
                dest_coord = coordinates[dest_idx]
                
                passenger = {
                    'id': f"STOP_{route_code}_{stop_idx:03d}_{i+1:02d}",
                    'type': 'route_pickup',
                    'origin': f"Stop {stop_idx//15 + 1}",
                    'origin_lat': stop_coord[1],
                    'origin_lon': stop_coord[0],
                    'dest_lat': dest_coord[1],
                    'dest_lon': dest_coord[0],
                    'wait_time': random.randint(1, 15),
                    'vehicle': random.choice(assigned_vehicles) if assigned_vehicles else 'N/A'
                }
                passengers.append(passenger)
        
        route_passengers[route_code] = {
            'route_name': route_name,
            'vehicles': assigned_vehicles,
            'passengers': passengers
        }
        
        print(f"   Passengers: {len(passengers)} total")
        print(f"   - Depot pickups: {len([p for p in passengers if p['type'] == 'depot_pickup'])}")
        print(f"   - Route pickups: {len([p for p in passengers if p['type'] == 'route_pickup'])}")
    
    return route_passengers


def display_route_passenger_table(route_passengers):
    """Display passengers organized by route in table format."""
    print(f"\n📊 PASSENGERS BY ROUTE - TABLE VIEW")
    print("=" * 100)
    
    # Get all route codes
    route_codes = list(route_passengers.keys())
    
    if not route_codes:
        print("❌ No routes with passengers found")
        return
    
    # Find the maximum number of passengers in any route
    max_passengers = max(len(data['passengers']) for data in route_passengers.values())
    
    # Create table data
    table_data = []
    
    for row_idx in range(max_passengers):
        row = []
        
        for route_code in route_codes:
            passengers = route_passengers[route_code]['passengers']
            
            if row_idx < len(passengers):
                passenger = passengers[row_idx]
                cell_content = f"{passenger['id']}\n({passenger['type'][:5]})\n{passenger['origin'][:12]}\nVeh: {passenger['vehicle'][:6]}\nWait: {passenger['wait_time']}min"
            else:
                cell_content = ""
            
            row.append(cell_content)
        
        table_data.append(row)
    
    # Create headers with route info
    headers = []
    for route_code in route_codes:
        route_name = route_passengers[route_code]['route_name'][:15]
        vehicle_count = len(route_passengers[route_code]['vehicles'])
        passenger_count = len(route_passengers[route_code]['passengers'])
        
        header = f"ROUTE {route_code}\n{route_name}\n{vehicle_count} vehicles\n{passenger_count} passengers"
        headers.append(header)
    
    # Display table
    print(tabulate(table_data, headers=headers, tablefmt="grid", stralign="left"))


def display_route_summary_table(route_passengers):
    """Display summary statistics for each route."""
    print(f"\n📈 ROUTE SUMMARY STATISTICS")
    print("=" * 80)
    
    summary_data = []
    total_passengers = 0
    total_vehicles = 0
    
    for route_code, data in route_passengers.items():
        passengers = data['passengers']
        vehicles = data['vehicles']
        
        depot_passengers = len([p for p in passengers if p['type'] == 'depot_pickup'])
        route_passengers_count = len([p for p in passengers if p['type'] == 'route_pickup'])
        avg_wait = sum(p['wait_time'] for p in passengers) / len(passengers) if passengers else 0
        
        summary_data.append([
            route_code,
            data['route_name'][:20],
            len(vehicles),
            len(passengers),
            depot_passengers,
            route_passengers_count,
            f"{avg_wait:.1f}",
            f"{len(passengers)/len(vehicles):.1f}" if vehicles else "0.0"
        ])
        
        total_passengers += len(passengers)
        total_vehicles += len(vehicles)
    
    headers = [
        "Route", "Name", "Vehicles", "Total Pass.", 
        "Depot Pass.", "Route Pass.", "Avg Wait (min)", "Pass./Vehicle"
    ]
    
    print(tabulate(summary_data, headers=headers, tablefmt="grid"))
    
    print(f"\n🎯 SYSTEM TOTALS:")
    print(f"   Routes: {len(route_passengers)}")
    print(f"   Vehicles: {total_vehicles}")
    print(f"   Total Passengers: {total_passengers}")
    print(f"   Average Passengers per Route: {total_passengers/len(route_passengers):.1f}")
    print(f"   Average Passengers per Vehicle: {total_passengers/total_vehicles:.1f}")


def display_vehicle_assignments(route_passengers):
    """Display which vehicles are assigned to which routes."""
    print(f"\n🚐 VEHICLE ASSIGNMENTS BY ROUTE")
    print("=" * 80)
    
    vehicle_data = []
    
    for route_code, data in route_passengers.items():
        vehicles = data['vehicles']
        passengers = data['passengers']
        
        for vehicle in vehicles:
            vehicle_passengers = [p for p in passengers if p['vehicle'] == vehicle]
            
            vehicle_data.append([
                vehicle,
                route_code,
                data['route_name'][:25],
                len(vehicle_passengers),
                len([p for p in vehicle_passengers if p['type'] == 'depot_pickup']),
                len([p for p in vehicle_passengers if p['type'] == 'route_pickup']),
                f"{sum(p['wait_time'] for p in vehicle_passengers) / len(vehicle_passengers):.1f}" if vehicle_passengers else "0.0"
            ])
    
    headers = [
        "Vehicle ID", "Route", "Route Name", "Total Pass.", 
        "Depot Pass.", "Route Pass.", "Avg Wait (min)"
    ]
    
    print(tabulate(vehicle_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    print("🚌 ROUTE-CENTRIC PASSENGER DISTRIBUTION")
    print("=" * 60)
    print("Organizing passengers by route with each route as a column")
    print()
    
    # Get data from API
    depots, routes, vehicles = get_api_data()
    
    if not routes:
        print("❌ No route data available")
        exit(1)
    
    if not vehicles:
        print("❌ No vehicle data available")
        exit(1)
    
    # Enhance depots with coordinates
    depots = enhance_depots_with_coordinates(depots)
    
    # Create passengers organized by route
    route_passengers = create_route_passengers(routes, vehicles, depots)
    
    # Display results
    display_route_passenger_table(route_passengers)
    display_route_summary_table(route_passengers)
    display_vehicle_assignments(route_passengers)
    
    print(f"\n✅ ROUTE-CENTRIC ANALYSIS COMPLETE")
    print(f"   📊 Each column shows all passengers for that specific route")
    print(f"   🚐 Vehicles assigned to routes with passenger distribution")
    print(f"   👥 Both depot pickups and route stops included")