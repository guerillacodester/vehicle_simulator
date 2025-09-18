#!/usr/bin/env python3
"""
Quick connectivity test for Strapi API and SSH tunnel
"""

import requests
import psycopg2
import socket

def test_strapi():
    """Test Strapi API connectivity"""
    try:
        response = requests.get('http://localhost:1337/api', timeout=5)
        print(f"✅ Strapi API: Status {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Strapi API: {e}")
        return False

def test_ssh_tunnel():
    """Test SSH tunnel connectivity"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5433))
        sock.close()
        if result == 0:
            print("✅ SSH Tunnel: Port 5433 is open")
            return True
        else:
            print("❌ SSH Tunnel: Port 5433 is not accessible")
            return False
    except Exception as e:
        print(f"❌ SSH Tunnel: {e}")
        return False

def test_database():
    """Test database connectivity through SSH tunnel"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            database='arknetglobal',
            user='arknetglobal',
            password='password123',
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        print("✅ Database: Connected successfully")
        return True
    except Exception as e:
        print(f"❌ Database: {e}")
        return False

if __name__ == "__main__":
    print("=== CONNECTIVITY TEST ===")
    
    strapi_ok = test_strapi()
    tunnel_ok = test_ssh_tunnel()
    db_ok = test_database() if tunnel_ok else False
    
    print("\n=== SUMMARY ===")
    if strapi_ok and tunnel_ok and db_ok:
        print("🎉 All systems ready for migration!")
    else:
        print("⚠️  Some systems need attention before migration can proceed.")