#!/usr/bin/env python3
"""
GPS Movement Analysis Script
Calculate distance and bearing changes from server GPS data
"""

import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in meters."""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    return c * r

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate the bearing between two points."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

# GPS movement data from server
gps_data = [
    {"time": 0.0, "lat": 13.281732, "lon": -59.646694, "speed": 25.0, "heading": 127.0, "coord_idx": 0},
    {"time": 5.1, "lat": 13.281557, "lon": -59.646610, "speed": 25.0, "heading": 146.4, "coord_idx": 2},
    {"time": 10.1, "lat": 13.280811, "lon": -59.646457, "speed": 25.0, "heading": 243.9, "coord_idx": 4},
    {"time": 15.2, "lat": 13.280428, "lon": -59.647131, "speed": 25.0, "heading": 211.9, "coord_idx": 7},
    {"time": 20.2, "lat": 13.280083, "lon": -59.647373, "speed": 25.0, "heading": 217.9, "coord_idx": 9},
    {"time": 25.3, "lat": 13.279814, "lon": -59.647609, "speed": 25.0, "heading": 225.6, "coord_idx": 11}
]

print("🔍 GPS MOVEMENT ANALYSIS")
print("=" * 50)

total_distance = 0.0
print("\n📊 DISTANCE CALCULATIONS:")
print("-" * 30)

for i in range(1, len(gps_data)):
    prev = gps_data[i-1]
    curr = gps_data[i]
    
    # Calculate distance between consecutive points
    distance = haversine_distance(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
    total_distance += distance
    
    # Calculate actual bearing between points
    actual_bearing = calculate_bearing(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
    
    # Time and speed analysis
    time_diff = curr["time"] - prev["time"]
    expected_distance = (curr["speed"] * 1000 / 3600) * time_diff  # Convert km/h to m/s * time
    
    print(f"Segment {i}: t={prev['time']:.1f}s → t={curr['time']:.1f}s")
    print(f"  📍 From: ({prev['lat']:.6f}, {prev['lon']:.6f}) [coord {prev['coord_idx']}]")
    print(f"  📍 To:   ({curr['lat']:.6f}, {curr['lon']:.6f}) [coord {curr['coord_idx']}]")
    print(f"  📏 Distance: {distance:.2f} meters")
    print(f"  🧭 Reported heading: {curr['heading']:.1f}°")
    print(f"  🧭 Calculated bearing: {actual_bearing:.1f}°")
    print(f"  ⏱️  Time: {time_diff:.1f} seconds")
    print(f"  🚄 Expected distance at 25km/h: {expected_distance:.2f}m")
    print()

print(f"📊 SUMMARY:")
print(f"  🎯 Total Distance Traveled: {total_distance:.2f} meters")
print(f"  ⏱️  Total Time: {gps_data[-1]['time']:.1f} seconds")
print(f"  🚄 Average Speed: {(total_distance / gps_data[-1]['time']):.2f} m/s ({(total_distance / gps_data[-1]['time']) * 3.6:.1f} km/h)")

print(f"\n🧭 HEADING CHANGES:")
print("-" * 20)
headings = [point["heading"] for point in gps_data]
for i in range(1, len(headings)):
    heading_change = headings[i] - headings[i-1]
    if heading_change > 180:
        heading_change -= 360
    elif heading_change < -180:
        heading_change += 360
    
    direction = "right" if heading_change > 0 else "left" if heading_change < 0 else "straight"
    print(f"  Segment {i}: {headings[i-1]:.1f}° → {headings[i]:.1f}° (Δ{heading_change:+.1f}° {direction})")