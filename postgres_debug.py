#!/usr/bin/env python3
"""
PostgreSQL Connection Debugging - Match Navicat Settings
"""

import sys
import os
import time
import logging
import psycopg2
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config.database import get_ssh_tunnel, get_db_config, SSH_HOST, SSH_USER, SSH_PASS, DB_NAME, DB_USER, DB_PASS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_connection_params():
    """Show exactly what connection parameters we're using"""
    print("🔍 Current Connection Parameters:")
    print(f"   SSH Host: {SSH_HOST}")
    print(f"   SSH User: {SSH_USER}")
    print(f"   SSH Pass: {'*' * len(SSH_PASS) if SSH_PASS else 'None'}")
    print(f"   DB Name: {DB_NAME}")
    print(f"   DB User: {DB_USER}")
    print(f"   DB Pass: {'*' * len(DB_PASS) if DB_PASS else 'None'}")

def test_ssh_tunnel_verbose():
    """Test SSH tunnel with detailed logging"""
    print("\n🚇 Testing SSH Tunnel (Verbose)...")
    
    try:
        tunnel = get_ssh_tunnel()
        
        # Enable debug logging for SSH
        import paramiko
        paramiko.util.log_to_file('ssh_debug.log', level=paramiko.util.DEBUG)
        
        print("   Starting tunnel...")
        tunnel.start()
        
        print(f"   ✅ Tunnel started")
        print(f"   Local bind: 127.0.0.1:{tunnel.local_bind_port}")
        print(f"   Remote bind: 127.0.0.1:5432")  # We know this is the target
        print(f"   SSH server: {tunnel.ssh_host}:{tunnel.ssh_port}")
        
        # Wait longer for tunnel to stabilize
        print("   Waiting 5 seconds for tunnel to stabilize...")
        time.sleep(5)
        
        # Test if tunnel is actually working
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', tunnel.local_bind_port))
        sock.close()
        
        if result == 0:
            print("   ✅ Local tunnel port is responding")
        else:
            print(f"   ❌ Local tunnel port not responding (error: {result})")
            
        return tunnel
        
    except Exception as e:
        print(f"   ❌ Tunnel failed: {e}")
        return None

def test_direct_psycopg2(tunnel):
    """Test direct psycopg2 connection with various settings"""
    print(f"\n🔌 Testing Direct psycopg2 Connection...")
    
    if not tunnel:
        print("   ❌ No tunnel available")
        return False
    
    # Try different connection approaches
    connection_configs = [
        {
            "name": "Standard Connection",
            "params": {
                "host": "127.0.0.1",
                "port": tunnel.local_bind_port,
                "dbname": DB_NAME,
                "user": DB_USER,
                "password": DB_PASS,
                "connect_timeout": 30
            }
        },
        {
            "name": "With sslmode=disable",
            "params": {
                "host": "127.0.0.1",
                "port": tunnel.local_bind_port,
                "dbname": DB_NAME,
                "user": DB_USER,
                "password": DB_PASS,
                "connect_timeout": 30,
                "sslmode": "disable"
            }
        },
        {
            "name": "With sslmode=prefer",
            "params": {
                "host": "127.0.0.1",
                "port": tunnel.local_bind_port,
                "dbname": DB_NAME,
                "user": DB_USER,
                "password": DB_PASS,
                "connect_timeout": 30,
                "sslmode": "prefer"
            }
        }
    ]
    
    for config in connection_configs:
        print(f"\n   Testing: {config['name']}")
        try:
            conn = psycopg2.connect(**config['params'])
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"   ✅ Success! PostgreSQL: {version[:50]}...")
            
            # Test a simple query
            cursor.execute("SELECT current_database(), current_user")
            db, user = cursor.fetchone()
            print(f"   Database: {db}, User: {user}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            continue
    
    return False

def test_alternative_ports():
    """Test if PostgreSQL might be on a different port"""
    print(f"\n🔍 Testing Alternative PostgreSQL Ports...")
    
    tunnel = None
    try:
        # Test common PostgreSQL ports
        ports_to_test = [5432, 5433, 5434, 5435]
        
        for port in ports_to_test:
            print(f"\n   Testing remote port {port}...")
            
            try:
                from sshtunnel import SSHTunnelForwarder
                
                tunnel = SSHTunnelForwarder(
                    (SSH_HOST, 22),
                    ssh_username=SSH_USER,
                    ssh_password=SSH_PASS,
                    remote_bind_address=('127.0.0.1', port),  # Try different remote port
                    local_bind_address=('127.0.0.1', 0),  # Let system choose local port
                    mute_exceptions=False
                )
                
                tunnel.start()
                time.sleep(2)
                
                # Test connection
                conn = psycopg2.connect(
                    host="127.0.0.1",
                    port=tunnel.local_bind_port,
                    dbname=DB_NAME,
                    user=DB_USER,
                    password=DB_PASS,
                    connect_timeout=10,
                    sslmode="disable"
                )
                
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"   ✅ SUCCESS on port {port}! PostgreSQL: {version[:50]}...")
                
                conn.close()
                tunnel.stop()
                return port
                
            except Exception as e:
                print(f"   ❌ Port {port} failed: {e}")
                if tunnel:
                    tunnel.stop()
                continue
    
    except Exception as e:
        print(f"   ❌ Port testing failed: {e}")
    
    return None

def main():
    """Main debugging function"""
    print("=" * 80)
    print("🔬 PostgreSQL Connection Debugging - arknetglobal.com")
    print("=" * 80)
    
    debug_connection_params()
    
    # Test 1: SSH Tunnel
    tunnel = test_ssh_tunnel_verbose()
    
    if tunnel:
        # Test 2: Direct Connection
        success = test_direct_psycopg2(tunnel)
        
        if not success:
            # Test 3: Alternative ports
            working_port = test_alternative_ports()
            
            if working_port:
                print(f"\n✅ Found working PostgreSQL on port {working_port}")
                print(f"   Update your configuration to use remote port {working_port}")
            else:
                print(f"\n❌ Could not connect to PostgreSQL on any tested port")
        
        tunnel.stop()
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Check SSH debug log: ssh_debug.log")
    print(f"   2. Verify PostgreSQL is listening on 127.0.0.1 (not just localhost)")
    print(f"   3. Check PostgreSQL configuration: listen_addresses")
    print(f"   4. Verify database name and user credentials")

if __name__ == "__main__":
    main()
