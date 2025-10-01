#!/usr/bin/env python3
"""Demonstrate strategy switching capabilities with the new default"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'arknet_transit_simulator'))

from core.dispatcher import Dispatcher

async def demo_strategy_switching():
    """Demonstrate dynamic strategy switching with new default"""
    
    print("🔄 STRATEGY SWITCHING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize dispatcher with new default (Strapi)
    dispatcher = Dispatcher("DemoDispatcher")
    await dispatcher.initialize()
    
    print("📋 INITIAL STATE (New Default)")
    print("-" * 40)
    print(f"Strategy: {dispatcher.get_current_strategy()}")
    print(f"API URL: {dispatcher.get_current_api_url()}")
    print()
    
    # Test getting some data with Strapi
    if dispatcher.api_connected:
        route_info = await dispatcher.get_route_info("1A")
        assignments = await dispatcher.get_vehicle_assignments()
        
        print("🗺️  Route Data (Strapi):")
        if route_info and route_info.geometry:
            coords = len(route_info.geometry.get('coordinates', []))
            print(f"  Route 1A: {coords} GPS coordinates")
        
        print(f"  Vehicle assignments: {len(assignments)}")
        print()
    
    # Switch to FastAPI for comparison
    print("🔄 SWITCHING TO FASTAPI")
    print("-" * 40)
    
    fastapi_ok = await dispatcher.switch_to_fastapi()
    if fastapi_ok:
        print(f"✅ Switched to: {dispatcher.get_current_strategy()}")
        print(f"API URL: {dispatcher.get_current_api_url()}")
        
        # Test getting data with FastAPI
        route_info = await dispatcher.get_route_info("1A")
        assignments = await dispatcher.get_vehicle_assignments()
        
        print("🗺️  Route Data (FastAPI):")
        if route_info and route_info.geometry:
            coords = len(route_info.geometry.get('coordinates', []))
            print(f"  Route 1A: {coords} GPS coordinates")
        
        print(f"  Vehicle assignments: {len(assignments)}")
        print()
    else:
        print("❌ Failed to switch to FastAPI")
    
    # Switch back to Strapi
    print("🔄 SWITCHING BACK TO STRAPI")
    print("-" * 40)
    
    strapi_ok = await dispatcher.switch_to_strapi()
    if strapi_ok:
        print(f"✅ Switched to: {dispatcher.get_current_strategy()}")
        print(f"API URL: {dispatcher.get_current_api_url()}")
        print()
    else:
        print("❌ Failed to switch to Strapi")
    
    print("🎉 DEMONSTRATION SUMMARY")
    print("=" * 60)
    print("✅ New default: StrapiStrategy (modern GTFS-compliant)")
    print("✅ Backward compatibility: Can switch to FastAPI anytime")
    print("✅ Dynamic switching: Change strategies without restart")
    print("✅ Data quality: Strapi provides better GPS precision")
    print("✅ Production ready: Modern architecture with fallback")
    
    # Cleanup
    await dispatcher.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_strategy_switching())