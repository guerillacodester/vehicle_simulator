"""
Test Depot and Route Reservoirs

Tests the commuter reservoir implementations to ensure proper functionality.
"""

import asyncio
import logging
from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.route_reservoir import RouteReservoir
from commuter_service.socketio_client import CommuterDirection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_depot_reservoir():
    """Test depot reservoir functionality"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Depot Reservoir")
    logger.info("=" * 80 + "\n")
    
    reservoir = DepotReservoir(socketio_url="http://localhost:1337")
    
    try:
        # Start reservoir
        logger.info("1. Starting depot reservoir...")
        await reservoir.start()
        logger.info("✅ Depot reservoir started\n")
        
        await asyncio.sleep(1)
        
        # Spawn commuters at depot
        logger.info("2. Spawning commuters at depot...")
        depot_loc = (40.7128, -74.0060)  # NYC coordinates
        
        for i in range(5):
            commuter = await reservoir.spawn_commuter(
                depot_id="DEPOT_001",
                route_id="ROUTE_A",
                depot_location=depot_loc,
                destination=(40.7589, -73.9851),  # Times Square
                priority=3
            )
            logger.info(f"   Spawned commuter {commuter.commuter_id}")
        
        logger.info("✅ Spawned 5 commuters\n")
        
        await asyncio.sleep(1)
        
        # Query commuters
        logger.info("3. Querying commuters near depot...")
        vehicle_loc = (40.7130, -74.0062)  # Very close to depot
        commuters = reservoir.query_commuters_sync(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            vehicle_location=vehicle_loc,
            max_distance=500,
            max_count=10
        )
        logger.info(f"✅ Found {len(commuters)} available commuters\n")
        
        # Mark one as picked up
        if commuters:
            logger.info("4. Marking commuter as picked up...")
            picked_up = await reservoir.mark_picked_up(commuters[0].commuter_id)
            logger.info(f"✅ Pickup status: {picked_up}\n")
        
        # Get statistics
        logger.info("5. Reservoir statistics:")
        stats = reservoir.get_stats()
        logger.info(f"   Active commuters: {stats['total_active_commuters']}")
        logger.info(f"   Total spawned: {stats['total_spawned']}")
        logger.info(f"   Total picked up: {stats['total_picked_up']}")
        logger.info(f"   Total queues: {stats['total_queues']}")
        logger.info("✅ Statistics retrieved\n")
        
        # Stop reservoir
        logger.info("6. Stopping depot reservoir...")
        await reservoir.stop()
        logger.info("✅ Depot reservoir stopped\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Depot reservoir test failed: {e}")
        return False


async def test_route_reservoir():
    """Test route reservoir functionality"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Route Reservoir")
    logger.info("=" * 80 + "\n")
    
    reservoir = RouteReservoir(socketio_url="http://localhost:1337")
    
    try:
        # Start reservoir
        logger.info("1. Starting route reservoir...")
        await reservoir.start()
        logger.info("✅ Route reservoir started\n")
        
        await asyncio.sleep(1)
        
        # Spawn inbound commuters
        logger.info("2. Spawning inbound commuters along route...")
        for i in range(3):
            lat = 40.7200 + (i * 0.01)  # Spread along route
            lon = -74.0000 + (i * 0.01)
            
            commuter = await reservoir.spawn_commuter(
                route_id="ROUTE_A",
                current_location=(lat, lon),
                destination=(40.7128, -74.0060),  # Back to depot
                direction=CommuterDirection.INBOUND,
                priority=3
            )
            logger.info(f"   Spawned inbound commuter {commuter.commuter_id} at ({lat:.4f}, {lon:.4f})")
        
        logger.info("✅ Spawned 3 inbound commuters\n")
        
        # Spawn outbound commuters
        logger.info("3. Spawning outbound commuters along route...")
        for i in range(3):
            lat = 40.7300 + (i * 0.01)
            lon = -73.9900 + (i * 0.01)
            
            commuter = await reservoir.spawn_commuter(
                route_id="ROUTE_A",
                current_location=(lat, lon),
                destination=(40.7589, -73.9851),  # Times Square
                direction=CommuterDirection.OUTBOUND,
                priority=3
            )
            logger.info(f"   Spawned outbound commuter {commuter.commuter_id} at ({lat:.4f}, {lon:.4f})")
        
        logger.info("✅ Spawned 3 outbound commuters\n")
        
        await asyncio.sleep(1)
        
        # Query inbound commuters
        logger.info("4. Querying inbound commuters...")
        vehicle_loc = (40.7210, -73.9990)
        inbound = reservoir.query_commuters_sync(
            route_id="ROUTE_A",
            vehicle_location=vehicle_loc,
            direction=CommuterDirection.INBOUND,
            max_distance=2000,
            max_count=10
        )
        logger.info(f"✅ Found {len(inbound)} inbound commuters\n")
        
        # Query outbound commuters
        logger.info("5. Querying outbound commuters...")
        outbound = reservoir.query_commuters_sync(
            route_id="ROUTE_A",
            vehicle_location=(40.7310, -73.9890),
            direction=CommuterDirection.OUTBOUND,
            max_distance=2000,
            max_count=10
        )
        logger.info(f"✅ Found {len(outbound)} outbound commuters\n")
        
        # Mark one as picked up
        if inbound:
            logger.info("6. Marking inbound commuter as picked up...")
            picked_up = await reservoir.mark_picked_up(inbound[0].commuter_id)
            logger.info(f"✅ Pickup status: {picked_up}\n")
        
        # Get statistics
        logger.info("7. Reservoir statistics:")
        stats = reservoir.get_stats()
        logger.info(f"   Active commuters: {stats['total_active_commuters']}")
        logger.info(f"   Inbound: {stats['total_inbound']}")
        logger.info(f"   Outbound: {stats['total_outbound']}")
        logger.info(f"   Grid cells: {stats['total_grid_cells']}")
        logger.info(f"   Total spawned: {stats['total_spawned']}")
        logger.info(f"   Total picked up: {stats['total_picked_up']}")
        logger.info("✅ Statistics retrieved\n")
        
        # Stop reservoir
        logger.info("8. Stopping route reservoir...")
        await reservoir.stop()
        logger.info("✅ Route reservoir stopped\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Route reservoir test failed: {e}")
        return False


