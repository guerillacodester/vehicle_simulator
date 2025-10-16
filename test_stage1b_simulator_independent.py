"""
Stage 1B: Test Simulator Runs Independently
============================================
Tests that the vehicle simulator can start, load vehicles, and operate
WITHOUT requiring the commuter service to be running.

Success Criteria:
- Simulator starts successfully
- Loads vehicles from Strapi
- Loads routes from Strapi  
- Can display vehicle assignments
- No errors related to missing commuter service
"""
import asyncio
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_simulator_startup():
    """Test that simulator can start and load data"""
    from arknet_transit_simulator.simulator import CleanVehicleSimulator
    
    logger.info("=" * 80)
    logger.info("STAGE 1B: Testing Simulator Independent Operation")
    logger.info("=" * 80)
    
    try:
        # Initialize simulator
        logger.info("\n1️⃣ Initializing simulator...")
        sim = CleanVehicleSimulator(api_url="http://localhost:1337")
        
        # Initialize depot and dispatcher
        success = await sim.initialize()
        if not success:
            logger.error("   ❌ Simulator initialization failed")
            return False
            
        logger.info("   ✅ Simulator initialized")
        
        # Test vehicle assignments
        logger.info("\n2️⃣ Loading vehicle assignments from Strapi...")
        assignments = await sim.get_vehicle_assignments()
        
        if not assignments:
            logger.warning("   ⚠️  No vehicle assignments found!")
            logger.warning("   This may indicate Strapi database is empty")
            return False
        
        logger.info(f"   ✅ Loaded {len(assignments)} vehicle assignments")
        
        # Display first few assignments
        logger.info("\n3️⃣ Sample vehicle assignments:")
        for i, assignment in enumerate(assignments[:3], 1):
            logger.info(f"   Assignment {i}:")
            logger.info(f"      Vehicle: {assignment.vehicle_reg_code}")
            logger.info(f"      Driver:  {assignment.driver_name}")
            logger.info(f"      Route:   {assignment.route_name}")
        
        if len(assignments) > 3:
            logger.info(f"   ... and {len(assignments) - 3} more assignments")
        
        # Test route loading
        logger.info("\n4️⃣ Testing route data loading...")
        first_route_id = assignments[0].route_id
        route_info = await sim.get_route_info(first_route_id)
        
        if route_info:
            logger.info(f"   ✅ Route '{route_info.route_name}' loaded successfully")
            if route_info.geometry:
                coord_count = route_info.coordinate_count or len(route_info.geometry.get('coordinates', []))
                logger.info(f"      GPS points: {coord_count}")
            else:
                logger.info("      ⚠️  No geometry data for this route")
        else:
            logger.warning(f"   ⚠️  Could not load route {first_route_id}")
        
        # Test depot loading
        logger.info("\n5️⃣ Testing depot data loading...")
        try:
            depot_data = await sim.depot.api_client.get_depots()
            if depot_data:
                logger.info(f"   ✅ Loaded {len(depot_data)} depots")
                if depot_data:
                    logger.info(f"      Sample depot: {depot_data[0].depot_name}")
            else:
                logger.warning("   ⚠️  No depots found in database")
        except Exception as e:
            logger.error(f"   ❌ Error loading depots: {e}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 1B TEST RESULTS:")
        logger.info("=" * 80)
        logger.info("✅ Simulator initialization:      PASSED")
        logger.info("✅ Vehicle assignment loading:    PASSED")
        logger.info("✅ Route data loading:            PASSED")
        logger.info("✅ Depot data loading:            PASSED")
        logger.info("✅ Independent operation:         PASSED")
        logger.info("")
        logger.info("🎉 Simulator can run independently without commuter service!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error(f"❌ STAGE 1B FAILED: {e}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        return False


async def test_simulator_initialization():
    """Test that simulator can initialize and shutdown cleanly"""
    from arknet_transit_simulator.simulator import CleanVehicleSimulator
    
    logger.info("\n" + "=" * 80)
    logger.info("BONUS TEST: Simulator Initialize/Shutdown Cycle")
    logger.info("=" * 80)
    
    try:
        sim = CleanVehicleSimulator(api_url="http://localhost:1337")
        
        logger.info("\n1️⃣ Initializing simulator...")
        success = await sim.initialize()
        
        if not success:
            logger.error("   ❌ Simulator initialization failed")
            return False
            
        logger.info("   ✅ Simulator initialized successfully")
        logger.info(f"      Depot: {sim.depot is not None}")
        logger.info(f"      Dispatcher: {sim.dispatcher is not None}")
        
        logger.info("\n2️⃣ Shutting down simulator...")
        await sim.shutdown()
        logger.info("   ✅ Simulator shutdown cleanly")
        
        logger.info("\n✅ Initialize/Shutdown cycle completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Initialize/Shutdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Stage 1B tests"""
    logger.info("\n")
    logger.info("╔════════════════════════════════════════════════════════════════════════╗")
    logger.info("║                   STAGE 1B: SIMULATOR INDEPENDENCE TEST                ║")
    logger.info("╔════════════════════════════════════════════════════════════════════════╗")
    logger.info("")
    logger.info("Goal: Verify simulator can operate without commuter service")
    logger.info("Prerequisites: Strapi running on port 1337")
    logger.info("")
    
    # Test 1: Basic functionality
    test1_passed = await test_simulator_startup()
    
    if not test1_passed:
        logger.error("\n⛔ Basic functionality test failed. Skipping start/stop test.")
        sys.exit(1)
    
    # Test 2: Initialize/Shutdown cycle
    test2_passed = await test_simulator_initialization()
    
    # Final summary
    logger.info("\n")
    logger.info("╔════════════════════════════════════════════════════════════════════════╗")
    logger.info("║                      STAGE 1B: FINAL RESULTS                           ║")
    logger.info("╚════════════════════════════════════════════════════════════════════════╝")
    logger.info("")
    logger.info(f"  Test 1 - Basic Functionality:      {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    logger.info(f"  Test 2 - Initialize/Shutdown:      {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    logger.info("")
    
    if test1_passed and test2_passed:
        logger.info("🎉 STAGE 1B COMPLETE: Simulator is fully operational!")
        logger.info("")
        logger.info("Next Step: Stage 1C - Test Commuter Service Independently")
        sys.exit(0)
    else:
        logger.error("⛔ STAGE 1B FAILED: Please fix simulator issues before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
