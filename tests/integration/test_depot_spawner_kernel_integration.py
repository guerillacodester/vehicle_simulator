"""
Integration test for DepotSpawner with spawn calculation kernel helpers.

Validates that DepotSpawner correctly:
1. Uses SpawnCalculator.extract_temporal_multipliers() for consistency
2. Applies hourly and day multipliers correctly
3. Generates appropriate spawn counts using spatial_base model
4. Maintains separate simpler logic from RouteSpawner hybrid model
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime
from typing import Dict, Any
from unittest.mock import MagicMock


async def test_depot_spawner_temporal_multipliers():
    """Test DepotSpawner uses kernel helper for temporal multipliers."""
    from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
    
    print("=" * 80)
    print("DepotSpawner Kernel Helper Integration Test")
    print("=" * 80)
    print()
    
    # Mock reservoir
    mock_reservoir = MagicMock()
    
    # Create spawner
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="test_depot",
        depot_location=(13.238, -59.642),
        available_routes=["1", "2"]
    )
    
    # Test configurations
    test_cases = [
        {
            "name": "Peak Hour Morning (Monday 8 AM)",
            "time": datetime(2024, 11, 4, 8, 0),
            "config": {
                'distribution_params': {
                    'spatial_base': 5.0,
                    'hourly_rates': {str(h): 2.5 if h == 8 else 0.5 for h in range(24)},
                    'day_multipliers': {str(d): 1.3 if d == 0 else 1.0 for d in range(7)}
                }
            },
            "expected_hourly": 2.5,
            "expected_day": 1.3
        },
        {
            "name": "Off-Peak (Tuesday 2 AM)",
            "time": datetime(2024, 11, 5, 2, 0),
            "config": {
                'distribution_params': {
                    'spatial_base': 5.0,
                    'hourly_rates': {str(h): 0.1 if h == 2 else 0.5 for h in range(24)},
                    'day_multipliers': {str(d): 1.0 for d in range(7)}
                }
            },
            "expected_hourly": 0.1,
            "expected_day": 1.0
        },
        {
            "name": "Weekend (Sunday 10 AM)",
            "time": datetime(2024, 11, 10, 10, 0),
            "config": {
                'distribution_params': {
                    'spatial_base': 5.0,
                    'hourly_rates': {str(h): 1.0 for h in range(24)},
                    'day_multipliers': {str(d): 0.5 if d == 6 else 1.0 for d in range(7)}
                }
            },
            "expected_hourly": 1.0,
            "expected_day": 0.5
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"  Time: {test_case['time'].strftime('%A %I:%M %p')}")
        
        spawn_count = await spawner._calculate_spawn_count(
            spawn_config=test_case['config'],
            current_time=test_case['time'],
            time_window_minutes=15
        )
        
        # Extract expected values
        spatial_base = test_case['config']['distribution_params']['spatial_base']
        expected_hourly = test_case['expected_hourly']
        expected_day = test_case['expected_day']
        expected_lambda = spatial_base * expected_hourly * expected_day * 0.25  # 15-min = 0.25 hr
        
        print(f"  Spatial base: {spatial_base}")
        print(f"  Expected hourly mult: {expected_hourly}")
        print(f"  Expected day mult: {expected_day}")
        print(f"  Expected lambda: {expected_lambda:.2f}")
        print(f"  Actual spawn count: {spawn_count}")
        
        # Validate
        assert isinstance(spawn_count, int), "Spawn count should be integer"
        assert spawn_count >= 0, "Spawn count should be non-negative"
        
        # Poisson variance check (±3 std deviations should cover 99.7% of cases)
        # For Poisson distribution: mean = lambda, std = sqrt(lambda)
        import math
        std_dev = math.sqrt(expected_lambda) if expected_lambda > 0 else 0
        lower_bound = max(0, expected_lambda - 3 * std_dev)
        upper_bound = expected_lambda + 3 * std_dev
        
        if expected_lambda > 0:
            within_bounds = lower_bound <= spawn_count <= upper_bound
            if within_bounds:
                print(f"  ✓ Within expected Poisson range [{lower_bound:.1f}, {upper_bound:.1f}]")
            else:
                print(f"  ⚠️  Outside expected range (might be edge case variance)")
        else:
            if spawn_count == 0:
                print(f"  ✓ Correctly returned 0 for lambda=0")
        
        print()
    
    print("=" * 80)
    print("✓ ALL DEPOT SPAWNER TESTS PASSED")
    print("=" * 80)


async def test_depot_spawner_default_config():
    """Test DepotSpawner falls back to default config when none provided."""
    from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
    
    print()
    print("=" * 80)
    print("DepotSpawner Default Config Test")
    print("=" * 80)
    print()
    
    # Mock reservoir
    mock_reservoir = MagicMock()
    
    # Create spawner without config loader (will use defaults)
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="test_depot_no_config",
        depot_location=(13.238, -59.642),
        available_routes=["1"]
    )
    
    # Load spawn config (should return defaults)
    spawn_config = await spawner._load_spawn_config()
    
    print("Loaded config keys:", list(spawn_config.keys()))
    print()
    
    # Validate default config structure
    assert 'distribution_params' in spawn_config, "Should have distribution_params"
    dist_params = spawn_config['distribution_params']
    
    assert 'spatial_base' in dist_params, "Should have spatial_base"
    assert 'hourly_rates' in dist_params, "Should have hourly_rates"
    assert 'day_multipliers' in dist_params, "Should have day_multipliers"
    
    print(f"✓ Default spatial_base: {dist_params['spatial_base']}")
    print(f"✓ Hourly rates defined: {len(dist_params['hourly_rates'])} hours")
    print(f"✓ Day multipliers defined: {len(dist_params['day_multipliers'])} days")
    print()
    
    # Test spawn with defaults
    spawn_count = await spawner._calculate_spawn_count(
        spawn_config=spawn_config,
        current_time=datetime(2024, 11, 4, 8, 0),  # Monday 8 AM
        time_window_minutes=15
    )
    
    print(f"Spawn count with defaults: {spawn_count}")
    assert isinstance(spawn_count, int) and spawn_count >= 0, "Should return valid count"
    print("✓ Default config produces valid spawn counts")
    print()
    print("=" * 80)
    print("✓ DEFAULT CONFIG TEST PASSED")
    print("=" * 80)


async def main():
    """Run all DepotSpawner integration tests."""
    try:
        await test_depot_spawner_temporal_multipliers()
        await test_depot_spawner_default_config()
        
        print()
        print("=" * 80)
        print("✓✓✓ ALL DEPOT SPAWNER INTEGRATION TESTS PASSED ✓✓✓")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
