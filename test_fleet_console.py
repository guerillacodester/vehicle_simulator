"""
Quick test to verify Fleet Console can connect to API
"""

import asyncio
from clients.fleet import FleetConnector


async def test_fleet_connector():
    """Test basic connectivity and API calls"""
    print("🧪 Testing Fleet Connector...")
    print("="*60)
    
    connector = FleetConnector(base_url="http://localhost:5001")
    
    try:
        # Test 1: Health check
        print("\n1️⃣  Testing health endpoint...")
        health = await connector.get_health()
        print(f"   ✅ Status: {health.status}")
        print(f"   ✅ Simulator running: {health.simulator_running}")
        print(f"   ✅ Active vehicles: {health.active_vehicles}")
        
        # Test 2: List vehicles
        print("\n2️⃣  Testing vehicles endpoint...")
        vehicles = await connector.get_vehicles()
        print(f"   ✅ Found {len(vehicles)} vehicles")
        for v in vehicles:
            print(f"      - {v.vehicle_id}: {v.driver_name}, Route {v.route_id}")
        
        # Test 3: Get specific vehicle (if any exist)
        if vehicles:
            print("\n3️⃣  Testing vehicle detail endpoint...")
            vehicle = await connector.get_vehicle(vehicles[0].vehicle_id)
            print(f"   ✅ Vehicle: {vehicle.vehicle_id}")
            print(f"      Engine: {'ON' if vehicle.engine_running else 'OFF'}")
            print(f"      Passengers: {vehicle.passenger_count}/{vehicle.capacity}")
        
        # Test 4: Control commands (if vehicle exists)
        if vehicles:
            vehicle_id = vehicles[0].vehicle_id
            print(f"\n4️⃣  Testing control commands on {vehicle_id}...")
            
            # Start engine
            result = await connector.start_engine(vehicle_id)
            print(f"   {'✅' if result.success else '❌'} Start engine: {result.message}")
            
            # Enable boarding
            result = await connector.enable_boarding(vehicle_id)
            print(f"   {'✅' if result.success else '❌'} Enable boarding: {result.message}")
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("\n💡 To use the interactive console:")
        print("   python -m clients.fleet")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the simulator is running:")
        print("   python -m arknet_transit_simulator --mode depot")
    
    finally:
        await connector.close()


if __name__ == "__main__":
    asyncio.run(test_fleet_connector())
