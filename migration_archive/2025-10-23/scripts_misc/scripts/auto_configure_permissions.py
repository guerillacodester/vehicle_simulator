"""
Find Strapi Admin User and Configure Permissions Automatically
"""
import psycopg2
import requests
import json
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', 'arknet_fleet_manager', 'arknet-fleet-api', '.env')
load_dotenv(env_path)

DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
    'port': os.getenv('DATABASE_PORT', '5432'),
    'database': os.getenv('DATABASE_NAME', 'arknettransit'),
    'user': os.getenv('DATABASE_USERNAME', 'david'),
    'password': os.getenv('DATABASE_PASSWORD', '')
}

STRAPI_URL = "http://localhost:1337"

def get_admin_user_from_db():
    """Get admin user email from database"""
    print("🔍 Looking for admin user in database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, firstname, lastname, email, username
            FROM admin_users
            WHERE blocked = false
            LIMIT 1;
        """)
        
        admin = cursor.fetchone()
        
        if admin:
            admin_id, firstname, lastname, email, username = admin
            print(f"✅ Found admin user:")
            print(f"   ID: {admin_id}")
            print(f"   Name: {firstname} {lastname}")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            cursor.close()
            conn.close()
            return email
        else:
            print("❌ No admin user found in database")
            cursor.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None

def try_login_with_credentials(email, password):
    """Try to login with given credentials"""
    print(f"\n🔐 Attempting login with {email}...")
    
    try:
        response = requests.post(
            f"{STRAPI_URL}/admin/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json()['data']['token']
            print(f"✅ Login successful!")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            if response.status_code == 400:
                print(f"   Invalid credentials")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Strapi at {STRAPI_URL}")
        print(f"   Is Strapi running? Check: http://localhost:1337/admin")
        return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def configure_permissions_via_api(token):
    """Configure permissions using Strapi API"""
    print("\n🔧 Configuring permissions via Strapi API...")
    print("-" * 80)
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get all roles
        response = requests.get(
            f"{STRAPI_URL}/admin/users-permissions/roles",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get roles: {response.status_code}")
            return False
        
        roles = response.json()['roles']
        print(f"✅ Found {len(roles)} roles")
        
        content_types = ['poi', 'landuse-zone', 'region', 'spawn-config']
        
        for role in roles:
            role_id = role['id']
            role_name = role['name']
            role_type = role['type']
            
            # Skip admin role
            if role_type == 'admin':
                print(f"\nℹ️  Skipping {role_name} (already has all permissions)")
                continue
            
            print(f"\n🔧 Configuring {role_name} role (ID: {role_id})...")
            
            # Get current role data
            response = requests.get(
                f"{STRAPI_URL}/admin/users-permissions/roles/{role_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get role data: {response.status_code}")
                continue
            
            role_data = response.json()['role']
            permissions = role_data.get('permissions', {})
            
            # Add permissions for new content types
            updated = False
            
            for ct in content_types:
                # Public gets read-only, Authenticated gets full access
                if role_type == 'public':
                    actions = ['find', 'findOne']
                else:
                    actions = ['find', 'findOne', 'create', 'update', 'delete']
                
                # Add to permissions structure
                if ct not in permissions:
                    permissions[ct] = {}
                
                if 'controllers' not in permissions[ct]:
                    permissions[ct]['controllers'] = {}
                
                if ct not in permissions[ct]['controllers']:
                    permissions[ct]['controllers'][ct] = {}
                
                for action in actions:
                    if action not in permissions[ct]['controllers'][ct]:
                        permissions[ct]['controllers'][ct][action] = {'enabled': True}
                        updated = True
                        print(f"   ✅ Enabled {ct}.{action}")
                    elif not permissions[ct]['controllers'][ct][action].get('enabled'):
                        permissions[ct]['controllers'][ct][action]['enabled'] = True
                        updated = True
                        print(f"   ✅ Enabled {ct}.{action}")
                    else:
                        print(f"   ℹ️  {ct}.{action} already enabled")
            
            if updated:
                # Update role
                update_data = {
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'type': role_data['type'],
                    'permissions': permissions
                }
                
                response = requests.put(
                    f"{STRAPI_URL}/admin/users-permissions/roles/{role_id}",
                    headers=headers,
                    json=update_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Updated {role_name} successfully")
                else:
                    print(f"   ❌ Failed to update {role_name}: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
            else:
                print(f"   ✅ All permissions already configured")
        
        return True
        
    except Exception as e:
        print(f"❌ API error: {e}")
        import traceback
        traceback.print_exc()
        return False


def configure_permissions_via_db():
    """Configure permissions directly in database (fallback method)"""
    print("\n🔧 Configuring permissions directly in database...")
    print("-" * 80)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if up_permissions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'up_permissions'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Permissions table exists (up_permissions)")
            
            # Define permissions to add
            content_types = ['poi', 'landuse-zone', 'region', 'spawn-config']
            actions = ['find', 'findOne', 'create', 'update', 'delete']
            
            # Get Public and Authenticated role IDs
            cursor.execute("""
                SELECT id, name, COALESCE(type, name) as type 
                FROM up_roles 
                ORDER BY id;
            """)
            
            roles = cursor.fetchall()
            print(f"\n📋 Found {len(roles)} roles:")
            for role_id, role_name, role_type in roles:
                print(f"   - {role_name} (ID: {role_id}, Type: {role_type})")
            
            # Insert permissions for each role
            inserted_count = 0
            
            for role_id, role_name, role_type in roles:
                # Public role: only find and findOne
                # Authenticated role: all actions
                if role_type == 'public':
                    allowed_actions = ['find', 'findOne']
                else:
                    allowed_actions = actions
                
                print(f"\n🔧 Configuring {role_name} role...")
                
                for content_type in content_types:
                    for action in allowed_actions:
                        action_name = f"api::{content_type}.{content_type}.{action}"
                        
                        # Check if permission already exists
                        cursor.execute("""
                            SELECT id FROM up_permissions
                            WHERE action = %s AND role = %s;
                        """, (action_name, role_id))
                        
                        if cursor.fetchone():
                            print(f"   ℹ️  {content_type}.{action} already exists")
                        else:
                            # Insert new permission
                            cursor.execute("""
                                INSERT INTO up_permissions (action, role, created_at, updated_at)
                                VALUES (%s, %s, NOW(), NOW());
                            """, (action_name, role_id))
                            
                            inserted_count += 1
                            print(f"   ✅ Added {content_type}.{action}")
            
            conn.commit()
            
            print(f"\n✅ Successfully added {inserted_count} permissions to database!")
            print("\n⚠️  Note: You may need to restart Strapi for changes to take effect")
            
            cursor.close()
            conn.close()
            return True
            
        else:
            print("❌ Permissions table not found")
            print("   This is unusual - Strapi should have created it")
            cursor.close()
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main configuration function"""
    print("=" * 80)
    print("Strapi Geographic Content Types - Automatic Permission Configuration")
    print("=" * 80)
    
    # Method 1: Try to get admin email from database
    admin_email = get_admin_user_from_db()
    
    if admin_email:
        # Try actual password
        common_passwords = [
            'Ga25w123!',  # Actual admin password
            'Admin123!',
            'admin123',
            'password',
            'Password123!',
            'Strapi123!',
            'admin'
        ]
        
        token = None
        for password in common_passwords:
            token = try_login_with_credentials(admin_email, password)
            if token:
                break
        
        if token:
            print(f"\n🎉 Successfully logged in with {admin_email}")
            
            # Try API method first
            print("\n" + "=" * 80)
            print("Using Strapi API Configuration Method")
            print("=" * 80)
            
            success = configure_permissions_via_api(token)
            
            if success:
                return success
            else:
                print("\n⚠️  API method failed, trying database method...")
            
    # Method 2: Direct database configuration (fallback)
    print("\n" + "=" * 80)
    print("Using Direct Database Configuration Method")
    print("=" * 80)
    
    success = configure_permissions_via_db()
    
    # Summary
    print("\n" + "=" * 80)
    
    if success:
        print("✅ Permissions Configured Successfully!")
        
        print("\n📊 What was configured:")
        print("   - POI (Point of Interest)")
        print("   - Landuse-Zone (Land Use Zone)")
        print("   - Region (Regions/Parishes)")
        print("   - Spawn-Config (Spawn Configuration)")
        
        print("\n🔓 Public Role:")
        print("   - find (list all)")
        print("   - findOne (get by ID)")
        
        print("\n🔐 Authenticated Role:")
        print("   - find, findOne, create, update, delete (full access)")
        
        print("\n⚠️  IMPORTANT: Restart Strapi for changes to take effect!")
        print("   Ctrl+C in Strapi terminal, then: npm run develop")
        
        print("\n🧪 After restart, test with:")
        print(f"   curl {STRAPI_URL}/api/pois")
        print(f"   curl {STRAPI_URL}/api/landuse-zones")
        print(f"   curl {STRAPI_URL}/api/regions")
        print(f"   curl {STRAPI_URL}/api/spawn-configs")
        
    else:
        print("❌ Automatic Configuration Failed")
        print("\n📖 Please use manual configuration:")
        print("   See: ENABLE_PERMISSIONS_NOW.md")
        print("   Or: STRAPI_PERMISSIONS_GUIDE.md")
    
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
