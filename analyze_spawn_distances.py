"""
Analyze spawn distances from log data.
"""
import math

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points on Earth in km."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate compass bearing from one point to another."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing_rad = math.atan2(x, y)
    bearing_deg = (math.degrees(bearing_rad) + 360) % 360
    return bearing_deg

def analyze_spawns():
    """Analyze spawn locations from logs."""
    
    print("=" * 100)
    print("ROUTE 1A SPAWN DISTANCE ANALYSIS (from logs)")
    print("=" * 100)
    
    # Route spawns from commuter_startup.log (NEW - FIXED)
    route_spawns = [
        {
            "id": "COM_2DA2",
            "type": "ROUTE",
            "spawn": (13.2678, -59.6268),
            "dest": (13.3138, -59.6389),
            "direction": "OUTBOUND"
        }
    ]
    
    # Depot spawns for comparison (NEW - FIXED destinations on route)
    depot_spawns = [
        {
            "id": "COM_CAFC",
            "type": "DEPOT",
            "depot": "Speightstown Bus Terminal",
            "depot_coords": (13.2521, -59.6425),
            "dest": (13.3194, -59.6369),  # Now on the route!
            "route": "1A"
        },
        {
            "id": "COM_F9FD",
            "type": "DEPOT",
            "depot": "Constitution River Terminal",
            "depot_coords": (13.0965, -59.6086),
            "dest": (13.2973, -59.6420),  # Now on the route!
            "route": "1A"
        }
    ]
    
    print("\n" + "🚌 ROUTE SPAWNS (passengers waiting along the route)".center(100))
    print("=" * 100)
    
    for i, spawn in enumerate(route_spawns, 1):
        spawn_lat, spawn_lon = spawn["spawn"]
        dest_lat, dest_lon = spawn["dest"]
        
        distance = haversine(spawn_lat, spawn_lon, dest_lat, dest_lon)
        bearing = calculate_bearing(spawn_lat, spawn_lon, dest_lat, dest_lon)
        
        # Determine cardinal direction
        if bearing < 22.5 or bearing >= 337.5:
            direction_name = "North"
        elif bearing < 67.5:
            direction_name = "Northeast"
        elif bearing < 112.5:
            direction_name = "East"
        elif bearing < 157.5:
            direction_name = "Southeast"
        elif bearing < 202.5:
            direction_name = "South"
        elif bearing < 247.5:
            direction_name = "Southwest"
        elif bearing < 292.5:
            direction_name = "West"
        else:
            direction_name = "Northwest"
        
        print(f"\n🎯 SPAWN #{i} | ID: {spawn['id']} | Direction: {spawn['direction']}")
        print(f"   📍 Pickup Location:  ({spawn_lat:.6f}, {spawn_lon:.6f})")
        print(f"   🎯 Destination:      ({dest_lat:.6f}, {dest_lon:.6f})")
        print(f"   📏 Trip Distance:    {distance:.3f} km ({distance*1000:.0f} meters)")
        print(f"   🧭 Bearing:          {bearing:.1f}° ({direction_name})")
        print(f"   ⏱️  Est. Drive Time:  ~{distance/40*60:.1f} minutes (at 40 km/h avg)")
    
    print("\n\n" + "🏢 DEPOT SPAWNS (passengers waiting at terminals)".center(100))
    print("=" * 100)
    
    for i, spawn in enumerate(depot_spawns, 1):
        depot_lat, depot_lon = spawn["depot_coords"]
        dest_lat, dest_lon = spawn["dest"]
        
        distance = haversine(depot_lat, depot_lon, dest_lat, dest_lon)
        bearing = calculate_bearing(depot_lat, depot_lon, dest_lat, dest_lon)
        
        # Determine cardinal direction
        if bearing < 22.5 or bearing >= 337.5:
            direction_name = "North"
        elif bearing < 67.5:
            direction_name = "Northeast"
        elif bearing < 112.5:
            direction_name = "East"
        elif bearing < 157.5:
            direction_name = "Southeast"
        elif bearing < 202.5:
            direction_name = "South"
        elif bearing < 247.5:
            direction_name = "Southwest"
        elif bearing < 292.5:
            direction_name = "West"
        else:
            direction_name = "Northwest"
        
        print(f"\n🏢 DEPOT SPAWN #{i} | ID: {spawn['id']} | Route: {spawn['route']}")
        print(f"   🚏 Depot:            {spawn['depot']}")
        print(f"   📍 Depot Location:   ({depot_lat:.6f}, {depot_lon:.6f})")
        print(f"   🎯 Destination:      ({dest_lat:.6f}, {dest_lon:.6f})")
        print(f"   📏 Trip Distance:    {distance:.3f} km ({distance*1000:.0f} meters)")
        print(f"   🧭 Bearing:          {bearing:.1f}° ({direction_name})")
        print(f"   ⏱️  Est. Drive Time:  ~{distance/40*60:.1f} minutes (at 40 km/h avg)")
    
    # Calculate distance between the two route spawn locations
    print("\n\n" + "📊 INTER-SPAWN ANALYSIS".center(100))
    print("=" * 100)
    
    if len(route_spawns) >= 2:
        spawn1_lat, spawn1_lon = route_spawns[0]["spawn"]
        spawn2_lat, spawn2_lon = route_spawns[1]["spawn"]
        
        inter_spawn_distance = haversine(spawn1_lat, spawn1_lon, spawn2_lat, spawn2_lon)
        inter_spawn_bearing = calculate_bearing(spawn1_lat, spawn1_lon, spawn2_lat, spawn2_lon)
        
        print(f"\n🔗 Distance between route spawn locations:")
        print(f"   Spawn #1: ({spawn1_lat:.6f}, {spawn1_lon:.6f})")
        print(f"   Spawn #2: ({spawn2_lat:.6f}, {spawn2_lon:.6f})")
        print(f"   📏 Separation: {inter_spawn_distance:.3f} km ({inter_spawn_distance*1000:.0f} meters)")
        print(f"   🧭 Bearing (1→2): {inter_spawn_bearing:.1f}°")
    
    # Summary statistics
    print("\n\n" + "📈 SUMMARY STATISTICS".center(100))
    print("=" * 100)
    
    route_distances = [haversine(*spawn["spawn"], *spawn["dest"]) for spawn in route_spawns]
    depot_distances = [haversine(*spawn["depot_coords"], *spawn["dest"]) for spawn in depot_spawns]
    
    print(f"\n📊 Route Spawn Trips:")
    print(f"   Average distance: {sum(route_distances)/len(route_distances):.3f} km")
    print(f"   Min distance: {min(route_distances):.3f} km")
    print(f"   Max distance: {max(route_distances):.3f} km")
    
    print(f"\n📊 Depot Spawn Trips:")
    print(f"   Average distance: {sum(depot_distances)/len(depot_distances):.3f} km")
    print(f"   Min distance: {min(depot_distances):.3f} km")
    print(f"   Max distance: {max(depot_distances):.3f} km")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    analyze_spawns()
