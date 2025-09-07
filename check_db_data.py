#!/usr/bin/env python3
"""
Check actual database data to understand the patterns
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.fleet_management.database import FleetDatabaseService
import asyncio
from sqlalchemy import text

async def check_data():
    db_service = FleetDatabaseService()
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        print('=== ACTUAL DATABASE DATA ===')
        
        # Check routes data
        try:
            routes_query = text("SELECT route_id, name FROM routes ORDER BY route_id LIMIT 10")
            routes = session.execute(routes_query).fetchall()
            print(f'\n--- ROUTES ({len(routes)} samples) ---')
            for route in routes:
                print(f'  route_id: {route.route_id}, name: {route.name}')
        except Exception as e:
            print(f'Error checking routes: {e}')
        
        # Check vehicles data
        try:
            vehicles_query = text("SELECT vehicle_id, status, route_id FROM vehicles ORDER BY vehicle_id LIMIT 10")
            vehicles = session.execute(vehicles_query).fetchall()
            print(f'\n--- VEHICLES ({len(vehicles)} samples) ---')
            for vehicle in vehicles:
                print(f'  vehicle_id: {vehicle.vehicle_id}, status: {vehicle.status}, route_id: {vehicle.route_id}')
        except Exception as e:
            print(f'Error checking vehicles: {e}')
        
        # Check for country patterns in route_ids
        try:
            country_patterns_query = text("""
            SELECT 
                CASE 
                    WHEN route_id LIKE 'barbados_%' THEN 'barbados'
                    WHEN route_id LIKE 'jamaica_%' THEN 'jamaica'
                    WHEN route_id LIKE 'trinidad_%' THEN 'trinidad'
                    WHEN route_id LIKE '%barbados%' THEN 'barbados_variant'
                    WHEN route_id LIKE '%jamaica%' THEN 'jamaica_variant'
                    WHEN route_id LIKE '%trinidad%' THEN 'trinidad_variant'
                    ELSE 'unknown_pattern'
                END as pattern,
                COUNT(*) as count,
                array_agg(route_id) as sample_ids
            FROM routes 
            GROUP BY 
                CASE 
                    WHEN route_id LIKE 'barbados_%' THEN 'barbados'
                    WHEN route_id LIKE 'jamaica_%' THEN 'jamaica'
                    WHEN route_id LIKE 'trinidad_%' THEN 'trinidad'
                    WHEN route_id LIKE '%barbados%' THEN 'barbados_variant'
                    WHEN route_id LIKE '%jamaica%' THEN 'jamaica_variant'
                    WHEN route_id LIKE '%trinidad%' THEN 'trinidad_variant'
                    ELSE 'unknown_pattern'
                END
            ORDER BY count DESC
            """)
            
            patterns = session.execute(country_patterns_query).fetchall()
            print(f'\n--- ROUTE ID PATTERNS ---')
            for pattern in patterns:
                sample_ids = pattern.sample_ids[:3] if pattern.sample_ids else []
                print(f'  {pattern.pattern}: {pattern.count} routes (samples: {sample_ids})')
        except Exception as e:
            print(f'Error checking patterns: {e}')

if __name__ == '__main__':
    asyncio.run(check_data())
