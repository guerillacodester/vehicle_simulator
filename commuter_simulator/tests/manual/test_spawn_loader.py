"""
Quick manual test of SpawnConfigLoader
---------------------------------------
Verifies the loader works correctly with live API.

Run with:
    python commuter_simulator/tests/manual/test_spawn_loader.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.spawn.config_loader import SpawnConfigLoader


async def test_spawn_config_loader():
    """Test the SpawnConfigLoader with live Strapi API"""
    
    print("=" * 70)
    print("SpawnConfigLoader Manual Test")
    print("=" * 70)
    
    # Create loader
    loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    
    # Load Barbados config
    print("\n[1] Loading Barbados config...")
    config = await loader.get_config_by_country("Barbados")
    
    if not config:
        print("❌ FAILED: Could not load config")
        return False
    
    print(f"✅ Loaded: {config['name']}")
    print(f"   Description: {config['description']}")
    print(f"   Active: {config['is_active']}")
    print(f"   Buildings: {len(config.get('building_weights', []))}")
    print(f"   POIs: {len(config.get('poi_weights', []))}")
    print(f"   Landuse: {len(config.get('landuse_weights', []))}")
    print(f"   Hourly rates: {len(config.get('hourly_spawn_rates', []))}")
    print(f"   Day multipliers: {len(config.get('day_multipliers', []))}")
    
    # Test caching
    print("\n[2] Testing cache (second load should be instant)...")
    import time
    start = time.time()
    config2 = await loader.get_config_by_country("Barbados")
    elapsed = (time.time() - start) * 1000
    print(f"✅ Cache hit in {elapsed:.2f}ms (should be <1ms)")
    
    # Test hourly rates
    print("\n[3] Testing hourly rates...")
    morning_peak = loader.get_hourly_rate(config, 8)  # 8 AM
    evening_peak = loader.get_hourly_rate(config, 17)  # 5 PM
    late_night = loader.get_hourly_rate(config, 1)  # 1 AM
    
    print(f"✅ Morning peak (8am): {morning_peak}")
    print(f"✅ Evening peak (5pm): {evening_peak}")
    print(f"✅ Late night (1am): {late_night}")
    
    assert morning_peak > evening_peak > late_night, "Peak hours should be ordered correctly"
    
    # Test building weights
    print("\n[4] Testing building weights...")
    residential = loader.get_building_weight(config, "residential", apply_peak_multiplier=True)
    commercial = loader.get_building_weight(config, "commercial", apply_peak_multiplier=True)
    school = loader.get_building_weight(config, "school", apply_peak_multiplier=True)
    
    print(f"✅ Residential (with peak): {residential}")
    print(f"✅ Commercial (with peak): {commercial}")
    print(f"✅ School (with peak): {school}")
    
    # Test POI weights
    print("\n[5] Testing POI weights...")
    bus_station = loader.get_poi_weight(config, "bus_station", apply_peak_multiplier=True)
    marketplace = loader.get_poi_weight(config, "marketplace", apply_peak_multiplier=True)
    
    print(f"✅ Bus station: {bus_station}")
    print(f"✅ Marketplace: {marketplace}")
    
    # Test day multipliers
    print("\n[6] Testing day multipliers...")
    monday = loader.get_day_multiplier(config, "monday")
    saturday = loader.get_day_multiplier(config, "saturday")
    sunday = loader.get_day_multiplier(config, "sunday")
    
    print(f"✅ Monday: {monday}")
    print(f"✅ Saturday: {saturday}")
    print(f"✅ Sunday: {sunday}")
    
    assert monday == 1.0, "Weekday should be 1.0"
    assert sunday < saturday < monday, "Weekend should be reduced"
    
    # Test distribution params
    print("\n[7] Testing distribution parameters...")
    dist_params = loader.get_distribution_params(config)
    
    print(f"✅ Poisson lambda: {dist_params['poisson_lambda']}")
    print(f"✅ Max spawns/cycle: {dist_params['max_spawns_per_cycle']}")
    print(f"✅ Spawn radius: {dist_params['spawn_radius_meters']}m")
    print(f"✅ Min interval: {dist_params['min_spawn_interval_seconds']}s")
    
    # Test full spawn probability calculation
    print("\n[8] Testing full spawn probability calculation...")
    
    # Monday morning rush hour at residential building
    prob_mon_8am_residential = loader.calculate_spawn_probability(
        config,
        feature_weight=residential,
        current_hour=8,
        day_of_week="monday"
    )
    
    # Sunday morning at school (should be very low)
    prob_sun_8am_school = loader.calculate_spawn_probability(
        config,
        feature_weight=school,
        current_hour=8,
        day_of_week="sunday"
    )
    
    print(f"✅ Residential, Monday 8am: {prob_mon_8am_residential}")
    print(f"✅ School, Sunday 8am: {prob_sun_8am_school}")
    
    assert prob_mon_8am_residential > prob_sun_8am_school, "Weekday should have higher spawn probability"
    
    # Test cache clearing
    print("\n[9] Testing cache clearing...")
    loader.clear_cache("Barbados")
    print("✅ Cache cleared for Barbados")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_spawn_config_loader())
    sys.exit(0 if success else 1)
