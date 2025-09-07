#!/usr/bin/env python3
"""
Database Connection Diagnostics
"""

import sys
import os
import time
import socket
import subprocess
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config.database import get_ssh_tunnel, get_db_config, SSH_HOST, SSH_USER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ssh_connectivity():
    """Test basic SSH connectivity"""
    print("🔌 Testing SSH connectivity...")
    try:
        # Test basic SSH connection
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10', 
            '-o', 'BatchMode=yes',
            f'{SSH_USER}@{SSH_HOST}', 
            'echo "SSH connection successful"'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ SSH connection successful")
            return True
        else:
            print(f"❌ SSH connection failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ SSH test failed: {e}")
        return False

def check_remote_postgresql():
    """Check if PostgreSQL is running on remote server"""
    print("🗄️  Testing remote PostgreSQL...")
    try:
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10',
            f'{SSH_USER}@{SSH_HOST}',
            'sudo systemctl status postgresql || service postgresql status || ps aux | grep postgres'
        ], capture_output=True, text=True, timeout=15)
        
        if 'active (running)' in result.stdout or 'postgres' in result.stdout:
            print("✅ PostgreSQL appears to be running")
            return True
        else:
            print(f"❌ PostgreSQL status unclear: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Remote PostgreSQL check failed: {e}")
        return False

def check_postgresql_port():
    """Check if PostgreSQL is listening on port 5432"""
    print("🔍 Checking PostgreSQL port...")
    try:
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10',
            f'{SSH_USER}@{SSH_HOST}',
            'netstat -ln | grep :5432 || ss -ln | grep :5432'
        ], capture_output=True, text=True, timeout=15)
        
        if ':5432' in result.stdout:
            print("✅ PostgreSQL listening on port 5432")
            print(f"   Details: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL not listening on port 5432")
            return False
            
    except Exception as e:
        print(f"❌ Port check failed: {e}")
        return False

def test_tunnel_only():
    """Test just the SSH tunnel without database connection"""
    print("🚇 Testing SSH tunnel...")
    tunnel = None
    try:
        tunnel = get_ssh_tunnel()
        tunnel.start()
        
        print(f"✅ Tunnel started on local port {tunnel.local_bind_port}")
        
        # Test if local port is actually bound
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', tunnel.local_bind_port))
        sock.close()
        
        if result == 0:
            print("✅ Local tunnel port is accessible")
            return True
        else:
            print("❌ Local tunnel port is not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Tunnel test failed: {e}")
        return False
    finally:
        if tunnel:
            tunnel.stop()
            print("🔌 Tunnel stopped")

def check_database_credentials():
    """Test database authentication"""
    print("🔐 Testing database credentials...")
    try:
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10',
            f'{SSH_USER}@{SSH_HOST}',
            'sudo -u postgres psql -c "\\l" || psql -U postgres -c "\\l"'
        ], capture_output=True, text=True, timeout=15)
        
        if 'arknettransit' in result.stdout:
            print("✅ Database 'arknettransit' exists")
            return True
        else:
            print(f"❌ Database check failed: {result.stdout}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Database credential check failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("=" * 60)
    print("🏥 Database Connection Diagnostics")
    print("=" * 60)
    
    tests = [
        ("SSH Connectivity", check_ssh_connectivity),
        ("Remote PostgreSQL", check_remote_postgresql),
        ("PostgreSQL Port", check_postgresql_port),
        ("SSH Tunnel", test_tunnel_only),
        ("Database Credentials", check_database_credentials),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print("📊 Diagnostic Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<25} {status}")
    
    # Recommendations
    print(f"\n🔧 Recommendations:")
    if not results.get("SSH Connectivity", False):
        print("   • Check SSH credentials and network connectivity")
    if not results.get("Remote PostgreSQL", False):
        print("   • Start PostgreSQL service on remote server")
    if not results.get("PostgreSQL Port", False):
        print("   • Configure PostgreSQL to listen on 127.0.0.1:5432")
    if not results.get("Database Credentials", False):
        print("   • Check database name and user permissions")

if __name__ == "__main__":
    main()
