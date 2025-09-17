"""
Database Schema Inspector
========================
Compare table structures between remote and local databases
to understand the schema differences and create proper mapping.
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrate_data import SSHTunnel

def get_table_structure(conn, table_name):
    """Get detailed table structure"""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        return cursor.fetchall()

def get_all_tables(conn):
    """Get all table names from database"""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return [row['table_name'] for row in cursor.fetchall()]

def inspect_remote_database():
    """Inspect remote database structure"""
    print("🔍 Inspecting REMOTE database structure...")
    
    ssh_config = {
        'ssh_host': 'arknetglobal.com',
        'ssh_port': 22,
        'ssh_user': 'david',
        'ssh_pass': 'Cabbyminnie5!',
        'remote_host': 'localhost',
        'remote_port': 5432,
        'local_port': 6543
    }
    
    remote_config = {
        'host': '127.0.0.1',
        'port': 6543,
        'database': 'arknettransit',
        'user': 'david',
        'password': 'Ga25w123!'
    }
    
    tunnel = None
    conn = None
    
    try:
        tunnel = SSHTunnel(**ssh_config)
        tunnel.start()
        
        conn = psycopg2.connect(**remote_config, cursor_factory=RealDictCursor)
        
        tables = get_all_tables(conn)
        print(f"Remote database has {len(tables)} tables:")
        
        remote_schema = {}
        for table in tables:
            structure = get_table_structure(conn, table)
            remote_schema[table] = structure
            print(f"\n📋 Table: {table}")
            print(f"   Columns: {len(structure)}")
            for col in structure[:3]:  # Show first 3 columns
                print(f"   - {col['column_name']} ({col['data_type']})")
            if len(structure) > 3:
                print(f"   ... and {len(structure) - 3} more columns")
                
        return remote_schema
        
    except Exception as e:
        print(f"❌ Error inspecting remote database: {e}")
        return {}
        
    finally:
        if conn:
            conn.close()
        if tunnel:
            tunnel.stop()

def inspect_local_database():
    """Inspect local database structure"""
    print("\n🔍 Inspecting LOCAL database structure...")
    
    local_config = {
        'host': '127.0.0.1',
        'port': 5432,
        'database': 'arknettransit',
        'user': 'david',
        'password': 'Ga25w123!'
    }
    
    try:
        conn = psycopg2.connect(**local_config, cursor_factory=RealDictCursor)
        
        tables = get_all_tables(conn)
        print(f"Local database has {len(tables)} tables:")
        
        local_schema = {}
        
        # Focus on our content type tables (not Strapi admin tables)
        content_tables = [t for t in tables if not t.startswith(('admin_', 'files', 'i18n_', 'strapi_', 'up_'))]
        
        print(f"\nContent type tables ({len(content_tables)}):")
        for table in content_tables:
            structure = get_table_structure(conn, table)
            local_schema[table] = structure
            print(f"\n📋 Table: {table}")
            print(f"   Columns: {len(structure)}")
            for col in structure:
                print(f"   - {col['column_name']} ({col['data_type']})")
                
        return local_schema
        
    except Exception as e:
        print(f"❌ Error inspecting local database: {e}")
        return {}
        
    finally:
        if conn:
            conn.close()

def compare_schemas(remote_schema, local_schema):
    """Compare remote and local schemas"""
    print("\n" + "="*60)
    print("SCHEMA COMPARISON")
    print("="*60)
    
    print("\n🔍 Looking for matching tables...")
    
    # Look for similar table names
    remote_tables = set(remote_schema.keys())
    local_tables = set(local_schema.keys())
    
    print(f"\nRemote tables: {sorted(remote_tables)}")
    print(f"\nLocal tables: {sorted(local_tables)}")
    
    # Try to find mappings
    possible_mappings = {}
    
    for remote_table in remote_tables:
        # Direct match
        if remote_table in local_tables:
            possible_mappings[remote_table] = remote_table
        # Plural/singular variations
        elif remote_table.rstrip('s') in local_tables:
            possible_mappings[remote_table] = remote_table.rstrip('s')
        elif remote_table + 's' in local_tables:
            possible_mappings[remote_table] = remote_table + 's'
    
    print(f"\n🎯 Possible table mappings:")
    for remote, local in possible_mappings.items():
        print(f"   {remote} → {local}")
        
        # Compare column structures
        remote_cols = [col['column_name'] for col in remote_schema[remote]]
        local_cols = [col['column_name'] for col in local_schema[local]]
        
        print(f"      Remote columns: {remote_cols[:5]}{'...' if len(remote_cols) > 5 else ''}")
        print(f"      Local columns:  {local_cols[:5]}{'...' if len(local_cols) > 5 else ''}")
    
    return possible_mappings

def main():
    """Main inspection function"""
    print("=" * 60)
    print("ArkNet Transit Database Schema Inspector")
    print("=" * 60)
    
    remote_schema = inspect_remote_database()
    local_schema = inspect_local_database()
    
    if remote_schema and local_schema:
        mappings = compare_schemas(remote_schema, local_schema)
        
        print(f"\n💡 Found {len(mappings)} potential table mappings")
        print("\n⚠️  The schemas are different because:")
        print("   - Remote DB: Original FastAPI/SQLAlchemy schema")
        print("   - Local DB:  Strapi-generated schema with different conventions")
        print("\n🔧 We need to create a custom mapping script!")
        
    else:
        print("❌ Could not inspect both databases")

if __name__ == "__main__":
    main()