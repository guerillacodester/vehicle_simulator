#!/usr/bin/env python3
"""
Test the vehicles API with assigned drivers and routes
"""
import requests
import json

def test_detailed_vehicles():
    """Test the detailed vehicles endpoint"""
    try:
        print('=== TESTING DETAILED VEHICLES ENDPOINT ===')
        response = requests.get('http://localhost:8000/api/v1/vehicles/all/detailed', timeout=10)
        if response.status_code == 200:
            vehicles = response.json()
            if vehicles:
                print(f'✅ Found {len(vehicles)} vehicles with detailed information')
                
                for i, vehicle in enumerate(vehicles):
                    print(f'\n--- Vehicle {i+1} ---')
                    print(f'Registration: {vehicle.get("reg_code", "N/A")}')
                    print(f'Status: {vehicle.get("status", "N/A")}')
                    print(f'Capacity: {vehicle.get("capacity", "N/A")}')
                    
                    if vehicle.get('assigned_driver'):
                        driver = vehicle['assigned_driver']
                        print(f'Assigned Driver: {driver.get("name", "N/A")} (License: {driver.get("license_no", "N/A")})')
                    else:
                        print('Assigned Driver: None')
                        
                    if vehicle.get('assigned_route'):
                        route = vehicle['assigned_route']
                        print(f'Assigned Route: {route.get("short_name", "N/A")} - {route.get("long_name", "N/A")}')
                    else:
                        print('Assigned Route: None')
                        
                    if vehicle.get('depot'):
                        depot = vehicle['depot']
                        print(f'Depot: {depot.get("name", "N/A")}')
                    else:
                        print('Depot: None')
                        
            else:
                print('❌ No vehicles found')
        else:
            print(f'❌ API Error: {response.status_code}')
            print('Response:', response.text)
            
    except Exception as e:
        print(f'❌ Error: {e}')

def test_regular_vehicles():
    """Test the regular vehicles endpoint to see if it includes driver info"""
    try:
        print('\n=== TESTING REGULAR VEHICLES ENDPOINT ===')
        response = requests.get('http://localhost:8000/api/v1/vehicles', timeout=10)
        if response.status_code == 200:
            vehicles = response.json()
            if vehicles:
                first_vehicle = vehicles[0]
                print('First vehicle fields:')
                for key in sorted(first_vehicle.keys()):
                    print(f'  {key}: {first_vehicle[key]}')
                    
                if 'assigned_driver_id' in first_vehicle:
                    print('✅ assigned_driver_id field is present!')
                else:
                    print('❌ assigned_driver_id field is MISSING')
            else:
                print('❌ No vehicles found')
        else:
            print(f'❌ API Error: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_detailed_vehicles()
    test_regular_vehicles()