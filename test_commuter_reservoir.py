"""
Test Commuter Reservoir System
==============================

Test the basic reservoir functionality:
1. Initialize reservoir with GTFS data
2. Spawn commuters using statistical models
3. Query commuters by location/depot/route
4. Consume commuters (simulate pickup)
"""

import asyncio
import logging
from datetime import datetime
from commuter_service.commuter_reservoir import CommuterReservoir, ReservoirQuery
from commuter_service.strapi_api_client import StrapiApiClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_reservoir_initialization():
    """Test reservoir initialization with GTFS data"""
    print("\n🏊 Testing Reservoir Initialization...")
    
    api_client = StrapiApiClient()
    reservoir = CommuterReservoir(api_client)
    
    try:
        await api_client.connect()
        success = await reservoir.initialize()
        
        if success:
            status = reservoir.get_reservoir_status()
            print(f"✅ Reservoir initialized successfully")
            print(f"   Depot locations: {len(status['commuters_by_depot'])}")
            print(f"   Route geometries: {len(status['commuters_by_route'])}")
            print(f"   Total commuters: {status['total_commuters']}")
            return reservoir
        else:
            print("❌ Reservoir initialization failed")
            return None
            
    except Exception as e:
        print(f"❌ Error initializing reservoir: {e}")
        return None

async def test_commuter_spawning(reservoir: CommuterReservoir):
    """Test statistical commuter spawning"""
    print("\n🎯 Testing Commuter Spawning...")
    
    try:
        current_time = datetime.now()
        spawned_count = await reservoir.spawn_commuters_statistical(current_time, time_window_minutes=10)
        
        status = reservoir.get_reservoir_status()
        print(f"✅ Spawned {spawned_count} commuters")
        print(f"   Total in reservoir: {status['total_commuters']}")
        print(f"   Average wait time: {status['average_wait_minutes']}min")
        print(f"   Recent spawn rate: {status['recent_spawn_rate']:.1f}/min")
        
        # Show commuters by depot
        for depot_id, count in status['commuters_by_depot'].items():
            if count > 0:
                print(f"   {depot_id}: {count} commuters")
        
        return spawned_count > 0
        
    except Exception as e:
        print(f"❌ Error spawning commuters: {e}")
        return False

async def test_commuter_queries(reservoir: CommuterReservoir):
    """Test commuter querying from reservoir"""
    print("\n🔍 Testing Commuter Queries...")
    
    try:
        # Query by depot
        depot_query = ReservoirQuery(depot_id="test-depot_id-123", max_commuters=3)
        depot_commuters = reservoir.query_commuters(depot_query)
        
        print(f"✅ Depot query found {len(depot_commuters)} commuters")
        for commuter in depot_commuters[:2]:
            print(f"   - {commuter.person_id}: {commuter.origin_stop_id} → {commuter.destination_stop_id}")
        
        # Query by route
        route_query = ReservoirQuery(route_id="1A", max_commuters=5)
        route_commuters = reservoir.query_commuters(route_query)
        
        print(f"✅ Route query found {len(route_commuters)} commuters")
        
        # Query by location (if we have depot location)
        if reservoir.depot_locations:
            depot_location = list(reservoir.depot_locations.values())[0]
            location_query = ReservoirQuery(
                location=depot_location, 
                radius_km=2.0, 
                max_commuters=4
            )
            location_commuters = reservoir.query_commuters(location_query)
            
            print(f"✅ Location query found {len(location_commuters)} commuters")
            print(f"   Search location: {depot_location}")
        
        return len(depot_commuters) > 0 or len(route_commuters) > 0
        
    except Exception as e:
        print(f"❌ Error querying commuters: {e}")
        return False

async def test_commuter_consumption(reservoir: CommuterReservoir):
    """Test commuter consumption (pickup simulation)"""
    print("\n🚌 Testing Commuter Consumption...")
    
    try:
        # Get some commuters to consume
        query = ReservoirQuery(max_commuters=3)
        commuters_to_pickup = reservoir.query_commuters(query)
        
        if commuters_to_pickup:
            initial_count = reservoir.get_reservoir_status()['total_commuters']
            
            # Consume (pickup) commuters
            consumed_count = reservoir.consume_commuters(commuters_to_pickup)
            
            final_count = reservoir.get_reservoir_status()['total_commuters']
            
            print(f"✅ Consumed {consumed_count} commuters")
            print(f"   Before: {initial_count} commuters")
            print(f"   After: {final_count} commuters")
            print(f"   Difference: {initial_count - final_count}")
            
            return consumed_count > 0
        else:
            print("⚠️  No commuters available for consumption")
            return True  # Not a failure, just no commuters
            
    except Exception as e:
        print(f"❌ Error consuming commuters: {e}")
        return False

async def test_reservoir_statistics(reservoir: CommuterReservoir):
    """Test reservoir statistics and monitoring"""
    print("\n📊 Testing Reservoir Statistics...")
    
    try:
        status = reservoir.get_reservoir_status()
        
        print(f"✅ Reservoir Statistics:")
        print(f"   Total spawned: {status['total_spawned']}")
        print(f"   Total consumed: {status['total_consumed']}")
        print(f"   Efficiency: {status['efficiency_rate']:.1f}%")
        print(f"   Current commuters: {status['total_commuters']}")
        print(f"   Spatial grid cells: {status['spatial_grid_cells']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False

async def main():
    """Run all reservoir tests"""
    print("🧪 COMMUTER RESERVOIR SYSTEM TESTS")
    print("=" * 50)
    
    # Test 1: Initialize reservoir
    reservoir = await test_reservoir_initialization()
    if not reservoir:
        print("❌ Cannot proceed - reservoir initialization failed")
        return
    
    # Test 2: Spawn commuters
    spawn_success = await test_commuter_spawning(reservoir)
    if not spawn_success:
        print("⚠️  No commuters spawned - continuing with empty reservoir")
    
    # Test 3: Query commuters
    query_success = await test_commuter_queries(reservoir)
    
    # Test 4: Consume commuters
    consumption_success = await test_commuter_consumption(reservoir)
    
    # Test 5: Statistics
    stats_success = await test_reservoir_statistics(reservoir)
    
    # Final summary
    print(f"\n🎯 TEST SUMMARY:")
    print(f"   Initialization: {'✅' if reservoir else '❌'}")
    print(f"   Spawning: {'✅' if spawn_success else '⚠️'}")
    print(f"   Querying: {'✅' if query_success else '❌'}")
    print(f"   Consumption: {'✅' if consumption_success else '❌'}")
    print(f"   Statistics: {'✅' if stats_success else '❌'}")
    
    # Cleanup
    await reservoir.api_client.close()
    
    print(f"\n🎉 Reservoir system test completed!")

if __name__ == "__main__":
    asyncio.run(main())