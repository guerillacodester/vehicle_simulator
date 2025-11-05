#!/usr/bin/env python3
"""
Commuter Service CLI Test Workflow
===================================
Complete workflow test:
1. Connect to commuter service
2. Delete all existing passengers
3. Spawn new passengers for Monday (24 hours)
4. Visualize via table and barchart
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.commuter.connector import CommuterConnector


async def test_workflow():
    """Run complete test workflow"""
    
    connector = CommuterConnector(base_url="http://localhost:4000")
    
    print("="*80)
    print("COMMUTER SERVICE CLI TEST WORKFLOW")
    print("="*80)
    
    # Step 1: Connect
    print("\n📡 Step 1: Connecting to commuter service...")
    try:
        await connector.connect()
        print("✅ Connected successfully!")
        print(f"   HTTP API: {connector.base_url}")
        print(f"   WebSocket: {'✅ Connected' if connector.sio_connected else '⚠️ Not available'}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Step 2: Check current passenger count
    print("\n📊 Step 2: Checking current passenger count...")
    try:
        # Get manifest for route 1 to see current count
        manifest = await connector.get_manifest(route="1", limit=1000)
        current_count = manifest.count
        print(f"   Current passengers for Route 1: {current_count}")
    except Exception as e:
        print(f"⚠️  Could not get current count: {e}")
        current_count = 0
    
    # Step 3: Delete existing passengers
    if current_count > 0:
        print(f"\n🗑️  Step 3: Deleting {current_count} existing passengers...")
        confirm = input(f"   ⚠️  DELETE ALL PASSENGERS? (yes/no): ")
        
        if confirm.lower() == 'yes':
            try:
                result = await connector.delete_passengers(route="1", confirm=True)
                print(f"✅ Deleted {result.get('deleted', 0)} passengers")
            except Exception as e:
                print(f"❌ Deletion failed: {e}")
                return
        else:
            print("❌ Deletion cancelled - keeping existing passengers")
    else:
        print("\n✅ Step 3: No existing passengers to delete")
    
    # Step 4: Spawn new passengers for Monday (24 hours)
    print("\n🌱 Step 4: Spawning passengers for Monday (24 hours)...")
    print("   Route: 1")
    print("   Day: monday")
    print("   Hours: 0-23 (full day)")
    
    confirm_spawn = input("   Proceed with spawning? (yes/no): ")
    
    if confirm_spawn.lower() == 'yes':
        try:
            # Spawn for each hour of Monday
            total_spawned = 0
            for hour in range(24):
                result = await connector.spawn_passengers(
                    route="1",
                    day="monday",
                    hour_range=f"{hour}-{hour}"
                )
                spawned = result.get('spawned', 0)
                total_spawned += spawned
                print(f"   ✅ Hour {hour:02d}: Spawned {spawned} passengers (Total: {total_spawned})")
            
            print(f"\n🎉 Successfully spawned {total_spawned} passengers!")
        except Exception as e:
            print(f"❌ Spawning failed: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        print("❌ Spawning cancelled")
        return
    
    # Step 5: Get updated manifest
    print("\n📋 Step 5: Fetching updated manifest...")
    try:
        manifest = await connector.get_manifest(route="1", limit=1000)
        passengers = manifest.passengers
        total = manifest.count
        
        print(f"✅ Manifest retrieved: {total} passengers")
        
        # Show first 10 passengers
        print("\n" + "="*80)
        print("PASSENGER MANIFEST - Route 1 (First 10)")
        print("="*80)
        print(f"{'#':<5} {'Passenger ID':<40} {'Time':<8} {'Status':<10}")
        print("-"*80)
        
        for i, passenger in enumerate(passengers[:10], 1):
            p_id = passenger.passenger_id[:40]
            time = passenger.spawned_at.strftime("%H:%M") if hasattr(passenger.spawned_at, 'strftime') else str(passenger.spawned_at)[:5]
            status = passenger.status
            print(f"{i:<5} {p_id:<40} {time:<8} {status:<10}")
        
        if total > 10:
            print(f"\n... and {total - 10} more passengers")
        
    except Exception as e:
        print(f"❌ Manifest retrieval failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Get barchart visualization
    print("\n📊 Step 6: Generating barchart visualization...")
    try:
        barchart = await connector.get_barchart(route="1")
        
        print("\n" + "="*80)
        print("PASSENGER DISTRIBUTION BARCHART - Route 1")
        print("="*80)
        
        for hour_data in barchart.hours:
            hour = hour_data.hour
            count = hour_data.count
            bar = "█" * (count // 2)  # Scale down for display
            print(f"{hour:02d}:00 | {count:3d} | {bar}")
        
        print("="*80)
        print(f"Total: {barchart.total_passengers} passengers")
        print(f"Peak hour: {barchart.peak_hour} ({barchart.peak_count} passengers)")
        
    except Exception as e:
        print(f"❌ Barchart generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 7: Disconnect
    print("\n👋 Step 7: Disconnecting...")
    await connector.disconnect()
    print("✅ Disconnected successfully")
    
    print("\n" + "="*80)
    print("TEST WORKFLOW COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_workflow())
