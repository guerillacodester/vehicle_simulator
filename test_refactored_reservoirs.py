"""
Test Refactored Reservoirs

Tests the refactored reservoir implementations with base class inheritance.
"""

import asyncio
import logging
from commuter_service.depot_reservoir_refactored import DepotReservoir
from commuter_service.route_reservoir_refactored import RouteReservoir
from commuter_service.socketio_client import CommuterDirection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_refactored_reservoirs():
    """Test both refactored reservoirs"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Refactored Reservoirs with Base Class")
    logger.info("=" * 80 + "\n")
    
    depot_res = DepotReservoir()
    route_res = RouteReservoir()
    
    try:
        # Start both
        logger.info("1. Starting both refactored reservoirs...")
        await depot_res.start()
        await route_res.start()
        logger.info("✅ Both reservoirs started\n")
        
        await asyncio.sleep(1)
        
        # Test depot reservoir
        logger.info("2. Testing depot reservoir...")
        depot_commuter = await depot_res.spawn_commuter(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            depot_location=(40.7128, -74.0060),
            destination=(40.7589, -73.9851),
            priority=0.5
        )
        logger.info(f"   ✓ Spawned depot commuter: {depot_commuter.commuter_id}")
        
        depot_results = depot_res.query_commuters_sync(
            depot_id="DEPOT_001",
            route_id="ROUTE_A",
            vehicle_location=(40.7130, -74.0062),
            max_distance=500
        )
        logger.info(f"   ✓ Found {len(depot_results)} depot commuters")
        logger.info("✅ Depot reservoir working\n")
        
        # Test route reservoir
        logger.info("3. Testing route reservoir...")
        route_commuter = await route_res.spawn_commuter(
            route_id="ROUTE_A",
            current_location=(40.7200, -74.0000),
            destination=(40.7589, -73.9851),
            direction=CommuterDirection.OUTBOUND,
            priority=0.5
        )
        logger.info(f"   ✓ Spawned route commuter: {route_commuter.commuter_id}")
        
        route_results = route_res.query_commuters_sync(
            route_id="ROUTE_A",
            vehicle_location=(40.7210, -73.9990),
            direction=CommuterDirection.OUTBOUND,
            max_distance=2000
        )
        logger.info(f"   ✓ Found {len(route_results)} route commuters")
        logger.info("✅ Route reservoir working\n")
        
        # Test base class functionality
        logger.info("4. Testing base class features...")
        
        # Test distance calculation (inherited)
        distance = depot_res.calculate_distance(
            (40.7128, -74.0060),
            (40.7589, -73.9851)
        )
        logger.info(f"   ✓ Distance calculation: {distance:.2f} meters")
        
        # Test mark_picked_up (inherited)
        picked_up = await depot_res.mark_picked_up(depot_commuter.commuter_id)
        logger.info(f"   ✓ Mark picked up: {picked_up}")
        
        # Test statistics (inherited + extended)
        depot_stats = depot_res.get_stats()
        route_stats = route_res.get_stats()
        logger.info(f"   ✓ Depot stats: {depot_stats['total_active_commuters']} active, {depot_stats['total_queues']} queues")
        logger.info(f"   ✓ Route stats: {route_stats['total_active_commuters']} active, {route_stats['total_grid_cells']} cells")
        logger.info("✅ Base class features working\n")
        
        # Stop both
        logger.info("5. Stopping both reservoirs...")
        await depot_res.stop()
        await route_res.stop()
        logger.info("✅ Both reservoirs stopped\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_test():
    """Run the refactored reservoir test"""
    logger.info("\n" + "🔧" * 40)
    logger.info("REFACTORED RESERVOIR TEST")
    logger.info("🔧" * 40 + "\n")
    
    success = await test_refactored_reservoirs()
    
    if success:
        logger.info("\n" + "🎉" * 30)
        logger.info("REFACTORED RESERVOIRS WORKING!")
        logger.info("Benefits:")
        logger.info("  - Code deduplication via base class")
        logger.info("  - Configurable via reservoir_config.py")
        logger.info("  - Shared distance calculations")
        logger.info("  - Shared lifecycle management")
        logger.info("  - Shared statistics tracking")
        logger.info("🎉" * 30 + "\n")
    else:
        logger.info("\n" + "⚠️ " * 30)
        logger.info("TEST FAILED. Review the logs above.")
        logger.info("⚠️ " * 30 + "\n")
    
    return success


if __name__ == "__main__":
    print("\n" + "⚠️ " * 30)
    print("PREREQUISITES:")
    print("1. Strapi server running on http://localhost:1337")
    print("2. Socket.IO initialized (Phase 1 complete)")
    print("⚠️ " * 30 + "\n")
    
    input("Press ENTER when Strapi server is running...")
    
    success = asyncio.run(run_test())
    
    if success:
        print("\n✅ Refactoring successful!")
    else:
        print("\n❌ Refactoring needs fixes.")
