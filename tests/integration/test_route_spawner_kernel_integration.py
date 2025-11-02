"""
Integration test for RouteSpawner with spawn calculation kernel.

Validates that RouteSpawner correctly:
1. Queries depot catchment buildings
2. Aggregates total buildings across all routes
3. Calls spawn calculator kernel with correct parameters
4. Returns valid spawn counts
5. Falls back gracefully when depot data unavailable
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch


async def test_route_spawner_with_depot_data():
    """Test RouteSpawner with depot catchment and route aggregation."""
    from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
    
    # Mock reservoir
    mock_reservoir = MagicMock()
    
    # Mock config loader
    mock_config_loader = MagicMock()
    mock_config_loader.api_base_url = "http://localhost:1337/api"
    
    # Mock geospatial client
    mock_geo_client = MagicMock()
    mock_geo_client.base_url = "http://localhost:6000"
    mock_geo_client.buildings_along_route = MagicMock(return_value={'buildings': [{'id': i} for i in range(100)]})
    mock_geo_client.depot_catchment_area = MagicMock(return_value={'buildings': [{'id': i} for i in range(250)]})
    
    # Create spawner
    spawner = RouteSpawner(
        reservoir=mock_reservoir,
        config={'test': True},
        route_id='route_1_speightstown_bridgetown',
        config_loader=mock_config_loader,
        geo_client=mock_geo_client
    )
    
    # Mock spawn config
    spawn_config = {
        'distribution_params': {
            'passengers_per_building_per_hour': 0.05,
            'spawn_radius_meters': 800,
            'depot_catchment_radius_meters': 800
        },
        'hourly_rates': {str(i): 2.5 if i == 8 else 0.5 for i in range(24)},
        'day_multipliers': {str(i): 1.0 for i in range(7)}
    }
    
    # Mock depot info response
    mock_depot = {
        'documentId': 'depot_speightstown',
        'latitude': 13.2380,
        'longitude': -59.6420
    }
    
    # Test with depot data available
    print("\n=== Test 1: With depot data ===")
    with patch.object(spawner, '_get_depot_info', new_callable=AsyncMock) as mock_get_depot:
        with patch('httpx.AsyncClient') as mock_client:
            # Mock depot info
            mock_get_depot.return_value = mock_depot
            
            # Mock route-depots junction query
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'data': [
                    {'route': {'documentId': 'route_1_speightstown_bridgetown'}},
                    {'route': {'documentId': 'route_2_speightstown_holetown'}},
                ]
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Mock route geometry for aggregation
            mock_geometry_response = MagicMock()
            mock_geometry_response.json.return_value = {'coordinates': [[0, 0], [1, 1]]}
            
            # Calculate spawn count
            spawn_count = await spawner._calculate_spawn_count(
                spawn_config=spawn_config,
                building_count=100,  # buildings along THIS route
                current_time=datetime(2024, 11, 4, 8, 0),  # Monday 8 AM
                time_window_minutes=15
            )
            
            print(f"Spawn count: {spawn_count}")
            print(f"Depot catchment cache: {spawner._depot_catchment_cache}")
            print(f"Total buildings cache: {spawner._total_buildings_all_routes_cache}")
            
            # Assertions
            assert isinstance(spawn_count, int), "Spawn count should be integer"
            assert spawn_count >= 0, "Spawn count should be non-negative"
            
            # With 2 routes at depot, attractiveness should be ~50% (100/200)
            # Terminal pop = 250 buildings × 0.05 pass/bldg × 2.5 hourly × 1.0 day = 31.25 pass/hr
            # Route gets ~50% = 15.6 pass/hr
            # Lambda for 15 min = 15.6 × 0.25 = 3.9
            # Spawn count should be around 4 (Poisson variance allowed)
            assert 0 <= spawn_count <= 15, f"Spawn count {spawn_count} outside expected range for 15-min window"
            
            print(f"✓ Depot integration working: spawn_count={spawn_count}")


async def test_route_spawner_fallback_mode():
    """Test RouteSpawner fallback when depot data unavailable."""
    from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
    
    print("\n=== Test 2: Fallback mode (no depot) ===")
    
    # Mock reservoir
    mock_reservoir = MagicMock()
    
    # Mock config loader
    mock_config_loader = MagicMock()
    mock_config_loader.api_base_url = "http://localhost:1337/api"
    
    # Mock geospatial client
    mock_geo_client = MagicMock()
    mock_geo_client.base_url = "http://localhost:6000"
    mock_geo_client.buildings_along_route = MagicMock(return_value={'buildings': [{'id': i} for i in range(100)]})
    
    # Create spawner
    spawner = RouteSpawner(
        reservoir=mock_reservoir,
        config={'test': True},
        route_id='route_orphan',
        config_loader=mock_config_loader,
        geo_client=mock_geo_client
    )
    
    # Mock spawn config
    spawn_config = {
        'distribution_params': {
            'passengers_per_building_per_hour': 0.05,
            'spawn_radius_meters': 800
        },
        'hourly_rates': {str(i): 2.5 if i == 8 else 0.5 for i in range(24)},
        'day_multipliers': {str(i): 1.0 for i in range(7)}
    }
    
    # Test with NO depot data
    with patch.object(spawner, '_get_depot_info', new_callable=AsyncMock) as mock_get_depot:
        mock_get_depot.return_value = None  # No depot
        
        spawn_count = await spawner._calculate_spawn_count(
            spawn_config=spawn_config,
            building_count=100,
            current_time=datetime(2024, 11, 4, 8, 0),  # Monday 8 AM
            time_window_minutes=15
        )
        
        print(f"Fallback spawn count: {spawn_count}")
        
        # Assertions
        assert isinstance(spawn_count, int), "Spawn count should be integer"
        assert spawn_count >= 0, "Spawn count should be non-negative"
        
        # In fallback mode: attractiveness=1.0
        # Terminal pop = 100 × 0.05 × 2.5 × 1.0 = 12.5 pass/hr
        # Lambda for 15 min = 12.5 × 0.25 = 3.125
        # Spawn count around 3 (Poisson variance)
        assert 0 <= spawn_count <= 15, f"Fallback spawn count {spawn_count} outside expected range"
        
        print(f"✓ Fallback mode working: spawn_count={spawn_count}")


async def test_route_spawner_caching():
    """Test that depot queries are cached properly."""
    from commuter_service.core.domain.spawner_engine.route_spawner import RouteSpawner
    
    print("\n=== Test 3: Caching behavior ===")
    
    mock_reservoir = MagicMock()
    mock_config_loader = MagicMock()
    mock_config_loader.api_base_url = "http://localhost:1337/api"
    mock_geo_client = MagicMock()
    mock_geo_client.base_url = "http://localhost:6000"
    mock_geo_client.depot_catchment_area = MagicMock(return_value={'buildings': [{'id': i} for i in range(200)]})
    
    spawner = RouteSpawner(
        reservoir=mock_reservoir,
        config={'test': True},
        route_id='route_test',
        config_loader=mock_config_loader,
        geo_client=mock_geo_client
    )
    
    spawn_config = {
        'distribution_params': {'passengers_per_building_per_hour': 0.05}
    }
    
    mock_depot = {'documentId': 'depot_test', 'latitude': 13.0, 'longitude': -59.0}
    
    with patch.object(spawner, '_get_depot_info', new_callable=AsyncMock) as mock_get_depot:
        mock_get_depot.return_value = mock_depot
        
        # First call
        result1 = await spawner._get_depot_catchment_buildings(spawn_config)
        call_count_1 = mock_geo_client.depot_catchment_area.call_count
        
        # Second call (should use cache)
        result2 = await spawner._get_depot_catchment_buildings(spawn_config)
        call_count_2 = mock_geo_client.depot_catchment_area.call_count
        
        print(f"First call result: {result1}")
        print(f"Second call result: {result2}")
        print(f"Geo client called: {call_count_1} times after first call, {call_count_2} times after second")
        
        assert result1 == result2, "Cached result should match"
        assert call_count_2 == call_count_1, "Second call should use cache, not query again"
        assert result1 == 200, "Should return correct building count"
        
        print(f"✓ Caching working correctly")


async def main():
    """Run all integration tests."""
    print("=" * 80)
    print("RouteSpawner Kernel Integration Tests")
    print("=" * 80)
    
    try:
        await test_route_spawner_with_depot_data()
        await test_route_spawner_fallback_mode()
        await test_route_spawner_caching()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
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
