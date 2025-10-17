"""
Simple test: Can the driver start the engine?

This script tests the basic engine start mechanism without any conductor complexity.
Goal: Verify that calling driver.start_engine() works and produces telemetry updates.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from arknet_transit_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver
from arknet_transit_simulator.vehicle.engine.engine_block import Engine
from arknet_transit_simulator.vehicle.engine.engine_buffer import EngineBuffer
from arknet_transit_simulator.vehicle.engine import sim_speed_model


async def test_engine_start():
    """Test if driver can start engine and get telemetry updates."""
    
    print("\n" + "="*60)
    print("TEST: Driver Engine Start")
    print("="*60)
    
    # 1. Create engine components
    print("\n[1] Creating engine components...")
    engine_buffer = EngineBuffer()
    speed_model = sim_speed_model.load_speed_model("fixed", speed=25.0)  # 25 km/h
    
    engine = Engine(
        vehicle_id="TEST-001",
        model=speed_model,
        buffer=engine_buffer,
        tick_time=0.5
    )
    print("✅ Engine created")
    
    # 2. Create driver with simple route
    print("\n[2] Creating driver...")
    test_route = [
        [-59.636900, 13.319443],  # Start point (lon, lat)
        [-59.636800, 13.319543],  # Point 100m away
        [-59.636700, 13.319643],  # Point 200m away
    ]
    
    driver = VehicleDriver(
        driver_id="TEST-DRIVER-001",
        driver_name="Test Driver",
        vehicle_id="TEST-001",
        route_coordinates=test_route,
        route_name="TEST-ROUTE",
        engine_buffer=engine_buffer
    )
    print("✅ Driver created")
    
    # 3. Set vehicle components
    print("\n[3] Setting vehicle components...")
    driver.set_vehicle_components(engine=engine, gps_device=None)  # No GPS for this test
    print("✅ Components set")
    
    # 4. Board vehicle (this should set state to WAITING, not ONBOARD)
    print("\n[4] Driver boarding vehicle...")
    await driver._start_implementation()  # Use internal method directly
    print(f"✅ Driver state: {driver.current_state.value}")
    
    # 5. Check initial telemetry (engine should be OFF)
    print("\n[5] Initial telemetry (engine OFF)...")
    initial_telemetry = driver.step()
    if initial_telemetry:
        print(f"   Speed: {initial_telemetry.get('speed', 0):.2f} km/h")
        print(f"   Position: ({initial_telemetry.get('lat', 0):.6f}, {initial_telemetry.get('lon', 0):.6f})")
    else:
        print("   ⚠️ No telemetry (expected when engine is OFF)")
    
    # 6. START ENGINE - THIS IS THE CRITICAL TEST
    print("\n[6] 🔥 STARTING ENGINE...")
    result = await driver.start_engine()
    print(f"   Result: {result}")
    print(f"   Driver state: {driver.current_state.value}")
    
    # 7. Check telemetry after engine start
    print("\n[7] Checking telemetry after engine start...")
    await asyncio.sleep(1)  # Wait for engine to tick
    
    for i in range(5):
        telemetry = driver.step()
        if telemetry:
            print(f"   [T+{i+1}s] Speed: {telemetry.get('speed', 0):.2f} km/h | "
                  f"Position: ({telemetry.get('lat', 0):.6f}, {telemetry.get('lon', 0):.6f})")
        else:
            print(f"   [T+{i+1}s] ⚠️ No telemetry")
        await asyncio.sleep(1)
    
    # 8. Stop driver
    print("\n[8] Stopping driver...")
    await driver.stop()
    print("✅ Driver stopped")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_engine_start())
