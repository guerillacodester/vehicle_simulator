#!/usr/bin/env python3
"""
Cross-reference GPS telemetry data with Fleet Manager API assignments
"""
import json
import requests

def main():
    print("🔍 GPS TELEMETRY vs FLEET MANAGER API CROSS-REFERENCE:")
    print("=" * 60)
    
    # GPS telemetry data from server logs
    gps_data = [
        {
            'device': 'GPS-ZR101', 
            'vehicle': 'ZR101', 
            'driver_id': 'LIC002', 
            'driver_name': 'Jane Doe', 
            'route': '1A', 
            'lat': 13.281732, 
            'lon': -59.646694
        },
        {
            'device': 'GPS-ZR203', 
            'vehicle': 'ZR203', 
            'driver_id': 'LIC001', 
            'driver_name': 'John Smith', 
            'route': '1B', 
            'lat': 13.276043, 
            'lon': -59.638425
        },
        {
            'device': 'GPS-ZR232', 
            'vehicle': 'ZR232', 
            'driver_id': 'LIC003', 
            'driver_name': 'Michael Johnson', 
            'route': '1A', 
            'lat': 13.281732, 
            'lon': -59.646694
        },
        {
            'device': 'GPS-ZR400', 
            'vehicle': 'ZR400', 
            'driver_id': 'LIC004', 
            'driver_name': 'Sarah Williams', 
            'route': '1', 
            'lat': 13.319443, 
            'lon': -59.6369
        }
    ]
    
    # Fetch Fleet Manager API data
    try:
        response = requests.get('http://localhost:8000/api/v1/search/vehicle-driver-pairs')
        api_data = response.json()
        
        for gps in gps_data:
            api_match = next((api for api in api_data if api['registration'] == gps['vehicle']), None)
            if api_match:
                print(f"📡 {gps['device']}:")
                
                # Vehicle validation
                vehicle_match = "✅" if gps['vehicle'] == api_match['registration'] else "❌"
                print(f"   Vehicle: {gps['vehicle']} {vehicle_match} (API: {api_match['registration']})")
                
                # Driver validation
                driver_match = "✅" if (gps['driver_name'] == api_match['driver_name'] and 
                                     gps['driver_id'] == api_match['driver_license']) else "❌"
                print(f"   Driver: {gps['driver_name']} ({gps['driver_id']}) {driver_match}")
                print(f"           (API: {api_match['driver_name']} ({api_match['driver_license']}))")
                
                # Route validation
                route_match = "✅" if gps['route'] == api_match['route_code'] else "❌"
                print(f"   Route: {gps['route']} {route_match} (API: {api_match['route_code']})")
                
                # Status info
                print(f"   Status: GPS Active ✅ (API Vehicle: {api_match['vehicle_status']})")
                print(f"   Position: lat={gps['lat']}, lon={gps['lon']}")
                print()
            else:
                print(f"📡 {gps['device']}: ❌ NO API MATCH FOUND")
                print()
        
        # Summary
        total_matches = sum(1 for gps in gps_data 
                          if any(api['registration'] == gps['vehicle'] for api in api_data))
        print(f"📊 SUMMARY: {total_matches}/{len(gps_data)} GPS devices match API assignments")
        
    except Exception as e:
        print(f"❌ Error fetching API data: {e}")

if __name__ == "__main__":
    main()