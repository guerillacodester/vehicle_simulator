"""
Automated Content Type Creation for Strapi v5
==============================================
Creates the operational-configurations collection type programmatically
using Strapi's Content-Type Builder API.

This automates what would otherwise be manual UI work.
"""

import requests
import json
import sys
import time

STRAPI_URL = "http://localhost:1337"
ADMIN_EMAIL = "admin@example.com"  # Update if different
ADMIN_PASSWORD = "Admin123!"  # Update if different


def get_admin_token():
    """Authenticate and get admin JWT token."""
    print("🔐 Authenticating with Strapi admin...")
    
    try:
        response = requests.post(
            f"{STRAPI_URL}/admin/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('data', {}).get('token')
            if token:
                print("   ✅ Authentication successful")
                return token
            else:
                print("   ❌ No token in response")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return None
        else:
            print(f"   ❌ Authentication failed (status: {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            
            if response.status_code == 400:
                print("\n   ⚠️  Please update ADMIN_EMAIL and ADMIN_PASSWORD in this script")
                print("   Or create admin user via: http://localhost:1337/admin")
            
            return None
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


def create_content_type(token):
    """Create the operational-configurations content type."""
    print("\n📋 Creating operational-configurations content type...")
    
    # Content type schema matching Strapi v5 format
    content_type_data = {
        "contentType": {
            "kind": "collectionType",
            "collectionName": "operational_configurations",
            "info": {
                "singularName": "operational-configuration",
                "pluralName": "operational-configurations",
                "displayName": "Operational Configuration",
                "description": "Runtime-configurable operational parameters"
            },
            "options": {
                "draftAndPublish": False
            },
            "pluginOptions": {},
            "attributes": {
                "section": {
                    "type": "string",
                    "required": True
                },
                "parameter": {
                    "type": "string",
                    "required": True
                },
                "value": {
                    "type": "json",
                    "required": True
                },
                "value_type": {
                    "type": "enumeration",
                    "enum": ["number", "string", "boolean", "object"],
                    "required": True
                },
                "default_value": {
                    "type": "json",
                    "required": True
                },
                "constraints": {
                    "type": "json"
                },
                "description": {
                    "type": "text"
                },
                "display_name": {
                    "type": "string"
                },
                "ui_group": {
                    "type": "string"
                },
                "requires_restart": {
                    "type": "boolean",
                    "default": False
                }
            }
        }
    }
    
    try:
        response = requests.post(
            f"{STRAPI_URL}/admin/content-type-builder/content-types",
            json=content_type_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code in [200, 201]:
            print("   ✅ Content type created successfully")
            print("   ⏳ Strapi is restarting to apply changes...")
            print("   This may take 30-60 seconds...")
            
            # Wait for Strapi to restart
            wait_for_strapi_restart()
            
            return True
        else:
            print(f"   ❌ Failed to create content type (status: {response.status_code})")
            print(f"   Response: {response.text[:500]}")
            
            # Check if already exists
            if "already exists" in response.text.lower():
                print("   ℹ️  Content type may already exist")
                return True
            
            return False
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def wait_for_strapi_restart(max_wait=120, check_interval=5):
    """Wait for Strapi to restart after schema changes."""
    print(f"\n⏳ Waiting for Strapi to restart (max {max_wait}s)...")
    
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait:
        try:
            response = requests.get(f"{STRAPI_URL}/_health", timeout=2)
            if response.status_code == 200:
                print("   ✅ Strapi is back online!")
                return True
        except:
            pass
        
        elapsed = int(time.time() - start_time)
        print(f"   ... {elapsed}s elapsed, still waiting...")
        time.sleep(check_interval)
    
    print("   ⚠️  Timeout waiting for restart, but may still be okay")
    return False


def set_permissions(token):
    """Enable public API permissions for operational-configurations."""
    print("\n🔓 Setting API permissions...")
    
    # Get public role ID
    try:
        response = requests.get(
            f"{STRAPI_URL}/admin/users-permissions/roles",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"   ⚠️  Failed to fetch roles (status: {response.status_code})")
            return False
        
        roles = response.json().get('data', [])
        public_role = next((r for r in roles if r.get('type') == 'public'), None)
        
        if not public_role:
            print("   ⚠️  Public role not found")
            return False
        
        role_id = public_role.get('id')
        print(f"   📊 Found public role (ID: {role_id})")
        
        # Update permissions
        # Note: Strapi v5 permissions API may differ - this is a best effort
        permissions_data = {
            "permissions": {
                "api::operational-configuration.operational-configuration": {
                    "controllers": {
                        "operational-configuration": {
                            "find": {"enabled": True},
                            "findOne": {"enabled": True},
                            "create": {"enabled": True},
                            "update": {"enabled": True},
                            "delete": {"enabled": True}
                        }
                    }
                }
            }
        }
        
        response = requests.put(
            f"{STRAPI_URL}/admin/users-permissions/roles/{role_id}",
            json=permissions_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code in [200, 201]:
            print("   ✅ Permissions updated")
            return True
        else:
            print(f"   ⚠️  Permissions update returned {response.status_code}")
            print("   ℹ️  You may need to enable permissions manually in admin UI")
            print("   Go to: Settings → Roles → Public → Operational-configuration")
            return False
    
    except Exception as e:
        print(f"   ⚠️  Exception setting permissions: {e}")
        print("   ℹ️  Enable manually: Settings → Roles → Public → Operational-configuration")
        return False


def verify_creation():
    """Verify the content type was created successfully."""
    print("\n✅ Verifying content type creation...")
    
    try:
        response = requests.get(
            f"{STRAPI_URL}/api/operational-configurations?pagination[limit]=1"
        )
        
        if response.status_code == 200:
            print("   ✅ Content type is accessible via API")
            data = response.json()
            print(f"   📊 Response structure: {list(data.keys())}")
            return True
        elif response.status_code == 403:
            print("   ⚠️  Content type exists but permissions not enabled")
            print("   Please enable permissions manually:")
            print("   Settings → Roles → Public → Operational-configuration")
            print("   Enable: find, findOne, create, update")
            return False
        else:
            print(f"   ❌ Content type not accessible (status: {response.status_code})")
            return False
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    """Main execution flow."""
    print("="*80)
    print("AUTOMATED CONTENT TYPE CREATION - STRAPI V5")
    print("="*80)
    
    # Check Strapi is running
    print("\n🔍 Checking if Strapi is running...")
    try:
        response = requests.get(f"{STRAPI_URL}/_health", timeout=5)
        print("   ✅ Strapi is running")
    except:
        print("   ❌ Strapi is not responding")
        print(f"   Please start Strapi at {STRAPI_URL}")
        return False
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("\n" + "="*80)
        print("MANUAL STEPS REQUIRED:")
        print("="*80)
        print("1. Ensure Strapi admin account exists")
        print("2. Update ADMIN_EMAIL and ADMIN_PASSWORD in this script")
        print("3. Or follow manual creation instructions in PHASE4_STEP1_INSTRUCTIONS.md")
        return False
    
    # Create content type
    success = create_content_type(token)
    if not success:
        print("\n❌ Content type creation failed")
        print("   You may need to create it manually - see PHASE4_STEP1_INSTRUCTIONS.md")
        return False
    
    # Set permissions
    set_permissions(token)
    
    # Verify
    verified = verify_creation()
    
    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    
    if verified:
        print("✅ Content type created and accessible!")
        print("\nNext steps:")
        print("1. Run: cd arknet_fleet_manager && python seed_operational_config.py")
        print("2. Test: cd .. && python test_step1_config_collection.py")
    else:
        print("⚠️  Content type created but may need manual permission setup")
        print("\nManual steps:")
        print("1. Go to: http://localhost:1337/admin")
        print("2. Settings → Roles → Public → Operational-configuration")
        print("3. Enable: find, findOne, create, update")
        print("4. Save")
        print("\nThen:")
        print("5. Run: cd arknet_fleet_manager && python seed_operational_config.py")
        print("6. Test: cd .. && python test_step1_config_collection.py")
    
    print("="*80)
    
    return verified


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
