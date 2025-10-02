#!/usr/bin/env python3
"""
Alternative: Create Route-Shapes Content Type via File Generation
================================================================
Generates the necessary Strapi schema files directly.
This bypasses the admin API requirement.
"""
import os
import json

def create_route_shapes_schema_files():
    """Create the schema files directly in Strapi"""
    print("📁 CREATING ROUTE-SHAPES SCHEMA FILES DIRECTLY")
    print("=" * 60)
    
    # Path to Strapi API schemas
    strapi_api_path = "arknet-fleet-api/src/api"
    route_shapes_path = os.path.join(strapi_api_path, "route-shape")
    
    print(f"Target path: {route_shapes_path}")
    
    # Check if Strapi API directory exists
    if not os.path.exists(strapi_api_path):
        print(f"❌ Strapi API directory not found: {strapi_api_path}")
        print("💡 Make sure you're running this from the correct directory")
        return False
    
    try:
        # Create route-shape directory structure
        os.makedirs(route_shapes_path, exist_ok=True)
        os.makedirs(os.path.join(route_shapes_path, "content-types", "route-shape"), exist_ok=True)
        os.makedirs(os.path.join(route_shapes_path, "controllers"), exist_ok=True)
        os.makedirs(os.path.join(route_shapes_path, "routes"), exist_ok=True)
        os.makedirs(os.path.join(route_shapes_path, "services"), exist_ok=True)
        
        # 1. Schema definition
        schema_content = {
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
            "pluginOptions": {},
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
        
        # Write schema file
        schema_file = os.path.join(route_shapes_path, "content-types", "route-shape", "schema.json")
        with open(schema_file, 'w') as f:
            json.dump(schema_content, f, indent=2)
        print(f"✅ Created schema file: {schema_file}")
        
        # 2. Controller
        controller_content = '''module.exports = require('@strapi/strapi').factories.createCoreController('api::route-shape.route-shape');
'''
        
        controller_file = os.path.join(route_shapes_path, "controllers", "route-shape.js")
        with open(controller_file, 'w') as f:
            f.write(controller_content)
        print(f"✅ Created controller file: {controller_file}")
        
        # 3. Routes
        routes_content = '''module.exports = require('@strapi/strapi').factories.createCoreRouter('api::route-shape.route-shape');
'''
        
        routes_file = os.path.join(route_shapes_path, "routes", "route-shape.js")
        with open(routes_file, 'w') as f:
            f.write(routes_content)
        print(f"✅ Created routes file: {routes_file}")
        
        # 4. Service
        service_content = '''module.exports = require('@strapi/strapi').factories.createCoreService('api::route-shape.route-shape');
'''
        
        service_file = os.path.join(route_shapes_path, "services", "route-shape.js")
        with open(service_file, 'w') as f:
            f.write(service_content)
        print(f"✅ Created service file: {service_file}")
        
        print(f"\n🎉 Route-shapes content type files created successfully!")
        print(f"📁 Created directory structure:")
        print(f"   {route_shapes_path}/")
        print(f"   ├── content-types/route-shape/schema.json")
        print(f"   ├── controllers/route-shape.js")
        print(f"   ├── routes/route-shape.js")
        print(f"   └── services/route-shape.js")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema files: {e}")
        return False

def restart_strapi_instruction():
    """Provide instructions to restart Strapi"""
    print(f"\n🔄 RESTART STRAPI TO APPLY CHANGES")
    print("=" * 60)
    print("1. Stop the current Strapi server (Ctrl+C)")
    print("2. Restart Strapi: npm run develop")
    print("3. The new route-shapes content type will be available")
    print("4. Run the next step once Strapi has restarted")

if __name__ == "__main__":
    print("📁 ALTERNATIVE: DIRECT FILE CREATION FOR ROUTE-SHAPES")
    print("=" * 80)
    
    if create_route_shapes_schema_files():
        restart_strapi_instruction()
    else:
        print("❌ Failed to create schema files")
        print("💡 You may need to create the content type manually in Strapi admin")