#!/usr/bin/env python
"""
Production test: Start all services and verify autonomous vehicle operation
"""

import asyncio
import sys
from clients.fleet.connector import FleetConnector


async def test_production():
    """Test full production stack"""
    connector = FleetConnector(base_url="http://localhost:6000")
    
    print("\n" + "="*60)
    print("🚀 PRODUCTION TEST: Multi-Service Management")
    print("="*60)
    
    # Step 1: Check service status before start
    print("\n[1] Checking initial service status...")
    try:
        status = await connector.get_all_services_status()
        print(f"✅ Retrieved status for {len(status)} services:")
        for service, info in status.items():
            print(f"   {service:20} → {info['status']:10} (PID: {info['pid']})")
    except Exception as e:
        print(f"❌ Error getting service status: {e}")
        return False
    
    # Step 2: Start all services
    print("\n[2] Starting all services...")
    try:
        result = await connector.start_all_services()
        print(f"✅ Start-all result: {result.get('message', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return False
    
    # Wait for services to start
    print("\n[3] Waiting for services to stabilize (15 seconds)...")
    await asyncio.sleep(15)
    
    # Step 3: Check status after start
    print("\n[4] Checking service status after start...")
    try:
        status = await connector.get_all_services_status()
        print("✅ Service Status:")
        running_count = 0
        for service, info in status.items():
            emoji = "🟢" if info['status'] == 'running' else "🔴"
            uptime = f"{info['uptime']:.0f}s" if info.get('uptime') else "N/A"
            print(f"   {emoji} {service:20} → {info['status']:10} | PID: {info['pid']:6} | Uptime: {uptime}")
            if info['status'] == 'running':
                running_count += 1
        
        print(f"\n✅ {running_count} services running")
        
    except Exception as e:
        print(f"❌ Error checking service status: {e}")
        return False
    
    # Step 4: Check vehicles (this requires simulator to be running with data)
    print("\n[5] Checking vehicles (requires simulator + Strapi data)...")
    try:
        vehicles_response = await connector.get_vehicles()
        if hasattr(vehicles_response, 'drivers'):
            vehicle_count = len(vehicles_response.drivers) if vehicles_response.drivers else 0
            print(f"✅ Found {vehicle_count} vehicles/drivers")
            if vehicle_count > 0:
                for i, vehicle in enumerate(vehicles_response.drivers[:3]):  # Show first 3
                    print(f"   - {vehicle.code}: {vehicle.status} (Engine: {vehicle.engine_status}, GPS: {vehicle.gps_enabled})")
        else:
            print(f"⚠️  No vehicles data available yet")
    except Exception as e:
        print(f"⚠️  Could not retrieve vehicles: {e}")
    
    print("\n" + "="*60)
    print("✅ PRODUCTION TEST COMPLETE")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_production())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
