#!/usr/bin/env python3
"""
Direct Database Test Through Tunnel
"""

import sys
import os
import time
import logging
import psycopg2
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config.database import get_ssh_tunnel, get_db_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def database_connection():
    """Context manager for database connection"""
    tunnel = None
    conn = None
    try:
        print("🚇 Starting SSH tunnel...")
        tunnel = get_ssh_tunnel()
        tunnel.start()
        print(f"✅ Tunnel active on port {tunnel.local_bind_port}")
        
        # Wait for tunnel to stabilize
        time.sleep(3)
        
        print("🔌 Connecting to database...")
        db_config = get_db_config(tunnel)
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=int(db_config['port']),
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            connect_timeout=10
        )
        
        print("✅ Database connected successfully!")
        yield conn
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed")
        if tunnel:
            tunnel.stop()
            print("🚇 SSH tunnel stopped")

def test_database_operations():
    """Test basic database operations"""
    try:
        with database_connection() as conn:
            cursor = conn.cursor()
            
            # Test 1: Check PostgreSQL version
            print("\n📊 Database Information:")
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"   PostgreSQL: {version[:80]}...")
            
            # Test 2: List databases
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            databases = [row[0] for row in cursor.fetchall()]
            print(f"   Databases: {', '.join(databases)}")
            
            # Test 3: Check our tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   Tables: {', '.join(tables) if tables else 'None found'}")
            
            # Test 4: Check vehicle data
            if 'vehicles' in tables:
                cursor.execute("SELECT COUNT(*) FROM vehicles")
                vehicle_count = cursor.fetchone()[0]
                print(f"   Vehicles: {vehicle_count} records")
                
                cursor.execute("SELECT vehicle_id, status, route_id FROM vehicles LIMIT 5")
                vehicles = cursor.fetchall()
                print("   Sample vehicles:")
                for vehicle_id, status, route_id in vehicles:
                    print(f"     • {vehicle_id}: {status} (Route: {route_id or 'None'})")
            
            # Test 5: Check route data
            if 'routes' in tables:
                cursor.execute("SELECT COUNT(*) FROM routes")
                route_count = cursor.fetchone()[0]
                print(f"   Routes: {route_count} records")
                
                cursor.execute("SELECT route_id, name FROM routes LIMIT 5")
                routes = cursor.fetchall()
                print("   Sample routes:")
                for route_id, name in routes:
                    print(f"     • {route_id}: {name or 'Unnamed'}")
                    
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🔬 Direct Database Connection Test")
    print("=" * 60)
    
    success = test_database_operations()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Database connection and operations successful!")
        print("   The database is working correctly.")
        print("   Issue may be with connection pooling or timeouts.")
    else:
        print("❌ Database connection failed.")
        print("   Check PostgreSQL configuration on remote server.")

if __name__ == "__main__":
    main()
