#!/usr/bin/env python3
"""
Server Telemetry Analysis
========================
Analyze GPS server logs for kinematic accuracy, distance calculation,
bearing verification, and traversal smoothness assessment.
"""

import json
import math
from datetime import datetime
from typing import List, Tuple, Dict, Any

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in meters."""
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
    
    return (bearing_degrees + 360) % 360

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime object."""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

def analyze_telemetry_logs(log_data: str) -> Dict[str, Any]:
    """Analyze GPS server telemetry logs from user's server output."""
    
    # Extract GPS packets from the log data
    packets = []
    lines = log_data.strip().split('\n')
    
    current_packet = None
    brace_count = 0
    packet_lines = []
    
    for line in lines:
        if 'RAW packet from GPS-ZR101:' in line:
            # Start of new packet
            if current_packet and packet_lines:
                # Process previous packet
                try:
                    packet_json = '\n'.join(packet_lines)
                    packet = json.loads(packet_json)
                    packets.append(packet)
                except:
                    pass
            packet_lines = []
            brace_count = 0
            continue
        
        if packet_lines is not None or line.strip().startswith('{'):
            packet_lines.append(line.strip())
            brace_count += line.count('{') - line.count('}')
            
            if brace_count == 0 and line.strip().endswith('}'):
                # End of packet
                try:
                    packet_json = '\n'.join(packet_lines)
                    packet = json.loads(packet_json)
                    packets.append(packet)
                except Exception as e:
                    print(f"Failed to parse packet: {e}")
                packet_lines = []
                brace_count = 0
    
    if not packets:
        return {"error": "No valid packets found in log data"}
    
    print(f"📊 Analyzing {len(packets)} GPS packets...")
    
    # Extract unique coordinates (remove duplicates)
    unique_coords = []
    seen_coords = set()
    
    for packet in packets:
        coord_key = (packet['lat'], packet['lon'])
        if coord_key not in seen_coords:
            unique_coords.append({
                'lat': packet['lat'],
                'lon': packet['lon'],
                'speed': packet['speed'],
                'heading': packet['heading'],
                'timestamp': packet['timestamp']
            })
            seen_coords.add(coord_key)
    
    print(f"📍 Found {len(unique_coords)} unique coordinate positions")
    
    # Analyze movement between coordinates
    total_distance = 0.0
    bearing_accuracy = []
    speeds = []
    
    analysis = {
        'total_packets': len(packets),
        'unique_positions': len(unique_coords),
        'coordinates': unique_coords,
        'movement_analysis': [],
        'smoothness_issues': []
    }
    
    for i in range(len(unique_coords) - 1):
        current = unique_coords[i]
        next_coord = unique_coords[i + 1]
        
        # Calculate actual distance between coordinates
        distance = haversine_distance(
            current['lat'], current['lon'],
            next_coord['lat'], next_coord['lon']
        )
        total_distance += distance
        
        # Calculate expected bearing
        expected_bearing = calculate_bearing(
            current['lat'], current['lon'],
            next_coord['lat'], next_coord['lon']
        )
        
        # Compare with reported heading
        reported_heading = next_coord['heading']
        bearing_error = abs(expected_bearing - reported_heading)
        if bearing_error > 180:
            bearing_error = 360 - bearing_error
        
        movement = {
            'segment': i + 1,
            'from': {'lat': current['lat'], 'lon': current['lon']},
            'to': {'lat': next_coord['lat'], 'lon': next_coord['lon']},
            'distance_meters': round(distance, 2),
            'expected_bearing': round(expected_bearing, 1),
            'reported_heading': reported_heading,
            'bearing_error': round(bearing_error, 1),
            'reported_speed': next_coord['speed']
        }
        
        analysis['movement_analysis'].append(movement)
        bearing_accuracy.append(bearing_error)
        speeds.append(next_coord['speed'])
    
    # Calculate statistics
    analysis['summary'] = {
        'total_distance_meters': round(total_distance, 2),
        'average_bearing_error': round(sum(bearing_accuracy) / len(bearing_accuracy), 1) if bearing_accuracy else 0,
        'max_bearing_error': round(max(bearing_accuracy), 1) if bearing_accuracy else 0,
        'consistent_speed': len(set(speeds)) == 1 if speeds else False,
        'reported_speed': speeds[0] if speeds else 0
    }
    
    # Check for smoothness issues
    packet_counts = {}
    for packet in packets:
        coord_key = (packet['lat'], packet['lon'])
        packet_counts[coord_key] = packet_counts.get(coord_key, 0) + 1
    
    for coord_key, count in packet_counts.items():
        if count > 1:
            analysis['smoothness_issues'].append({
                'coordinate': coord_key,
                'repeat_count': count,
                'issue': f"Coordinate repeated {count} times (not smooth traversal)"
            })
    
    return analysis

