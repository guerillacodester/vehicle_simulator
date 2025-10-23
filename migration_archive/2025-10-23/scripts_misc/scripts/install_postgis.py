"""
Install PostGIS Extension in arknettransit Database
"""
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'arknet_fleet_manager', 'arknet-fleet-api', '.env')
load_dotenv(env_path)

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', '127.0.0.1'),
    'port': os.getenv('DATABASE_PORT', '5432'),
    'database': os.getenv('DATABASE_NAME', 'arknettransit'),
    'user': os.getenv('DATABASE_USERNAME', 'david'),
    'password': os.getenv('DATABASE_PASSWORD', '')
}

def install_postgis():
    """Install PostGIS extension in the database"""
    print("=" * 80)
    print("PostGIS Extension Installation")
    print("=" * 80)
    
    try:
        # Connect to database
        print(f"\n📡 Connecting to database: {DB_CONFIG['database']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if PostGIS is already installed
        print("\n🔍 Checking current PostGIS status...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'postgis'
            );
        """)
        postgis_installed = cursor.fetchone()[0]
        
        if postgis_installed:
            print("✅ PostGIS is already installed!")
            cursor.execute("SELECT PostGIS_version();")
            version = cursor.fetchone()[0]
            print(f"   Version: {version}")
        else:
            print("❌ PostGIS is not installed")
            print("\n🔧 Installing PostGIS extension...")
            
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                print("✅ PostGIS extension created successfully!")
                
                # Verify installation
                cursor.execute("SELECT PostGIS_version();")
                version = cursor.fetchone()[0]
                print(f"   Version: {version}")
                
            except psycopg2.Error as e:
                print(f"❌ Failed to install PostGIS: {e}")
                print("\n🔧 Troubleshooting:")
                print("   1. PostGIS must be installed on your system first")
                print("   2. Download from: https://postgis.net/install/")
                print("   3. Or use Stack Builder (comes with PostgreSQL)")
                print("   4. Ensure your PostgreSQL user has SUPERUSER privileges")
                return False
        
        # Check for additional PostGIS extensions
        print("\n🔍 Checking optional PostGIS extensions...")
        
        optional_extensions = [
            ('postgis_topology', 'Topology support'),
            ('postgis_raster', 'Raster data support'),
            ('postgis_sfcgal', 'Advanced 3D operations')
        ]
        
        for ext_name, description in optional_extensions:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM pg_available_extensions 
                    WHERE name = '{ext_name}'
                );
            """)
            available = cursor.fetchone()[0]
            
            if available:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_extension 
                        WHERE extname = '{ext_name}'
                    );
                """)
                installed = cursor.fetchone()[0]
                
                if installed:
                    print(f"   ✅ {ext_name}: Installed ({description})")
                else:
                    print(f"   ⚠️  {ext_name}: Available but not installed ({description})")
            else:
                print(f"   ❌ {ext_name}: Not available ({description})")
        
        # Test PostGIS functionality
        print("\n🧪 Testing PostGIS functionality...")
        
        test_queries = [
            ("Point creation", "SELECT ST_AsText(ST_MakePoint(-59.6202, 13.0969));"),
            ("Distance calculation", "SELECT ST_Distance(ST_MakePoint(0,0), ST_MakePoint(1,1));"),
            ("GeoJSON support", "SELECT ST_AsGeoJSON(ST_MakePoint(-59.6202, 13.0969));")
        ]
        
        for test_name, query in test_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                print(f"   ✅ {test_name}: Working")
                print(f"      Result: {result}")
            except Exception as e:
                print(f"   ❌ {test_name}: Failed - {e}")
        
        print("\n" + "=" * 80)
        print("✅ PostGIS Installation Complete!")
        print("=" * 80)
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("   1. Ensure PostgreSQL is running")
        print("   2. Check database credentials in .env file")
        print("   3. Verify database exists: arknettransit")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = install_postgis()
    exit(0 if success else 1)
