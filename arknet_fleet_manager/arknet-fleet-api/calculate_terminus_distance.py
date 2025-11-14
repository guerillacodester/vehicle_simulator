import math

def haversine(coord1, coord2):
    """Calculate great-circle distance between two points in kilometers"""
    R = 6371.0  # Earth radius in km
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)
    
    a = math.sin(dLat/2)**2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# First coordinate (start terminus)
start = [-59.61552132051129, 13.326607060339862]

# Last coordinate (end terminus)
end = [-59.642139094938095, 13.25009746989317]

# Calculate straight-line distance between termini
straight_distance = haversine(start, end)

print(f"Route 1 Terminus Analysis")
print(f"=" * 50)
print(f"Start: {start[1]:.6f}, {start[0]:.6f}")
print(f"End:   {end[1]:.6f}, {end[0]:.6f}")
print(f"\nStraight-line distance (as crow flies): {straight_distance:.3f} km")
print(f"Actual route length (following roads):  13.394 km")
print(f"\nRoute is {(13.394 / straight_distance):.2f}x longer than straight line")
print(f"(This shows the route follows the road network)")
