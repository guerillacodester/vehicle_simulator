"""
Test Enable/Disable Flags for RouteSpawner and DepotSpawner

This script runs 4 test scenarios:
1. RouteSpawner OFF, DepotSpawner ON
2. RouteSpawner ON, DepotSpawner OFF
3. Both ON
4. Both OFF
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from commuter_simulator.services.spawner_coordinator import SpawnerCoordinator
from commuter_simulator.core.domain.spawner_engine import DepotSpawner, SpawnerInterface, SpawnRequest
from commuter_simulator.core.domain.reservoirs import RouteReservoir, DepotReservoir
from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository
from datetime import datetime
import random
import uuid


class MockRouteSpawner(SpawnerInterface):
    """Simplified RouteSpawner for testing"""
    
    def __init__(self, reservoir, config, route_id: str):
        super().__init__(reservoir, config)
        self.route_id = route_id
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def spawn(self, current_time: datetime, time_window_minutes: int = 60):
        import numpy as np
        spawn_count = np.random.poisson(1.5)
        
        self.logger.info(f"Route {self.route_id}: spawning {spawn_count} passengers")
        
        spawn_requests = []
        for i in range(spawn_count):
            passenger_id = f"ROUTE_{self.route_id}_{uuid.uuid4().hex[:8].upper()}"
            spawn_requests.append(SpawnRequest(
                passenger_id=passenger_id,
                spawn_location=(33.75 + random.uniform(-0.01, 0.01), -84.39 + random.uniform(-0.01, 0.01)),
                destination_location=(33.75 + random.uniform(-0.01, 0.01), -84.39 + random.uniform(-0.01, 0.01)),
                route_id=self.route_id,
                spawn_time=current_time,
                spawn_context="ROUTE",
                priority=1.0,
                generation_method="poisson_test"
            ))
        
        return spawn_requests


async def run_test(test_name: str, enable_route: bool, enable_depot: bool):
    """Run a single test scenario"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print(f"RouteSpawner: {'ENABLED' if enable_route else 'DISABLED'}")
    print(f"DepotSpawner: {'ENABLED' if enable_depot else 'DISABLED'}")
    print("="*80)
    
    config = {
        'enable_mockroutespawner': enable_route,
        'enable_depotspawner': enable_depot,
        'enable_redis_cache': False,
        'continuous_mode': False,
    }
    
    # Initialize resources
    passenger_repo = PassengerRepository(strapi_url="http://localhost:1337")
    await passenger_repo.connect()
    
    route_reservoir = RouteReservoir(passenger_repository=passenger_repo, enable_redis_cache=False)
    depot_reservoir = DepotReservoir(depot_id="DEPOT_01", passenger_repository=passenger_repo, enable_redis_cache=False)
    
    route_spawner = MockRouteSpawner(reservoir=route_reservoir, config={}, route_id="TEST_ROUTE_1")
    depot_spawner = DepotSpawner(
        reservoir=depot_reservoir,
        config={},
        depot_id="DEPOT_01",
        depot_location=(33.7490, -84.3880),
        available_routes=["route_1", "route_2"]
    )
    
    spawners = [route_spawner, depot_spawner]
    coordinator = SpawnerCoordinator(spawners=spawners, config=config)
    
    # Run test
    await coordinator.start(current_time=datetime.utcnow(), time_window_minutes=60)
    
    # Cleanup
    await passenger_repo.disconnect()
    
    print(f"✅ {test_name} COMPLETE\n")


async def main():
    """Run all 4 test scenarios"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("\n" + "="*80)
    print("ENABLE/DISABLE FLAG TEST SUITE")
    print("Testing all combinations of RouteSpawner and DepotSpawner")
    print("="*80)
    
    # Test 1: Only DepotSpawner
    await run_test(
        test_name="Test 1: DepotSpawner ONLY",
        enable_route=False,
        enable_depot=True
    )
    
    await asyncio.sleep(1)  # Brief pause between tests
    
    # Test 2: Only RouteSpawner
    await run_test(
        test_name="Test 2: RouteSpawner ONLY",
        enable_route=True,
        enable_depot=False
    )
    
    await asyncio.sleep(1)
    
    # Test 3: Both enabled
    await run_test(
        test_name="Test 3: BOTH Spawners",
        enable_route=True,
        enable_depot=True
    )
    
    await asyncio.sleep(1)
    
    # Test 4: Both disabled
    await run_test(
        test_name="Test 4: NO Spawners",
        enable_route=False,
        enable_depot=False
    )
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
