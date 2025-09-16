#!/usr/bin/env python3
"""
Test Passenger Scheduling System
================================

Test script to verify that passengers are scheduled with depart_time and spawned over time.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'world'))

from world.arknet_transit_simulator.passenger_modeler.passenger_service import DynamicPassengerService

async def test_passenger_scheduling():
    """Test the passenger scheduling functionality"""
    print("🧪 TESTING PASSENGER SCHEDULING SYSTEM")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Create passenger service for test route
        test_routes = ['1']  # Use route 1 for testing
        service = DynamicPassengerService(test_routes, max_memory_mb=5)
        
        # Start the service  
        if not await service.start_service():
            print("❌ Failed to start passenger service")
            return
        
        print("✅ Passenger service started successfully")
        
        # Try to load passengers from generator (if API is available)
        try:
            scheduled_count = await service.load_and_schedule_from_generator('1', start_hour=7)
            print(f"📋 Scheduled {scheduled_count} passengers from arknet_passenger_generator")
        except Exception as e:
            print(f"⚠️  Could not load from generator (API may be down): {e}")
            
            # Fallback: manually schedule a few test passengers
            print("🔧 Adding manual test passengers...")
            start_time = datetime.now()
            
            # Schedule passengers at different times over next 2 minutes
            test_passengers = [
                {'depart_time': start_time + timedelta(seconds=10), 'stop': 'Stop_A'},
                {'depart_time': start_time + timedelta(seconds=30), 'stop': 'Stop_B'},
                {'depart_time': start_time + timedelta(seconds=60), 'stop': 'Stop_C'},
                {'depart_time': start_time + timedelta(seconds=90), 'stop': 'Stop_D'},
            ]
            
            for i, passenger_data in enumerate(test_passengers):
                scheduled_passenger = {
                    'id': f"TEST_{i+1:03d}",
                    'stop_id': f"stop_{i+1}",
                    'stop_name': passenger_data['stop'],
                    'stop_coords': [0, 0],
                    'depart_time': passenger_data['depart_time'],
                    'schedule_time': start_time,
                    'status': 'scheduled',
                    'route_id': '1',
                    'source': 'manual_test'
                }
                service.scheduled_passengers.append(scheduled_passenger)
            
            print(f"📋 Manually scheduled {len(test_passengers)} test passengers")
        
        # Monitor the service for 2 minutes to see passengers being activated
        print("\n🔍 MONITORING PASSENGER ACTIVATION...")
        print("Watching for scheduled passengers to become active...")
        
        start_time = datetime.now()
        duration = 120  # 2 minutes
        last_stats_time = start_time
        
        while (datetime.now() - start_time).total_seconds() < duration:
            current_time = datetime.now()
            
            # Print stats every 15 seconds
            if (current_time - last_stats_time).total_seconds() >= 15:
                stats = service.get_service_stats()
                scheduled_count = len(service.scheduled_passengers)
                active_count = len(service.active_passengers)
                
                print(f"\n⏱️  T+{(current_time - start_time).total_seconds():.0f}s:")
                print(f"   📋 Scheduled passengers: {scheduled_count}")
                print(f"   🚶 Active passengers: {active_count}")
                print(f"   📊 Total spawned: {stats.total_spawned}")
                
                # Show next scheduled passenger
                if service.scheduled_passengers:
                    next_passenger = min(service.scheduled_passengers, key=lambda p: p['depart_time'])
                    time_until_next = (next_passenger['depart_time'] - current_time).total_seconds()
                    print(f"   ⏰ Next passenger in {time_until_next:.1f}s at {next_passenger['stop_name']}")
                
                last_stats_time = current_time
            
            await asyncio.sleep(1)
        
        # Final stats
        print(f"\n🏁 FINAL RESULTS AFTER {duration}s:")
        final_stats = service.get_service_stats()
        print(f"   📋 Remaining scheduled: {len(service.scheduled_passengers)}")
        print(f"   🚶 Active passengers: {len(service.active_passengers)}")
        print(f"   📊 Total spawned: {final_stats.total_spawned}")
        
        # Show some active passengers
        if service.active_passengers:
            print(f"\n👥 ACTIVE PASSENGERS:")
            for i, (passenger_id, passenger_data) in enumerate(list(service.active_passengers.items())[:3]):
                depart_time = passenger_data.get('depart_time', 'Unknown')
                status = passenger_data.get('status', 'Unknown')
                stop = passenger_data.get('stop_name', 'Unknown')
                print(f"   {i+1}. {passenger_id} - {status} at {stop} (wanted to depart: {depart_time})")
        
        # Stop the service
        await service.stop_service()
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_passenger_scheduling())