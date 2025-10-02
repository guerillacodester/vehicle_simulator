"""
Verify Strapi Database Tables
Checks that Strapi has auto-generated the geographic tables
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'arknet_fleet_manager', 'arknet-fleet-api', '.env')
load_dotenv(env_path)

DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
    'port': os.getenv('DATABASE_PORT', '5432'),
    'database': os.getenv('DATABASE_NAME', 'arknettransit'),
    'user': os.getenv('DATABASE_USERNAME', 'david'),
    'password': os.getenv('DATABASE_PASSWORD', '')
}

def verify_tables():
    """Verify that Strapi has created the new geographic tables"""
    print("=" * 80)
    print("Strapi Database Table Verification")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Tables to check
        expected_tables = {
            'pois': 'Points of Interest',
            'landuse_zones': 'Land Use Zones',
            'regions': 'Regions/Parishes',
            'spawn_configs': 'Spawn Configurations'
        }
        
        print(f"\n📡 Connected to database: {DB_CONFIG['database']}")
        print("\n🔍 Checking for new geographic tables...")
        print("-" * 80)
        
        all_found = True
        table_info = []
        
        for table_name, description in expected_tables.items():
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            
            exists = cursor.fetchone()[0]
            
            if exists:
                # Get column count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = %s;
                """, (table_name,))
                col_count = cursor.fetchone()[0]
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = cursor.fetchone()[0]
                except:
                    row_count = "N/A"
                
                print(f"  ✅ {table_name}: Exists ({col_count} columns, {row_count} rows)")
                print(f"     {description}")
                table_info.append((table_name, col_count, row_count))
            else:
                print(f"  ❌ {table_name}: NOT FOUND")
                print(f"     {description}")
                all_found = False
        
        # Check updated country table for new relation columns
        print("\n🔍 Checking country table for new relation support...")
        print("-" * 80)
        
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'countries'
            ORDER BY ordinal_position;
        """)
        
        country_columns = cursor.fetchall()
        print(f"  ✅ countries: {len(country_columns)} columns")
        
        # Note: Relations in Strapi are managed via link tables or foreign keys
        # The country table won't have direct columns for oneToMany relations
        # But we can check if the reverse foreign keys exist in the new tables
        
        reverse_fk_checks = [
            ('pois', 'country_id'),
            ('landuse_zones', 'country_id'),
            ('regions', 'country_id'),
            ('spawn_configs', 'country_id')
        ]
        
        print("\n🔍 Checking foreign key relationships...")
        print("-" * 80)
        
        for table_name, fk_column in reverse_fk_checks:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = '{fk_column}'
                );
            """)
            
            exists = cursor.fetchone()[0]
            
            if exists:
                print(f"  ✅ {table_name}.{fk_column} → countries.id")
            else:
                print(f"  ⚠️  {table_name}.{fk_column} not found (may use different naming)")
        
        # PostGIS check
        print("\n🔍 Checking PostGIS status...")
        print("-" * 80)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'postgis'
            );
        """)
        postgis_installed = cursor.fetchone()[0]
        
        if postgis_installed:
            cursor.execute("SELECT PostGIS_version();")
            version = cursor.fetchone()[0]
            print(f"  ✅ PostGIS: Installed (Version: {version})")
        else:
            print(f"  ⚠️  PostGIS: NOT INSTALLED")
            print(f"     Geographic queries will use lat/lon fields instead")
            print(f"     See POSTGIS_WINDOWS_INSTALL.md for installation instructions")
        
        # Summary
        print("\n" + "=" * 80)
        
        if all_found:
            print("✅ All Geographic Tables Created Successfully!")
            
            print("\n📊 Database Summary:")
            print(f"  - New geographic tables: {len(table_info)}")
            print(f"  - Total columns across new tables: {sum(t[1] for t in table_info)}")
            print(f"  - PostGIS: {'Installed' if postgis_installed else 'Not Installed'}")
            
            print("\n⏭️  Next Steps:")
            print("  1. Load Barbados GeoJSON data:")
            print("     python scripts/load_barbados_data.py")
            print("\n  2. Verify data in Strapi Admin:")
            print("     http://localhost:1337/admin")
            print("     Content Manager → POI / Land Use Zone / Region")
            
            if not postgis_installed:
                print("\n  3. (Optional) Install PostGIS for advanced spatial queries:")
                print("     See POSTGIS_WINDOWS_INSTALL.md")
        else:
            print("❌ Some Tables Missing!")
            print("\n🔧 Troubleshooting:")
            print("  1. Ensure Strapi was restarted after creating schema files")
            print("  2. Check Strapi console for errors")
            print("  3. Delete arknet-fleet-api/.cache and restart")
            print("  4. Verify schema.json files are valid JSON")
        
        print("=" * 80)
        
        cursor.close()
        conn.close()
        
        return all_found
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check database credentials in .env file")
        print("  3. Ensure Strapi has been started at least once")
        return False

if __name__ == "__main__":
    success = verify_tables()
    exit(0 if success else 1)
