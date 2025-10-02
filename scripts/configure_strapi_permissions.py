"""
Configure Strapi API Permissions for New Geographic Content Types

This script sets up permissions for the new content types:
- POI (Point of Interest)
- Land Use Zone
- Region
- Spawn Configuration

It grants Public and Authenticated roles access to these APIs.
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'arknet_fleet_manager', 'arknet-fleet-api', '.env')
load_dotenv(env_path)

STRAPI_URL = "http://localhost:1337"
STRAPI_ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@arknettransit.com')
STRAPI_ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin123!')

def login_admin():
    """Login as admin to get JWT token"""
    print("🔐 Logging in as admin...")
    
    try:
        response = requests.post(
            f"{STRAPI_URL}/admin/login",
            json={
                "email": STRAPI_ADMIN_EMAIL,
                "password": STRAPI_ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data['data']['token']
            print(f"✅ Login successful!")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def get_roles(token):
    """Get all roles (Public, Authenticated)"""
    print("\n📋 Fetching roles...")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{STRAPI_URL}/admin/users-permissions/roles",
            headers=headers
        )
        
        if response.status_code == 200:
            roles = response.json()['roles']
            print(f"✅ Found {len(roles)} roles:")
            for role in roles:
                print(f"   - {role['name']} (ID: {role['id']})")
            return roles
        else:
            print(f"❌ Failed to fetch roles: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching roles: {e}")
        return []

def update_role_permissions(token, role_id, role_name):
    """Update permissions for a specific role"""
    print(f"\n🔧 Updating permissions for role: {role_name} (ID: {role_id})...")
    
    # New content types to enable
    new_content_types = [
        'poi',
        'landuse-zone',
        'region',
        'spawn-config'
    ]
    
    # Permissions to grant for each content type
    permissions = ['find', 'findOne', 'create', 'update', 'delete']
    
    # For Public role, we typically only allow read operations
    if role_name.lower() == 'public':
        permissions = ['find', 'findOne']
    
    try:
        # First, get current role configuration
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{STRAPI_URL}/admin/users-permissions/roles/{role_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get role {role_id}: {response.status_code}")
            return False
        
        role_data = response.json()['role']
        current_permissions = role_data.get('permissions', {})
        
        # Update permissions for new content types
        updated = False
        
        for content_type in new_content_types:
            api_key = f"api::{content_type}.{content_type}"
            
            if api_key not in current_permissions:
                current_permissions[api_key] = {}
            
            if 'controllers' not in current_permissions[api_key]:
                current_permissions[api_key]['controllers'] = {}
            
            if content_type not in current_permissions[api_key]['controllers']:
                current_permissions[api_key]['controllers'][content_type] = {}
            
            # Enable each permission
            for perm in permissions:
                if perm not in current_permissions[api_key]['controllers'][content_type]:
                    current_permissions[api_key]['controllers'][content_type][perm] = {
                        'enabled': True
                    }
                    updated = True
                    print(f"   ✅ Enabled {content_type}.{perm}")
                elif not current_permissions[api_key]['controllers'][content_type][perm].get('enabled', False):
                    current_permissions[api_key]['controllers'][content_type][perm]['enabled'] = True
                    updated = True
                    print(f"   ✅ Enabled {content_type}.{perm}")
                else:
                    print(f"   ℹ️  {content_type}.{perm} already enabled")
        
        if updated:
            # Update the role with new permissions
            update_payload = {
                "name": role_data['name'],
                "description": role_data['description'],
                "permissions": current_permissions
            }
            
            response = requests.put(
                f"{STRAPI_URL}/admin/users-permissions/roles/{role_id}",
                headers=headers,
                json=update_payload
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully updated {role_name} permissions!")
                return True
            else:
                print(f"❌ Failed to update {role_name}: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        else:
            print(f"✅ All permissions already configured for {role_name}")
            return True
            
    except Exception as e:
        print(f"❌ Error updating {role_name} permissions: {e}")
        import traceback
        traceback.print_exc()
        return False

def configure_permissions():
    """Main function to configure all permissions"""
    print("=" * 80)
    print("Strapi Geographic Content Types - Permission Configuration")
    print("=" * 80)
    
    # Login
    token = login_admin()
    if not token:
        print("\n❌ Cannot proceed without admin token")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure Strapi is running: http://localhost:1337/admin")
        print("   2. Check admin credentials in .env file:")
        print("      ADMIN_EMAIL=admin@arknettransit.com")
        print("      ADMIN_PASSWORD=Admin123!")
        print("   3. Or update this script with correct credentials")
        return False
    
    # Get roles
    roles = get_roles(token)
    if not roles:
        print("\n❌ No roles found")
        return False
    
    # Update permissions for each role
    success = True
    
    for role in roles:
        role_id = role['id']
        role_name = role['name']
        
        # Skip admin role (already has all permissions)
        if role_name.lower() == 'admin':
            print(f"\nℹ️  Skipping {role_name} role (already has all permissions)")
            continue
        
        if not update_role_permissions(token, role_id, role_name):
            success = False
    
    # Summary
    print("\n" + "=" * 80)
    
    if success:
        print("✅ All Permissions Configured Successfully!")
        
        print("\n📊 Summary:")
        print("   - POI (Point of Interest)")
        print("   - Land Use Zone")
        print("   - Region")
        print("   - Spawn Configuration")
        
        print("\n🔓 Public Role Access:")
        print("   - find (list all)")
        print("   - findOne (get by ID)")
        
        print("\n🔐 Authenticated Role Access:")
        print("   - find, findOne (read)")
        print("   - create, update, delete (write)")
        
        print("\n🧪 Test API Endpoints:")
        print(f"   GET  {STRAPI_URL}/api/pois")
        print(f"   GET  {STRAPI_URL}/api/landuse-zones")
        print(f"   GET  {STRAPI_URL}/api/regions")
        print(f"   GET  {STRAPI_URL}/api/spawn-configs")
        
        print("\n⏭️  Next Steps:")
        print("   1. Verify table creation:")
        print("      python scripts/verify_strapi_tables.py")
        print("\n   2. Load Barbados data:")
        print("      python scripts/load_barbados_data.py")
        
    else:
        print("⚠️  Some Permissions May Not Be Configured Correctly")
        print("\n🔧 Manual Configuration:")
        print("   1. Open Strapi Admin: http://localhost:1337/admin")
        print("   2. Go to: Settings → Users & Permissions plugin → Roles")
        print("   3. Edit 'Public' role:")
        print("      - Enable 'find' and 'findOne' for:")
        print("        • POI")
        print("        • Landuse-zone")
        print("        • Region")
        print("        • Spawn-config")
        print("   4. Edit 'Authenticated' role:")
        print("      - Enable all actions for the same content types")
    
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    success = configure_permissions()
    exit(0 if success else 1)
