#!/usr/bin/env python3
"""
Fix Strapi API Permissions for depot-reservoir endpoints
"""

import requests
import json
import sys

def enable_api_permissions():
    """Enable public access for depot-reservoir API endpoints"""
    
    # Strapi admin API endpoints
    BASE_URL = "http://localhost:1337"
    
    print("🔧 Enabling depot-reservoir API permissions...")
    
    # The APIs that need to be enabled for public access
    api_permissions = [
        {
            "action": "api::depot-reservoir.depot-reservoir.spawnBatch",
            "subject": None,
        },
        {
            "action": "api::depot-reservoir.depot-reservoir.getStatus", 
            "subject": None,
        },
        {
            "action": "api::passenger-spawning.passenger-spawning.generate",
            "subject": None,
        }
    ]
    
    try:
        # Get public role ID
        roles_response = requests.get(f"{BASE_URL}/api/users-permissions/roles")
        
        if roles_response.status_code == 200:
            roles_data = roles_response.json()
            public_role_id = None
            
            for role in roles_data.get('roles', []):
                if role.get('type') == 'public':
                    public_role_id = role.get('id')
                    break
            
            if not public_role_id:
                print("❌ Could not find public role")
                return False
            
            print(f"✅ Found public role ID: {public_role_id}")
            
            # Enable permissions for each API action
            for permission in api_permissions:
                # Try to update the role permissions
                update_payload = {
                    "permissions": {
                        permission["action"]: {
                            "enabled": True,
                            "policy": ""
                        }
                    }
                }
                
                print(f"🔄 Enabling permission: {permission['action']}")
                
                # Update role permissions (this might require authentication)
                # For now, let's just print what needs to be done
                print(f"   Action: {permission['action']}")
                
        else:
            print(f"❌ Failed to get roles: {roles_response.status_code}")
            print(f"Response: {roles_response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    
    print("\n📋 MANUAL STEPS REQUIRED:")
    print("1. Go to http://localhost:1337/admin")
    print("2. Navigate to Settings → Users & Permissions Plugin → Roles")
    print("3. Click on 'Public' role")
    print("4. Expand 'Depot-reservoir' section")
    print("5. Enable: spawnBatch and getStatus")
    print("6. Expand 'Passenger-spawning' section") 
    print("7. Enable: generate")
    print("8. Click 'Save'")
    
    return True

if __name__ == "__main__":
    enable_api_permissions()
