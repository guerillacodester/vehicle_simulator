"""
Test Database Connections
========================
Test script to verify connections to both remote and local databases
before running the full migration.
"""

import sys
import os
import psycopg2
import paramiko
import threading
import socket
import time
from psycopg2.extras import RealDictCursor

# Add the current directory to Python path to import from migrate_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrate_data import SSHTunnel, DataMigrator

def test_local_connection():
    """Test connection to local PostgreSQL database"""
    print("🔍 Testing local database connection...")
    
    local_config = {
        'host': '127.0.0.1',
        'port': 5432,
        'database': 'arknettransit',
        'user': 'david',
        'password': 'Ga25w123!'
    }
    
    try:
        conn = psycopg2.connect(**local_config, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Local database connected successfully!")
            print(f"   PostgreSQL version: {version['version']}")
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"   Found {len(tables)} tables in local database")
            for table in tables[:5]:  # Show first 5 tables
                print(f"   - {table['table_name']}")
            if len(tables) > 5:
                print(f"   ... and {len(tables) - 5} more tables")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Local database connection failed: {e}")
        return False

def test_remote_connection():
    """Test connection to remote PostgreSQL database via SSH tunnel"""
    print("🔍 Testing remote database connection via SSH tunnel...")
    
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
        # Start SSH tunnel
        print("   Starting SSH tunnel...")
        tunnel = SSHTunnel(**ssh_config)
        tunnel.start()
        
        # Connect to database via tunnel
        print("   Connecting to remote database...")
        conn = psycopg2.connect(**remote_config, cursor_factory=RealDictCursor)
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Remote database connected successfully!")
            print(f"   PostgreSQL version: {version['version']}")
            
            # Check if tables exist and get row counts
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"   Found {len(tables)} tables in remote database")
            
            # Get row counts for key tables
            key_tables = ['countries', 'vehicles', 'drivers', 'routes', 'depots']
            for table_name in key_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                    count = cursor.fetchone()
                    print(f"   - {table_name}: {count['count']} rows")
                except Exception as e:
                    print(f"   - {table_name}: table not found or error")
        
        return True
        
    except Exception as e:
        print(f"❌ Remote database connection failed: {e}")
        return False
        
    finally:
        if conn:
            conn.close()
        if tunnel:
            tunnel.stop()

def main():
    """Main test function"""
    print("=" * 60)
    print("ArkNet Transit Database Connection Test")
    print("=" * 60)
    
    # Test local connection
    local_ok = test_local_connection()
    print()
    
    # Test remote connection
    remote_ok = test_remote_connection()
    print()
    
    # Summary
    print("=" * 60)
    print("Connection Test Summary:")
    print(f"Local Database:  {'✅ PASS' if local_ok else '❌ FAIL'}")
    print(f"Remote Database: {'✅ PASS' if remote_ok else '❌ FAIL'}")
    
    if local_ok and remote_ok:
        print("\n🎉 All connections successful! Ready to run data migration.")
        return True
    else:
        print("\n⚠️  Fix connection issues before running migration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)