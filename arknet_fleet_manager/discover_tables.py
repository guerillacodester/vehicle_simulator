#!/usr/bin/env python3
"""
Database Table Discovery - Find actual table names in remote database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from migrate_data import SSHTunnel
import psycopg2
from psycopg2.extras import RealDictCursor

def discover_remote_tables():
    """Discover all tables in remote database"""
    print("🔍 DISCOVERING ALL TABLES IN REMOTE DATABASE")
    print("=" * 60)
    
    tunnel = SSHTunnel('arknetglobal.com', 22, 'david', 'Cabbyminnie5!', 'localhost', 5432, 6543)
    tunnel.start()
    
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=6543, database='arknettransit', user='david', password='Ga25w123!')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all tables
        cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
            count = cursor.fetchone()['count']
            print(f"  - {table['table_name']} ({table['table_type']}) - {count} records")
        
        # Look for likely candidates
        target_keywords = ['driver', 'depot', 'route', 'vehicle', 'bus', 'operator', 'fleet']
        
        print(f"\n🎯 POTENTIAL MIGRATION TARGETS:")
        for table in tables:
            table_name = table['table_name'].lower()
            for keyword in target_keywords:
                if keyword in table_name:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
                    count = cursor.fetchone()['count']
                    print(f"  ✅ {table['table_name']} - {count} records (contains '{keyword}')")
                    break
        
        # Show detailed structure for promising tables
        promising_tables = []
        for table in tables:
            table_name = table['table_name'].lower()
            for keyword in target_keywords:
                if keyword in table_name:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
                    count = cursor.fetchone()['count']
                    if count > 0:  # Only analyze tables with data
                        promising_tables.append(table['table_name'])
                    break
        
        print(f"\n📋 DETAILED ANALYSIS OF TABLES WITH DATA:")
        for table_name in promising_tables:
            print(f"\n--- {table_name.upper()} ---")
            
            # Get structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            
            print(f"Columns ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  - {col['column_name']}: {col['data_type']} {nullable}")
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            
            if sample:
                print("Sample record:")
                for key, value in sample.items():
                    display_value = str(value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    print(f"  {key}: {display_value}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    discover_remote_tables()