#!/usr/bin/env python3
"""
Simple Shapes Table Inspector
============================
Direct inspection of the shapes table to understand its structure.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor

def inspect_shapes_table():
    """Simple direct inspection of shapes table"""
    print("🔍 DIRECT SHAPES TABLE INSPECTION")
    print("=" * 60)
    
    # Set up SSH tunnel
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=6543, 
            database='arknettransit',
            user='david',
            password='Ga25w123!'
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("📋 SHAPES TABLE STRUCTURE")
        print("-" * 40)
        
        # Get column names and types
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'shapes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"Columns ({len(columns)}):")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        print(f"\n📊 SHAPES TABLE DATA")
        print("-" * 40)
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM shapes;")
        total_count = cursor.fetchone()[0]
        print(f"Total records: {total_count}")
        
        if total_count > 0:
            # Sample first few records
            cursor.execute("SELECT * FROM shapes LIMIT 5;")
            sample_records = cursor.fetchall()
            
            print(f"\nSample Records ({len(sample_records)}):")
            for i, record in enumerate(sample_records, 1):
                print(f"\nRecord {i}:")
                for key, value in record.items():
                    # Handle potential binary/geometry data
                    if value is not None:
                        if isinstance(value, (bytes, memoryview)):
                            print(f"  {key}: [BINARY DATA - {len(value)} bytes]")
                        elif isinstance(value, str) and len(value) > 100:
                            print(f"  {key}: {value[:100]}...")
                        else:
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: NULL")
        
        print(f"\n🔍 ROUTE_SHAPES TABLE INSPECTION")
        print("-" * 40)
        
        # Check route_shapes table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'route_shapes'
            ORDER BY ordinal_position;
        """)
        
        rs_columns = cursor.fetchall()
        print(f"Route_shapes columns ({len(rs_columns)}):")
        for col in rs_columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Count route_shapes records
        cursor.execute("SELECT COUNT(*) FROM route_shapes;")
        rs_count = cursor.fetchone()[0]
        print(f"Route_shapes records: {rs_count}")
        
        if rs_count > 0:
            cursor.execute("SELECT * FROM route_shapes LIMIT 5;")
            rs_records = cursor.fetchall()
            
            print(f"\nSample Route_shapes Records:")
            for i, record in enumerate(rs_records, 1):
                print(f"Record {i}: {dict(record)}")
        
        # Check if PostGIS functions are available
        print(f"\n🌍 POSTGIS FUNCTION CHECK")
        print("-" * 40)
        
        try:
            cursor.execute("SELECT ST_AsText(ST_GeomFromText('POINT(0 0)', 4326));")
            result = cursor.fetchone()[0]
            print(f"✅ PostGIS functions available: {result}")
        except Exception as e:
            print(f"❌ PostGIS functions not available: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    inspect_shapes_table()