"""Test vehicle performance service capacity fetching"""
import asyncio
from arknet_transit_simulator.services.vehicle_performance import VehiclePerformanceService

async def test_fetch_vehicle():
    """Test fetching vehicle ZR102"""
    try:
        print("🔍 Testing VehiclePerformanceService.get_performance_async('ZR102')...")
        
        perf = await VehiclePerformanceService.get_performance_async('ZR102')
        
        print(f"✅ SUCCESS!")
        print(f"   Vehicle: ZR102")
        print(f"   Capacity: {perf.capacity}")
        print(f"   Max Speed: {perf.max_speed_kmh} km/h")
        print(f"   Acceleration: {perf.acceleration_mps2} m/s²")
        print(f"   Braking: {perf.braking_mps2} m/s²")
        print(f"   Eco Mode: {perf.eco_mode}")
        print(f"   Profile: {perf.performance_profile}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

async def main():
    success = await test_fetch_vehicle()
    if success:
        print("\n✅ Step 1 Complete: VehiclePerformanceService can fetch capacity from Strapi")
    else:
        print("\n❌ Step 1 Failed: Check Strapi API connection")

if __name__ == "__main__":
    asyncio.run(main())
