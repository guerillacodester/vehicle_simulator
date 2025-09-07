#!/usr/bin/env python3
"""
Quick database connection test
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from config.database import get_ssh_tunnel, get_db_config
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection"""
    tunnel = None
    try:
        print("🔌 Testing SSH tunnel connection...")
        tunnel = get_ssh_tunnel()
        tunnel.start()
        print(f"✅ SSH tunnel started on port {tunnel.local_bind_port}")
        
        # Wait for tunnel
        time.sleep(2)
        
        print("🗄️  Testing database connection...")
        db_config = get_db_config(tunnel)
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        engine = create_engine(connection_string, connect_args={'connect_timeout': 10})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected: {version[:50]}...")
            
            # Test our tables
            result = conn.execute(text("SELECT COUNT(*) FROM vehicles"))
            vehicle_count = result.fetchone()[0]
            print(f"📊 Found {vehicle_count} vehicles in database")
            
            result = conn.execute(text("SELECT COUNT(*) FROM routes"))
            route_count = result.fetchone()[0]
            print(f"🛣️  Found {route_count} routes in database")
            
        print("✅ Connection test successful!")
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
        
    finally:
        if tunnel:
            tunnel.stop()
            print("🔌 SSH tunnel closed")
            
    return True

if __name__ == "__main__":
    test_connection()
