"""
Simple Commuter Spawning Test
============================
Test spawning at current time to avoid expiration issues
"""

import asyncio
import logging
from datetime import datetime
from commuter_service.commuter_reservoir import CommuterReservoir, ReservoirQuery
from commuter_service.strapi_api_client import StrapiApiClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def simple_spawning_test():
    """Simple test of current-time spawning"""
    
    api_client = StrapiApiClient()
    reservoir = CommuterReservoir(api_client)
    
    try:
        await api_client.connect()
        await reservoir.initialize()
        
        print("\n🎯 SIMPLE SPAWNING TEST")
        print("=" * 30)
        
        # Use current time to avoid expiration
        current_time = datetime.now()
        print(f"Current time: {current_time.strftime('%H:%M:%S')}")
        
        print(f"Base spawn rate: 5.0 commuters/hour (hardcoded)")
        print(f"Depots: {len(reservoir.depot_locations)}")
        print(f"Routes: {len(reservoir.route_geometries)}")
        
        # Show current hour to understand time factor
        hour = current_time.hour
        is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
        print(f"Current hour: {hour}, Is peak time: {is_peak}")
        
        # Spawn commuters
        spawned = await reservoir.spawn_commuters_statistical(current_time, time_window_minutes=10)
        
        print(f"\n✅ Spawned {spawned} commuters")
        
        # Check reservoir status
        status = reservoir.get_reservoir_status()
        print(f"Reservoir status:")
        print(f"  Total: {status['total_commuters']}")
        print(f"  By depot: {status['commuters_by_depot']}")
        print(f"  By route: {status['commuters_by_route']}")
        
        # Test queries if we have commuters
        if status['total_commuters'] > 0:
            print(f"\n🔍 QUERY TESTS")
            
            # Query all commuters
            all_query = ReservoirQuery(max_commuters=100)
            all_commuters = reservoir.query_commuters(all_query)
            print(f"All commuters query: {len(all_commuters)} found")
            
            # Show first few commuters
            for i, commuter in enumerate(all_commuters[:3]):
                print(f"  Commuter {i+1}: {commuter.person_id}")
                print(f"    Type: {type(commuter)}")
                print(f"    Origin: {getattr(commuter, 'origin_stop_id', 'N/A')}")
                print(f"    Destination: {getattr(commuter, 'destination_stop_id', 'N/A')}")
                print(f"    Trip purpose: {getattr(commuter, 'trip_purpose', 'N/A')}")
            
            # Test consumption
            print(f"\n🚌 CONSUMPTION TEST")
            to_pickup = all_commuters[:2] if len(all_commuters) >= 2 else all_commuters
            consumed = reservoir.consume_commuters(to_pickup)
            print(f"Consumed {consumed} commuters")
            
            # Final status
            final_status = reservoir.get_reservoir_status()
            print(f"Final total: {final_status['total_commuters']}")
        
        # Rates are hardcoded in the reservoir, no need to restore
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await api_client.close()

if __name__ == "__main__":
    asyncio.run(simple_spawning_test())