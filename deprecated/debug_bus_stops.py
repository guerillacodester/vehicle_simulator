#!/usr/bin/env python3
"""
Bus Stop Proximity Diagnostic
============================

Investigate why passenger at 13.272424,-59.646313 shows 0 nearby bus stops
when we have 1,332 bus stops in the Barbados GeoJSON data.
"""

import json
import math
from typing import List, Dict, Any


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in meters."""
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


def investigate_bus_stops():
    """Investigate bus stop proximity for the suspicious passenger location."""
    
    # Suspicious passenger coordinates
    passenger_lat = 13.272424
    passenger_lon = -59.646313
    
    print("🔍 BUS STOP PROXIMITY DIAGNOSTIC")
    print("=" * 50)
    print(f"Investigating passenger at: {passenger_lat:.6f}, {passenger_lon:.6f}")
    
    # Load bus stops data
    try:
        with open("world/arknet_transit_simulator/passenger_modeler/data/barbados/barbados_busstops.geojson", 'r') as f:
            busstops_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading bus stops: {e}")
        return
    
    print(f"📍 Loaded {len(busstops_data.get('features', []))} bus stops")
    
    # Find all stops within various distances
    distances = [50, 100, 200, 500, 1000]  # meters
    
    for max_distance in distances:
        nearby_stops = []
        
        for i, feature in enumerate(busstops_data['features']):
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Point':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    stop_lon, stop_lat = coords[0], coords[1]
                    distance = haversine_distance(passenger_lat, passenger_lon, stop_lat, stop_lon)
                    
                    if distance <= max_distance:
                        nearby_stops.append({
                            'index': i,
                            'name': properties.get('stop_name', properties.get('full_id', 'Unknown')),
                            'distance_m': round(distance, 1),
                            'coordinates': [stop_lat, stop_lon]
                        })
        
        nearby_stops.sort(key=lambda x: x['distance_m'])
        print(f"\n🚏 Within {max_distance}m: {len(nearby_stops)} stops")
        
        # Show closest 5 stops
        for i, stop in enumerate(nearby_stops[:5]):
            print(f"   {i+1}. {stop['name']} - {stop['distance_m']}m at [{stop['coordinates'][0]:.6f}, {stop['coordinates'][1]:.6f}]")
    
    # Check coordinate system - are we using the right lat/lon order?
    print(f"\n🌍 COORDINATE SYSTEM CHECK:")
    print(f"Passenger coordinates: Lat={passenger_lat:.6f}, Lon={passenger_lon:.6f}")
    print(f"Expected region: Barbados (~13.1°N, ~59.5°W)")
    
    # Check if coordinates are in reasonable range for Barbados
    if 13.0 <= passenger_lat <= 13.4 and -59.8 <= passenger_lon <= -59.4:
        print("✅ Coordinates are in valid Barbados range")
    else:
        print("❌ Coordinates are outside expected Barbados range!")
    
    # Sample a few bus stops to check their coordinate range
    print(f"\n📊 SAMPLE BUS STOP COORDINATES:")
    for i in range(0, min(10, len(busstops_data['features'])), 2):
        feature = busstops_data['features'][i]
        coords = feature['geometry']['coordinates']
        stop_name = feature['properties'].get('stop_name', feature['properties'].get('full_id', 'Unknown'))
        print(f"   {stop_name}: [{coords[1]:.6f}, {coords[0]:.6f}] (lat, lon)")
    
    # Check if the passenger location makes sense geographically
    print(f"\n🗺️ GEOGRAPHIC SANITY CHECK:")
    print(f"Passenger location: https://www.google.com/maps?q={passenger_lat},{passenger_lon}")


if __name__ == "__main__":
    investigate_bus_stops()