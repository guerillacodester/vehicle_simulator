"""
Test Passenger Reservoir System
==============================

Test the basic reservoir functionality:
1. Initialize reservoir with GTFS data
2. Spawn passengers using statistical models
3. Query passengers by location/depot/route
4. Consume passengers (simulate pickup)
"""

import asyncio
import logging
from datetime import datetime
from passenger_service.passenger_reservoir import PassengerReservoir, ReservoirQuery
from passenger_service.strapi_api_client import StrapiApiClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_reservoir_initialization():
    """Test reservoir initialization with GTFS data"""
    print("\n🏊 Testing Reservoir Initialization...")
    
    api_client = StrapiApiClient()
    reservoir = PassengerReservoir(api_client)
    
    try:
        await api_client.connect()
        success = await reservoir.initialize()
        
        if success:
            status = reservoir.get_reservoir_status()
            print(f"✅ Reservoir initialized successfully")
            print(f"   Depot locations: {len(status['passengers_by_depot'])}")
            print(f"   Route geometries: {len(status['passengers_by_route'])}")
            print(f"   Total passengers: {status['total_passengers']}")
            return reservoir
        else:
            print("❌ Reservoir initialization failed")
            return None
            
    except Exception as e:
        print(f"❌ Error initializing reservoir: {e}")
        return None

async def test_passenger_spawning(reservoir: PassengerReservoir):
    """Test statistical passenger spawning"""
    print("\n🎯 Testing Passenger Spawning...")
    
    try:
        current_time = datetime.now()
        spawned_count = await reservoir.spawn_passengers_statistical(current_time, time_window_minutes=10)
        
        status = reservoir.get_reservoir_status()
        print(f"✅ Spawned {spawned_count} passengers")
        print(f"   Total in reservoir: {status['total_passengers']}")
        print(f"   Average wait time: {status['average_wait_minutes']}min")
        print(f"   Recent spawn rate: {status['recent_spawn_rate']:.1f}/min")
        
        # Show passengers by depot
        for depot_id, count in status['passengers_by_depot'].items():
            if count > 0:
                print(f"   {depot_id}: {count} passengers")
        
        return spawned_count > 0
        
    except Exception as e:
        print(f"❌ Error spawning passengers: {e}")
        return False

async def test_passenger_queries(reservoir: PassengerReservoir):
    """Test passenger querying from reservoir"""
    print("\n🔍 Testing Passenger Queries...")
    
    try:
        # Query by depot
        depot_query = ReservoirQuery(depot_id="test-depot_id-123", max_passengers=3)
        depot_passengers = reservoir.query_passengers(depot_query)
        
        print(f"✅ Depot query found {len(depot_passengers)} passengers")
        for passenger in depot_passengers[:2]:
            print(f"   - {passenger.person_id}: {passenger.origin_stop_id} → {passenger.destination_stop_id}")
        
        # Query by route
        route_query = ReservoirQuery(route_id="1A", max_passengers=5)
        route_passengers = reservoir.query_passengers(route_query)
        
        print(f"✅ Route query found {len(route_passengers)} passengers")
        
        # Query by location (if we have depot location)
        if reservoir.depot_locations:
            depot_location = list(reservoir.depot_locations.values())[0]
            location_query = ReservoirQuery(
                location=depot_location, 
                radius_km=2.0, 
                max_passengers=4
            )
            location_passengers = reservoir.query_passengers(location_query)
            
            print(f"✅ Location query found {len(location_passengers)} passengers")
            print(f"   Search location: {depot_location}")
        
        return len(depot_passengers) > 0 or len(route_passengers) > 0
        
    except Exception as e:
        print(f"❌ Error querying passengers: {e}")
        return False

async def test_passenger_consumption(reservoir: PassengerReservoir):
    """Test passenger consumption (pickup simulation)"""
    print("\n🚌 Testing Passenger Consumption...")
    
    try:
        # Get some passengers to consume
        query = ReservoirQuery(max_passengers=3)
        passengers_to_pickup = reservoir.query_passengers(query)
        
        if passengers_to_pickup:
            initial_count = reservoir.get_reservoir_status()['total_passengers']
            
            # Consume (pickup) passengers
            consumed_count = reservoir.consume_passengers(passengers_to_pickup)
            
            final_count = reservoir.get_reservoir_status()['total_passengers']
            
            print(f"✅ Consumed {consumed_count} passengers")
            print(f"   Before: {initial_count} passengers")
            print(f"   After: {final_count} passengers")
            print(f"   Difference: {initial_count - final_count}")
            
            return consumed_count > 0
        else:
            print("⚠️  No passengers available for consumption")
            return True  # Not a failure, just no passengers
            
    except Exception as e:
        print(f"❌ Error consuming passengers: {e}")
        return False

async def test_reservoir_statistics(reservoir: PassengerReservoir):
    """Test reservoir statistics and monitoring"""
    print("\n📊 Testing Reservoir Statistics...")
    
    try:
        status = reservoir.get_reservoir_status()
        
        print(f"✅ Reservoir Statistics:")
        print(f"   Total spawned: {status['total_spawned']}")
        print(f"   Total consumed: {status['total_consumed']}")
        print(f"   Efficiency: {status['efficiency_rate']:.1f}%")
        print(f"   Current passengers: {status['total_passengers']}")
        print(f"   Spatial grid cells: {status['spatial_grid_cells']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False

async def main():
    """Run all reservoir tests"""
    print("🧪 PASSENGER RESERVOIR SYSTEM TESTS")
    print("=" * 50)
    
    # Test 1: Initialize reservoir
    reservoir = await test_reservoir_initialization()
    if not reservoir:
        print("❌ Cannot proceed - reservoir initialization failed")
        return
    
    # Test 2: Spawn passengers
    spawn_success = await test_passenger_spawning(reservoir)
    if not spawn_success:
        print("⚠️  No passengers spawned - continuing with empty reservoir")
    
    # Test 3: Query passengers
    query_success = await test_passenger_queries(reservoir)
    
    # Test 4: Consume passengers
    consumption_success = await test_passenger_consumption(reservoir)
    
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