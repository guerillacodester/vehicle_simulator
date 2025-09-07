#!/usr/bin/env python3
"""
Quick Database Table Check
========================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from config.database import get_ssh_tunnel, get_db_config

def list_tables():
    """List all tables in the database"""
    tunnel = None
    try:
        print("🔌 Connecting...")
        
        tunnel = get_ssh_tunnel()
        tunnel.start()
        
        db_config = get_db_config(tunnel)
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            print("📋 Database Tables:")
            
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            for i, table in enumerate(tables, 1):
                print(f"{i:2d}. {table}")
                
            print(f"\nTotal: {len(tables)} tables")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    finally:
        if tunnel:
            tunnel.stop()

if __name__ == "__main__":
    list_tables()
