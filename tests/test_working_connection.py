#!/usr/bin/env python3
"""
Test the working PostgreSQL connection configuration
"""

import psycopg2
from config.database import get_ssh_tunnel, get_db_config
import time

def test_connection():
    """Test the database connection that we know works"""
    
    print("🔬 Testing Working PostgreSQL Connection")
    print("=" * 50)
    
    # Create SSH tunnel
    print("🚇 Starting SSH tunnel...")
    tunnel = get_ssh_tunnel()
    
    try:
        tunnel.start()
        print(f"   ✅ Tunnel started on local port: {tunnel.local_bind_port}")
        
        # Wait for tunnel to stabilize
        print("   ⏳ Waiting 3 seconds for tunnel...")
        time.sleep(3)
        
        # Get database configuration
        db_config = get_db_config(tunnel)
        print(f"   📊 Database: {db_config['dbname']}")
        print(f"   👤 User: {db_config['user']}")
        print(f"   🔌 Host: {db_config['host']}:{db_config['port']}")
        
        # Test connection
        print("\n🗄️ Testing database connection...")
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"   ✅ Connected! PostgreSQL version:")
        print(f"      {version}")
        
        # Test database-specific query
        cursor.execute("SELECT current_database(), current_user, now()")
        result = cursor.fetchone()
        print(f"   📊 Database: {result[0]}")
        print(f"   👤 User: {result[1]}")
        print(f"   ⏰ Time: {result[2]}")
        
        # Test our tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"   📋 Tables ({len(tables)}):")
        for table in tables:
            print(f"      - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 SUCCESS: Database connection is working perfectly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    finally:
        if tunnel:
            tunnel.stop()
            print("   🔒 Tunnel closed")

if __name__ == "__main__":
    test_connection()
