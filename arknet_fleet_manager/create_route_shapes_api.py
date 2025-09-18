#!/usr/bin/env python3
"""
Create Route-Shapes Content Type via Strapi Admin API
====================================================
Creates the route-shapes content type directly through Strapi's admin API.
"""
import requests
import json

def login_to_strapi():
    """Login to Strapi admin and get JWT token"""
    print("🔐 LOGGING INTO STRAPI ADMIN")
    print("=" * 60)
    
    # Try to login (you may need to update credentials)
    login_data = {
        "identifier": "admin@arknet.com",  # Update if needed
        "password": "ArknetAdmin2024!"     # Update if needed
    }
    
    try:
        response = requests.post(
            'http://localhost:1337/admin/auth/local',
            headers={'Content-Type': 'application/json'},
            json=login_data
        )
        
        if response.status_code == 200:
            token = response.json()['data']['token']
            print("✅ Successfully logged into Strapi admin")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print("Response:", response.text)
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def create_route_shapes_content_type(token):
    """Create the route-shapes content type"""
    print(f"\n🚀 CREATING ROUTE-SHAPES CONTENT TYPE")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Content type definition
    content_type_data = {
        "contentType": {
            "kind": "collectionType",
            "collectionName": "route_shapes",
            "info": {
                "singularName": "route-shape",
                "pluralName": "route-shapes", 
                "displayName": "Route Shape",
                "description": "Links routes to their geometric shapes with variants"
            },
            "options": {
                "draftAndPublish": True
            },
            "attributes": {
                "route_shape_id": {
                    "type": "uid",
                    "required": True
                },
                "route_id": {
                    "type": "string",
                    "required": True
                },
                "shape_id": {
                    "type": "string", 
                    "required": True
                },
                "variant_code": {
                    "type": "string",
                    "required": False
                },
                "is_default": {
                    "type": "boolean",
                    "default": False,
                    "required": False
                }
            }
        }
    }
    
    try:
        response = requests.post(
            'http://localhost:1337/admin/content-type-builder/content-types',
            headers=headers,
            json=content_type_data
        )
        
        if response.status_code in [200, 201]:
            print("✅ Route-shapes content type created successfully!")
            return True
        else:
            print(f"❌ Failed to create content type: {response.status_code}")
            print("Response:", response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error creating content type: {e}")
        return False

def setup_permissions(token):
    """Setup public permissions for route-shapes"""
    print(f"\n🔧 SETTING UP PERMISSIONS")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get public role ID
    try:
        response = requests.get(
            'http://localhost:1337/admin/users-permissions/roles',
            headers=headers
        )
        
        if response.status_code == 200:
            roles = response.json()['data']
            public_role = next((role for role in roles if role['type'] == 'public'), None)
            
            if public_role:
                role_id = public_role['id']
                print(f"✅ Found public role ID: {role_id}")
                
                # Update permissions
                permissions_data = {
                    "permissions": {
                        "api::route-shape.route-shape": {
                            "controllers": {
                                "route-shape": {
                                    "find": {
                                        "enabled": True
                                    },
                                    "findOne": {
                                        "enabled": True
                                    },
                                    "create": {
                                        "enabled": True
                                    },
                                    "update": {
                                        "enabled": True
                                    },
                                    "delete": {
                                        "enabled": True
                                    }
                                }
                            }
                        }
                    }
                }
                
                response = requests.put(
                    f'http://localhost:1337/admin/users-permissions/roles/{role_id}',
                    headers=headers,
                    json=permissions_data
                )
                
                if response.status_code == 200:
                    print("✅ Permissions set successfully!")
                    return True
                else:
                    print(f"❌ Failed to set permissions: {response.status_code}")
                    return False
            else:
                print("❌ Public role not found")
                return False
        else:
            print(f"❌ Failed to get roles: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting permissions: {e}")
        return False

def test_endpoint():
    """Test if the route-shapes endpoint works"""
    print(f"\n✅ TESTING ROUTE-SHAPES ENDPOINT")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:1337/api/route-shapes')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Route-shapes endpoint is working!")
            print(f"📊 Current records: {len(data['data'])}")
            return True
        else:
            print(f"❌ Endpoint test failed: {response.status_code}")
            print("Response:", response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def main():
    print("🚀 CREATE ROUTE-SHAPES API ENDPOINT")
    print("=" * 80)
    
    # Login
    token = login_to_strapi()
    if not token:
        print("❌ Cannot proceed without admin access")
        print("💡 Make sure Strapi admin is set up and credentials are correct")
        return
    
    # Create content type
    if create_route_shapes_content_type(token):
        print("⏳ Waiting for Strapi to process the new content type...")
        import time
        time.sleep(3)
        
        # Setup permissions
        if setup_permissions(token):
            print("⏳ Waiting for permissions to take effect...")
            time.sleep(2)
            
            # Test endpoint
            if test_endpoint():
                print(f"\n🎉 SUCCESS! Route-shapes API endpoint is ready!")
                print("🚀 You can now proceed with Step 3: Geometry Migration")
            else:
                print(f"\n⚠️  Content type created but endpoint not working yet")
                print("💡 Try restarting Strapi or check admin panel")
        else:
            print(f"\n⚠️  Content type created but permissions failed")
            print("💡 Set permissions manually in admin panel")
    else:
        print(f"\n❌ Failed to create content type")

if __name__ == "__main__":
    main()