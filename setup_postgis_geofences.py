"""
Setup PostGIS Geofence Views
This script creates materialized views for fast spatial queries
"""

import psycopg2
from psycopg2 import sql

# Database config from .env
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'arknettransit',
    'user': 'david',
    'password': 'Ga25w123!'
}

def run_sql_file(cursor, sql_file_path):
    """Run SQL commands from file"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_commands = f.read()
    
    cursor.execute(sql_commands)

def setup_postgis_views():
    """Create PostGIS materialized views for geofences"""
    
    print("\n" + "="*60)
    print("SETUP POSTGIS GEOFENCE VIEWS")
    print("="*60)
    
    # Connect to database
    print("\n📡 Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        print("  ✓ Connected to database: arknettransit")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return
    
    try:
        # Run SQL file
        sql_file = "arknet_fleet_manager/create_geofence_postgis_views.sql"
        print(f"\n🔧 Running SQL script: {sql_file}")
        
        run_sql_file(cursor, sql_file)
        
        print("  ✓ SQL script executed successfully")
        
        # Commit changes
        conn.commit()
        print("  ✓ Changes committed")
        
        # Verify views created
        print("\n🔍 Verifying materialized views...")
        
        cursor.execute("""
            SELECT matviewname 
            FROM pg_matviews 
            WHERE schemaname = 'public' 
            AND matviewname LIKE 'geofence%'
            ORDER BY matviewname
        """)
        
        matviews = cursor.fetchall()
        if matviews:
            print(f"  ✓ Found {len(matviews)} materialized views:")
            for mv in matviews:
                print(f"    - {mv[0]}")
        else:
            print("  ⚠️  No materialized views found")
        
        # Check regular views
        cursor.execute("""
            SELECT viewname 
            FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname LIKE 'geofence%'
            ORDER BY viewname
        """)
        
        views = cursor.fetchall()
        if views:
            print(f"  ✓ Found {len(views)} regular views:")
            for v in views:
                print(f"    - {v[0]}")
        
        # Verify functions
        print("\n🔍 Verifying functions...")
        cursor.execute("""
            SELECT proname 
            FROM pg_proc 
            WHERE proname LIKE '%geofence%'
            ORDER BY proname
        """)
        
        functions = cursor.fetchall()
        if functions:
            print(f"  ✓ Found {len(functions)} functions:")
            for func in functions:
                print(f"    - {func[0]}()")
        
        # Test query - check data in views
        print("\n📊 Checking data in views...")
        
        cursor.execute("SELECT COUNT(*) FROM geofence_circles")
        circle_count = cursor.fetchone()[0]
        print(f"  ✓ geofence_circles: {circle_count} rows")
        
        cursor.execute("SELECT COUNT(*) FROM geofence_polygons")
        polygon_count = cursor.fetchone()[0]
        print(f"  ✓ geofence_polygons: {polygon_count} rows")
        
        # Show sample data
        if circle_count > 0:
            print("\n📋 Sample circle geofences:")
            cursor.execute("""
                SELECT geofence_id, name, center_lat, center_lon, radius_meters, area_sqm
                FROM geofence_circles
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            for row in rows:
                gf_id, name, lat, lon, radius, area = row
                print(f"  • {gf_id}: {name}")
                print(f"    Center: ({lat:.6f}, {lon:.6f})")
                print(f"    Radius: {radius:.1f}m, Area: {area:.2f} sqm")
        
        print("\n" + "="*60)
        print("✅ POSTGIS SETUP COMPLETE!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        print("  ⚠️  Changes rolled back")
    
    finally:
        cursor.close()
        conn.close()
        print("\n📡 Database connection closed")

if __name__ == "__main__":
    setup_postgis_views()
