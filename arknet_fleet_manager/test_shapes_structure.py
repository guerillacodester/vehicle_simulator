#!/usr/bin/env python3
"""
Test Strapi Shapes Content Type Structure
"""
import requests
import json

def test_shapes_structure():
    """Test what fields are available in Strapi shapes content type"""
    print("🔍 TESTING STRAPI SHAPES CONTENT TYPE")
    print("=" * 50)
    
    # Test empty POST to see required fields
    response = requests.post('http://localhost:1337/api/shapes',
                           headers={'Content-Type': 'application/json'},
                           json={'data': {}})
    
    if response.status_code == 400:
        error_data = response.json()
        print("📋 Required fields from empty POST:")
        error_details = error_data.get('error', {}).get('details', {})
        
        if 'errors' in error_details:
            for error in error_details['errors']:
                if 'path' in error and error['path']:
                    print(f"  - {error['path'][0]}: {error.get('message', 'required')}")
    
    # Test with minimal data
    test_data = {
        "data": {
            "shape_id": "test-shape-123",
            "geometry": "test-geometry-data"
        }
    }
    
    print(f"\n🧪 Testing with minimal data:")
    response = requests.post('http://localhost:1337/api/shapes',
                           headers={'Content-Type': 'application/json'},
                           json=test_data)
    
    print(f"Status: {response.status_code}")
    response_data = response.json()
    
    if response.status_code in [200, 201]:
        print("✅ Success! Created test record:")
        print(json.dumps(response_data, indent=2))
        
        # Clean up
        created_id = response_data['data']['id']
        delete_response = requests.delete(f'http://localhost:1337/api/shapes/{created_id}')
        print(f"🧹 Cleanup: {delete_response.status_code}")
        
    else:
        print(f"❌ Failed: {response.status_code}")
        print(json.dumps(response_data, indent=2))

if __name__ == "__main__":
    test_shapes_structure()