"""
Interactive Content Type Creator
=================================
Creates operational-configurations content type with user-provided credentials.
More secure than hardcoding credentials.
"""

import requests
import json
import sys
import time
import getpass

STRAPI_URL = "http://localhost:1337"


def get_credentials():
    """Prompt user for admin credentials."""
    print("\n🔐 Strapi Admin Authentication Required")
    print("-" * 40)
    email = input("Admin Email: ").strip()
    password = getpass.getpass("Admin Password: ")
    return email, password


def authenticate(email, password):
    """Authenticate and get admin JWT token."""
    print("\n🔐 Authenticating...")
    
    try:
        response = requests.post(
            f"{STRAPI_URL}/admin/login",
            json={"email": email, "password": password},
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
                return None
        else:
            print(f"   ❌ Authentication failed (status: {response.status_code})")
            print(f"   Error: {response.json().get('error', {}).get('message', 'Unknown')}")
            return None
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


def create_content_type(token):
    """Create the operational-configurations content type."""
    print("\n📋 Creating operational-configurations content type...")
    
    # Strapi v5 uses component schema format
    content_type_data = {
        "component": {
            "category": "api",
            "displayName": "operational-configuration",
            "icon": "cog",
            "attributes": {
                "section": {"type": "string", "required": True},
                "parameter": {"type": "string", "required": True},
                "value": {"type": "json", "required": True},
                "value_type": {
                    "type": "enumeration",
                    "enum": ["number", "string", "boolean", "object"],
                    "required": True
                },
                "default_value": {"type": "json", "required": True},
                "constraints": {"type": "json"},
                "description": {"type": "text"},
                "display_name": {"type": "string"},
                "ui_group": {"type": "string"},
                "requires_restart": {"type": "boolean", "default": False}
            }
        }
    }
    
    # Try component creation first (Strapi v5 pattern)
    try:
        print("   Attempting component creation...")
        response = requests.post(
            f"{STRAPI_URL}/content-type-builder/components",
            json=content_type_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code in [200, 201]:
            print("   ✅ Created as component")
            print("   ⏳ Strapi is restarting...")
            time.sleep(30)
            return True
    except Exception as e:
        print(f"   Component creation failed: {e}")
    
    # Fall back to direct schema file creation
    print("   Trying direct content type creation...")
    
    content_type_schema = {
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
            "section": {"type": "string", "required": True},
            "parameter": {"type": "string", "required": True},
            "value": {"type": "json", "required": True},
            "value_type": {
                "type": "enumeration",
                "enum": ["number", "string", "boolean", "object"],
                "required": True
            },
            "default_value": {"type": "json", "required": True},
            "constraints": {"type": "json"},
            "description": {"type": "text"},
            "display_name": {"type": "string"},
            "ui_group": {"type": "string"},
            "requires_restart": {"type": "boolean", "default": False}
        }
    }
    
    try:
        response = requests.post(
            f"{STRAPI_URL}/content-type-builder/content-types",
            json={"contentType": content_type_schema},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code in [200, 201]:
            print("   ✅ Content type created successfully")
            print("   ⏳ Strapi is restarting (wait 30-60 seconds)...")
            
            # Wait for restart
            print("\n⏳ Waiting for Strapi restart...")
            for i in range(12):  # 60 seconds max
                time.sleep(5)
                try:
                    health = requests.get(f"{STRAPI_URL}/_health", timeout=2)
                    if health.status_code == 200:
                        print("   ✅ Strapi is back online!")
                        break
                except:
                    print(f"   ... {(i+1)*5}s elapsed...")
            
            return True
        else:
            print(f"   ❌ Failed (status: {response.status_code})")
            error_msg = response.text[:300]
            print(f"   Error: {error_msg}")
            
            if "already exists" in error_msg.lower():
                print("   ℹ️  Content type may already exist - this is okay!")
                return True
            
            return False
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    """Main execution."""
    print("="*80)
    print("INTERACTIVE CONTENT TYPE CREATION")
    print("="*80)
    
    # Check Strapi
    print("\n🔍 Checking Strapi...")
    try:
        requests.get(f"{STRAPI_URL}/_health", timeout=5)
        print("   ✅ Strapi is running")
    except:
        print(f"   ❌ Strapi not responding at {STRAPI_URL}")
        return False
    
    # Get credentials
    email, password = get_credentials()
    
    # Authenticate
    token = authenticate(email, password)
    if not token:
        print("\n❌ Authentication failed")
        print("   Make sure you have an admin account at: http://localhost:1337/admin")
        return False
    
    # Create content type
    success = create_content_type(token)
    
    if success:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print("\nContent type created. Now:")
        print("1. Enable API permissions (if needed):")
        print("   - Go to: http://localhost:1337/admin")
        print("   - Settings → Roles → Public → Operational-configuration")
        print("   - Enable: find, findOne, create, update")
        print("   - Save")
        print("\n2. Seed initial data:")
        print("   python seed_operational_config.py")
        print("\n3. Test:")
        print("   cd .. && python test_step1_config_collection.py")
    else:
        print("\n❌ Creation failed - see error above")
    
    print("="*80)
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
