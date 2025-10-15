"""
Direct Schema File Creation for Strapi
=======================================
Creates the schema.json file directly in the Strapi project structure.
This is more reliable than using the API for Strapi v5.
"""

import json
import os
from pathlib import Path

# Schema definition
SCHEMA = {
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

def find_strapi_project():
    """Try to locate the Strapi project directory."""
    possible_paths = [
        Path("arknet-fleet-api"),
        Path("../arknet-fleet-api"),
        Path("arknet_fleet_manager/arknet-fleet-api"),
        Path("../../arknet-fleet-api"),
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "src" / "api").exists():
            return path
    
    return None

def create_schema_file(strapi_path):
    """Create the schema.json file in the Strapi project."""
    # Create directory structure
    api_dir = strapi_path / "src" / "api" / "operational-configuration"
    content_types_dir = api_dir / "content-types" / "operational-configuration"
    
    print(f"📁 Creating directory: {content_types_dir}")
    content_types_dir.mkdir(parents=True, exist_ok=True)
    
    # Write schema.json
    schema_file = content_types_dir / "schema.json"
    print(f"📝 Writing schema: {schema_file}")
    
    with open(schema_file, 'w') as f:
        json.dump(SCHEMA, f, indent=2)
    
    print(f"   ✅ Schema file created")
    
    # Create controllers directory
    controllers_dir = api_dir / "controllers"
    controllers_dir.mkdir(exist_ok=True)
    
    controller_file = controllers_dir / "operational-configuration.js"
    if not controller_file.exists():
        print(f"📝 Creating controller: {controller_file}")
        with open(controller_file, 'w') as f:
            f.write("""'use strict';

/**
 * operational-configuration controller
 */

const { createCoreController } = require('@strapi/strapi').factories;

module.exports = createCoreController('api::operational-configuration.operational-configuration');
""")
        print(f"   ✅ Controller created")
    
    # Create routes directory
    routes_dir = api_dir / "routes"
    routes_dir.mkdir(exist_ok=True)
    
    route_file = routes_dir / "operational-configuration.js"
    if not route_file.exists():
        print(f"📝 Creating routes: {route_file}")
        with open(route_file, 'w') as f:
            f.write("""'use strict';

/**
 * operational-configuration router
 */

const { createCoreRouter } = require('@strapi/strapi').factories;

module.exports = createCoreRouter('api::operational-configuration.operational-configuration');
""")
        print(f"   ✅ Routes created")
    
    # Create services directory
    services_dir = api_dir / "services"
    services_dir.mkdir(exist_ok=True)
    
    service_file = services_dir / "operational-configuration.js"
    if not service_file.exists():
        print(f"📝 Creating service: {service_file}")
        with open(service_file, 'w') as f:
            f.write("""'use strict';

/**
 * operational-configuration service
 */

const { createCoreService } = require('@strapi/strapi').factories;

module.exports = createCoreService('api::operational-configuration.operational-configuration');
""")
        print(f"   ✅ Service created")
    
    return True

def main():
    print("="*80)
    print("DIRECT SCHEMA FILE CREATION")
    print("="*80)
    
    print("\n🔍 Locating Strapi project...")
    strapi_path = find_strapi_project()
    
    if not strapi_path:
        print("   ❌ Could not find Strapi project")
        print("\n   Please provide the path to arknet-fleet-api:")
        manual_path = input("   Path: ").strip()
        
        if manual_path:
            strapi_path = Path(manual_path)
            if not strapi_path.exists():
                print(f"   ❌ Path does not exist: {strapi_path}")
                return False
        else:
            print("   ❌ No path provided")
            return False
    
    print(f"   ✅ Found Strapi project at: {strapi_path.absolute()}")
    
    # Create schema
    success = create_schema_file(strapi_path)
    
    if success:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print("\n📋 Schema files created in Strapi project")
        print("\nNext steps:")
        print("1. Restart Strapi to load the new content type:")
        print("   cd arknet-fleet-api && npm run develop")
        print("\n2. Enable API permissions:")
        print("   - Go to: http://localhost:1337/admin")
        print("   - Settings → Roles → Public → Operational-configuration")
        print("   - Enable: find, findOne, create, update")
        print("   - Save")
        print("\n3. Seed initial data:")
        print("   python seed_operational_config.py")
        print("\n4. Test:")
        print("   cd .. && python test_step1_config_collection.py")
        print("="*80)
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
