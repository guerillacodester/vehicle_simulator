"""
Integrated ZR Van Depot Operations
----------------------------------
Complete implementation of authentic Barbados ZR van operational cycle.
Integrates queue management, capacity loading, fleet communication, and navigation.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .vehicle_state import DepotQueueManager, VehicleState, VehicleStatus
from .fleet_communication import FleetManagerCommunicator, MockFleetManagerCommunicator
from ..vehicle.driver.navigation.enhanced_navigator import EnhancedNavigator, NavigationState

logger = logging.getLogger(__name__)


class ZRVanDepotOperations:
    """
    Complete ZR van depot operations manager.
    Orchestrates the full operational cycle from passenger loading to journey completion.
    """
    
    def __init__(self, data_provider=None, use_mock_fleet_manager: bool = True):
        """
        Initialize ZR van depot operations.
        
        Args:
            data_provider: Fleet data provider for vehicle/route information
            use_mock_fleet_manager: Use mock fleet manager for testing
        """
        self.data_provider = data_provider
        
        # Core components
        self.queue_manager = DepotQueueManager()
        
        # Fleet manager communication
        if use_mock_fleet_manager:
            self.fleet_communicator = MockFleetManagerCommunicator()
        else:
            self.fleet_communicator = FleetManagerCommunicator()
            
        # Vehicle navigators
        self.navigators: Dict[str, EnhancedNavigator] = {}
        
        # Operational state
        self.active = False
        self.passenger_boarding_active = False
        
        # Worker threads
        self._boarding_thread: Optional[threading.Thread] = None
        self._monitoring_thread: Optional[threading.Thread] = None
        
        # Setup callbacks
        self._setup_callbacks()
        
    def _setup_callbacks(self):
        """Setup callbacks for fleet communication and navigation"""
        # No specific vehicle callbacks needed yet - will register per vehicle
        pass
    
    def initialize_depot(self, vehicle_ids: List[str]) -> bool:
        """
        Initialize depot with vehicles.
        
        Args:
            vehicle_ids: List of vehicle IDs to add to depot
            
        Returns:
            bool: Success of initialization
        """
        try:
            logger.info(f"🏢 Initializing ZR van depot with {len(vehicle_ids)} vehicles")
            
            # Get vehicle data from provider
            if self.data_provider:
                vehicles = self.data_provider.get_vehicles()
                vehicle_data = {v['id']: v for v in vehicles}
            else:
                # Use default capacity for all vehicles
                vehicle_data = {vid: {'capacity': 11} for vid in vehicle_ids}
            
            # Add vehicles to queue
            for vehicle_id in vehicle_ids:
                capacity = vehicle_data.get(vehicle_id, {}).get('capacity', 11)
                self.queue_manager.add_vehicle_to_queue(vehicle_id, capacity)
                
                # Create navigator for vehicle
                navigator = EnhancedNavigator(vehicle_id)
                navigator.register_journey_complete_callback(self._on_journey_complete)
                navigator.register_state_change_callback(self._on_navigation_state_change)
                self.navigators[vehicle_id] = navigator
                
                # Register fleet communication callback
                self.fleet_communicator.register_route_dispatch_callback(
                    vehicle_id, self._on_route_received
                )
            
            logger.info(f"🏢 ✅ Depot initialized with {len(vehicle_ids)} vehicles in queue")
            return True
            
        except Exception as e:
            logger.error(f"🏢 ❌ Failed to initialize depot: {e}")
            return False
    
    def start_operations(self) -> bool:
        """Start depot operations"""
        if self.active:
            logger.warning("🏢 Depot operations already active")
            return False
            
        try:
            self.active = True
            self.passenger_boarding_active = True
            
            # Start passenger boarding simulation
            self._boarding_thread = threading.Thread(target=self._passenger_boarding_worker, daemon=True)
            self._boarding_thread.start()
            
            # Start operations monitoring
            self._monitoring_thread = threading.Thread(target=self._operations_monitoring_worker, daemon=True)
            self._monitoring_thread.start()
            
            logger.info("🏢 ✅ ZR van depot operations started")
            logger.info("🚶 Passenger boarding simulation active")
            return True
            
        except Exception as e:
            logger.error(f"🏢 ❌ Failed to start depot operations: {e}")
            return False
    
    def stop_operations(self):
        """Stop depot operations"""
        self.active = False
        self.passenger_boarding_active = False
        
        # Stop all vehicle engines
        for navigator in self.navigators.values():
            if navigator.engine_on:
                navigator.stop_engine()
        
        logger.info("🏢 ⏹️ ZR van depot operations stopped")
    
    def _passenger_boarding_worker(self):
        """Worker thread for passenger boarding simulation"""
        import random
        
        logger.info("🚶 Passenger boarding worker started")
        
        while self.passenger_boarding_active:
            try:
                # Check if there's an active loading vehicle
                loading_status = self.queue_manager.get_loading_vehicle_status()
                
                if loading_status and loading_status['state'] == 'loading':
                    vehicle_id = loading_status['vehicle_id']
                    
                    # Simulate random passenger arrivals (1-3 passengers every 3-8 seconds)
                    passenger_count = random.randint(1, 3)
                    boarding_interval = random.uniform(3, 8)
                    
                    # Board passengers
                    vehicle_full = self.queue_manager.board_passengers(vehicle_id, passenger_count)
                    
                    if vehicle_full:
                        # Vehicle is full - notify fleet manager
                        status = self.queue_manager.get_vehicle_status(vehicle_id)
                        if status:
                            self.fleet_communicator.notify_vehicle_full(
                                vehicle_id, status.passengers, status.capacity
                            )
                    
                    time.sleep(boarding_interval)
                else:
                    # No active loading vehicle, wait
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"🚶 Passenger boarding error: {e}")
                time.sleep(5)
        
        logger.info("🚶 Passenger boarding worker stopped")
    
    def _operations_monitoring_worker(self):
        """Worker thread for monitoring depot operations"""
        logger.info("👁️ Operations monitoring worker started")
        
        status_interval = 10  # Status update every 10 seconds
        last_status_time = time.time()
        
        while self.active:
            try:
                current_time = time.time()
                
                # Periodic status reporting
                if current_time - last_status_time >= status_interval:
                    self._log_depot_status()
                    last_status_time = current_time
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"👁️ Operations monitoring error: {e}")
                time.sleep(5)
        
        logger.info("👁️ Operations monitoring worker stopped")
    
    def _log_depot_status(self):
        """Log current depot status"""
        queue_status = self.queue_manager.get_queue_status()
        loading_status = self.queue_manager.get_loading_vehicle_status()
        
        logger.info("🏢 === DEPOT STATUS ===")
        logger.info(f"🚌 Vehicles in queue: {queue_status['queue_length']}")
        
        if loading_status:
            logger.info(f"🚌 Active loading: {loading_status['vehicle_id']} "
                       f"({loading_status['loading_progress']})")
        else:
            logger.info("🚌 No active loading vehicle")
        
        # Log vehicle states
        for vehicle_id, state_info in queue_status['vehicle_states'].items():
            state = state_info['state']
            if state == 'queued':
                pos = state_info.get('queue_position', '?')
                logger.info(f"   🚐 {vehicle_id}: Position {pos} in queue")
            elif state == 'loading':
                passengers = state_info['passengers']
                capacity = state_info['capacity']
                logger.info(f"   🚌 {vehicle_id}: Loading passengers ({passengers}/{capacity})")
            else:
                logger.info(f"   🚗 {vehicle_id}: {state}")
    
    def _on_route_received(self, vehicle_id: str, route_data: Dict[str, Any]):
        """Handle route dispatch from fleet manager"""
        logger.info(f"📡 Route received for {vehicle_id}: {route_data.get('route_name', 'Unknown')}")
        
        try:
            # Load route into navigator
            navigator = self.navigators.get(vehicle_id)
            if not navigator:
                logger.error(f"📡 ❌ No navigator found for vehicle {vehicle_id}")
                return
                
            if navigator.load_route(route_data):
                # Update depot queue
                if self.queue_manager.dispatch_vehicle(vehicle_id, route_data):
                    # Start vehicle engine and journey
                    navigator.start_engine()
                    logger.info(f"🚗 ✅ Vehicle {vehicle_id} dispatched and engine started")
                else:
                    logger.error(f"🚗 ❌ Failed to dispatch vehicle {vehicle_id}")
            else:
                logger.error(f"🗺️ ❌ Failed to load route for vehicle {vehicle_id}")
                
        except Exception as e:
            logger.error(f"📡 ❌ Route dispatch error for vehicle {vehicle_id}: {e}")
    
    def _on_journey_complete(self, vehicle_id: str, journey_data: Dict[str, Any]):
        """Handle vehicle journey completion"""
        logger.info(f"🏁 Journey completed for vehicle {vehicle_id}")
        
        try:
            # Notify fleet manager
            self.fleet_communicator.notify_journey_completed(vehicle_id, journey_data)
            
            # Return vehicle to depot queue
            self.queue_manager.vehicle_completed_journey(vehicle_id)
            
            logger.info(f"🏁 ✅ Vehicle {vehicle_id} returned to depot queue")
            
        except Exception as e:
            logger.error(f"🏁 ❌ Journey completion error for vehicle {vehicle_id}: {e}")
    
    def _on_navigation_state_change(self, vehicle_id: str, old_state: NavigationState, new_state: NavigationState):
        """Handle navigation state changes"""
        logger.info(f"🗺️ {vehicle_id} navigation: {old_state.value} → {new_state.value}")
        
        # Update fleet manager with state changes
        self.fleet_communicator.update_vehicle_state(
            vehicle_id, new_state.value,
            timestamp=datetime.now().isoformat()
        )
    
    def get_depot_status(self) -> Dict[str, Any]:
        """Get complete depot status"""
        queue_status = self.queue_manager.get_queue_status()
        loading_status = self.queue_manager.get_loading_vehicle_status()
        
        # Get navigation status for all vehicles
        navigation_status = {}
        for vehicle_id, navigator in self.navigators.items():
            navigation_status[vehicle_id] = navigator.get_navigation_status()
        
        return {
            'depot_active': self.active,
            'passenger_boarding_active': self.passenger_boarding_active,
            'queue_status': queue_status,
            'loading_status': loading_status,
            'navigation_status': navigation_status,
            'last_updated': datetime.now().isoformat()
        }
    
    def force_vehicle_full(self, vehicle_id: str) -> bool:
        """Force a vehicle to full capacity for testing"""
        status = self.queue_manager.get_vehicle_status(vehicle_id)
        if not status:
            return False
            
        remaining_capacity = status.capacity - status.passengers
        if remaining_capacity > 0:
            return self.queue_manager.board_passengers(vehicle_id, remaining_capacity)
        return True
