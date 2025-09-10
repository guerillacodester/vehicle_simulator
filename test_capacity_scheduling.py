#!/usr/bin/env python3
"""
Test Capacity-Based Scheduling
------------------------------
Demonstrates ZR van style capacity-based departure system with passenger boarding simulation.
"""

import time
import logging
from datetime import datetime
from world.vehicle_simulator.core.timetable_scheduler import TimetableScheduler, CapacityBasedOperation

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockDataProvider:
    """Mock data provider for testing"""
    
    def is_api_available(self):
        return True
    
    def get_schedules(self):
        return [
            {
                'vehicle_id': 'ZR001',
                'route_id': 'R001',
                'driver_id': 'D001',
                'max_wait_time': 60  # 1 minute for testing
            },
            {
                'vehicle_id': 'ZR002', 
                'route_id': 'R002',
                'driver_id': 'D002',
                'max_wait_time': 90  # 1.5 minutes for testing
            }
        ]
    
    def get_routes(self):
        return {
            'R001': {'short_name': 'Route 1', 'long_name': 'City to Airport'},
            'R002': {'short_name': 'Route 2', 'long_name': 'Bridgetown to Oistins'}
        }
    
    def get_vehicles(self):
        return {
            'ZR001': {'capacity': 11, 'reg_code': 'ZR001'},
            'ZR002': {'capacity': 14, 'reg_code': 'ZR002'}  # Larger van
        }


def test_capacity_based_scheduling():
    """Test the capacity-based scheduling system"""
    
    print("🚌 TESTING ZR VAN CAPACITY-BASED SCHEDULING")
    print("=" * 60)
    print("🎯 ZR vans depart when full OR after max wait time")
    print("📊 Simulating passenger arrivals and departures")
    print("-" * 60)
    
    # Create mock data provider
    data_provider = MockDataProvider()
    
    # Create scheduler in capacity mode
    scheduler = TimetableScheduler(
        data_provider=data_provider,
        precision_seconds=1,  # Fast for testing
        default_mode='capacity',
        default_capacity=11
    )
    
    # Load capacity-based operations
    scheduler.load_today_schedule()
    
    # Start scheduler
    scheduler.start()
    
    print(f"✅ Scheduler started with {len(scheduler.capacity_operations)} capacity operations")
    
    # Display initial status
    status = scheduler.get_schedule_status()
    print(f"📋 Schedule Mode: {status['mode'].upper()}")
    print(f"🚌 Total Operations: {status['total_operations']}")
    
    # Show capacity operations
    print("\n🚐 CAPACITY OPERATIONS:")
    for op in status['capacity_operations']:
        print(f"   🚌 {op['vehicle_id']} (Route {op['route_id']}) - "
              f"Capacity: {op['passengers']} - "
              f"Status: {'Boarding' if op['boarding'] else 'Waiting'}")
    
    print("\n" + "=" * 60)
    print("🎬 SIMULATION STARTING - Watch passenger boarding!")
    print("=" * 60)
    
    # Simulate for 30 seconds
    start_time = time.time()
    last_status_time = 0
    
    try:
        while time.time() - start_time < 30:
            current_time = time.time() - start_time
            
            # Show status every 10 seconds
            if current_time - last_status_time >= 10:
                print(f"\n⏰ Time: {current_time:.1f}s")
                
                # Get current status
                status = scheduler.get_schedule_status()
                
                if status.get('next_departure'):
                    next_dep = status['next_departure']
                    if next_dep.get('ready_to_depart'):
                        print(f"🚐 {next_dep['vehicle_id']} READY TO DEPART: {next_dep['departure_reason']}")
                    else:
                        print(f"🚌 {next_dep['vehicle_id']} boarding: {next_dep['passengers']} "
                              f"(Max wait: {next_dep['max_wait_remaining']})")
                
                # Show all capacity operations
                for op in status['capacity_operations']:
                    status_emoji = "✅" if op['executed'] else ("🚌" if op['boarding'] else "⏳")
                    boarding_text = "BOARDING" if op['boarding'] else "WAITING"
                    ready_text = " - READY!" if op['ready'] else ""
                    print(f"   {status_emoji} {op['vehicle_id']}: {op['passengers']} - {boarding_text}{ready_text}")
                
                last_status_time = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulation interrupted")
    
    # Final status
    print("\n" + "=" * 60)
    print("📊 FINAL STATUS")
    print("=" * 60)
    
    final_status = scheduler.get_schedule_status()
    print(f"✅ Completed Operations: {final_status['completed_operations']}")
    print(f"⏳ Pending Operations: {final_status['pending_operations']}")
    
    for op in final_status['capacity_operations']:
        status_text = "COMPLETED" if op['executed'] else "PENDING"
        print(f"   🚌 {op['vehicle_id']}: {op['passengers']} - {status_text}")
    
    # Stop scheduler
    scheduler.stop()
    print("\n✅ Test completed!")


if __name__ == "__main__":
    test_capacity_based_scheduling()
