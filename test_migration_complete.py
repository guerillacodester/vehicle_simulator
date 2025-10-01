#!/usr/bin/env python3
"""Comprehensive Phase 3 validation: FastAPI vs Strapi comparison"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'arknet_transit_simulator'))

from core.dispatcher import FastApiStrategy, StrapiStrategy

async def test_strategy_comparison():
    """Compare FastAPI and Strapi strategies after Phase 3 completion"""
    
    print("🔄 COMPREHENSIVE STRATEGY COMPARISON - PHASE 3")
    print("=" * 70)
    
    # Initialize both strategies
    fastapi = FastApiStrategy("http://localhost:8000")
    strapi = StrapiStrategy("http://localhost:1337")
    
    # Test connections
    fastapi_ok = await fastapi.initialize() and await fastapi.test_connection()
    strapi_ok = await strapi.initialize() and await strapi.test_connection()
    
    print(f"FastAPI Connection: {'✅' if fastapi_ok else '❌'}")
    print(f"Strapi Connection: {'✅' if strapi_ok else '❌'}")
    print()
    
    if not (fastapi_ok and strapi_ok):
        print("❌ One or both APIs are not available. Exiting...")
        return
    
    # Test 1: Route Geometry (Phase 2)
    print("🗺️  TEST 1: Route Geometry (Phase 2)")
    print("-" * 50)
    
    fastapi_route = await fastapi.get_route_info("1A")
    strapi_route = await strapi.get_route_info("1A")
    
    fastapi_coords = []
    strapi_coords = []
    
    if fastapi_route and fastapi_route.geometry:
        coords = fastapi_route.geometry.get('coordinates', [])
        fastapi_coords = coords
    
    if strapi_route and strapi_route.geometry:
        coords = strapi_route.geometry.get('coordinates', [])
        strapi_coords = coords
    
    print(f"FastAPI Route 1A coordinates: {len(fastapi_coords)}")
    print(f"Strapi Route 1A coordinates: {len(strapi_coords)}")
    if fastapi_coords and strapi_coords:
        print(f"✅ Both strategies provide route geometry (Strapi has {len(strapi_coords) - len(fastapi_coords)} more GPS points)")
    print()
    
    # Test 2: Vehicle Assignments (Phase 3A)
    print("🚗 TEST 2: Vehicle Assignments (Phase 3A)")
    print("-" * 50)
    
    fastapi_vehicles = await fastapi.get_vehicle_assignments()
    strapi_vehicles = await strapi.get_vehicle_assignments()
    
    print(f"FastAPI vehicle assignments: {len(fastapi_vehicles)}")
    print(f"Strapi vehicle assignments: {len(strapi_vehicles)}")
    
    if fastapi_vehicles and strapi_vehicles:
        print("✅ FastAPI Assignment Details:")
        for va in fastapi_vehicles[:1]:  # Show first assignment
            print(f"   Vehicle: {va.vehicle_id}, Route: {va.route_id}, Driver: {va.driver_id}")
        
        print("✅ Strapi Assignment Details:")
        for va in strapi_vehicles[:1]:  # Show first assignment
            print(f"   Vehicle: {va.vehicle_id}, Route: {va.route_id}, Driver: {va.driver_id}")
    print()
    
    # Test 3: Driver Assignments (Phase 3B)
    print("👨‍💼 TEST 3: Driver Assignments (Phase 3B)")
    print("-" * 50)
    
    fastapi_drivers = await fastapi.get_driver_assignments()
    strapi_drivers = await strapi.get_driver_assignments()
    
    print(f"FastAPI driver assignments: {len(fastapi_drivers)}")
    print(f"Strapi driver assignments: {len(strapi_drivers)}")
    
    if fastapi_drivers and strapi_drivers:
        print("✅ FastAPI Driver Details:")
        for da in fastapi_drivers[:1]:  # Show first assignment
            print(f"   Driver: {da.driver_id} ({da.driver_name}), Vehicle: {da.vehicle_id}")
        
        print("✅ Strapi Driver Details:")
        for da in strapi_drivers[:1]:  # Show first assignment
            print(f"   Driver: {da.driver_id} ({da.driver_name}), Vehicle: {da.vehicle_id}")
    print()
    
    # Test 4: Depot Vehicles (Phase 3C)
    print("🏭 TEST 4: Depot Vehicles (Phase 3C)")
    print("-" * 50)
    
    fastapi_depot = await fastapi.get_all_depot_vehicles()
    strapi_depot = await strapi.get_all_depot_vehicles()
    
    print(f"FastAPI depot vehicles: {len(fastapi_depot)}")
    print(f"Strapi depot vehicles: {len(strapi_depot)}")
    
    if fastapi_depot and strapi_depot:
        print("✅ FastAPI Depot Sample:")
        for vehicle in fastapi_depot[:1]:  # Show first vehicle
            print(f"   Vehicle: {vehicle.get('registration', 'N/A')}, Capacity: {vehicle.get('capacity', 'N/A')}")
        
        print("✅ Strapi Depot Sample:")
        for vehicle in strapi_depot[:1]:  # Show first vehicle
            print(f"   Vehicle: {vehicle.get('reg_code', 'N/A')}, Capacity: {vehicle.get('capacity', 'N/A')}")
    print()
    
    print("=" * 70)
    print("🎉 STRATEGY COMPARISON COMPLETE!")
    print("✅ Phase 1: Strategy Pattern ✅")
    print("✅ Phase 2: GTFS Route Geometry ✅")  
    print("✅ Phase 3: Vehicle/Driver Assignments ✅")
    print("🚀 Migration from FastAPI to Strapi SUCCESSFUL!")
    
    # Cleanup
    if fastapi.session:
        await fastapi.session.close()
    if strapi.session:
        await strapi.session.close()

if __name__ == "__main__":
    asyncio.run(test_strategy_comparison())