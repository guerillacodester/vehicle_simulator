#!/usr/bin/env python3
"""
Quick route_shapes table structure check
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor

def check_route_shapes_structure():
    """Check route_shapes table structure"""
    print("🔍 ROUTE_SHAPES TABLE STRUCTURE CHECK")
    print("=" * 50)
    
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
        
        # Get column structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'route_shapes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"Route_shapes columns ({len(columns)}):")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Get sample data
        cursor.execute("SELECT COUNT(*) FROM route_shapes;")
        count = cursor.fetchone()[0]
        print(f"\nTotal records: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM route_shapes LIMIT 3;")
            samples = cursor.fetchall()
            print(f"\nSample records:")
            for i, record in enumerate(samples, 1):
                print(f"Record {i}: {dict(record)}")
        
        cursor.close()
        conn.close()
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    check_route_shapes_structure()