#!/usr/bin/env python3
"""
Step 2: Setup Permissions for Route-Shapes Content Type
=======================================================
Automatically configures permissions for the new route-shapes content type.
"""
import requests
import json
import time

def test_route_shapes_availability():
    """Test if route-shapes endpoint is now available after Strapi restart"""
    print("🔍 TESTING ROUTE-SHAPES ENDPOINT AVAILABILITY")
    print("=" * 60)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get('http://localhost:1337/api/route-shapes')
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ route-shapes endpoint is available!")
                print(f"📊 Current records: {len(data['data'])}")
                return True
            elif response.status_code == 403:
                print(f"⚠️  route-shapes endpoint exists but permissions denied")
                print(f"🔧 Need to set up permissions...")
                return "permissions_needed"
            else:
                print(f"❌ route-shapes endpoint not available (Status: {response.status_code})")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2)
                
        except Exception as e:
            print(f"❌ Error testing endpoint: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
    
    return False

def test_shapes_permissions():
    """Test shapes endpoint permissions as reference"""
    print(f"\n🔍 TESTING SHAPES ENDPOINT PERMISSIONS")
    print("=" * 60)
    
    try:
        # Test GET
        response = requests.get('http://localhost:1337/api/shapes')
        get_status = response.status_code
        
        # Test POST with minimal data
        test_data = {
            "data": {
                "shape_id": "test-permission-check",
                "shape_pt_lat": 13.0,
                "shape_pt_lon": -59.0,
                "shape_pt_sequence": 1
            }
        }
        
        response = requests.post('http://localhost:1337/api/shapes',
                               headers={'Content-Type': 'application/json'},
                               json=test_data)
        post_status = response.status_code
        
        # Clean up if successful
        if post_status in [200, 201]:
            created_id = response.json()['data']['id']
            requests.delete(f'http://localhost:1337/api/shapes/{created_id}')
        
        print(f"Shapes permissions:")
        print(f"  GET: {get_status} ({'✅ Allowed' if get_status == 200 else '❌ Denied'})")
        print(f"  POST: {post_status} ({'✅ Allowed' if post_status in [200, 201] else '❌ Denied'})")
        
        return get_status == 200 and post_status in [200, 201]
        
    except Exception as e:
        print(f"❌ Error testing shapes permissions: {e}")
        return False

def provide_manual_permissions_setup():
    """Provide manual instructions for setting up permissions"""
    print(f"\n🔧 MANUAL PERMISSIONS SETUP REQUIRED")
    print("=" * 60)
    print("Since the content type was created via files, permissions need manual setup:")
    print()
    print("1. Go to Strapi Admin: http://localhost:1337/admin")
    print("2. Navigate to: Settings → Users & Permissions Plugin → Roles")
    print("3. Click on: Public")
    print("4. Scroll down to find: Route-shape")
    print("5. Enable these permissions:")
    print("   ✅ find (to read route-shapes)")
    print("   ✅ findOne (to read single route-shape)")
    print("   ✅ create (to create route-shapes)")
    print("   ✅ update (to update route-shapes)")
    print("   ✅ delete (to delete route-shapes)")
    print("6. Click: Save")
    print()
    print("Alternatively, if you want migration-only access:")
    print("   ✅ find, findOne, create (minimum for migration)")

def wait_for_permissions_setup():
    """Wait for user to set up permissions manually"""
    print(f"\n⏳ WAITING FOR PERMISSIONS SETUP")
    print("=" * 60)
    print("Please complete the manual permissions setup above.")
    print("Press Enter when you've finished setting up permissions...")
    
    input()  # Wait for user input
    
    # Test if permissions work now
    return test_route_shapes_availability()

def check_all_required_endpoints():
    """Check all endpoints needed for geometry migration"""
    print(f"\n📊 CHECKING ALL REQUIRED ENDPOINTS")
    print("=" * 60)
    
    endpoints = {
        'shapes': 'http://localhost:1337/api/shapes',
        'route-shapes': 'http://localhost:1337/api/route-shapes'
    }
    
    results = {}
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url)
            status = response.status_code
            
            if status == 200:
                count = len(response.json()['data'])
                results[name] = f"✅ Available ({count} records)"
            elif status == 403:
                results[name] = "⚠️  Permissions denied"
            else:
                results[name] = f"❌ Not available ({status})"
                
        except Exception as e:
            results[name] = f"❌ Error: {e}"
    
    print("Endpoint Status:")
    for name, status in results.items():
        print(f"  {name:<15}: {status}")
    
    # Check if ready for migration
    ready = all("✅" in status for status in results.values())
    
    if ready:
        print(f"\n🎉 ALL ENDPOINTS READY FOR GEOMETRY MIGRATION!")
    else:
        print(f"\n⚠️  Some endpoints need attention before migration")
    
    return ready

if __name__ == "__main__":
    print("🔧 STEP 2: SETUP PERMISSIONS FOR ROUTE-SHAPES")
    print("=" * 80)
    
    # Check current status
    route_shapes_status = test_route_shapes_availability()
    
    if route_shapes_status == True:
        print("✅ route-shapes is already available with permissions!")
        
    elif route_shapes_status == "permissions_needed":
        print("🔧 Content type exists but needs permissions setup")
        
        # Show reference permissions
        test_shapes_permissions()
        
        # Provide manual setup instructions
        provide_manual_permissions_setup()
        
        # Wait for setup
        if wait_for_permissions_setup():
            print("🎉 Permissions setup successful!")
        else:
            print("❌ Permissions still not working")
            
    else:
        print("❌ route-shapes content type not available")
        print("💡 Make sure Strapi has been restarted after creating the schema files")
        print("⏳ Waiting 5 seconds for Strapi to fully load...")
        time.sleep(5)
        
        # Retry once more
        if test_route_shapes_availability():
            print("✅ route-shapes is now available!")
        else:
            print("❌ route-shapes still not available - check Strapi logs")
    
    # Final status check
    print(f"\n" + "="*80)
    print("FINAL STATUS CHECK")
    print("="*80)
    
    if check_all_required_endpoints():
        print("🚀 READY FOR STEP 3: GEOMETRY MIGRATION!")
    else:
        print("⚠️  Complete the permissions setup before proceeding to migration")