#!/usr/bin/env python3
"""Check which strategy is currently in use"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'arknet_transit_simulator'))

from core.dispatcher import Dispatcher

async def check_current_strategy():
    """Check which strategy is currently being used by the simulator"""
    
    # Initialize dispatcher the same way the simulator does (using new default)
    dispatcher = Dispatcher("FleetDispatcher")
    
    # Check the strategy type
    strategy_type = type(dispatcher.api_strategy).__name__
    strategy_url = getattr(dispatcher.api_strategy, 'api_base_url', 'Unknown')
    
    print("🔍 CURRENT STRATEGY ANALYSIS")
    print("=" * 50)
    print(f"Strategy Type: {strategy_type}")
    print(f"API Base URL: {strategy_url}")
    print()
    
    # Test connection to see if it's working
    await dispatcher.api_strategy.initialize()
    connection_ok = await dispatcher.api_strategy.test_connection()
    
    if connection_ok:
        print(f"✅ {strategy_type} connection successful")
        print(f"   Connected to: {strategy_url}")
        
        # Try to get some data to confirm it's working
        try:
            vehicle_assignments = await dispatcher.api_strategy.get_vehicle_assignments()
            print(f"   Vehicle assignments: {len(vehicle_assignments)}")
            
            depot_vehicles = await dispatcher.api_strategy.get_all_depot_vehicles()
            print(f"   Depot vehicles: {len(depot_vehicles)}")
            
        except Exception as e:
            print(f"   Data retrieval test failed: {e}")
    else:
        print(f"❌ {strategy_type} connection failed")
        print(f"   Could not connect to: {strategy_url}")
    
    print()
    print("📋 CONCLUSION:")
    if strategy_type == "FastApiStrategy":
        print("   🏭 Currently using: FASTAPI STRATEGY (Legacy)")
        print("   📍 Status: Deprecated but functional")
        print("   🔄 Migration: Ready to switch to Strapi")
    elif strategy_type == "StrapiStrategy":
        print("   🆕 Currently using: STRAPI STRATEGY (Modern)")
        print("   📍 Status: GTFS-compliant with improved data")
        print("   ✅ Migration: Complete")
    else:
        print(f"   ❓ Unknown strategy type: {strategy_type}")
    
    # Cleanup
    if hasattr(dispatcher.api_strategy, 'session') and dispatcher.api_strategy.session:
        await dispatcher.api_strategy.session.close()

if __name__ == "__main__":
    asyncio.run(check_current_strategy())