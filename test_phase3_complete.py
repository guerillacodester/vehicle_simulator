#!/usr/bin/env python3
"""Complete test of Phase 3: Vehicle and Driver assignments"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'arknet_transit_simulator'))

from core.dispatcher import StrapiStrategy

async def test_phase3_complete():
    """Test complete Phase 3: Vehicle and Driver assignments"""
    
    # Initialize Strapi strategy
    strapi = StrapiStrategy("http://localhost:1337")
    
    # Initialize and test connection
    await strapi.initialize()
    connection_ok = await strapi.test_connection()
    
    if not connection_ok:
        print("❌ Failed to connect to Strapi API")
        return
    
    print("✅ Strapi API connection successful")
    print("=" * 60)
    
    # Test vehicle assignments
    print("🚗 PHASE 3A: Vehicle Assignments")
    print("-" * 40)
    vehicle_assignments = await strapi.get_vehicle_assignments()
    
    if vehicle_assignments:
        print(f"✅ Found {len(vehicle_assignments)} vehicle assignments:")
        for assignment in vehicle_assignments:
            print(f"  📋 Vehicle: {assignment.vehicle_id}")
            print(f"     Route: {assignment.route_id} ({assignment.route_name})")
            print(f"     Driver: {assignment.driver_id} ({assignment.driver_name})")
            print(f"     Status: {assignment.vehicle_status}")
            print()
    else:
        print("❌ No vehicle assignments found")
    
    print("=" * 60)
    
    # Test driver assignments
    print("👨‍💼 PHASE 3B: Driver Assignments")
    print("-" * 40)
    driver_assignments = await strapi.get_driver_assignments()
    
    if driver_assignments:
        print(f"✅ Found {len(driver_assignments)} driver assignments:")
        for assignment in driver_assignments:
            print(f"  👨‍💼 Driver: {assignment.driver_id} ({assignment.driver_name})")
            print(f"      License: {assignment.license_number}")
            print(f"      Vehicle: {assignment.vehicle_id}")
            print(f"      Route: {assignment.route_id}")
            print(f"      Status: {assignment.status}")
            print()
    else:
        print("❌ No driver assignments found")
    
    print("=" * 60)
    
    # Test depot vehicles
    print("🏭 PHASE 3C: Depot Vehicles")
    print("-" * 40)
    depot_vehicles = await strapi.get_all_depot_vehicles()
    
    if depot_vehicles:
        print(f"✅ Found {len(depot_vehicles)} depot vehicles:")
        for vehicle in depot_vehicles:
            print(f"  🚌 Vehicle: {vehicle.get('reg_code', 'Unknown')}")
            print(f"     Type: {vehicle.get('type', 'Unknown')}")
            print(f"     Capacity: {vehicle.get('capacity', 'Unknown')}")
            print(f"     Status: {vehicle.get('status', 'Unknown')}")
            print()
    else:
        print("❌ No depot vehicles found")
    
    print("=" * 60)
    print("🎉 PHASE 3 TESTING COMPLETE!")
    
    # Cleanup
    if strapi.session:
        await strapi.session.close()

if __name__ == "__main__":
    asyncio.run(test_phase3_complete())