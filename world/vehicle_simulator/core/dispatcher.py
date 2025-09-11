#!/usr/bin/env python3
"""
Dispatcher
----------
Handles route assignment and vehicle coordination between DepotManager and VehicleDrivers.
Manages vehicle queuing, route loading, and dispatch operations in the realistic depot hierarchy.

Architecture Position: DepotManager → Dispatcher → VehicleDriver → Conductor (future)
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Route coordination utilities
from world.vehicle_simulator.utils.routes.route_coordinator import get_route_coordinates, create_navigator_with_route
from world.vehicle_simulator.vehicle.driver.navigation.vehicle_driver import VehicleDriver

# Create logger for this module
logger = logging.getLogger(__name__)

class VehicleStatus(Enum):
    """Vehicle status from dispatcher perspective"""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    DISPATCHED = "dispatched"
    IN_SERVICE = "in_service"
    RETURNING = "returning"
    MAINTENANCE = "maintenance"

@dataclass
class DispatchAssignment:
    """Represents a dispatch assignment"""
    vehicle_id: str
    route_id: str
    route_coordinates: List[Tuple[float, float]]
    priority: int = 0
    scheduled_time: Optional[str] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class VehicleRegistration:
    """Vehicle registration in dispatcher system"""
    vehicle_id: str
    vehicle_handler: Dict[str, Any]  # Reference to DepotManager vehicle handler
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_assignment: Optional[DispatchAssignment] = None
    registered_at: float = None
    
    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = time.time()

class Dispatcher:
    """
    Vehicle dispatch coordinator for realistic depot operations.
    
    Responsibilities:
    - Route assignment management
    - Vehicle queuing and coordination  
    - API route loading with fallback
    - Communication bridge between DepotManager and VehicleDrivers
    """
    
    def __init__(self, enable_route_caching: bool = True, 
                 max_queue_size: int = 50,
                 dispatch_interval: float = 1.0):
        """
        Initialize Dispatcher.
        
        Args:
            enable_route_caching: Whether to cache loaded routes
            max_queue_size: Maximum number of queued assignments
            dispatch_interval: Time interval for dispatch processing
        """
        # Core configuration
        self.enable_route_caching = enable_route_caching
        self.max_queue_size = max_queue_size
        self.dispatch_interval = dispatch_interval
        
        # State management
        self.running = False
        self.vehicles: Dict[str, VehicleRegistration] = {}
        self.assignment_queue: List[DispatchAssignment] = []
        self.route_cache: Dict[str, List[Tuple[float, float]]] = {}
        
        # Statistics
        self.stats = {
            'assignments_processed': 0,
            'assignments_failed': 0,
            'routes_cached': 0,
            'vehicles_dispatched': 0,
            'queue_high_water_mark': 0
        }
        
        logger.info("✅ Dispatcher initialized")
    
    # ==================== VEHICLE REGISTRATION ====================
    
    def register_vehicle(self, vehicle_id: str, vehicle_handler: Dict[str, Any]) -> bool:
        """
        Register a vehicle with the dispatcher.
        
        Args:
            vehicle_id: Unique vehicle identifier
            vehicle_handler: Reference to DepotManager vehicle handler
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if vehicle_id in self.vehicles:
                logger.warning(f"Vehicle {vehicle_id} already registered, updating registration")
            
            registration = VehicleRegistration(
                vehicle_id=vehicle_id,
                vehicle_handler=vehicle_handler,
                status=VehicleStatus.AVAILABLE
            )
            
            self.vehicles[vehicle_id] = registration
            logger.info(f"✅ Vehicle {vehicle_id} registered with dispatcher")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register vehicle {vehicle_id}: {e}")
            return False
    
    def unregister_vehicle(self, vehicle_id: str) -> bool:
        """
        Unregister a vehicle from the dispatcher.
        
        Args:
            vehicle_id: Vehicle to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if vehicle_id not in self.vehicles:
                logger.warning(f"Vehicle {vehicle_id} not registered")
                return False
            
            # Clean up any active assignments
            registration = self.vehicles[vehicle_id]
            if registration.current_assignment:
                logger.info(f"Canceling active assignment for vehicle {vehicle_id}")
                registration.current_assignment = None
            
            del self.vehicles[vehicle_id]
            logger.info(f"✅ Vehicle {vehicle_id} unregistered from dispatcher")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister vehicle {vehicle_id}: {e}")
            return False
    
    # ==================== ROUTE MANAGEMENT ====================
    
    def load_route(self, route_id: str, route_file: Optional[str] = None, 
                   direction: str = "outbound") -> Optional[List[Tuple[float, float]]]:
        """
        Load route coordinates using route_coordinator.
        
        Args:
            route_id: Route identifier for database lookup
            route_file: Optional file path for fallback
            direction: Route direction ("outbound" or "inbound")
            
        Returns:
            List of (lon, lat) coordinates or None if failed
        """
        try:
            # Check cache first
            cache_key = f"{route_id}_{direction}"
            if self.enable_route_caching and cache_key in self.route_cache:
                logger.debug(f"Route {route_id} ({direction}) loaded from cache")
                return self.route_cache[cache_key]
            
            # Load route using route_coordinator
            coordinates = get_route_coordinates(
                route_id=route_id,
                route_file=route_file,
                direction=direction
            )
            
            # Cache the result
            if self.enable_route_caching and coordinates:
                self.route_cache[cache_key] = coordinates
                self.stats['routes_cached'] += 1
                logger.debug(f"Route {route_id} ({direction}) cached ({len(coordinates)} coords)")
            
            logger.info(f"✅ Route {route_id} loaded ({len(coordinates) if coordinates else 0} coordinates)")
            return coordinates
            
        except Exception as e:
            logger.error(f"Failed to load route {route_id}: {e}")
            return None
    
    def clear_route_cache(self):
        """Clear all cached routes"""
        cache_size = len(self.route_cache)
        self.route_cache.clear()
        logger.info(f"Route cache cleared ({cache_size} entries removed)")
    
    # ==================== ASSIGNMENT MANAGEMENT ====================
    
    def queue_assignment(self, vehicle_id: str, route_id: str, 
                        route_file: Optional[str] = None,
                        priority: int = 0,
                        scheduled_time: Optional[str] = None) -> bool:
        """
        Queue a route assignment for a vehicle.
        
        Args:
            vehicle_id: Target vehicle
            route_id: Route to assign
            route_file: Optional route file for fallback
            priority: Assignment priority (higher = more urgent)
            scheduled_time: Optional scheduled dispatch time
            
        Returns:
            True if queued successfully, False otherwise
        """
        try:
            # Check vehicle registration
            if vehicle_id not in self.vehicles:
                logger.error(f"Vehicle {vehicle_id} not registered with dispatcher")
                return False
            
            # Check queue capacity
            if len(self.assignment_queue) >= self.max_queue_size:
                logger.warning(f"Assignment queue full ({self.max_queue_size}), cannot queue assignment")
                return False
            
            # Load route coordinates
            route_coordinates = self.load_route(route_id, route_file)
            if not route_coordinates:
                logger.error(f"Failed to load route {route_id} for assignment")
                return False
            
            # Create assignment
            assignment = DispatchAssignment(
                vehicle_id=vehicle_id,
                route_id=route_id,
                route_coordinates=route_coordinates,
                priority=priority,
                scheduled_time=scheduled_time
            )
            
            # Add to queue (sorted by priority)
            self.assignment_queue.append(assignment)
            self.assignment_queue.sort(key=lambda x: x.priority, reverse=True)
            
            # Update queue statistics
            self.stats['queue_high_water_mark'] = max(
                self.stats['queue_high_water_mark'],
                len(self.assignment_queue)
            )
            
            logger.info(f"✅ Assignment queued: vehicle {vehicle_id} → route {route_id} (priority {priority})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue assignment: {e}")
            return False
    
    def process_assignment_queue(self) -> int:
        """
        Process pending assignments in the queue.
        
        Returns:
            Number of assignments processed
        """
        processed = 0
        failed_assignments = []
        
        try:
            for assignment in self.assignment_queue[:]:  # Create copy for iteration
                try:
                    if self._execute_assignment(assignment):
                        self.assignment_queue.remove(assignment)
                        processed += 1
                        self.stats['assignments_processed'] += 1
                    else:
                        failed_assignments.append(assignment)
                        self.stats['assignments_failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process assignment for vehicle {assignment.vehicle_id}: {e}")
                    failed_assignments.append(assignment)
                    self.stats['assignments_failed'] += 1
            
            # Remove failed assignments from queue
            for failed in failed_assignments:
                if failed in self.assignment_queue:
                    self.assignment_queue.remove(failed)
                    logger.warning(f"Removed failed assignment: vehicle {failed.vehicle_id} → route {failed.route_id}")
            
            if processed > 0:
                logger.info(f"✅ Processed {processed} assignments, {len(failed_assignments)} failed")
            
            return processed
            
        except Exception as e:
            logger.error(f"Failed to process assignment queue: {e}")
            return processed
    
    def _execute_assignment(self, assignment: DispatchAssignment) -> bool:
        """
        Execute a specific assignment.
        
        Args:
            assignment: Assignment to execute
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vehicle_id = assignment.vehicle_id
            
            # Check vehicle availability
            if vehicle_id not in self.vehicles:
                logger.error(f"Vehicle {vehicle_id} not registered")
                return False
            
            registration = self.vehicles[vehicle_id]
            if registration.status not in [VehicleStatus.AVAILABLE, VehicleStatus.RETURNING]:
                logger.warning(f"Vehicle {vehicle_id} not available (status: {registration.status})")
                return False
            
            # Get vehicle handler from DepotManager
            vehicle_handler = registration.vehicle_handler
            
            # Create new VehicleDriver with route
            try:
                new_navigator = VehicleDriver(
                    vehicle_id=vehicle_id,
                    route_coordinates=assignment.route_coordinates,
                    engine_buffer=vehicle_handler.get('_engine_buffer') or vehicle_handler['_engine'].buffer,
                    tick_time=0.1,  # Default tick time
                    mode="geodesic",
                    direction="outbound"
                )
                
                # Update vehicle handler with new navigator
                old_navigator = vehicle_handler.get('_navigator')
                if old_navigator:
                    old_navigator.off()  # Stop old navigator
                
                vehicle_handler['_navigator'] = new_navigator
                logger.info(f"✅ VehicleDriver updated for vehicle {vehicle_id} with route {assignment.route_id}")
                
            except Exception as e:
                logger.error(f"Failed to create VehicleDriver for vehicle {vehicle_id}: {e}")
                return False
            
            # Update registration status
            registration.status = VehicleStatus.ASSIGNED
            registration.current_assignment = assignment
            
            self.stats['vehicles_dispatched'] += 1
            
            logger.info(f"✅ Assignment executed: vehicle {vehicle_id} assigned route {assignment.route_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute assignment: {e}")
            return False
    
    # ==================== STATUS AND MONITORING ====================
    
    def get_vehicle_status(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific vehicle"""
        if vehicle_id not in self.vehicles:
            return None
        
        registration = self.vehicles[vehicle_id]
        return {
            'vehicle_id': vehicle_id,
            'status': registration.status.value,
            'registered_at': registration.registered_at,
            'current_assignment': {
                'route_id': registration.current_assignment.route_id,
                'priority': registration.current_assignment.priority,
                'created_at': registration.current_assignment.created_at
            } if registration.current_assignment else None
        }
    
    def get_dispatcher_status(self) -> Dict[str, Any]:
        """Get comprehensive dispatcher status"""
        return {
            'running': self.running,
            'vehicles_registered': len(self.vehicles),
            'vehicles_available': len([v for v in self.vehicles.values() 
                                    if v.status == VehicleStatus.AVAILABLE]),
            'assignments_queued': len(self.assignment_queue),
            'routes_cached': len(self.route_cache),
            'statistics': self.stats.copy(),
            'queue_status': {
                'size': len(self.assignment_queue),
                'max_size': self.max_queue_size,
                'high_water_mark': self.stats['queue_high_water_mark']
            }
        }
    
    def get_queue_summary(self) -> List[Dict[str, Any]]:
        """Get summary of current assignment queue"""
        return [
            {
                'vehicle_id': assignment.vehicle_id,
                'route_id': assignment.route_id,
                'priority': assignment.priority,
                'scheduled_time': assignment.scheduled_time,
                'created_at': assignment.created_at,
                'age_seconds': time.time() - assignment.created_at
            }
            for assignment in self.assignment_queue
        ]
    
    # ==================== LIFECYCLE MANAGEMENT ====================
    
    def start(self):
        """Start dispatcher operations"""
        try:
            self.running = True
            logger.info("✅ Dispatcher started")
            
        except Exception as e:
            logger.error(f"Failed to start dispatcher: {e}")
            raise
    
    def stop(self):
        """Stop dispatcher operations"""
        try:
            self.running = False
            
            # Clear assignment queue
            queue_size = len(self.assignment_queue)
            self.assignment_queue.clear()
            
            # Reset vehicle statuses to available
            for registration in self.vehicles.values():
                registration.status = VehicleStatus.AVAILABLE
                registration.current_assignment = None
            
            logger.info(f"✅ Dispatcher stopped (cleared {queue_size} queued assignments)")
            
        except Exception as e:
            logger.error(f"Failed to stop dispatcher: {e}")
    
    # ==================== UTILITY METHODS ====================
    
    def force_dispatch_vehicle(self, vehicle_id: str, route_id: str) -> bool:
        """Force immediate dispatch of a vehicle (for testing/debugging)"""
        try:
            # Create high-priority assignment
            success = self.queue_assignment(
                vehicle_id=vehicle_id,
                route_id=route_id,
                priority=999  # Highest priority
            )
            
            if success:
                # Process immediately
                processed = self.process_assignment_queue()
                if processed > 0:
                    logger.info(f"✅ Force dispatched vehicle {vehicle_id} to route {route_id}")
                    return True
            
            logger.error(f"Failed to force dispatch vehicle {vehicle_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to force dispatch: {e}")
            return False
    
    def get_available_vehicles(self) -> List[str]:
        """Get list of available vehicle IDs"""
        return [
            vehicle_id for vehicle_id, registration in self.vehicles.items()
            if registration.status == VehicleStatus.AVAILABLE
        ]
    
    def get_route_cache_info(self) -> Dict[str, Any]:
        """Get route cache information"""
        return {
            'enabled': self.enable_route_caching,
            'cached_routes': len(self.route_cache),
            'cache_keys': list(self.route_cache.keys()) if self.enable_route_caching else []
        }


# ---------------------------
# Testing support
# ---------------------------
if __name__ == "__main__":
    # Basic functionality test
    dispatcher = Dispatcher()
    print(f"Dispatcher initialized: {dispatcher.get_dispatcher_status()}")