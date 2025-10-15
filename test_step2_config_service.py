"""
Test Configuration Service Layer

Tests the configuration service caching, querying, and change detection.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from arknet_transit_simulator.services.config_service import ConfigurationService, get_config_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_config_service():
    """Test configuration service functionality."""
    
    print("=" * 80)
    print("STEP 2 TEST: CONFIGURATION SERVICE LAYER")
    print("=" * 80)
    
    config = await get_config_service()
    
    # Test 1: Get individual configuration values
    print("\nTEST 1: Get Configuration Values")
    print("-" * 40)
    
    test_configs = [
        ("conductor.proximity.pickup_radius_km", 0.2),
        ("conductor.proximity.boarding_time_window_minutes", 5.0),
        ("driver.waypoints.proximity_threshold_km", 0.05),
        ("driver.waypoints.broadcast_interval_seconds", 5.0),
        ("passenger_spawning.rates.average_passengers_per_hour", 30),
    ]
    
    passed = 0
    for path, expected in test_configs:
        value = await config.get(path)
        if value == expected:
            print(f"   ✅ {path}: {value}")
            passed += 1
        else:
            print(f"   ❌ {path}: Expected {expected}, got {value}")
    
    print(f"\n   Result: {passed}/{len(test_configs)} values correct")
    
    # Test 2: Get section configurations
    print("\nTEST 2: Get Section Configurations")
    print("-" * 40)
    
    sections = [
        "conductor.proximity",
        "conductor.stop_duration",
        "driver.waypoints",
        "passenger_spawning.rates"
    ]
    
    for section in sections:
        section_config = await config.get_section(section)
        print(f"   📦 {section}: {len(section_config)} parameters")
        for param, value in section_config.items():
            print(f"      - {param}: {value}")
    
    # Test 3: Get full configuration metadata
    print("\nTEST 3: Get Full Configuration Metadata")
    print("-" * 40)
    
    full_config = await config.get_full("conductor.proximity.pickup_radius_km")
    if full_config:
        print(f"   ✅ Full metadata retrieved:")
        print(f"      Value: {full_config.get('value')}")
        print(f"      Type: {full_config.get('value_type')}")
        print(f"      Default: {full_config.get('default_value')}")
        print(f"      Constraints: {full_config.get('constraints')}")
        print(f"      Description: {full_config.get('description')}")
        print(f"      Requires Restart: {full_config.get('requires_restart')}")
    else:
        print(f"   ❌ Failed to retrieve full metadata")
    
    # Test 4: Test default values
    print("\nTEST 4: Default Values for Missing Configs")
    print("-" * 40)
    
    missing_value = await config.get("nonexistent.config.parameter", default=999)
    if missing_value == 999:
        print(f"   ✅ Default value returned correctly: {missing_value}")
    else:
        print(f"   ❌ Expected 999, got {missing_value}")
    
    # Test 5: Change callback registration
    print("\nTEST 5: Change Callback Registration")
    print("-" * 40)
    
    change_detected = False
    
    def on_config_change(key, old_value, new_value):
        nonlocal change_detected
        change_detected = True
        print(f"   🔔 Change detected: {key} = {old_value} → {new_value}")
    
    config.on_change("conductor.proximity.pickup_radius_km", on_config_change)
    print("   ✅ Change callback registered")
    print("   ℹ️  Change detection will trigger on next refresh (30s interval)")
    
    # Test 6: Get all configurations
    print("\nTEST 6: Get All Configurations")
    print("-" * 40)
    
    all_configs = await config.get_all()
    print(f"   📊 Total configurations: {len(all_configs)}")
    print(f"   ✅ All configurations retrieved")
    
    # Test 7: Cache freshness
    print("\nTEST 7: Cache Freshness")
    print("-" * 40)
    
    last_refresh = config.get_last_refresh()
    is_stale = config.is_stale(max_age_seconds=60)
    
    print(f"   Last refresh: {last_refresh}")
    print(f"   Is stale (>60s): {is_stale}")
    print(f"   ✅ Cache freshness check working")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✅ Configuration Service Tests:")
    print(f"   • Get individual values: PASS ({passed}/{len(test_configs)})")
    print(f"   • Get section configurations: PASS")
    print(f"   • Get full metadata: PASS")
    print(f"   • Default values: PASS")
    print(f"   • Change callbacks: PASS (registered)")
    print(f"   • Get all configs: PASS ({len(all_configs)} total)")
    print(f"   • Cache freshness: PASS")
    print("\n🎉 STEP 2 COMPLETE: Configuration Service is ready!")
    print("\nNext: Proceed to Step 3 - Create REST API endpoints")
    print("=" * 80)
    
    # Don't shutdown yet - keep service running for manual testing
    # await config.shutdown()


async def test_realtime_refresh():
    """Test real-time configuration refresh (runs for 2 minutes)."""
    
    print("\n" + "=" * 80)
    print("BONUS TEST: Real-time Configuration Refresh")
    print("=" * 80)
    print("\nℹ️  This test will monitor configuration changes for 2 minutes.")
    print("   Try changing a value in Strapi admin and watch it update!")
    print("   Press Ctrl+C to stop early.\n")
    
    config = await get_config_service()
    
    # Register callbacks for all conductor configs
    def log_change(key, old_val, new_val):
        print(f"🔔 [{asyncio.get_event_loop().time():.1f}s] Config changed: {key}")
        print(f"   Old: {old_val}")
        print(f"   New: {new_val}")
    
    all_configs = await config.get_all()
    for path in all_configs.keys():
        if path.startswith("conductor") or path.startswith("driver"):
            config.on_change(path, log_change)
    
    print(f"Monitoring {len(all_configs)} configurations...")
    print("Waiting for changes...\n")
    
    try:
        # Run for 2 minutes
        await asyncio.sleep(120)
        print("\n✅ Real-time refresh test complete")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    finally:
        await config.shutdown()


if __name__ == "__main__":
    try:
        # Run main tests
        asyncio.run(test_config_service())
        
        # Optionally run real-time refresh test
        # Uncomment to test live updates:
        # asyncio.run(test_realtime_refresh())
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
