#!/usr/bin/env python3
"""
Check actual database schema structure
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.fleet_management.database import FleetDatabaseService
import asyncio
from sqlalchemy import text

async def check_schema():
    db_service = FleetDatabaseService()
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        # Check what tables exist
        tables_query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """)
        
        tables = session.execute(tables_query).fetchall()
        print('=== EXISTING TABLES ===')
        for table in tables:
            print(f'- {table.table_name}')
        
        # Check countries table structure
        print('\n=== COUNTRIES TABLE STRUCTURE ===')
        countries_query = text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'countries' AND table_schema = 'public'
        ORDER BY ordinal_position
        """)
        
        try:
            countries_cols = session.execute(countries_query).fetchall()
            if countries_cols:
                for col in countries_cols:
                    print(f'- {col.column_name}: {col.data_type} (nullable: {col.is_nullable})')
            else:
                print('No countries table found')
        except Exception as e:
            print(f'Error checking countries table: {e}')
        
        # Check routes table structure
        print('\n=== ROUTES TABLE STRUCTURE ===')
        routes_query = text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'routes' AND table_schema = 'public'
        ORDER BY ordinal_position
        """)
        
        try:
            routes_cols = session.execute(routes_query).fetchall()
            if routes_cols:
                for col in routes_cols:
                    print(f'- {col.column_name}: {col.data_type} (nullable: {col.is_nullable})')
            else:
                print('No routes table found')
        except Exception as e:
            print(f'Error checking routes table: {e}')
        
        # Check vehicles table structure  
        print('\n=== VEHICLES TABLE STRUCTURE ===')
        vehicles_query = text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'vehicles' AND table_schema = 'public'
        ORDER BY ordinal_position
        """)
        
        try:
            vehicles_cols = session.execute(vehicles_query).fetchall()
            if vehicles_cols:
                for col in vehicles_cols:
                    print(f'- {col.column_name}: {col.data_type} (nullable: {col.is_nullable})')
            else:
                print('No vehicles table found')
        except Exception as e:
            print(f'Error checking vehicles table: {e}')
        
        # Check what data exists
        print('\n=== DATA SAMPLES ===')
        
        # Sample countries data
        try:
            sample_countries = session.execute(text("SELECT * FROM countries LIMIT 5")).fetchall()
            print(f'Countries count: {len(sample_countries)}')
            for country in sample_countries:
                print(f'  - {country}')
        except Exception as e:
            print(f'Error checking countries data: {e}')
        
        # Sample routes data
        try:
            sample_routes = session.execute(text("SELECT * FROM routes LIMIT 5")).fetchall()
            print(f'Routes count: {len(sample_routes)}')
            for route in sample_routes:
                print(f'  - {route}')
        except Exception as e:
            print(f'Error checking routes data: {e}')
        
        # Sample vehicles data
        try:
            sample_vehicles = session.execute(text("SELECT * FROM vehicles LIMIT 5")).fetchall()
            print(f'Vehicles count: {len(sample_vehicles)}')
            for vehicle in sample_vehicles:
                print(f'  - {vehicle}')
        except Exception as e:
            print(f'Error checking vehicles data: {e}')

if __name__ == '__main__':
    asyncio.run(check_schema())
