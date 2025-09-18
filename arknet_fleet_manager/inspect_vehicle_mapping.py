"""
Database Schema Inspector for Vehicle Migration
==============================================
Intelligently inspect both remote and local vehicle structures 
to understand the mapping requirements.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import sys
import os
import json
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel

class SchemaInspector:
    """Inspect and compare database schemas intelligently"""
    
    def __init__(self):
        self.strapi_base_url = "http://localhost:1337/api"
        
        # Remote database configuration
        self.ssh_config = {
            'ssh_host': 'arknetglobal.com',
            'ssh_port': 22,
            'ssh_user': 'david',
            'ssh_pass': 'Cabbyminnie5!',
            'remote_host': 'localhost',
            'remote_port': 5432,
            'local_port': 6543
        }
        
        self.remote_config = {
            'host': '127.0.0.1',
            'port': 6543,
            'database': 'arknettransit',
            'user': 'david',
            'password': 'Ga25w123!'
        }
        
        self.local_config = {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'arknettransit',
            'user': 'david',
            'password': 'Ga25w123!'
        }
        
        self.tunnel = None
        self.remote_conn = None
        self.local_conn = None
    
    def connect_databases(self):
        """Connect to both remote and local databases"""
        try:
            # Connect to remote via SSH tunnel
            print("🔗 Connecting to remote database...")
            self.tunnel = SSHTunnel(**self.ssh_config)
            self.tunnel.start()
            
            self.remote_conn = psycopg2.connect(**self.remote_config, cursor_factory=RealDictCursor)
            print("✅ Remote database connected")
            
            # Connect to local database
            print("🔗 Connecting to local database...")
            self.local_conn = psycopg2.connect(**self.local_config, cursor_factory=RealDictCursor)
            print("✅ Local database connected")
            
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def get_table_structure(self, conn, table_name: str) -> Dict:
        """Get detailed table structure"""
        try:
            with conn.cursor() as cursor:
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable, 
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                
                # Get sample data (first 3 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                
                return {
                    'columns': columns,
                    'sample_data': sample_data,
                    'row_count': len(sample_data)
                }
        except Exception as e:
            print(f"❌ Error inspecting {table_name}: {e}")
            return {'columns': [], 'sample_data': [], 'row_count': 0}
    
    def inspect_remote_vehicles(self):
        """Inspect remote vehicles table structure"""
        print("\n" + "=" * 60)
        print("🔍 REMOTE DATABASE - Vehicles Table Analysis")
        print("=" * 60)
        
        structure = self.get_table_structure(self.remote_conn, 'vehicles')
        
        print(f"📊 Found {len(structure['columns'])} columns:")
        for col in structure['columns']:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   {col['column_name']:<20} {col['data_type']:<15} {nullable}{default}")
        
        print(f"\n📋 Sample data ({structure['row_count']} rows):")
        for i, row in enumerate(structure['sample_data']):
            print(f"   Row {i+1}:")
            for key, value in row.items():
                print(f"      {key}: {value}")
            print()
        
        return structure
    
    def inspect_local_vehicles(self):
        """Inspect local vehicles table structure"""
        print("\n" + "=" * 60)
        print("🔍 LOCAL DATABASE - Vehicles Table Analysis")
        print("=" * 60)
        
        structure = self.get_table_structure(self.local_conn, 'vehicles')
        
        print(f"📊 Found {len(structure['columns'])} columns:")
        for col in structure['columns']:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   {col['column_name']:<20} {col['data_type']:<15} {nullable}{default}")
        
        print(f"\n📋 Sample data ({structure['row_count']} rows):")
        for i, row in enumerate(structure['sample_data']):
            print(f"   Row {i+1}:")
            for key, value in row.items():
                print(f"      {key}: {value}")
            print()
        
        return structure
    
    def get_strapi_vehicle_schema(self):
        """Get Strapi vehicle content type schema"""
        print("\n" + "=" * 60)
        print("🔍 STRAPI SCHEMA - Vehicle Content Type")
        print("=" * 60)
        
        try:
            # Read the schema file
            schema_path = "arknet-fleet-api/src/api/vehicle/content-types/vehicle/schema.json"
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            print("📋 Strapi Vehicle Attributes:")
            for attr_name, attr_config in schema['attributes'].items():
                attr_type = attr_config.get('type', 'unknown')
                required = attr_config.get('required', False)
                default = attr_config.get('default', '')
                
                if attr_type == 'relation':
                    target = attr_config.get('target', 'unknown')
                    relation = attr_config.get('relation', 'unknown')
                    print(f"   {attr_name:<20} {attr_type:<10} → {target} ({relation})")
                else:
                    req_str = "REQUIRED" if required else "optional"
                    default_str = f" DEFAULT: {default}" if default != '' else ""
                    print(f"   {attr_name:<20} {attr_type:<10} {req_str}{default_str}")
            
            return schema
        except Exception as e:
            print(f"❌ Error reading Strapi schema: {e}")
            return {}
    
    def analyze_mapping_requirements(self, remote_structure, local_structure, strapi_schema):
        """Analyze and suggest intelligent mapping"""
        print("\n" + "=" * 60)
        print("🧠 INTELLIGENT MAPPING ANALYSIS")
        print("=" * 60)
        
        remote_cols = {col['column_name']: col for col in remote_structure['columns']}
        local_cols = {col['column_name']: col for col in local_structure['columns']}
        strapi_attrs = strapi_schema.get('attributes', {})
        
        print("📊 Column Comparison:")
        print(f"   Remote columns: {len(remote_cols)}")
        print(f"   Local columns:  {len(local_cols)}")
        print(f"   Strapi attrs:   {len(strapi_attrs)}")
        
        print("\n🔍 Mapping Analysis:")
        
        # Direct matches
        direct_matches = []
        for remote_col in remote_cols:
            if remote_col in strapi_attrs:
                direct_matches.append(remote_col)
                print(f"   ✅ DIRECT: {remote_col} → {remote_col}")
        
        # Possible relationship mappings
        print(f"\n🔗 Relationship Mappings Needed:")
        for attr_name, attr_config in strapi_attrs.items():
            if attr_config.get('type') == 'relation':
                target = attr_config.get('target', '')
                print(f"   🔗 {attr_name} → {target}")
                
                # Look for potential foreign key columns in remote
                potential_fks = [col for col in remote_cols.keys() 
                               if attr_name.replace('_', '') in col.replace('_', '').lower() 
                               or 'id' in col.lower()]
                if potential_fks:
                    print(f"      Potential remote columns: {potential_fks}")
        
        # Unmapped remote columns
        unmapped_remote = [col for col in remote_cols if col not in strapi_attrs]
        if unmapped_remote:
            print(f"\n⚠️  Unmapped remote columns:")
            for col in unmapped_remote:
                col_info = remote_cols[col]
                print(f"   - {col} ({col_info['data_type']})")
        
        # Missing in remote
        strapi_only = [attr for attr in strapi_attrs if attr not in remote_cols 
                      and strapi_attrs[attr].get('type') != 'relation']
        if strapi_only:
            print(f"\n💡 Strapi-only attributes (will use defaults):")
            for attr in strapi_only:
                attr_config = strapi_attrs[attr]
                default = attr_config.get('default', 'null')
                print(f"   - {attr} (default: {default})")
    
    def run_inspection(self):
        """Run complete inspection"""
        print("=" * 70)
        print("🔍 INTELLIGENT DATABASE SCHEMA INSPECTION")
        print("=" * 70)
        
        if not self.connect_databases():
            return False
        
        try:
            # Inspect all three sources
            remote_structure = self.inspect_remote_vehicles()
            local_structure = self.inspect_local_vehicles()
            strapi_schema = self.get_strapi_vehicle_schema()
            
            # Analyze mapping requirements
            self.analyze_mapping_requirements(remote_structure, local_structure, strapi_schema)
            
            return True
        except Exception as e:
            print(f"❌ Inspection failed: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up connections"""
        if self.remote_conn:
            self.remote_conn.close()
        if self.local_conn:
            self.local_conn.close()
        if self.tunnel:
            self.tunnel.stop()

def main():
    """Main execution"""
    inspector = SchemaInspector()
    
    try:
        success = inspector.run_inspection()
        if success:
            print("\n" + "=" * 50)
            print("❓ QUESTIONS FOR YOU:")
            print("=" * 50)
            print("1. Which remote columns should map to which Strapi relationships?")
            print("2. What should we do with unmapped remote columns?")
            print("3. Are there any data transformations needed?")
            print("4. Should we create default values for missing data?")
            print("\nPlease review the analysis above and let me know how to proceed!")
        else:
            print("❌ Inspection failed")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    main()