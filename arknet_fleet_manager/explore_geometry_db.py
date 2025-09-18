#!/usr/bin/env python3
"""
Quick database explorer to find the geometry data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2

def explore_databases():
    """Find which database has the geometry data"""
    print("🔍 EXPLORING DATABASES FOR GEOMETRY DATA")
    print("=" * 60)
    
    # Set up tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        # Try both databases
        databases = ['arknettransit', 'barbados_transit_gtfs']
        
        for db_name in databases:
            print(f"\n📊 Database: {db_name}")
            print("-" * 40)
            
            try:
                conn = psycopg2.connect(
                    host='127.0.0.1',
                    port=6543, 
                    database=db_name,
                    user='david',
                    password='Ga25w123!'
                )
                
                cursor = conn.cursor()
                
                # Check if shapes table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'shapes'
                    );
                """)
                shapes_exists = cursor.fetchone()[0]
                
                if shapes_exists:
                    # Check columns in shapes table
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'shapes'
                        ORDER BY ordinal_position;
                    """)
                    columns = cursor.fetchall()
                    
                    print(f"✅ Shapes table found with columns:")
                    for col_name, data_type in columns:
                        print(f"   - {col_name}: {data_type}")
                    
                    # Check if has PostGIS geometry
                    has_geometry = any('geom' in col[0] for col in columns)
                    if has_geometry:
                        cursor.execute("SELECT COUNT(*) FROM shapes WHERE shape_geom IS NOT NULL")
                        geom_count = cursor.fetchone()[0]
                        print(f"   🎯 HAS GEOMETRY DATA: {geom_count} records")
                    else:
                        print(f"   ❌ No geometry columns found")
                        
                    # Count total shapes
                    cursor.execute("SELECT COUNT(*) FROM shapes")
                    total_count = cursor.fetchone()[0]
                    print(f"   📊 Total shapes: {total_count}")
                    
                else:
                    print("❌ No shapes table found")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"❌ Error accessing {db_name}: {e}")
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    explore_databases()