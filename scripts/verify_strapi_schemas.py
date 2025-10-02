"""
Verify Strapi Content Type Schemas
Checks that all new geographic content types are properly defined
"""
import json
import os
from pathlib import Path

def check_schema_file(schema_path, expected_name):
    """Check if a schema file exists and is valid"""
    if not os.path.exists(schema_path):
        return False, f"❌ Schema file not found: {schema_path}"
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Check basic structure
        if schema.get('kind') != 'collectionType':
            return False, f"❌ Invalid kind: {schema.get('kind')}"
        
        if schema.get('info', {}).get('singularName') != expected_name:
            return False, f"❌ Invalid singularName: {schema.get('info', {}).get('singularName')}"
        
        # Check attributes exist
        attributes = schema.get('attributes', {})
        if not attributes:
            return False, "❌ No attributes defined"
        
        return True, f"✅ {expected_name}: Valid ({len(attributes)} attributes)"
        
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

def verify_schemas():
    """Verify all geographic content type schemas"""
    print("=" * 80)
    print("Strapi Content Type Schema Verification")
    print("=" * 80)
    
    base_path = Path(__file__).parent.parent / 'arknet_fleet_manager' / 'arknet-fleet-api' / 'src' / 'api'
    
    schemas_to_check = [
        ('poi', 'poi/content-types/poi/schema.json'),
        ('landuse-zone', 'landuse-zone/content-types/landuse-zone/schema.json'),
        ('region', 'region/content-types/region/schema.json'),
        ('spawn-config', 'spawn-config/content-types/spawn-config/schema.json'),
    ]
    
    all_valid = True
    
    print("\n📋 New Geographic Content Types:")
    print("-" * 80)
    
    for name, relative_path in schemas_to_check:
        schema_path = base_path / relative_path
        valid, message = check_schema_file(schema_path, name)
        print(f"  {message}")
        if not valid:
            all_valid = False
    
    # Check updated country schema
    print("\n📋 Updated Existing Content Types:")
    print("-" * 80)
    
    country_schema_path = base_path / 'country' / 'content-types' / 'country' / 'schema.json'
    
    try:
        with open(country_schema_path, 'r', encoding='utf-8') as f:
            country_schema = json.load(f)
        
        attributes = country_schema.get('attributes', {})
        new_relations = ['pois', 'landuse_zones', 'regions', 'spawn_config']
        
        missing = []
        found = []
        
        for relation in new_relations:
            if relation in attributes:
                found.append(relation)
            else:
                missing.append(relation)
        
        if found:
            print(f"  ✅ country: Added {len(found)} new relations:")
            for rel in found:
                rel_target = attributes[rel].get('target', 'unknown')
                print(f"     - {rel} → {rel_target}")
        
        if missing:
            print(f"  ⚠️  country: Missing relations: {', '.join(missing)}")
            all_valid = False
        
    except Exception as e:
        print(f"  ❌ country: Error checking schema: {e}")
        all_valid = False
    
    # Summary
    print("\n" + "=" * 80)
    
    if all_valid:
        print("✅ All Schemas Valid!")
        print("\n📊 Summary:")
        print("  - 4 new content types created (POI, Land Use Zone, Region, Spawn Config)")
        print("  - Country schema updated with 4 new relations")
        print("  - Total geographic attributes: ~100+ fields")
        
        print("\n⏭️  Next Steps:")
        print("  1. Restart Strapi to generate database tables:")
        print("     cd arknet_fleet_manager\\arknet-fleet-api")
        print("     npm run develop")
        print("\n  2. Verify tables created in database:")
        print("     python scripts/verify_strapi_tables.py")
        print("\n  3. Load Barbados GeoJSON data:")
        print("     python scripts/load_barbados_data.py")
        
    else:
        print("❌ Some Schemas Invalid - Please Review Errors Above")
    
    print("=" * 80)
    
    return all_valid

if __name__ == "__main__":
    success = verify_schemas()
    exit(0 if success else 1)