def main():
    """Main analysis function."""
    print("🔍 GPS Server Telemetry Analysis")
    print("=" * 50)
    
    # GPS server log data from user (extracted from their message)
    log_data = '''
2025-09-13 08:59:36,840 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:34.785176+00:00",
  "lat": 13.281732,
  "lon": -59.646694,
  "speed": 0.0,
  "heading": 0.0
}
2025-09-13 08:59:36,841 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:35.785687+00:00",
  "lat": 13.281732,
  "lon": -59.646694,
  "speed": 25.0,
  "heading": 127.0
}
2025-09-13 08:59:38,788 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:38.786978+00:00",
  "lat": 13.281732,
  "lon": -59.646694,
  "speed": 25.0,
  "heading": 155.1
}
2025-09-13 08:59:41,790 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:41.789122+00:00",
  "lat": 13.281557,
  "lon": -59.64661,
  "speed": 25.0,
  "heading": 146.4
}
2025-09-13 08:59:44,792 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:44.790686+00:00",
  "lat": 13.280811,
  "lon": -59.646457,
  "speed": 25.0,
  "heading": 243.9
}
2025-09-13 08:59:47,794 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:47.792886+00:00",
  "lat": 13.280666,
  "lon": -59.646762,
  "speed": 25.0,
  "heading": 240.7
}
2025-09-13 08:59:50,813 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:50.812365+00:00",
  "lat": 13.280428,
  "lon": -59.647131,
  "speed": 25.0,
  "heading": 211.9
}
2025-09-13 08:59:53,815 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:53.814270+00:00",
  "lat": 13.280289,
  "lon": -59.64722,
  "speed": 25.0,
  "heading": 215.9
}
2025-09-13 08:59:56,816 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:56.815784+00:00",
  "lat": 13.280083,
  "lon": -59.647373,
  "speed": 25.0,
  "heading": 217.9
}
2025-09-13 08:59:59,819 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T07:59:59.817614+00:00",
  "lat": 13.279814,
  "lon": -59.647609,
  "speed": 25.0,
  "heading": 225.6
}
2025-09-13 09:00:02,820 [INFO] RAW packet from GPS-ZR101:
{
  "deviceId": "GPS-ZR101",
  "route": "1A",
  "vehicleReg": "ZR101",
  "driverId": "LIC002",
  "driverName": {
    "first": "Jane",
    "last": "Doe"
  },
  "timestamp": "2025-09-13T08:00:02.819236+00:00",
  "lat": 13.279733,
  "lon": -59.647694,
  "speed": 25.0,
  "heading": 193.0
}
'''
    
    # Analyze the telemetry data
    analysis = analyze_telemetry_logs(log_data)
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        return
    
    # Print results
    print(f"\n📈 KINEMATIC ANALYSIS RESULTS")
    print(f"=" * 40)
    print(f"Total GPS Packets: {analysis['total_packets']}")
    print(f"Unique Positions: {analysis['unique_positions']}")
    print(f"Total Distance Traveled: {analysis['summary']['total_distance_meters']:.2f} meters")
    print(f"Average Bearing Error: {analysis['summary']['average_bearing_error']}°")
    print(f"Maximum Bearing Error: {analysis['summary']['max_bearing_error']}°")
    print(f"Consistent Speed: {analysis['summary']['consistent_speed']} ({analysis['summary']['reported_speed']} km/h)")
    
    print(f"\n🗺️  ROUTE TRAVERSAL DETAILS")
    print(f"=" * 30)
    for movement in analysis['movement_analysis']:
        print(f"Segment {movement['segment']}: {movement['distance_meters']}m, "
              f"Expected: {movement['expected_bearing']}°, "
              f"Reported: {movement['reported_heading']}°, "
              f"Error: {movement['bearing_error']}°")
    
    print(f"\n⚠️  SMOOTHNESS ISSUES")
    print(f"=" * 20)
    if analysis['smoothness_issues']:
        for issue in analysis['smoothness_issues']:
            lat, lon = issue['coordinate']
            print(f"• Lat {lat}, Lon {lon}: {issue['issue']}")
    else:
        print("✅ No smoothness issues detected")
    
    # Speed analysis
    print(f"\n🚗 SPEED ANALYSIS")
    print(f"=" * 16)
    reported_speed = analysis['summary']['reported_speed']
    distance = analysis['summary']['total_distance_meters']
    test_duration = 30  # seconds
    
    # Calculate expected distance at 25 km/h for 30 seconds
    expected_distance = (25 * 1000 / 3600) * test_duration  # Convert km/h to m/s
    
    print(f"Reported Speed: {reported_speed} km/h")
    print(f"Test Duration: {test_duration} seconds")
    print(f"Expected Distance: {expected_distance:.2f} meters")
    print(f"Actual Distance: {distance:.2f} meters")
    print(f"Distance Accuracy: {(distance/expected_distance)*100:.1f}%")
    
    # Final assessment
    print(f"\n🎯 OVERALL ASSESSMENT")
    print(f"=" * 20)
    
    if analysis['summary']['average_bearing_error'] < 5:
        print("✅ Bearing Accuracy: EXCELLENT (< 5° average error)")
    elif analysis['summary']['average_bearing_error'] < 15:
        print("✅ Bearing Accuracy: GOOD (< 15° average error)")
    else:
        print("⚠️  Bearing Accuracy: NEEDS IMPROVEMENT (> 15° average error)")
    
    if abs(distance - expected_distance) / expected_distance < 0.2:
        print("✅ Distance Accuracy: EXCELLENT (< 20% error)")
    else:
        print("⚠️  Distance Accuracy: NEEDS IMPROVEMENT (> 20% error)")
    
    if len(analysis['smoothness_issues']) == 0:
        print("✅ Route Traversal: SMOOTH")
    else:
        print(f"⚠️  Route Traversal: {len(analysis['smoothness_issues'])} smoothness issues")

if __name__ == "__main__":
    main()