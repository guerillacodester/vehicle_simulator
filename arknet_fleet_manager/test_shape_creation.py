#!/usr/bin/env python3
"""
Test shape creation to debug validation issues
"""
import requests
import json

def test_shape_creation():
    """Test creating a single shape record to understand validation"""
    print("🧪 TESTING SHAPE CREATION")
    print("=" * 50)
    
    # Test data
    test_payload = {
        "data": {
            "shape_id": "test-shape-123",
            "shape_pt_sequence": 1,
            "shape_pt_lat": 13.0969,
            "shape_pt_lon": -59.6145
        }
    }
    
    print("Test payload:")
    print(json.dumps(test_payload, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:1337/api/shapes',
            headers={'Content-Type': 'application/json'},
            json=test_payload
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Shape creation successful!")
            created_id = response.json()['data']['id']
            
            # Clean up - delete the test record
            delete_response = requests.delete(f'http://localhost:1337/api/shapes/{created_id}')
            print(f"Cleanup: {delete_response.status_code}")
            
        else:
            print("❌ Shape creation failed!")
            try:
                error_data = response.json()
                print("Error details:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Could not parse error response")
                
    except Exception as e:
        print(f"❌ Request error: {e}")

def test_route_shape_creation():
    """Test creating a route-shape record"""
    print(f"\n🧪 TESTING ROUTE-SHAPE CREATION")
    print("=" * 50)
    
    test_payload = {
        "data": {
            "route_shape_id": "test-route-shape-123",
            "route_id": "0e9018ce-6e2a-42ef-a872-aa0248d2077a",
            "shape_id": "test-shape-456",
            "variant_code": None,
            "is_default": False
        }
    }
    
    print("Test payload:")
    print(json.dumps(test_payload, indent=2))
    
    try:
        response = requests.post(
            'http://localhost:1337/api/route-shapes',
            headers={'Content-Type': 'application/json'},
            json=test_payload
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Route-shape creation successful!")
            created_id = response.json()['data']['id']
            
            # Clean up
            delete_response = requests.delete(f'http://localhost:1337/api/route-shapes/{created_id}')
            print(f"Cleanup: {delete_response.status_code}")
        else:
            print("❌ Route-shape creation failed!")
            try:
                error_data = response.json()
                print("Error details:")
                print(json.dumps(error_data, indent=2))
            except:
                print("Could not parse error response")
                
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    test_shape_creation()
    test_route_shape_creation()