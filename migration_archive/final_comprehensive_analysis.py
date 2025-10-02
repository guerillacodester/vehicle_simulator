#!/usr/bin/env python3
"""
Simplified comprehensive analysis focusing on what we discovered
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json

# Based on our discovery, here are the actual tables with data:
MIGRATION_TABLES = {
    'drivers': {
        'remote_records': 4,
        'strapi_endpoint': 'drivers',
        'strapi_required': ['driver_id', 'name', 'license_no'],
        'remote_structure': {
            'driver_id': 'uuid NOT NULL',
            'country_id': 'uuid NOT NULL', 
            'name': 'text NOT NULL',
            'license_no': 'text NOT NULL',
            'home_depot_id': 'uuid NULL',
            'employment_status': 'text NOT NULL',
            'created_at': 'timestamp with time zone NOT NULL',
            'updated_at': 'timestamp with time zone NOT NULL'
        },
        'sample_data': {
            'driver_id': '4a68b672-1010-4ec0-b544-ac2f4b38c6b2',
            'country_id': 'df0e7389-600c-47c9-a1e5-0d67a1e5209d',
            'name': 'John Smith',
            'license_no': 'LIC001',
            'home_depot_id': '583e951c-0c5d-4a20-8ce2-0d67a1e5209d',
            'employment_status': 'active'
        }
    },
    'depots': {
        'remote_records': 1,
        'strapi_endpoint': 'depots',
        'strapi_required': ['depot_id', 'name'],
        'remote_structure': {
            'depot_id': 'uuid NOT NULL',
            'country_id': 'uuid NOT NULL',
            'name': 'text NOT NULL',
            'location': 'USER-DEFINED NULL',
            'capacity': 'integer NULL',
            'notes': 'text NULL',
            'created_at': 'timestamp with time zone NOT NULL',
            'updated_at': 'timestamp with time zone NOT NULL'
        },
        'sample_data': {
            'depot_id': '583e951c-0c5d-4a20-8ce2-0d67a1e5209d',
            'country_id': 'df0e7389-600c-47c9-a1e5-0d67a1e5209d',
            'name': 'Bridgetown',
            'location': None,
            'capacity': 100,
            'notes': None
        }
    },
    'routes': {
        'remote_records': 3,
        'strapi_endpoint': 'routes',
        'strapi_required': ['route_id', 'short_name'],
        'remote_structure': {
            'route_id': 'uuid NOT NULL',
            'country_id': 'uuid NOT NULL',
            'short_name': 'text NOT NULL',
            'long_name': 'text NULL',
            'parishes': 'text NULL',
            'is_active': 'boolean NOT NULL',
            'valid_from': 'date NULL',
            'valid_to': 'date NULL',
            'created_at': 'timestamp with time zone NOT NULL',
            'updated_at': 'timestamp with time zone NOT NULL',
            'description': 'text NULL',
            'color': 'character varying NULL'
        },
        'sample_data': {
            'route_id': '0e9018ce-6e2a-42ef-a872-aa0248d2077a',
            'country_id': 'df0e7389-600c-47c9-a1e5-0d67a1e5209d',
            'short_name': '1',
            'long_name': 'route 1',
            'parishes': None,
            'is_active': True,
            'valid_from': '2025-09-10',
            'valid_to': None,
            'description': None,
            'color': None
        }
    },
    'vehicles': {
        'remote_records': 4,
        'strapi_endpoint': 'vehicles',
        'strapi_required': ['vehicle_id', 'reg_code'],
        'remote_structure': {
            'vehicle_id': 'uuid NOT NULL',
            'country_id': 'uuid NOT NULL',
            'reg_code': 'text NOT NULL',
            'home_depot_id': 'uuid NULL',
            'preferred_route_id': 'uuid NULL',
            'status': 'USER-DEFINED NOT NULL',
            'profile_id': 'text NULL',
            'notes': 'text NULL',
            'created_at': 'timestamp with time zone NOT NULL',
            'updated_at': 'timestamp with time zone NOT NULL',
            'capacity': 'integer NULL',
            'assigned_driver_id': 'uuid NULL',
            'assigned_gps_device_id': 'uuid NULL',
            'max_speed_kmh': 'double precision NOT NULL',
            'acceleration_mps2': 'double precision NOT NULL',
            'braking_mps2': 'double precision NOT NULL',
            'eco_mode': 'boolean NOT NULL',
            'performance_profile': 'text NULL'
        },
        'sample_data': {
            'vehicle_id': 'f5ac8768-b526-4bf1-b8f4-33cac761499c',
            'country_id': 'df0e7389-600c-47c9-a1e5-0d67a1e5209d',
            'reg_code': 'ZR232',
            'home_depot_id': '583e951c-0c5d-4a20-8ce2-0d67a1e5209d',
            'preferred_route_id': '3e771e2e-9a93-43ef-a1ef-3a889474893a',
            'status': 'retired',
            'profile_id': None,
            'notes': None,
            'capacity': 16,
            'assigned_driver_id': '70a11999-083e-496f-9870-b738f60edf9a',
            'assigned_gps_device_id': '6f069145-c834-4f17-9f95-eea9d1ade9e1',
            'max_speed_kmh': 100.0,
            'acceleration_mps2': 2.2,
            'braking_mps2': 2.0,
            'eco_mode': False,
            'performance_profile': None
        }
    }
}

def analyze_strapi_content_type(endpoint):
    """Get detailed Strapi content type structure"""
    print(f"\n=== STRAPI CONTENT TYPE: {endpoint.upper()} ===")
    
    # Get existing records to understand full structure
    response = requests.get(f'http://localhost:1337/api/{endpoint}')
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Existing records: {len(data['data'])}")
        
        if data['data']:
            sample = data['data'][0]
            print("📋 Available Strapi fields:")
            for key, value in sample.items():
                if key not in ['id', 'documentId', 'createdAt', 'updatedAt', 'publishedAt']:
                    field_type = type(value).__name__
                    if value is None:
                        field_type = "nullable"
                    print(f"  - {key}: {field_type} (sample: {value})")
            return sample
    else:
        print(f"❌ Could not fetch Strapi records: {response.status_code}")
        return {}

def create_field_mapping(table_name, table_info):
    """Create field mapping based on our knowledge"""
    print(f"\n=== FIELD MAPPING FOR {table_name.upper()} ===")
    
    remote_fields = list(table_info['remote_structure'].keys())
    strapi_required = table_info['strapi_required']
    sample_data = table_info['sample_data']
    
    print(f"📊 Remote fields ({len(remote_fields)}): {remote_fields}")
    print(f"📊 Required Strapi fields: {strapi_required}")
    
    # Create mapping
    field_mappings = {}
    
    # Direct mappings for required fields
    for req_field in strapi_required:
        
        # Check for exact match first
        if req_field in remote_fields:
            field_mappings[req_field] = req_field
            print(f"✅ Direct: {req_field} → {req_field}")
            continue
        
        # Special mapping rules
        mapping_found = False
        
        # ID mappings - Remote UUIDs need to be converted to strings for Strapi
        if req_field.endswith('_id') and req_field in remote_fields:
            field_mappings[req_field] = req_field  # UUID to string conversion
            print(f"🔄 UUID→String: {req_field} → {req_field}")
            mapping_found = True
        
        # Name mappings
        elif req_field == 'name' and 'name' in remote_fields:
            field_mappings['name'] = 'name'
            print(f"✅ Direct: name → name")
            mapping_found = True
        
        # License mapping
        elif req_field == 'license_no' and 'license_no' in remote_fields:
            field_mappings['license_no'] = 'license_no'
            print(f"✅ Direct: license_no → license_no")
            mapping_found = True
        
        # Short name mapping
        elif req_field == 'short_name' and 'short_name' in remote_fields:
            field_mappings['short_name'] = 'short_name'
            print(f"✅ Direct: short_name → short_name")
            mapping_found = True
        
        # Registration code mapping
        elif req_field == 'reg_code' and 'reg_code' in remote_fields:
            field_mappings['reg_code'] = 'reg_code'
            print(f"✅ Direct: reg_code → reg_code")
            mapping_found = True
        
        if not mapping_found:
            print(f"❌ No mapping found for required field: {req_field}")
    
    # Optional field mappings
    optional_mappings = {
        'employment_status': 'employment_status',
        'capacity': 'capacity', 
        'notes': 'notes',
        'is_active': 'is_active',
        'long_name': 'long_name',
        'parishes': 'parishes',
        'description': 'description',
        'color': 'color',
        'valid_from': 'valid_from',
        'valid_to': 'valid_to',
        'profile_id': 'profile_id',
        'max_speed_kmh': 'max_speed_kmh',
        'acceleration_mps2': 'acceleration_mps2',
        'braking_mps2': 'braking_mps2',
        'eco_mode': 'eco_mode',
        'performance_profile': 'performance_profile'
    }
    
    print(f"\n🔄 Optional mappings:")
    for remote_field, strapi_field in optional_mappings.items():
        if remote_field in remote_fields:
            field_mappings[remote_field] = strapi_field
            sample_val = sample_data.get(remote_field, 'N/A')
            print(f"  {remote_field} → {strapi_field} (sample: {sample_val})")
    
    # Check if all required fields are covered
    mapped_strapi_fields = set(field_mappings.values())
    missing_required = set(strapi_required) - mapped_strapi_fields
    
    if missing_required:
        print(f"❌ Missing required Strapi fields: {list(missing_required)}")
        return field_mappings, False
    else:
        print(f"✅ All required fields mapped!")
        return field_mappings, True

def generate_migration_code(table_name, field_mappings, sample_data, is_ready):
    """Generate the migration function"""
    if not is_ready:
        print(f"⚠️  Cannot generate migration code for {table_name} - missing required field mappings")
        return None
    
    print(f"\n=== MIGRATION CODE FOR {table_name.upper()} ===")
    
    singular = table_name[:-1]  # Remove 's'
    
    code = f'''def create_strapi_{singular}(remote_{singular}):
    """Create {singular} in Strapi - FIELD MAPPINGS FROM COMPREHENSIVE ANALYSIS"""
    
    strapi_data = {{
        "data": {{'''
    
    # Add field mappings
    for remote_field, strapi_field in field_mappings.items():
        sample_val = sample_data.get(remote_field)
        
        if isinstance(sample_val, bool):
            code += f'\n            "{strapi_field}": remote_{singular}.get("{remote_field}", False),'
        elif isinstance(sample_val, (int, float)):
            code += f'\n            "{strapi_field}": remote_{singular}.get("{remote_field}"),'
        elif sample_val is None:
            code += f'\n            "{strapi_field}": remote_{singular}.get("{remote_field}"),'
        else:
            # String, UUID, or other - convert to string
            code += f'\n            "{strapi_field}": str(remote_{singular}.get("{remote_field}")) if remote_{singular}.get("{remote_field}") else None,'
    
    code += '''
        }
    }
    
    # Remove None values for optional fields
    strapi_data["data"] = {k: v for k, v in strapi_data["data"].items() if v is not None}
    
    response = requests.post(f'http://localhost:1337/api/''' + table_name + '''',
                           headers={'Content-Type': 'application/json'},
                           json=strapi_data)
    
    if response.status_code in [200, 201]:
        created = response.json()
        return created['data']['id']
    else:
        print(f"Error creating ''' + singular + ''': {response.status_code} - {response.text}")
        return None'''
    
    print(code)
    return code

def main():
    """Run comprehensive analysis"""
    print("🎯 COMPREHENSIVE MIGRATION ANALYSIS - ALL TABLES")
    print("=" * 80)
    
    results = {}
    
    for table_name, table_info in MIGRATION_TABLES.items():
        print(f"\n{'='*60}")
        print(f"ANALYZING: {table_name.upper()}")
        print(f"Remote records: {table_info['remote_records']}")
        print(f"{'='*60}")
        
        # Analyze Strapi structure
        strapi_structure = analyze_strapi_content_type(table_info['strapi_endpoint'])
        
        # Create field mappings
        field_mappings, is_ready = create_field_mapping(table_name, table_info)
        
        # Generate migration code
        migration_code = generate_migration_code(table_name, field_mappings, table_info['sample_data'], is_ready)
        
        results[table_name] = {
            'remote_records': table_info['remote_records'],
            'field_mappings': field_mappings,
            'migration_code': migration_code,
            'ready': is_ready
        }
    
    # Final summary
    print(f"\n{'='*80}")
    print("🎯 FINAL MIGRATION READINESS SUMMARY")
    print(f"{'='*80}")
    
    ready_tables = []
    for table_name, result in results.items():
        status = "✅ READY" if result['ready'] else "❌ NEEDS WORK"
        mappings = len(result['field_mappings'])
        records = result['remote_records']
        print(f"{table_name.upper():<10} | Records: {records:<2} | Mappings: {mappings:<2} | {status}")
        
        if result['ready']:
            ready_tables.append(table_name)
    
    print(f"\n🎉 READY FOR MIGRATION: {ready_tables}")
    print(f"📊 Migration readiness: {len(ready_tables)}/{len(MIGRATION_TABLES)} tables")
    
    if len(ready_tables) == len(MIGRATION_TABLES):
        print("\n✅ ALL TABLES ARE READY FOR MIGRATION!")
        print("🚀 You can now create individual migration scripts for each table.")
    else:
        print(f"\n⚠️  {len(MIGRATION_TABLES) - len(ready_tables)} tables need field mapping fixes")

if __name__ == "__main__":
    main()