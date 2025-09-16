"""
Route Queue Builder for organizing vehicles by route assignments.

Manages vehicle queues for depot operations, organizing vehicles by their assigned routes
and providing efficient access patterns for dispatch operations.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from .interfaces import VehicleAssignment, DriverAssignment, RouteInfo


@dataclass
class RouteQueue:
    """A queue of vehicles assigned to a specific route."""
    route_id: str
    route_name: str
    route_type: str
    vehicles: deque = field(default_factory=deque)  # Ordered queue of VehicleAssignment
    active_count: int = 0
    waiting_count: int = 0
    total_capacity: int = 0
    geometry_available: bool = False
    
    def add_vehicle(self, vehicle: VehicleAssignment) -> None:
        """Add a vehicle to this route queue."""
        self.vehicles.append(vehicle)
        self.waiting_count += 1
        # Estimate capacity (typical ZR van = 11 passengers)
        self.total_capacity += 11
    
    def get_next_vehicle(self) -> Optional[VehicleAssignment]:
        """Get the next vehicle in queue for dispatch."""
        if self.vehicles:
            vehicle = self.vehicles.popleft()
            self.waiting_count = max(0, self.waiting_count - 1)
            self.active_count += 1
            return vehicle
        return None
    
    def mark_vehicle_returned(self) -> None:
        """Mark that a vehicle has returned from service."""
        self.active_count = max(0, self.active_count - 1)
    
    def get_queue_status(self) -> Dict[str, any]:
        """Get current queue status for monitoring."""
        return {
            'route_id': self.route_id,
            'route_name': self.route_name,
            'route_type': self.route_type,
            'vehicles_waiting': self.waiting_count,
            'vehicles_active': self.active_count,
            'total_vehicles': len(self.vehicles) + self.active_count,
            'total_capacity': self.total_capacity,
            'geometry_available': self.geometry_available
        }


class RouteQueueBuilder:
    """
    Builds and manages route-based vehicle queues for depot operations.
    
    Organizes vehicles by their route assignments, providing efficient access
    for dispatch operations and route coordination.
    """
    
    def __init__(self, component_name: str = "RouteQueueBuilder"):
        self.component_name = component_name
        self.route_queues: Dict[str, RouteQueue] = {}
        self.vehicle_to_route: Dict[str, str] = {}  # vehicle_id -> route_id mapping
        self.driver_to_route: Dict[str, str] = {}   # driver_id -> route_id mapping
        self.unassigned_vehicles: List[VehicleAssignment] = []
        self.route_info_cache: Dict[str, RouteInfo] = {}
        self.initialized = False
        
        logging.info(f"[{self.component_name}] Route queue builder initialized")
    
    def build_queues(self, 
                     vehicle_assignments: List[VehicleAssignment],
                     driver_assignments: List[DriverAssignment],
                     route_info: List[RouteInfo]) -> bool:
        """
        Build route queues from vehicle and driver assignments.
        
        Args:
            vehicle_assignments: List of vehicle assignments from API
            driver_assignments: List of driver assignments from API  
            route_info: List of route information from API
            
        Returns:
            bool: True if queues built successfully
        """
        try:
            # Clear existing queues
            self.route_queues.clear()
            self.vehicle_to_route.clear()
            self.driver_to_route.clear()
            self.unassigned_vehicles.clear()
            self.route_info_cache.clear()
            
            # Cache route information
            for route in route_info:
                self.route_info_cache[route.route_id] = route
                logging.debug(f"[{self.component_name}] Cached route info: {route.route_name} ({route.route_id})")
            
            # Create route queues from route info
            for route_id, route in self.route_info_cache.items():
                queue = RouteQueue(
                    route_id=route_id,
                    route_name=route.route_name,
                    route_type=route.route_type,
                    geometry_available=(route.geometry is not None)
                )
                self.route_queues[route_id] = queue
                logging.debug(f"[{self.component_name}] Created queue for route: {route.route_name}")
            
            # Build driver-to-route mapping
            for driver in driver_assignments:
                if driver.route_id:
                    self.driver_to_route[driver.driver_id] = driver.route_id
                    logging.debug(f"[{self.component_name}] Mapped driver {driver.driver_name} to route {driver.route_id}")
            
            # Organize vehicles into route queues
            assigned_count = 0
            unassigned_count = 0
            excluded_reasons = []
            
            for vehicle in vehicle_assignments:
                # Try to find route assignment through driver
                route_id = None
                if vehicle.route_id:
                    route_id = vehicle.route_id
                elif vehicle.driver_id and vehicle.driver_id in self.driver_to_route:
                    route_id = self.driver_to_route[vehicle.driver_id]
                
                if route_id and route_id in self.route_queues:
                    # Assign vehicle to route queue
                    self.route_queues[route_id].add_vehicle(vehicle)
                    self.vehicle_to_route[vehicle.vehicle_id] = route_id
                    assigned_count += 1
                    
                    route_name = self.route_queues[route_id].route_name
                    vehicle_reg = vehicle.vehicle_reg_code or vehicle.vehicle_id[:8]
                    logging.debug(f"[{self.component_name}] Assigned vehicle {vehicle_reg} to route {route_name}")
                else:
                    # Vehicle has no route assignment - determine why
                    self.unassigned_vehicles.append(vehicle)
                    unassigned_count += 1
                    vehicle_reg = vehicle.vehicle_reg_code or vehicle.vehicle_id[:8]
                    
                    # Determine exclusion reason
                    if not vehicle.route_id:
                        reason = f"Vehicle {vehicle_reg}: No route assignment"
                        excluded_reasons.append(reason)
                        logging.debug(f"[{self.component_name}] {reason}")
                    elif route_id not in self.route_queues:
                        reason = f"Vehicle {vehicle_reg}: Route '{route_id}' not found in system"
                        excluded_reasons.append(reason)
                        logging.debug(f"[{self.component_name}] {reason}")
                    else:
                        reason = f"Vehicle {vehicle_reg}: Unknown assignment issue"
                        excluded_reasons.append(reason)
                        logging.debug(f"[{self.component_name}] {reason}")
            
            # Log queue building results
            queue_count = len(self.route_queues)
            logging.info(f"[{self.component_name}] Route queues built successfully:")
            logging.info(f"  • {queue_count} route queues created")
            logging.info(f"  • {assigned_count} vehicles assigned to routes")
            logging.info(f"  • {unassigned_count} unassigned vehicles")
            
            # Log individual queue status
            for queue in self.route_queues.values():
                if queue.waiting_count > 0:
                    logging.info(f"  • Route {queue.route_name}: {queue.waiting_count} vehicles, capacity {queue.total_capacity}")
            
            # Log excluded vehicles and reasons
            if excluded_reasons:
                logging.info(f"[{self.component_name}] Excluded vehicles:")
                for reason in excluded_reasons:
                    logging.info(f"  • {reason}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Failed to build route queues: {e}")
            return False
    
    def get_route_queue(self, route_id: str) -> Optional[RouteQueue]:
        """Get the queue for a specific route."""
        return self.route_queues.get(route_id)
    
    def get_route_by_name(self, route_name: str) -> Optional[RouteQueue]:
        """Get the queue for a route by name."""
        for queue in self.route_queues.values():
            if queue.route_name.lower() == route_name.lower():
                return queue
        return None
    
    def get_next_vehicle_for_route(self, route_id: str) -> Optional[VehicleAssignment]:
        """Get the next available vehicle for a specific route."""
        queue = self.get_route_queue(route_id)
        if queue:
            return queue.get_next_vehicle()
        return None
    
    def get_all_queue_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all route queues."""
        status = {}
        for route_id, queue in self.route_queues.items():
            status[route_id] = queue.get_queue_status()
        return status
    
    def get_summary_statistics(self) -> Dict[str, any]:
        """Get summary statistics for all queues."""
        total_vehicles = sum(len(q.vehicles) + q.active_count for q in self.route_queues.values())
        total_waiting = sum(q.waiting_count for q in self.route_queues.values())
        total_active = sum(q.active_count for q in self.route_queues.values())
        total_capacity = sum(q.total_capacity for q in self.route_queues.values())
        routes_with_vehicles = len([q for q in self.route_queues.values() if q.waiting_count > 0])
        
        return {
            'total_routes': len(self.route_queues),
            'routes_with_vehicles': routes_with_vehicles,
            'total_vehicles': total_vehicles,
            'vehicles_waiting': total_waiting,
            'vehicles_active': total_active,
            'unassigned_vehicles': len(self.unassigned_vehicles),
            'total_passenger_capacity': total_capacity,
            'initialized': self.initialized
        }
    
    def get_route_names(self) -> List[str]:
        """Get list of all route names with vehicles."""
        return [queue.route_name for queue in self.route_queues.values() if queue.waiting_count > 0]
    
    def mark_vehicle_returned(self, vehicle_id: str) -> bool:
        """Mark a vehicle as returned from service."""
        route_id = self.vehicle_to_route.get(vehicle_id)
        if route_id and route_id in self.route_queues:
            self.route_queues[route_id].mark_vehicle_returned()
            return True
        return False
    
    def reassign_vehicle(self, vehicle_id: str, new_route_id: str) -> bool:
        """Reassign a vehicle to a different route."""
        # Remove from current route if assigned
        current_route_id = self.vehicle_to_route.get(vehicle_id)
        if current_route_id and current_route_id in self.route_queues:
            # Would need to implement vehicle removal from queue
            logging.warning(f"[{self.component_name}] Vehicle reassignment not fully implemented")
            return False
        
        # Add to new route (would need VehicleAssignment object)
        if new_route_id in self.route_queues:
            self.vehicle_to_route[vehicle_id] = new_route_id
            return True
        
        return False