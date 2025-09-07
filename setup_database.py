#!/usr/bin/env python3
"""
Database Migration and Setup Script
==================================
Runs Alembic migrations and populates initial data
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from config.database import get_ssh_tunnel, get_db_config
from models import Base, Country, Route, Vehicle, Stop, Depot

logger = logging.getLogger(__name__)

async def run_migrations():
    """Run Alembic migrations"""
    try:
        print("🔄 Running database migrations...")
        
        # Setup Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

async def populate_initial_data():
    """Populate database with initial data"""
    try:
        print("🌱 Populating initial data...")
        
        # Start SSH tunnel
        tunnel = get_ssh_tunnel()
        tunnel.start()
        
        # Get database config
        db_config = get_db_config(tunnel)
        connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        # Create engine
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Check if countries already exist
            result = conn.execute(text("SELECT COUNT(*) FROM countries")).fetchone()
            
            if result[0] == 0:
                print("📍 Adding initial countries...")
                
                # Add countries
                countries_data = [
                    {'iso_code': 'BB', 'name': 'Barbados'},
                    {'iso_code': 'JM', 'name': 'Jamaica'},
                    {'iso_code': 'TT', 'name': 'Trinidad and Tobago'},
                    {'iso_code': 'GD', 'name': 'Grenada'},
                    {'iso_code': 'LC', 'name': 'Saint Lucia'},
                    {'iso_code': 'VC', 'name': 'Saint Vincent and the Grenadines'}
                ]
                
                for country in countries_data:
                    conn.execute(text("""
                        INSERT INTO countries (iso_code, name, created_at) 
                        VALUES (:iso_code, :name, NOW())
                    """), country)
                
                conn.commit()
                print(f"✅ Added {len(countries_data)} countries")
            else:
                print("📍 Countries already exist, skipping...")
        
        tunnel.stop()
        print("✅ Initial data population completed!")
        return True
        
    except Exception as e:
        print(f"❌ Data population failed: {str(e)}")
        if 'tunnel' in locals():
            tunnel.stop()
        return False

async def main():
    """Main setup function"""
    print("🚀 Setting up database...")
    
    # Run migrations
    migration_success = await run_migrations()
    if not migration_success:
        return False
    
    # Populate initial data
    data_success = await populate_initial_data()
    if not data_success:
        return False
    
    print("🎉 Database setup completed successfully!")
    return True

if __name__ == "__main__":
    asyncio.run(main())
