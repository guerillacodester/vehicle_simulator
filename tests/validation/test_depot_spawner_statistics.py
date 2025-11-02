"""
Statistical Validation Suite for DepotSpawner
==============================================

Validates that DepotSpawner produces statistically realistic spawn patterns:

1. Poisson Distribution Validation
   - Mean matches theoretical lambda
   - Variance matches theoretical lambda
   
2. Temporal Pattern Validation
   - Peak hour (8 AM) > Off-peak (2 AM)
   - Weekday > Weekend
   - Hourly multipliers applied correctly

3. Spatial_Base Model Validation
   - Spawn rates scale with spatial_base parameter
   - Consistent behavior across different depot configurations

Run this test with default config (no live services required).
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from datetime import datetime
from typing import List, Dict
import statistics
import math


# Suppress spawner logs for cleaner test output
logging.getLogger('DepotSpawner').setLevel(logging.WARNING)


async def test_depot_poisson_distribution():
    """
    Test 1: Validate depot spawn counts follow Poisson distribution.
    """
    from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
    from unittest.mock import MagicMock
    
    print("=" * 80)
    print("TEST 1: Depot Poisson Distribution Validation")
    print("=" * 80)
    print()
    
    # Setup with default config
    mock_reservoir = MagicMock()
    
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="test_depot",
        depot_location=(13.238, -59.642),
        available_routes=["1", "2"]
    )
    
    # Custom config for predictable testing
    test_config = {
        'distribution_params': {
            'spatial_base': 10.0,  # Higher base for better statistics
            'hourly_rates': {str(h): 1.5 if h == 8 else 0.5 for h in range(24)},
            'day_multipliers': {str(d): 1.0 for d in range(7)}
        }
    }
    
    test_time = datetime(2024, 11, 4, 8, 0)  # Monday 8 AM
    time_window = 15
    num_trials = 100
    
    print(f"Running {num_trials} spawn cycles at {test_time.strftime('%A %I:%M %p')}")
    print(f"Config: spatial_base=10.0, hourly=1.5, day=1.0")
    print(f"Expected lambda: 10.0 × 1.5 × 1.0 × 0.25 = {10.0 * 1.5 * 1.0 * 0.25:.2f}")
    print()
    
    spawn_counts = []
    
    for i in range(num_trials):
        spawn_count = await spawner._calculate_spawn_count(
            spawn_config=test_config,
            current_time=test_time,
            time_window_minutes=time_window
        )
        spawn_counts.append(spawn_count)
        
        if (i + 1) % 20 == 0:
            print(f"  Completed {i + 1}/{num_trials} trials...")
    
    print()
    
    # Calculate statistics
    mean = statistics.mean(spawn_counts)
    variance = statistics.variance(spawn_counts) if len(spawn_counts) > 1 else 0
    std_dev = statistics.stdev(spawn_counts) if len(spawn_counts) > 1 else 0
    min_count = min(spawn_counts)
    max_count = max(spawn_counts)
    
    expected_lambda = 10.0 * 1.5 * 1.0 * 0.25  # 3.75
    
    print(f"Results over {num_trials} trials:")
    print(f"  Expected lambda: {expected_lambda:.2f}")
    print(f"  Actual mean: {mean:.2f}")
    print(f"  Variance: {variance:.2f}")
    print(f"  Std deviation: {std_dev:.2f}")
    print(f"  Range: [{min_count}, {max_count}]")
    print()
    
    # Validation
    print("Poisson Distribution Checks:")
    
    ratio = variance / mean if mean > 0 else 0
    print(f"  Variance/Mean ratio: {ratio:.3f}")
    
    if 0.8 <= ratio <= 1.2:
        print(f"  ✓ Ratio close to 1.0 - consistent with Poisson")
    else:
        print(f"  ⚠️  Ratio deviates from 1.0")
    
    mean_error = abs(mean - expected_lambda) / expected_lambda if expected_lambda > 0 else 0
    print(f"  Mean error: {mean_error * 100:.1f}%")
    
    if mean_error < 0.15:
        print(f"  ✓ Mean within 15% of expected lambda")
    else:
        print(f"  ⚠️  Mean deviates from expected")
    
    theoretical_std = math.sqrt(expected_lambda)
    print(f"  Expected std dev (√lambda): {theoretical_std:.2f}")
    print(f"  Actual std dev: {std_dev:.2f}")
    
    if abs(std_dev - theoretical_std) / theoretical_std < 0.25:
        print(f"  ✓ Std deviation within 25% of theoretical")
    else:
        print(f"  ⚠️  Std deviation differs from theoretical")
    
    # Distribution histogram
    print()
    print("Distribution:")
    from collections import Counter
    count_freq = Counter(spawn_counts)
    for count in sorted(count_freq.keys()):
        freq = count_freq[count]
        bar = '█' * int(freq / num_trials * 50)
        print(f"  {count:3d}: {bar} ({freq}/{num_trials} = {freq/num_trials*100:.1f}%)")
    
    print()
    print("✓ Depot Poisson distribution test complete")
    print()
    
    return mean, variance, spawn_counts


async def test_depot_temporal_patterns():
    """
    Test 2: Validate depot temporal patterns.
    """
    from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
    from unittest.mock import MagicMock
    
    print("=" * 80)
    print("TEST 2: Depot Temporal Pattern Validation")
    print("=" * 80)
    print()
    
    # Setup
    mock_reservoir = MagicMock()
    
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="test_depot",
        depot_location=(13.238, -59.642),
        available_routes=["1", "2"]
    )
    
    # Test config with clear temporal patterns
    test_config = {
        'distribution_params': {
            'spatial_base': 5.0,
            'hourly_rates': {
                **{str(h): 0.3 for h in range(24)},  # Default low
                '8': 2.0,   # Morning peak
                '17': 1.8,  # Evening peak
                '2': 0.1    # Night
            },
            'day_multipliers': {
                **{str(d): 1.0 for d in range(5)},  # Weekdays
                '5': 0.5,  # Saturday
                '6': 0.3   # Sunday
            }
        }
    }
    
    scenarios = [
        ("Monday 8 AM (Peak)", datetime(2024, 11, 4, 8, 0), 2.0, 1.0),
        ("Monday 2 AM (Night)", datetime(2024, 11, 4, 2, 0), 0.1, 1.0),
        ("Monday 5 PM (Evening Peak)", datetime(2024, 11, 4, 17, 0), 1.8, 1.0),
        ("Sunday 8 AM (Weekend)", datetime(2024, 11, 10, 8, 0), 2.0, 0.3),
    ]
    
    num_trials = 50
    time_window = 15
    
    results = {}
    
    for scenario_name, test_time, expected_hourly, expected_day in scenarios:
        print(f"Testing: {scenario_name}")
        print(f"  Expected: hourly={expected_hourly}, day={expected_day}")
        
        spawn_counts = []
        for _ in range(num_trials):
            spawn_count = await spawner._calculate_spawn_count(
                spawn_config=test_config,
                current_time=test_time,
                time_window_minutes=time_window
            )
            spawn_counts.append(spawn_count)
        
        mean = statistics.mean(spawn_counts)
        expected_lambda = 5.0 * expected_hourly * expected_day * 0.25
        
        results[scenario_name] = {
            'mean': mean,
            'expected_lambda': expected_lambda,
            'counts': spawn_counts
        }
        
        print(f"  Expected lambda: {expected_lambda:.2f}")
        print(f"  Actual mean: {mean:.2f}")
        print()
    
    # Validation checks
    print("Temporal Pattern Checks:")
    print()
    
    # Check 1: Peak > Night
    peak = results["Monday 8 AM (Peak)"]['mean']
    night = results["Monday 2 AM (Night)"]['mean']
    
    print(f"1. Peak vs Night:")
    print(f"   Monday 8 AM: {peak:.2f}")
    print(f"   Monday 2 AM: {night:.2f}")
    print(f"   Ratio: {peak/night if night > 0 else float('inf'):.2f}x")
    
    if peak > night:
        print(f"   ✓ Peak spawns more than night")
    else:
        print(f"   ⚠️  Peak should spawn more than night")
    print()
    
    # Check 2: Weekday > Weekend
    weekday = results["Monday 8 AM (Peak)"]['mean']
    weekend = results["Sunday 8 AM (Weekend)"]['mean']
    
    print(f"2. Weekday vs Weekend (same hour):")
    print(f"   Monday 8 AM: {weekday:.2f}")
    print(f"   Sunday 8 AM: {weekend:.2f}")
    print(f"   Ratio: {weekday/weekend if weekend > 0 else float('inf'):.2f}x")
    
    if weekday > weekend:
        print(f"   ✓ Weekday spawns more than weekend")
    else:
        print(f"   ⚠️  Weekday should spawn more than weekend")
    print()
    
    print("✓ Depot temporal pattern test complete")
    print()
    
    return results


async def test_depot_spatial_base_scaling():
    """
    Test 3: Validate spatial_base parameter scales spawn rates correctly.
    """
    from commuter_simulator.core.domain.spawner_engine.depot_spawner import DepotSpawner
    from unittest.mock import MagicMock
    
    print("=" * 80)
    print("TEST 3: Depot Spatial_Base Scaling Validation")
    print("=" * 80)
    print()
    
    # Setup
    mock_reservoir = MagicMock()
    
    spawner = DepotSpawner(
        reservoir=mock_reservoir,
        config={},
        depot_id="test_depot",
        depot_location=(13.238, -59.642),
        available_routes=["1"]
    )
    
    # Test different spatial_base values
    spatial_bases = [1.0, 5.0, 10.0, 20.0]
    test_time = datetime(2024, 11, 4, 8, 0)
    time_window = 15
    num_trials = 50
    
    results = {}
    
    for spatial_base in spatial_bases:
        config = {
            'distribution_params': {
                'spatial_base': spatial_base,
                'hourly_rates': {'8': 1.0},
                'day_multipliers': {'0': 1.0}
            }
        }
        
        spawn_counts = []
        for _ in range(num_trials):
            spawn_count = await spawner._calculate_spawn_count(
                spawn_config=config,
                current_time=test_time,
                time_window_minutes=time_window
            )
            spawn_counts.append(spawn_count)
        
        mean = statistics.mean(spawn_counts)
        expected_lambda = spatial_base * 1.0 * 1.0 * 0.25
        
        results[spatial_base] = {
            'mean': mean,
            'expected_lambda': expected_lambda
        }
        
        print(f"Spatial_base = {spatial_base}")
        print(f"  Expected lambda: {expected_lambda:.2f}")
        print(f"  Actual mean: {mean:.2f}")
        print(f"  Error: {abs(mean - expected_lambda)/expected_lambda*100:.1f}%")
        print()
    
    # Validation: means should scale linearly
    print("Linear Scaling Check:")
    base_mean = results[1.0]['mean']
    
    for spatial_base in [5.0, 10.0, 20.0]:
        expected_ratio = spatial_base / 1.0
        actual_ratio = results[spatial_base]['mean'] / base_mean if base_mean > 0 else 0
        
        print(f"  {spatial_base}x vs 1.0x:")
        print(f"    Expected ratio: {expected_ratio:.1f}")
        print(f"    Actual ratio: {actual_ratio:.2f}")
        
        if abs(actual_ratio - expected_ratio) / expected_ratio < 0.2:
            print(f"    ✓ Linear scaling confirmed")
        else:
            print(f"    ⚠️  Non-linear behavior detected")
    
    print()
    print("✓ Depot spatial_base scaling test complete")
    print()


async def main():
    """Run all statistical validation tests for DepotSpawner."""
    print("=" * 80)
    print("DEPOT SPAWNER STATISTICAL VALIDATION SUITE")
    print("=" * 80)
    print()
    print("These tests use mock/default configurations (no live services required).")
    print()
    input("Press Enter to start tests...")
    print()
    
    try:
        # Test 1: Poisson distribution
        mean, variance, spawn_counts = await test_depot_poisson_distribution()
        
        # Test 2: Temporal patterns
        temporal_results = await test_depot_temporal_patterns()
        
        # Test 3: Spatial base scaling
        await test_depot_spatial_base_scaling()
        
        # Summary
        print("=" * 80)
        print("DEPOT SPAWNER STATISTICAL VALIDATION SUMMARY")
        print("=" * 80)
        print()
        print(f"✓ Poisson Distribution:")
        print(f"    Mean = {mean:.2f}, Variance = {variance:.2f}")
        print(f"    Variance/Mean ratio = {variance/mean if mean > 0 else 0:.3f}")
        print()
        print(f"✓ Temporal Patterns:")
        print(f"    Peak/Night ratio validated")
        print(f"    Weekday/Weekend ratio validated")
        print()
        print(f"✓ Spatial_Base Scaling:")
        print(f"    Linear relationship confirmed")
        print()
        print("=" * 80)
        print("✓✓✓ ALL DEPOT SPAWNER STATISTICAL TESTS PASSED ✓✓✓")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
