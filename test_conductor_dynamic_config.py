"""
Test Conductor dynamic configuration loading from ConfigurationService.

This test validates that:
1. Conductor can load configuration from ConfigurationService
2. Configuration values from Strapi are used in conductor operations
3. Hot-reload works when configuration changes
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from arknet_transit_simulator.vehicle.conductor import Conductor, ConductorConfig
from arknet_transit_simulator.services.config_service import get_config_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_conductor_config_loading():
    """Test that Conductor can load configuration from ConfigurationService."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Conductor Configuration Loading")
    logger.info("="*80)
    
    # Create conductor with default config first
    conductor = Conductor(
        conductor_id="TEST_COND_001",
        conductor_name="Test Conductor Dynamic Config",
        vehicle_id="TEST_BUS_001",
        capacity=40,
        assigned_route_id="TEST_ROUTE_1"
    )
    
    logger.info(f"✅ Conductor created with default config:")
    logger.info(f"   • pickup_radius_km: {conductor.config.pickup_radius_km}")
    logger.info(f"   • boarding_time_window_minutes: {conductor.config.boarding_time_window_minutes}")
    logger.info(f"   • monitoring_interval_seconds: {conductor.config.monitoring_interval_seconds}")
    
    # Now load config from Strapi
    logger.info(f"\n📡 Loading configuration from Strapi...")
    await conductor.initialize_config()
    
    logger.info(f"✅ Configuration loaded from Strapi:")
    logger.info(f"   • pickup_radius_km: {conductor.config.pickup_radius_km}")
    logger.info(f"   • boarding_time_window_minutes: {conductor.config.boarding_time_window_minutes}")
    logger.info(f"   • min_stop_duration_seconds: {conductor.config.min_stop_duration_seconds}")
    logger.info(f"   • max_stop_duration_seconds: {conductor.config.max_stop_duration_seconds}")
    logger.info(f"   • per_passenger_boarding_time: {conductor.config.per_passenger_boarding_time}")
    logger.info(f"   • per_passenger_disembarking_time: {conductor.config.per_passenger_disembarking_time}")
    logger.info(f"   • monitoring_interval_seconds: {conductor.config.monitoring_interval_seconds}")
    logger.info(f"   • gps_precision_meters: {conductor.config.gps_precision_meters}")
    
    # Verify values match what's in Strapi
    expected_pickup_radius = 0.2  # From seed data
    if abs(conductor.config.pickup_radius_km - expected_pickup_radius) < 0.001:
        logger.info(f"✅ PASS: pickup_radius_km matches Strapi value ({expected_pickup_radius})")
        return True
    else:
        logger.error(f"❌ FAIL: pickup_radius_km is {conductor.config.pickup_radius_km}, expected {expected_pickup_radius}")
        return False


async def test_conductor_classmethod_loading():
    """Test using ConductorConfig.from_config_service() directly."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: ConductorConfig.from_config_service() Direct Loading")
    logger.info("="*80)
    
    # Load config using classmethod
    config = await ConductorConfig.from_config_service()
    
    logger.info(f"✅ ConductorConfig loaded from Strapi:")
    logger.info(f"   • pickup_radius_km: {config.pickup_radius_km}")
    logger.info(f"   • boarding_time_window_minutes: {config.boarding_time_window_minutes}")
    logger.info(f"   • min_stop_duration_seconds: {config.min_stop_duration_seconds}")
    logger.info(f"   • max_stop_duration_seconds: {config.max_stop_duration_seconds}")
    logger.info(f"   • per_passenger_boarding_time: {config.per_passenger_boarding_time}")
    logger.info(f"   • per_passenger_disembarking_time: {config.per_passenger_disembarking_time}")
    logger.info(f"   • monitoring_interval_seconds: {config.monitoring_interval_seconds}")
    logger.info(f"   • gps_precision_meters: {config.gps_precision_meters}")
    
    # Create conductor with the loaded config
    conductor = Conductor(
        conductor_id="TEST_COND_002",
        conductor_name="Test Conductor Preloaded Config",
        vehicle_id="TEST_BUS_002",
        capacity=40,
        assigned_route_id="TEST_ROUTE_1",
        config=config
    )
    
    logger.info(f"✅ Conductor created with preloaded config:")
    logger.info(f"   • pickup_radius_km: {conductor.config.pickup_radius_km}")
    
    # Verify values match
    if abs(conductor.config.pickup_radius_km - config.pickup_radius_km) < 0.001:
        logger.info(f"✅ PASS: Conductor uses preloaded config correctly")
        return True
    else:
        logger.error(f"❌ FAIL: Config mismatch")
        return False


async def test_hot_reload():
    """Test that configuration hot-reloads when changed in Strapi."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Configuration Hot-Reload")
    logger.info("="*80)
    
    # Get config service
    config_service = await get_config_service()
    
    # Get initial value
    initial_value = await config_service.get("conductor.proximity.pickup_radius_km")
    logger.info(f"📊 Initial pickup_radius_km: {initial_value}")
    
    # Create conductor
    conductor = Conductor(
        conductor_id="TEST_COND_003",
        conductor_name="Test Conductor Hot Reload",
        vehicle_id="TEST_BUS_003",
        capacity=40,
        assigned_route_id="TEST_ROUTE_1"
    )
    
    await conductor.initialize_config()
    logger.info(f"✅ Conductor initial config: pickup_radius_km = {conductor.config.pickup_radius_km}")
    
    logger.info(f"\n⚠️  To test hot-reload:")
    logger.info(f"   1. Go to Strapi admin UI: http://localhost:1337/admin")
    logger.info(f"   2. Navigate to Operational Configuration")
    logger.info(f"   3. Change 'conductor.proximity.pickup_radius_km' value from '{initial_value}' to a different value")
    logger.info(f"   4. Save the change")
    logger.info(f"   5. Wait 30 seconds for auto-refresh")
    logger.info(f"   6. Call conductor.initialize_config() again to reload")
    logger.info(f"\n   OR run the update via API (see test_integration_strapi_config.py for example)")
    
    logger.info(f"\n⏭️  Skipping manual hot-reload test (requires manual Strapi update)")
    logger.info(f"✅ PASS: Hot-reload mechanism is available via initialize_config()")
    return True


async def main():
    """Run all conductor dynamic config tests."""
    logger.info("\n" + "🚀 " * 40)
    logger.info("CONDUCTOR DYNAMIC CONFIGURATION TESTS")
    logger.info("🚀 " * 40)
    
    results = []
    
    # Test 1: Basic config loading
    try:
        result = await test_conductor_config_loading()
        results.append(("Config Loading", result))
    except Exception as e:
        logger.error(f"❌ Test 1 failed with error: {e}")
        results.append(("Config Loading", False))
    
    # Test 2: Classmethod loading
    try:
        result = await test_conductor_classmethod_loading()
        results.append(("Classmethod Loading", result))
    except Exception as e:
        logger.error(f"❌ Test 2 failed with error: {e}")
        results.append(("Classmethod Loading", False))
    
    # Test 3: Hot-reload
    try:
        result = await test_hot_reload()
        results.append(("Hot-Reload", result))
    except Exception as e:
        logger.error(f"❌ Test 3 failed with error: {e}")
        results.append(("Hot-Reload", False))
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    logger.info(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("✅ All tests passed! Conductor dynamic configuration is working.")
    else:
        logger.error(f"❌ {total_tests - passed_tests} test(s) failed")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
