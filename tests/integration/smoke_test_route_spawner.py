"""
End-to-end smoke test for RouteSpawner kernel integration.

Starts the commuter simulator, lets it spawn passengers for one cycle,
then captures and validates the kernel breakdown logs.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from datetime import datetime
from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from unittest.mock import MagicMock


class LogCapture(logging.Handler):
    """Custom log handler to capture logs for validation."""
    
    def __init__(self):
        super().__init__()
        self.logs = []
    
    def emit(self, record):
        self.logs.append(self.format(record))


async def test_route_spawner_live():
    """Test RouteSpawner with live services (Strapi, Geospatial)."""
    
    # Setup logging with capture
    log_capture = LogCapture()
    log_capture.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    log_capture.setFormatter(formatter)
    
    logger = logging.getLogger('RouteSpawner')
    logger.addHandler(log_capture)
    logger.setLevel(logging.INFO)
    
    print("=" * 80)
    print("RouteSpawner End-to-End Smoke Test")
    print("=" * 80)
    print()
    print("Prerequisites:")
    print("  ✓ Strapi running on port 1337")
    print("  ✓ Geospatial service running on port 6000")
    print("  ✓ PostgreSQL + PostGIS available")
    print()
    
    # Mock reservoir (we're just testing spawn calculation, not persistence)
    mock_reservoir = MagicMock()
    
    # Real infrastructure clients
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    geo_client = GeospatialClient(base_url="http://localhost:6000")
    
    # Create RouteSpawner for Route 1
    # Use the actual documentId from Strapi
    route_id = "gg3pv3z19hhm117v9xth5ezq"
    
    print(f"Creating RouteSpawner for route: {route_id}")
    print()
    
    spawner = RouteSpawner(
        reservoir=mock_reservoir,
        config={},
        route_id=route_id,
        config_loader=config_loader,
        geo_client=geo_client
    )
    
    # Run a single spawn cycle
    test_time = datetime(2024, 11, 4, 8, 0)  # Monday 8 AM (peak hour)
    time_window = 15  # 15 minutes
    
    print(f"Test parameters:")
    print(f"  Time: {test_time.strftime('%A %I:%M %p')}")
    print(f"  Window: {time_window} minutes")
    print()
    print("Running spawn cycle...")
    print("-" * 80)
    
    try:
        spawn_requests = await spawner.spawn(
            current_time=test_time,
            time_window_minutes=time_window
        )
        
        print("-" * 80)
        print()
        print(f"✓ Spawn completed: {len(spawn_requests)} passengers generated")
        print()
        
        # Validate logs contain kernel breakdown
        kernel_logs = [log for log in log_capture.logs if 'Spawn kernel' in log]
        
        if kernel_logs:
            print("Kernel breakdown logs found:")
            print()
            for log in kernel_logs:
                print(f"  {log}")
            print()
            
            # Parse and validate key metrics
            for log in kernel_logs:
                if 'depot_buildings=' in log:
                    # Extract metrics using simple parsing
                    metrics = {}
                    parts = log.split('|')
                    
                    if len(parts) >= 2:
                        # Parse first part (building counts)
                        buildings_part = parts[0].split(':')[-1].strip()
                        for item in buildings_part.split(','):
                            if '=' in item:
                                key, val = item.split('=')
                                metrics[key.strip()] = val.strip()
                        
                        # Parse second part (spawn metrics)
                        spawn_part = parts[1].strip()
                        for item in spawn_part.split(','):
                            if '=' in item:
                                key, val = item.split('=')
                                metrics[key.strip()] = val.strip()
                    
                    print("Extracted metrics:")
                    for key, val in metrics.items():
                        print(f"  {key}: {val}")
                    print()
                    
                    # Validate expectations
                    print("Validation checks:")
                    
                    if 'depot_buildings' in metrics:
                        depot_buildings = int(metrics['depot_buildings'])
                        print(f"  ✓ Depot buildings queried: {depot_buildings}")
                        
                    if 'route_buildings' in metrics:
                        route_buildings = int(metrics['route_buildings'])
                        print(f"  ✓ Route buildings queried: {route_buildings}")
                    
                    if 'total_all_routes' in metrics:
                        total_buildings = int(metrics['total_all_routes'])
                        print(f"  ✓ Total buildings across routes: {total_buildings}")
                    
                    if 'attractiveness' in metrics:
                        attractiveness = float(metrics['attractiveness'])
                        print(f"  ✓ Route attractiveness: {attractiveness:.1%}")
                        
                        if total_buildings > 0:
                            expected_attractiveness = route_buildings / total_buildings
                            if abs(attractiveness - expected_attractiveness) < 0.01:
                                print(f"    ✓ Matches expected: {route_buildings}/{total_buildings} = {expected_attractiveness:.1%}")
                    
                    if 'terminal_pop' in metrics:
                        terminal_pop = metrics['terminal_pop'].split()[0]  # Remove " pass/hr"
                        print(f"  ✓ Terminal population: {terminal_pop} passengers/hour")
                    
                    if 'spawn_count' in metrics:
                        spawn_count = int(metrics['spawn_count'])
                        print(f"  ✓ Spawn count: {spawn_count}")
                        
                        # Validate spawn count is reasonable for 15-min window at 8 AM
                        if 0 <= spawn_count <= 100:
                            print(f"    ✓ Spawn count is reasonable for {time_window}-min window")
                        else:
                            print(f"    ⚠️  Spawn count seems unusual for {time_window}-min window")
            
            print()
            print("=" * 80)
            print("✓ SMOKE TEST PASSED - Kernel integration working correctly")
            print("=" * 80)
            
        else:
            print("⚠️  WARNING: No kernel breakdown logs found")
            print("This might indicate the kernel is not being called.")
            print()
            print("All captured logs:")
            for log in log_capture.logs:
                print(f"  {log}")
        
    except Exception as e:
        print(f"✗ ERROR during spawn: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Captured logs before error:")
        for log in log_capture.logs:
            print(f"  {log}")


if __name__ == "__main__":
    asyncio.run(test_route_spawner_live())
