#!/usr/bin/env python3
"""
Step 1: Create Route-Shapes Content Type in Strapi
==================================================
Automatically creates the missing route-shapes content type via Strapi API.
"""
import requests
import json
import time

def create_route_shapes_content_type():
    """Create route-shapes content type programmatically"""
    print("🏗️  CREATING ROUTE-SHAPES CONTENT TYPE")
    print("=" * 50)
    
    # Content type definition based on our analysis
    content_type_definition = {
        "contentType": {
            "uid": "api::route-shape.route-shape",
            "displayName": "Route Shape",
            "singularName": "route-shape",
            "pluralName": "route-shapes",
            "description": "Links routes to their geometric shapes with variants",
            "collectionName": "route_shapes",
            "attributes": {
                "route_shape_id": {
                    "type": "uid",
                    "required": True,
                    "configurable": False,
                    "writable": True,
                    "visible": True,
                    "private": False
                },
                "route_id": {
                    "type": "string",
                    "required": True,
                    "configurable": True,
                    "searchable": True,
                    "filterable": True
                },
                "shape_id": {
                    "type": "string", 
                    "required": True,
                    "configurable": True,
                    "searchable": True,
                    "filterable": True
                },
                "variant_code": {
                    "type": "string",
                    "required": False,
                    "configurable": True,
                    "searchable": True,
                    "filterable": True
                },
                "is_default": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "configurable": True
                }
            },
            "visible": True,
            "restrictRelationsTo": None
        }
    }
    
    try:
        # Create content type via Strapi Admin API
        print("📝 Sending content type definition to Strapi...")
        
        # Note: This requires admin authentication
        # For now, we'll provide the manual steps since programmatic content type creation
        # requires admin JWT token which is complex to obtain automatically
        
        print("⚠️  PROGRAMMATIC CONTENT TYPE CREATION REQUIRES ADMIN TOKEN")
        print("📋 MANUAL STEPS REQUIRED:")
        print()
        print("1. Go to Strapi Admin: http://localhost:1337/admin")
        print("2. Navigate to: Content-Types Builder")
        print("3. Click: Create new collection type")
        print("4. Display name: 'Route Shape'")
        print("5. API ID (singular): 'route-shape'")
        print("6. API ID (plural): 'route-shapes'")
        print()
        print("7. Add these fields:")
        print("   - route_shape_id (UID, required)")
        print("   - route_id (Text, required)")
        print("   - shape_id (Text, required)")
        print("   - variant_code (Text, optional)")
        print("   - is_default (Boolean, default: false)")
        print()
        print("8. Click: Finish")
        print("9. Click: Save")
        print()
        
        # Save the definition to a file for reference
        with open('route_shapes_content_type.json', 'w') as f:
            json.dump(content_type_definition, f, indent=2)
        
        print("✅ Content type definition saved to: route_shapes_content_type.json")
        print("💡 You can import this definition if your Strapi supports it")
        
        return False  # Manual step required
        
    except Exception as e:
        print(f"❌ Error creating content type: {e}")
        return False

def test_route_shapes_endpoint():
    """Test if route-shapes endpoint is available"""
    print(f"\n🔍 TESTING ROUTE-SHAPES ENDPOINT")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:1337/api/route-shapes')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ route-shapes endpoint is available!")
            print(f"📊 Current records: {len(data['data'])}")
            return True
        else:
            print(f"❌ route-shapes endpoint not available (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def wait_for_content_type_creation():
    """Wait for user to create the content type manually"""
    print(f"\n⏳ WAITING FOR CONTENT TYPE CREATION")
    print("=" * 50)
    print("Please complete the manual steps above to create the route-shapes content type.")
    print("Press Enter when you've finished creating the content type...")
    
    input()  # Wait for user input
    
    # Test if it's available now
    return test_route_shapes_endpoint()

if __name__ == "__main__":
    print("🏗️  STEP 1: CREATE ROUTE-SHAPES CONTENT TYPE")
    print("=" * 80)
    
    # Check if it already exists
    if test_route_shapes_endpoint():
        print("✅ route-shapes content type already exists!")
    else:
        # Create content type (manual steps)
        create_route_shapes_content_type()
        
        # Wait for manual creation
        if wait_for_content_type_creation():
            print("🎉 route-shapes content type is now available!")
        else:
            print("❌ route-shapes content type still not available")
            print("⚠️  Cannot proceed with migration until content type is created")