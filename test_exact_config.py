#!/usr/bin/env python3
"""
Test PostgreSQL connection using the exact working configuration from debug script
"""

import psycopg2
from sshtunnel import SSHTunnelForwarder
import time

# Use exact same settings that worked in debug
SSH_HOST = "arknetglobal.com"
SSH_PORT = 22
SSH_USER = "david"
SSH_PASS = "Cabbyminnie5!"

DB_NAME = "arknettransit"
DB_USER = "david"
DB_PASS = "Ga25w123!"

def test_exact_working_config():
    """Test using the exact configuration that worked in the debug script"""
    
    print("🔬 Testing Exact Working Configuration")
    print("=" * 50)
    
    print("🚇 Creating SSH tunnel...")
    
    # Use the exact same tunnel configuration that worked
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASS,
        remote_bind_address=('127.0.0.1', 5432),  # This is what worked!
        set_keepalive=30,
        mute_exceptions=False
    )
    
    try:
        print("   Starting tunnel...")
        tunnel.start()
        
        local_port = tunnel.local_bind_port
        print(f"   ✅ Tunnel started on local port: {local_port}")
        print(f"   🎯 Remote target: 127.0.0.1:5432")
        
        # Wait for tunnel
        print("   ⏳ Waiting 5 seconds for tunnel to stabilize...")
        time.sleep(5)
        
        # Test connection with exact parameters
        print(f"\n🗄️ Testing database connection...")
        print(f"   Connecting to: {DB_USER}@127.0.0.1:{local_port}/{DB_NAME}")
        
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=local_port,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=30,
            sslmode='prefer'
        )
        
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"   ✅ SUCCESS! PostgreSQL version:")
        print(f"      {version}")
        
        cursor.execute("SELECT current_database(), current_user, now()")
        result = cursor.fetchone()
        print(f"   📊 Database: {result[0]}")
        print(f"   👤 User: {result[1]}")
        print(f"   ⏰ Timestamp: {result[2]}")
        
        # Check our tables
        cursor.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        print(f"   📋 Public tables ({len(tables)}):")
        for schema, table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
            count = cursor.fetchone()[0]
            print(f"      - {table}: {count} rows")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 PERFECT! Database connection is working!")
        print(f"   Local port: {local_port}")
        print(f"   Remote: arknetglobal.com -> 127.0.0.1:5432")
        
        return local_port
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        if tunnel:
            tunnel.stop()
            print("   🔒 Tunnel closed")

if __name__ == "__main__":
    working_port = test_exact_working_config()
    if working_port:
        print(f"\n📝 Configuration Summary:")
        print(f"   SSH: {SSH_USER}@{SSH_HOST}:22")
        print(f"   Local: 127.0.0.1:{working_port}")
        print(f"   Remote: 127.0.0.1:5432")
        print(f"   Database: {DB_NAME}")
        print(f"   User: {DB_USER}")