async def test_both_reservoirs():
    """Test both reservoirs running simultaneously"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Both Reservoirs Simultaneously")
    logger.info("=" * 80 + "\n")
    
    depot_res = DepotReservoir(socketio_url="http://localhost:1337")
    route_res = RouteReservoir(socketio_url="http://localhost:1337")
    
    try:
        # Start both
        logger.info("1. Starting both reservoirs...")
        await depot_res.start()
        await route_res.start()
        logger.info("✅ Both reservoirs started\n")
        
        await asyncio.sleep(1)
        
        # Spawn commuters in both
        logger.info("2. Spawning commuters in both reservoirs...")
        
        # Depot commuters
        await depot_res.spawn_commuter(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            depot_location=(40.7128, -74.0060),
            destination=(40.7589, -73.9851),
            priority=3
        )
        logger.info("   ✓ Depot commuter spawned")
        
        # Route commuters
        await route_res.spawn_commuter(
            route_id="ROUTE_A",
            current_location=(40.7200, -74.0000),
            destination=(40.7589, -73.9851),
            direction=CommuterDirection.OUTBOUND,
            priority=3
        )
        logger.info("   ✓ Route commuter spawned")
        
        logger.info("✅ Commuters spawned in both reservoirs\n")
        
        await asyncio.sleep(1)
        
        # Get stats from both
        logger.info("3. Statistics from both reservoirs:")
        depot_stats = depot_res.get_stats()
        route_stats = route_res.get_stats()
        
        logger.info(f"   Depot: {depot_stats['total_active_commuters']} active")
        logger.info(f"   Route: {route_stats['total_active_commuters']} active")
        logger.info("✅ Both reservoirs operational\n")
        
        # Stop both
        logger.info("4. Stopping both reservoirs...")
        await depot_res.stop()
        await route_res.stop()
        logger.info("✅ Both reservoirs stopped\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Simultaneous reservoir test failed: {e}")
        return False


async def run_all_tests():
    """Run all reservoir tests"""
    logger.info("\n" + "🚀" * 40)
    logger.info("COMMUTER RESERVOIR TEST SUITE")
    logger.info("🚀" * 40 + "\n")
    
    tests = [
        ("Depot Reservoir", test_depot_reservoir),
        ("Route Reservoir", test_route_reservoir),
        ("Both Reservoirs", test_both_reservoirs),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            await asyncio.sleep(2)  # Brief pause between tests
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    logger.info("=" * 80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    print("\n" + "⚠️ " * 30)
    print("PREREQUISITES:")
    print("1. Strapi server running: cd arknet_fleet_manager/arknet-fleet-api && npm run dev")
    print("2. Socket.IO initialized (Phase 1 complete)")
    print("3. Wait for server to be ready (http://localhost:1337)")
    print("⚠️ " * 30 + "\n")
    
    input("Press ENTER when Strapi server is running...")
    
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n" + "🎉" * 30)
        print("ALL RESERVOIR TESTS PASSED!")
        print("🎉" * 30 + "\n")
    else:
        print("\n" + "⚠️ " * 30)
        print("SOME TESTS FAILED. Review the logs above.")
        print("⚠️ " * 30 + "\n")
