#!/usr/bin/env python3
"""
List Database Tables
==================
Show all tables in the current database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from sqlalchemy import create_engine, text
from config.database import get_ssh_tunnel, get_db_config

async def list_tables():
    """List all tables in the database"""
    tunnel = None
    try:
        print("🔌 Connecting to database...")
        
        # Start SSH tunnel
        tunnel = get_ssh_tunnel()
        tunnel.start()
        
        # Get database config
        db_config = get_db_config(tunnel)
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        # Create engine
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            print("📋 Current database tables:")
            print("=" * 50)
            
            # Get all tables in the public schema
            result = conn.execute(text("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            
            if not tables:
                print("❌ No tables found in the database")
            else:
                for table in tables:
                    print(f"📄 {table.table_name} ({table.table_type})")
                
                print(f"\n✅ Total: {len(tables)} tables found")
                
                # Get table details for each table
                print("\n🔍 Table details:")
                print("=" * 50)
                
                for table in tables:
                    table_name = table.table_name
                    
                    # Get column information
                    columns_result = conn.execute(text(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = '{table_name}'
                        ORDER BY ordinal_position;
                    """))
                    
                    columns = columns_result.fetchall()
                    
                    print(f"\n📋 Table: {table_name}")
                    print(f"   Columns ({len(columns)}):")
                    
                    for col in columns:
                        nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                        default = f" DEFAULT {col.column_default}" if col.column_default else ""
                        print(f"     • {col.column_name}: {col.data_type} {nullable}{default}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    finally:
        if tunnel:
            tunnel.stop()

if __name__ == "__main__":
    asyncio.run(list_tables())
