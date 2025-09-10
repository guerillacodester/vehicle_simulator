#!/usr/bin/env python3
"""
Complete ZR Van Operational Cycle Test
--------------------------------------
Demonstrates the full authentic Barbados ZR van operation:
1. Vehicles queue at depot
2. Random passenger boarding until full
3. Fleet manager route dispatch
4. Navigator engine start and route following
5. Destination loitering (5 minutes)
6. Return journey
7. Depot return and passenger disembarkation
8. Cycle repeat

This test simulates the real-world ZR van experience in Barbados.
"""

import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zr_van_operations.log')
    ]
)
logger = logging.getLogger(__name__)


def test_complete_zr_van_cycle():
    """Test the complete ZR van operational cycle"""
    
    print("🚌" * 20)
    print("🇧🇧 BARBADOS ZR VAN OPERATIONAL CYCLE TEST 🇧🇧")
    print("🚌" * 20)
    print()
    print("🎯 AUTHENTIC ZR VAN EXPERIENCE:")
    print("   📍 Depot queue management")
    print("   👥 Random passenger boarding")
    print("   📡 Fleet manager route dispatch")
    print("   🗺️ Complete route navigation")
    print("   ⏰ Destination loitering (5 min)")
    print("   🔄 Return journey and cycle repeat")
    print("=" * 80)
    print()
    
    try:
        # Import our components
        from world.vehicle_simulator.core.zr_van_depot import ZRVanDepotOperations
        
        # Initialize depot operations
        depot = ZRVanDepotOperations(use_mock_fleet_manager=True)
        
        # Test vehicles (ZR van fleet)
        test_vehicles = ['ZR001', 'ZR002', 'ZR003']
        
        print(f"🏢 Initializing depot with vehicles: {', '.join(test_vehicles)}")
        
        if not depot.initialize_depot(test_vehicles):
            print("❌ Failed to initialize depot")
            return
            
        print("✅ Depot initialized successfully")
        print()
        
        # Start depot operations
        print("🚀 Starting ZR van depot operations...")
        if not depot.start_operations():
            print("❌ Failed to start operations")
            return
            
        print("✅ Operations started - passenger boarding simulation active")
        print()
        
        # Run simulation
        simulation_duration = 120  # 2 minutes for demonstration
        start_time = time.time()
        status_interval = 15  # Status every 15 seconds
        last_status = start_time
        
        print(f"⏰ Running simulation for {simulation_duration} seconds...")
        print("📊 Watch the complete ZR van operational cycle!")
        print("-" * 80)
        print()
        
        while time.time() - start_time < simulation_duration:
            current_time = time.time()
            
            # Periodic status updates
            if current_time - last_status >= status_interval:
                elapsed = int(current_time - start_time)
                print(f"⏱️ SIMULATION TIME: {elapsed}s / {simulation_duration}s")
                print()
                
                # Get and display depot status
                status = depot.get_depot_status()
                display_depot_status(status)
                print("-" * 80)
                print()
                
                last_status = current_time
            
            time.sleep(1)
        
        print("🏁 SIMULATION COMPLETED")
        print()
        
        # Final status
        final_status = depot.get_depot_status()
        print("📊 FINAL DEPOT STATUS:")
        display_depot_status(final_status)
        
        # Stop operations
        depot.stop_operations()
        print()
        print("✅ ZR van depot operations stopped")
        print()
        print("🎉 Complete ZR van operational cycle test finished!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"❌ Test failed: {e}")


def display_depot_status(status: dict):
    """Display formatted depot status"""
    print("🏢 === DEPOT STATUS ===")
    
    # Overall status
    print(f"🔧 Depot Active: {'✅' if status['depot_active'] else '❌'}")
    print(f"🚶 Boarding Active: {'✅' if status['passenger_boarding_active'] else '❌'}")
    print()
    
    # Queue status
    queue_status = status['queue_status']
    print(f"🚌 Queue Length: {queue_status['queue_length']}")
    print(f"🎯 Active Loading: {queue_status['active_loading_vehicle'] or 'None'}")
    print()
    
    # Vehicle states
    print("🚐 VEHICLE STATES:")
    vehicle_states = queue_status['vehicle_states']
    
    for vehicle_id, vehicle_info in vehicle_states.items():
        state = vehicle_info['state']
        passengers = vehicle_info['passengers']
        capacity = vehicle_info['capacity']
        engine = "🔥" if vehicle_info['engine_on'] else "⚫"
        
        if state == 'queued':
            pos = vehicle_info.get('queue_position', '?')
            print(f"   🚐 {vehicle_id}: Queue Position {pos} {engine}")
        elif state == 'loading':
            print(f"   🚌 {vehicle_id}: Loading passengers ({passengers}/{capacity}) {engine}")
        elif state == 'full':
            print(f"   🚌 {vehicle_id}: FULL - Awaiting route ({passengers}/{capacity}) {engine}")
        elif state == 'dispatched':
            print(f"   🚗 {vehicle_id}: Dispatched on route {engine}")
        else:
            print(f"   🚗 {vehicle_id}: {state.title()} {engine}")
    
    # Navigation status
    nav_status = status['navigation_status']
    if nav_status:
        print()
        print("🗺️ NAVIGATION STATUS:")
        for vehicle_id, nav_info in nav_status.items():
            nav_state = nav_info['state']
            route_name = nav_info.get('route_name', 'No route')
            engine = "🔥" if nav_info['engine_on'] else "⚫"
            
            if nav_state != 'idle':
                print(f"   🗺️ {vehicle_id}: {nav_state.replace('_', ' ').title()} - {route_name} {engine}")


def simulate_manual_passenger_loading():
    """Simulate manual passenger loading for testing"""
    print()
    print("🎮 MANUAL TESTING MODE")
    print("This allows you to manually control passenger boarding")
    print()
    
    try:
        from world.vehicle_simulator.core.zr_van_depot import ZRVanDepotOperations
        
        depot = ZRVanDepotOperations(use_mock_fleet_manager=True)
        depot.initialize_depot(['ZR001'])
        depot.start_operations()
        
        print("🚌 Vehicle ZR001 is ready for manual passenger loading")
        print("Commands:")
        print("  'load <count>' - Load passengers (e.g., 'load 3')")
        print("  'status' - Show depot status")
        print("  'full' - Fill vehicle to capacity")
        print("  'quit' - Exit")
        print()
        
        while True:
            try:
                command = input("ZR> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'status':
                    status = depot.get_depot_status()
                    display_depot_status(status)
                elif command == 'full':
                    if depot.force_vehicle_full('ZR001'):
                        print("✅ Vehicle ZR001 filled to capacity")
                    else:
                        print("❌ Failed to fill vehicle")
                elif command.startswith('load '):
                    try:
                        count = int(command.split()[1])
                        if depot.queue_manager.board_passengers('ZR001', count):
                            print(f"✅ {count} passengers boarded")
                        else:
                            print("❌ Failed to board passengers")
                    except (IndexError, ValueError):
                        print("❌ Invalid load command. Use 'load <count>'")
                else:
                    print("❌ Unknown command")
                    
            except KeyboardInterrupt:
                break
        
        depot.stop_operations()
        print("👋 Manual testing ended")
        
    except Exception as e:
        print(f"❌ Manual testing failed: {e}")


if __name__ == "__main__":
    print("🚌 ZR Van Operational Cycle Test")
    print()
    print("Choose test mode:")
    print("1. Automatic simulation (2 minutes)")
    print("2. Manual passenger loading")
    print()
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == '1':
            test_complete_zr_van_cycle()
        elif choice == '2':
            simulate_manual_passenger_loading()
        else:
            print("Invalid choice. Running automatic simulation...")
            test_complete_zr_van_cycle()
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
