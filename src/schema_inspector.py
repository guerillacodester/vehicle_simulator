#!/usr/bin/env python3
"""
Database Schema Inspector
"""

import psycopg2
import psycopg2.extras
from config.database import get_ssh_tunnel, get_db_config
import time

def inspect_schema():
    """Inspect the database schema to understand table structures"""
    tunnel = None
    try:
        # Connect to database
        tunnel = get_ssh_tunnel()
        tunnel.start()
        time.sleep(2)
        
        db_config = get_db_config(tunnel)
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("🔍 Database Schema Inspector")
        print("=" * 50)
        
        # Check routes table
        print("\n📍 ROUTES table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'routes' 
            ORDER BY ordinal_position
        """)
        for col in cursor.fetchall():
            print(f"   {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
        # Sample routes data
        cursor.execute("SELECT * FROM routes LIMIT 3")
        routes = cursor.fetchall()
        print(f"\n   Sample data ({len(routes)} rows):")
        for route in routes:
            print(f"   - {route['id']}: {route['name']}")
            
        # Check vehicles table
        print("\n🚌 VEHICLES table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'vehicles' 
            ORDER BY ordinal_position
        """)
        for col in cursor.fetchall():
            print(f"   {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
        # Sample vehicles data
        cursor.execute("SELECT id, route_id, status FROM vehicles WHERE status = 'active' LIMIT 5")
        vehicles = cursor.fetchall()
        print(f"\n   Sample active vehicles ({len(vehicles)} rows):")
        for vehicle in vehicles:
            print(f"   - {vehicle['id']}: route {vehicle['route_id']}, status {vehicle['status']}")
            
        # Check timetables table
        print("\n📅 TIMETABLES table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'timetables' 
            ORDER BY ordinal_position
        """)
        for col in cursor.fetchall():
            print(f"   {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
        # Sample timetables data
        cursor.execute("SELECT route_id, stop_id, arrival_time FROM timetables LIMIT 5")
        timetables = cursor.fetchall()
        print(f"\n   Sample timetables ({len(timetables)} rows):")
        for tt in timetables:
            print(f"   - Route {tt['route_id']}, Stop {tt['stop_id']}: {tt['arrival_time']}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if tunnel:
            tunnel.stop()

if __name__ == "__main__":
    inspect_schema()
