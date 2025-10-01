#!/usr/bin/env python3
"""Test vehicle assignments with fixed Strapi populate syntax"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'arknet_transit_simulator'))

from core.dispatcher import StrapiStrategy

async def test_vehicle_assignments():
    """Test StrapiStrategy vehicle assignments with fixed populate syntax"""
    
    # Initialize Strapi strategy
    strapi = StrapiStrategy("http://localhost:1337")
    
    # Initialize and test connection
    await strapi.initialize()
    connection_ok = await strapi.test_connection()
    
    if not connection_ok:
        print("❌ Failed to connect to Strapi API")
        return
    
    print("✅ Strapi API connection successful")
    
    # Test vehicle assignments
    print("\n🚗 Testing Vehicle Assignments:")
    assignments = await strapi.get_vehicle_assignments()
    
    if assignments:
        print(f"✅ Found {len(assignments)} vehicle assignments:")
        for assignment in assignments:
            print(f"  📋 Vehicle: {assignment.vehicle_id}")
            print(f"     Route: {assignment.route_id}")
            print(f"     Driver: {assignment.driver_id}")
            print(f"     Status: {assignment.vehicle_status}")
            print(f"     Driver Name: {assignment.driver_name}")
            print(f"     Route Name: {assignment.route_name}")
            print()
    else:
        print("❌ No vehicle assignments found")
    
    # Cleanup
    if strapi.session:
        await strapi.session.close()

if __name__ == "__main__":
    asyncio.run(test_vehicle_assignments())