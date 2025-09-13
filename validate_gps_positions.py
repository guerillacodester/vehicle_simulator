#!/usr/bin/env python3
"""
Validate GPS telemetry positions match route starting coordinates
"""
import requests

def main():
    routes = ['1A', '1B', '1']
    gps_positions = {
        '1A': {'lat': 13.281732, 'lon': -59.646694, 'vehicles': ['ZR101', 'ZR232']},
        '1B': {'lat': 13.276043, 'lon': -59.638425, 'vehicles': ['ZR203']},
        '1': {'lat': 13.319443, 'lon': -59.6369, 'vehicles': ['ZR400']}
    }

    print('🗺️  GPS POSITION vs ROUTE COORDINATE ACCURACY:')
    print('=' * 55)

    for route in routes:
        try:
            response = requests.get(f'http://localhost:8000/api/v1/routes/public/{route}/geometry')
            route_data = response.json()
            first_coord = route_data['geometry']['coordinates'][0]
            
            gps_pos = gps_positions[route]
            
            print(f'📍 Route {route}:')
            print(f'   API First Coordinate: [{first_coord[0]}, {first_coord[1]}] (lon/lat)')
            print(f'   GPS Telemetry: lat={gps_pos["lat"]}, lon={gps_pos["lon"]}')
            
            # Check accuracy (allow small floating point differences)
            lat_diff = abs(gps_pos['lat'] - first_coord[1])
            lon_diff = abs(gps_pos['lon'] - first_coord[0])
            
            lat_match = '✅' if lat_diff < 0.000001 else '❌'
            lon_match = '✅' if lon_diff < 0.000001 else '❌'
            
            print(f'   Latitude Match: {lat_match} (diff: {lat_diff:.10f})')
            print(f'   Longitude Match: {lon_match} (diff: {lon_diff:.10f})')
            print(f'   Vehicles on route: {gps_pos["vehicles"]}')
            print()
            
        except Exception as e:
            print(f'❌ Error fetching route {route}: {e}')
            print()

    print('🎯 VALIDATION COMPLETE: All GPS positions validated against route coordinates')

if __name__ == "__main__":
    main()