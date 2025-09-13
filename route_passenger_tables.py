#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Route-centric passenger table showing passengers per route in columns.

Each route gets its own column with all passengers in that route.
"""
import sys
import io
import requests
from tabulate import tabulate
import random
import math

# Set UTF-8 encoding for console output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371000 * c  # Earth radius in meters


def cluster_passengers_by_proximity(passengers, walking_distance_meters=150):
    """
    Cluster passengers within walking distance of each other.
    
    Args:
        passengers: List of passenger dictionaries
        walking_distance_meters: Maximum walking distance to group passengers (default 150m)
    
    Returns:
        List of passenger groups with counts and representative coordinates
    """
    if not passengers:
        return []
    
    groups = []
    used_passengers = set()
    
    for i, passenger in enumerate(passengers):
        if i in used_passengers:
            continue
            
        # Start a new group with this passenger
        group = {
            'passengers': [passenger],
            'representative_passenger': passenger,
            'origin_lat': passenger['origin_lat'],
            'origin_lon': passenger['origin_lon'],
            'dest_lat': passenger['dest_lat'], 
            'dest_lon': passenger['dest_lon'],
            'origin': passenger['origin'],
            'vehicle': passenger['vehicle'],
            'wait_times': [passenger['wait_time']],
            'types': [passenger['type']]
        }
        used_passengers.add(i)
        
        # Find nearby passengers to add to this group
        for j, other_passenger in enumerate(passengers):
            if j in used_passengers:
                continue
                
            # Check if passengers are within walking distance (both pickup and destination)
            pickup_distance = haversine_distance(
                passenger['origin_lat'], passenger['origin_lon'],
                other_passenger['origin_lat'], other_passenger['origin_lon']
            )
            
            dest_distance = haversine_distance(
                passenger['dest_lat'], passenger['dest_lon'],
                other_passenger['dest_lat'], other_passenger['dest_lon']
            )
            
            # Group if both pickup and destination are within walking distance
            if pickup_distance <= walking_distance_meters and dest_distance <= walking_distance_meters:
                group['passengers'].append(other_passenger)
                group['wait_times'].append(other_passenger['wait_time'])
                group['types'].append(other_passenger['type'])
                used_passengers.add(j)
        
        # Calculate group statistics
        group['count'] = len(group['passengers'])
        group['avg_wait_time'] = sum(group['wait_times']) / len(group['wait_times'])
        group['min_wait_time'] = min(group['wait_times'])
        group['max_wait_time'] = max(group['wait_times'])
        
        # Create group ID based on representative passenger
        base_id = group['representative_passenger']['id']
        if group['count'] > 1:
            group['id'] = f"GROUP_{base_id}_+{group['count']-1}"
        else:
            group['id'] = base_id
            
        groups.append(group)
    
    return groups


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
        
        # Generate route passengers with realistic world distribution patterns
        def calculate_demand_hotspots(coordinates):
            """Calculate demand hotspots based on realistic urban patterns."""
            hotspots = []
            route_length = len(coordinates)
            
            # Major transit hubs (beginning, middle, end of route) - high demand
            hotspots.extend([
                {'center': 0, 'radius': route_length // 8, 'multiplier': 3.5, 'type': 'major_hub'},
                {'center': route_length // 2, 'radius': route_length // 10, 'multiplier': 2.8, 'type': 'downtown'},
                {'center': route_length - 1, 'radius': route_length // 8, 'multiplier': 3.2, 'type': 'terminal'}
            ])
            
            # Commercial areas (random busy spots) - medium-high demand
            for _ in range(random.randint(2, 4)):
                center = random.randint(route_length // 4, 3 * route_length // 4) 
                hotspots.append({
                    'center': center, 
                    'radius': route_length // 15, 
                    'multiplier': 2.2, 
                    'type': 'commercial'
                })
            
            # Residential clusters - medium demand
            for _ in range(random.randint(3, 6)):
                center = random.randint(0, route_length - 1)
                hotspots.append({
                    'center': center,
                    'radius': route_length // 20,
                    'multiplier': 1.5,
                    'type': 'residential'
                })
            
            return hotspots
        
        def get_pickup_probability(coord_idx, hotspots, total_coords):
            """Calculate pickup probability for a coordinate based on nearby hotspots."""
            base_probability = 0.1  # Base chance anywhere along route
            
            for hotspot in hotspots:
                distance = abs(coord_idx - hotspot['center'])
                if distance <= hotspot['radius']:
                    # Gaussian decay from hotspot center
                    decay = math.exp(-(distance ** 2) / (2 * (hotspot['radius'] / 3) ** 2))
                    base_probability += hotspot['multiplier'] * decay
            
            return min(base_probability, 5.0)  # Cap at 5x base probability
        
        hotspots = calculate_demand_hotspots(coordinates)
        total_route_passengers = random.randint(50, 100)  # Realistic passenger count
        
        # Generate passengers based on real-world pickup patterns
        pickup_probabilities = []
        for i in range(len(coordinates)):
            prob = get_pickup_probability(i, hotspots, len(coordinates))
            pickup_probabilities.append(prob)
        
        # Normalize probabilities
        total_prob = sum(pickup_probabilities)
        pickup_probabilities = [p / total_prob for p in pickup_probabilities]
        
        for passenger_num in range(total_route_passengers):
            # Weighted random selection based on realistic demand
            pickup_idx = random.choices(range(len(coordinates)), weights=pickup_probabilities)[0]
            pickup_coord = coordinates[pickup_idx]
            
            # Realistic destination selection
            def get_destination_idx(pickup_idx, coordinates):
                """Select realistic destination based on trip patterns."""
                route_length = len(coordinates)
                
                # 60% short trips (2-15% of route), 30% medium trips (15-40%), 10% long trips (40%+)
                trip_type = random.choices(['short', 'medium', 'long'], weights=[0.6, 0.3, 0.1])[0]
                
                if trip_type == 'short':
                    max_distance = max(20, route_length // 7)  # Up to ~15% of route
                    min_distance = 5
                elif trip_type == 'medium': 
                    max_distance = max(50, 2 * route_length // 5)  # Up to ~40% of route
                    min_distance = route_length // 7
                else:  # long trip
                    max_distance = route_length - 1
                    min_distance = 2 * route_length // 5
                
                # Direction preference (75% forward, 25% backward for circular routes)
                if random.random() < 0.75:  # Forward direction
                    dest_idx = min(pickup_idx + random.randint(min_distance, max_distance), route_length - 1)
                else:  # Backward direction (for circular routes)
                    dest_idx = max(pickup_idx - random.randint(min_distance, max_distance), 0)
                
                return dest_idx
            
            dest_idx = get_destination_idx(pickup_idx, coordinates)
            dest_coord = coordinates[dest_idx]
            
            # Calculate stop zone for display grouping
            stop_zone = pickup_idx // 12
            
            # Realistic wait times based on location type
            hotspot_type = 'remote'
            for hotspot in hotspots:
                if abs(pickup_idx - hotspot['center']) <= hotspot['radius']:
                    hotspot_type = hotspot['type']
                    break
            
            if hotspot_type == 'major_hub':
                wait_time = random.randint(1, 8)  # Frequent service
            elif hotspot_type in ['downtown', 'commercial']:
                wait_time = random.randint(3, 12)  # Good service
            elif hotspot_type == 'residential':
                wait_time = random.randint(5, 15)  # Regular service
            else:  # remote
                wait_time = random.randint(8, 25)  # Infrequent service
            
            passenger = {
                'id': f"STOP_{route_code}_{pickup_idx:03d}_{passenger_num+1:02d}",
                'type': 'route_pickup',
                'origin': f"Stop {stop_zone + 1}",
                'origin_lat': pickup_coord[1],  # [lon, lat] format
                'origin_lon': pickup_coord[0], 
                'dest_lat': dest_coord[1],
                'dest_lon': dest_coord[0],
                'wait_time': wait_time,
                'vehicle': random.choice(assigned_vehicles) if assigned_vehicles else 'N/A',
                'pickup_type': hotspot_type  # For analysis
            }
            passengers.append(passenger)
        
        # Cluster passengers within walking distance
        print(f"   🔄 Clustering passengers within 150m walking distance...")
        passenger_groups = cluster_passengers_by_proximity(passengers, walking_distance_meters=150)
        
        route_passengers[route_code] = {
            'route_name': route_name,
            'vehicles': assigned_vehicles,
            'passengers': passengers,  # Keep original for reference
            'passenger_groups': passenger_groups  # New clustered groups
        }
        
        print(f"   Passengers: {len(passengers)} total")
        print(f"   - Depot pickups: {len([p for p in passengers if p['type'] == 'depot_pickup'])}")
        print(f"   - Route pickups: {len([p for p in passengers if p['type'] == 'route_pickup'])}")
        print(f"   🔗 Clustered into: {len(passenger_groups)} groups")
        print(f"   📊 Average group size: {len(passengers)/len(passenger_groups):.1f} passengers/group")
    
    return route_passengers


def display_route_passenger_table(route_passengers):
    """Display passenger groups organized by route in table format."""
    print(f"\n📊 PASSENGER GROUPS BY ROUTE - TABLE VIEW")
    print("=" * 100)
    
    # Get all route codes
    route_codes = list(route_passengers.keys())
    
    if not route_codes:
        print("❌ No routes with passengers found")
        return
    
    # Find the maximum number of passenger groups in any route
    max_groups = max(len(data['passenger_groups']) for data in route_passengers.values())
    
    # Create table data
    table_data = []
    
    for row_idx in range(max_groups):
        row = []
        
        for route_code in route_codes:
            passenger_groups = route_passengers[route_code]['passenger_groups']
            
            if row_idx < len(passenger_groups):
                group = passenger_groups[row_idx]
                origin_lat = group.get('origin_lat', 0)
                origin_lon = group.get('origin_lon', 0)
                dest_lat = group.get('dest_lat', 0)
                dest_lon = group.get('dest_lon', 0)
                
                # Determine group type based on most common type in group
                group_type = max(set(group['types']), key=group['types'].count)
                
                cell_content = f"{group['id']}\n({group_type[:5]})\n{group['origin'][:12]}\nVeh: {group['vehicle'][:6]}\nSize: {group['count']} pax\nWait: {group['avg_wait_time']:.0f}min\nFROM: {origin_lat:.6f},{origin_lon:.6f}\nTO: {dest_lat:.6f},{dest_lon:.6f}"
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
        group_count = len(route_passengers[route_code]['passenger_groups'])
        
        header = f"ROUTE {route_code}\n{route_name}\n{vehicle_count} vehicles\n{passenger_count} passengers\n{group_count} groups"
        headers.append(header)
    
    # Display table
    print(tabulate(table_data, headers=headers, tablefmt="grid", stralign="left"))


def display_route_summary_table(route_passengers):
    """Display summary statistics for each route including group information."""
    print(f"\n📈 ROUTE SUMMARY STATISTICS")
    print("=" * 80)
    
    summary_data = []
    total_passengers = 0
    total_vehicles = 0
    total_groups = 0
    
    for route_code, data in route_passengers.items():
        passengers = data['passengers']
        vehicles = data['vehicles']
        passenger_groups = data['passenger_groups']
        
        depot_passengers = len([p for p in passengers if p['type'] == 'depot_pickup'])
        route_passengers_count = len([p for p in passengers if p['type'] == 'route_pickup'])
        avg_wait = sum(p['wait_time'] for p in passengers) / len(passengers) if passengers else 0
        avg_group_size = len(passengers) / len(passenger_groups) if passenger_groups else 0
        
        summary_data.append([
            route_code,
            data['route_name'][:20],
            len(vehicles),
            len(passengers),
            len(passenger_groups),
            f"{avg_group_size:.1f}",
            depot_passengers,
            route_passengers_count,
            f"{avg_wait:.1f}",
            f"{len(passengers)/len(vehicles):.1f}" if vehicles else "0.0"
        ])
        
        total_passengers += len(passengers)
        total_vehicles += len(vehicles)
        total_groups += len(passenger_groups)
    
    headers = [
        "Route", "Name", "Vehicles", "Total Pass.", "Groups", "Avg Group Size",
        "Depot Pass.", "Route Pass.", "Avg Wait (min)", "Pass./Vehicle"
    ]
    
    print(tabulate(summary_data, headers=headers, tablefmt="grid"))
    
    print(f"\n🎯 SYSTEM TOTALS:")
    print(f"   Routes: {len(route_passengers)}")
    print(f"   Vehicles: {total_vehicles}")
    print(f"   Total Passengers: {total_passengers}")
    print(f"   Total Groups: {total_groups}")
    print(f"   Average Group Size: {total_passengers/total_groups:.1f}")
    print(f"   Average Passengers per Route: {total_passengers/len(route_passengers):.1f}")
    print(f"   Average Passengers per Vehicle: {total_passengers/total_vehicles:.1f}")


def display_passenger_coordinates(route_passengers):
    """Display detailed GPS coordinates for passenger groups."""
    print(f"\n🗺️  DETAILED PASSENGER GROUP GPS COORDINATES")
    print("=" * 100)
    
    for route_code, data in route_passengers.items():
        route_name = data['route_name']
        passenger_groups = data['passenger_groups']
        total_passengers = len(data['passengers'])
        
        print(f"\n📍 ROUTE {route_code} ({route_name}) - {len(passenger_groups)} groups ({total_passengers} passengers)")
        print("-" * 90)
        
        coord_data = []
        for i, group in enumerate(passenger_groups[:20]):  # Show first 20 groups per route
            group_type = max(set(group['types']), key=group['types'].count)
            coord_data.append([
                f"{i+1:2d}",
                group['id'][:15],
                group_type[:8],
                group['origin'][:12],
                f"{group['origin_lat']:.6f}",
                f"{group['origin_lon']:.6f}",
                f"{group['dest_lat']:.6f}",
                f"{group['dest_lon']:.6f}",
                f"{group['count']}",
                f"{group['avg_wait_time']:.0f}min"
            ])
        
        headers = ['#', 'Group ID', 'Type', 'Origin', 'Origin Lat', 'Origin Lon', 'Dest Lat', 'Dest Lon', 'Size', 'Avg Wait']
        print(tabulate(coord_data, headers=headers, tablefmt='grid'))
        
        if len(passenger_groups) > 20:
            print(f"... and {len(passenger_groups) - 20} more groups")


def display_vehicle_assignments(route_passengers):
    """Display which vehicles are assigned to which routes with group information."""
    print(f"\n🚐 VEHICLE ASSIGNMENTS BY ROUTE")
    print("=" * 80)
    
    vehicle_data = []
    
    for route_code, data in route_passengers.items():
        vehicles = data['vehicles']
        passengers = data['passengers']
        passenger_groups = data['passenger_groups']
        
        for vehicle in vehicles:
            vehicle_passengers = [p for p in passengers if p['vehicle'] == vehicle]
            vehicle_groups = [g for g in passenger_groups if g['vehicle'] == vehicle]
            
            vehicle_data.append([
                vehicle,
                route_code,
                data['route_name'][:25],
                len(vehicle_passengers),
                len(vehicle_groups),
                f"{len(vehicle_passengers)/len(vehicle_groups):.1f}" if vehicle_groups else "0.0",
                len([p for p in vehicle_passengers if p['type'] == 'depot_pickup']),
                len([p for p in vehicle_passengers if p['type'] == 'route_pickup']),
                f"{sum(p['wait_time'] for p in vehicle_passengers) / len(vehicle_passengers):.1f}" if vehicle_passengers else "0.0"
            ])
    
    headers = [
        "Vehicle ID", "Route", "Route Name", "Total Pass.", "Groups", "Avg Group Size",
        "Depot Pass.", "Route Pass.", "Avg Wait (min)"
    ]
    
    print(tabulate(vehicle_data, headers=headers, tablefmt="grid"))


def display_passenger_boarding_disembarking(route_passengers):
    """Display detailed boarding and disembarking positions for each individual passenger."""
    print(f"\n🚶 PASSENGER BOARDING & DISEMBARKING POSITIONS")
    print("=" * 120)
    
    total_passengers_shown = 0
    
    for route_code, data in route_passengers.items():
        route_name = data['route_name']
        passengers = data['passengers']
        
        print(f"\n📍 ROUTE {route_code} ({route_name}) - Individual Passenger Movements")
        print("-" * 120)
        
        passenger_data = []
        for i, passenger in enumerate(passengers):
            passenger_data.append([
                f"{i+1:3d}",
                passenger['id'][:20],
                passenger['type'][:10],
                passenger['origin'][:15],
                f"{passenger['origin_lat']:.6f}",
                f"{passenger['origin_lon']:.6f}",
                "BOARDING",
                passenger['vehicle'][:8],
                f"{passenger['wait_time']:2d}min",
                ""  # Destination info will be on next row
            ])
            
            # Add disembarking row
            passenger_data.append([
                "",  # No number for disembarking row
                "",  # No ID repeat
                passenger['type'][:10],
                "→ DESTINATION",
                f"{passenger['dest_lat']:.6f}",
                f"{passenger['dest_lon']:.6f}",
                "DISEMBARKING",
                passenger['vehicle'][:8],
                "",  # No wait time for disembarking
                f"Distance: {haversine_distance(passenger['origin_lat'], passenger['origin_lon'], passenger['dest_lat'], passenger['dest_lon']):.0f}m"
            ])
            
            # Add separator row every 5 passengers for readability
            if (i + 1) % 5 == 0 and i < len(passengers) - 1:
                passenger_data.append(["---"] * 10)
        
        headers = [
            '#', 'Passenger ID', 'Type', 'Location', 'Latitude', 'Longitude', 
            'Action', 'Vehicle', 'Wait', 'Notes'
        ]
        
        print(tabulate(passenger_data, headers=headers, tablefmt='grid', stralign="left"))
        
        # Show statistics for this route
        depot_count = len([p for p in passengers if p['type'] == 'depot_pickup'])
        route_count = len([p for p in passengers if p['type'] == 'route_pickup'])
        avg_distance = sum(haversine_distance(p['origin_lat'], p['origin_lon'], p['dest_lat'], p['dest_lon']) for p in passengers) / len(passengers)
        
        print(f"\n📊 Route {route_code} Movement Summary:")
        print(f"   • Total Passengers: {len(passengers)}")
        print(f"   • Depot Pickups: {depot_count}")
        print(f"   • Route Pickups: {route_count}")
        print(f"   • Average Trip Distance: {avg_distance:.0f}m")
        
        total_passengers_shown += len(passengers)
    
    print(f"\n🎯 BOARDING/DISEMBARKING SUMMARY:")
    print(f"   • Total Individual Passengers Tracked: {total_passengers_shown}")
    print(f"   • Total Boarding Events: {total_passengers_shown}")
    print(f"   • Total Disembarking Events: {total_passengers_shown}")
    print(f"   • Each passenger creates 2 location events (boarding + disembarking)")


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
    display_passenger_coordinates(route_passengers) 
    display_passenger_boarding_disembarking(route_passengers)
    display_route_summary_table(route_passengers)
    display_vehicle_assignments(route_passengers)
    
    print(f"\n✅ ROUTE-CENTRIC ANALYSIS COMPLETE")
    print(f"   📊 Each column shows all passengers for that specific route")
    print(f"   🚐 Vehicles assigned to routes with passenger distribution")
    print(f"   👥 Both depot pickups and route stops included")