"""
Fleet Manager Communication
---------------------------
Handles communication between vehicles and fleet manager for route dispatch.
Manages vehicle-full notifications and route assignment responses.
"""

import logging
import requests
import json
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

logger = logging.getLogger(__name__)


class FleetManagerCommunicator:
    """
    Manages communication with fleet manager for vehicle operations.
    Handles route requests, vehicle status updates, and operational coordination.
    """
    
    def __init__(self, fleet_manager_url: str = "http://localhost:8000"):
        self.fleet_manager_url = fleet_manager_url
        self.api_base = f"{fleet_manager_url}/api/v1"
        self.route_dispatch_callbacks: Dict[str, Callable] = {}
        
    def register_route_dispatch_callback(self, vehicle_id: str, callback: Callable):
        """Register callback for when route is received for vehicle"""
        self.route_dispatch_callbacks[vehicle_id] = callback
        logger.info(f"📡 Registered route dispatch callback for vehicle {vehicle_id}")
    
    def notify_vehicle_full(self, vehicle_id: str, passenger_count: int, capacity: int) -> bool:
        """
        Notify fleet manager that vehicle is full and ready for route dispatch.
        
        Args:
            vehicle_id: ID of the full vehicle
            passenger_count: Current passenger count
            capacity: Vehicle capacity
            
        Returns:
            bool: Success of notification
        """
        try:
            payload = {
                'vehicle_id': vehicle_id,
                'passenger_count': passenger_count,
                'capacity': capacity,
                'status': 'full',
                'timestamp': datetime.now().isoformat(),
                'request_type': 'route_dispatch'
            }
            
            # Send notification to fleet manager
            response = requests.post(
                f"{self.api_base}/fleet/vehicle/{vehicle_id}/passenger-full",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"📡 ✅ Fleet Manager notified: Vehicle {vehicle_id} is full ({passenger_count}/{capacity})")
                
                # Process route response immediately if provided
                route_data = response.json().get('route_data')
                if route_data:
                    self._handle_route_dispatch(vehicle_id, route_data)
                    
                return True
            else:
                logger.error(f"📡 ❌ Fleet Manager notification failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"📡 ❌ Fleet Manager communication error: {e}")
            return False
    
    def request_route_assignment(self, vehicle_id: str, vehicle_type: str = "zr_van") -> Optional[Dict[str, Any]]:
        """
        Request route assignment from fleet manager.
        
        Args:
            vehicle_id: ID of requesting vehicle
            vehicle_type: Type of vehicle (zr_van, bus, etc.)
            
        Returns:
            Route data if successful, None otherwise
        """
        try:
            payload = {
                'vehicle_id': vehicle_id,
                'vehicle_type': vehicle_type,
                'timestamp': datetime.now().isoformat(),
                'status': 'requesting_route'
            }
            
            response = requests.post(
                f"{self.api_base}/fleet/vehicle/{vehicle_id}/request-route",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                route_data = response.json()
                logger.info(f"📡 ✅ Route received for vehicle {vehicle_id}: {route_data.get('route_name', 'Unknown')}")
                
                # Trigger callback if registered
                self._handle_route_dispatch(vehicle_id, route_data)
                return route_data
            else:
                logger.error(f"📡 ❌ Route request failed: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"📡 ❌ Route request error: {e}")
            return None
    
    def _handle_route_dispatch(self, vehicle_id: str, route_data: Dict[str, Any]):
        """Handle route dispatch response from fleet manager"""
        if vehicle_id in self.route_dispatch_callbacks:
            callback = self.route_dispatch_callbacks[vehicle_id]
            try:
                callback(vehicle_id, route_data)
                logger.info(f"📡 ✅ Route dispatched to vehicle {vehicle_id}")
            except Exception as e:
                logger.error(f"📡 ❌ Route dispatch callback error: {e}")
    
    def update_vehicle_state(self, vehicle_id: str, state: str, **kwargs) -> bool:
        """
        Update vehicle state in fleet manager.
        
        Args:
            vehicle_id: ID of vehicle
            state: New vehicle state
            **kwargs: Additional state data
            
        Returns:
            bool: Success of update
        """
        try:
            payload = {
                'vehicle_id': vehicle_id,
                'state': state,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            }
            
            response = requests.put(
                f"{self.api_base}/fleet/vehicle/{vehicle_id}/state",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"📡 ✅ Vehicle {vehicle_id} state updated to {state}")
                return True
            else:
                logger.error(f"📡 ❌ State update failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"📡 ❌ State update error: {e}")
            return False
    
    def notify_journey_completed(self, vehicle_id: str, journey_data: Dict[str, Any]) -> bool:
        """
        Notify fleet manager that vehicle has completed its journey.
        
        Args:
            vehicle_id: ID of vehicle
            journey_data: Journey completion data
            
        Returns:
            bool: Success of notification
        """
        try:
            payload = {
                'vehicle_id': vehicle_id,
                'status': 'journey_completed',
                'timestamp': datetime.now().isoformat(),
                **journey_data
            }
            
            response = requests.post(
                f"{self.api_base}/fleet/vehicle/{vehicle_id}/completed-journey",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"📡 ✅ Journey completion reported for vehicle {vehicle_id}")
                return True
            else:
                logger.error(f"📡 ❌ Journey completion notification failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"📡 ❌ Journey completion error: {e}")
            return False
    
    def get_available_routes(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of available routes from fleet manager"""
        try:
            response = requests.get(f"{self.api_base}/routes", timeout=10)
            
            if response.status_code == 200:
                routes = response.json()
                logger.info(f"📡 ✅ Retrieved {len(routes)} available routes")
                return routes
            else:
                logger.error(f"📡 ❌ Failed to get routes: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"📡 ❌ Route retrieval error: {e}")
            return None


class MockFleetManagerCommunicator(FleetManagerCommunicator):
    """
    Mock implementation for testing without actual fleet manager.
    Simulates fleet manager responses for development and testing.
    """
    
    def __init__(self):
        # Don't call parent __init__ to avoid actual HTTP setup
        self.route_dispatch_callbacks: Dict[str, Callable] = {}
        self.mock_routes = {
            'route_1': {
                'route_id': 'route_1',
                'route_name': 'Bridgetown to Oistins',
                'origin': 'Bridgetown Terminal',
                'destination': 'Oistins Terminal',
                'coordinates': [
                    (13.0969, -59.6145),  # Bridgetown
                    (13.0969, -59.6000),  # Intermediate
                    (13.0731, -59.5379)   # Oistins
                ],
                'stops': [
                    {'name': 'Bridgetown Terminal', 'lat': 13.0969, 'lng': -59.6145},
                    {'name': 'Hastings', 'lat': 13.0900, 'lng': -59.5800},
                    {'name': 'Worthing', 'lat': 13.0850, 'lng': -59.5600},
                    {'name': 'Oistins Terminal', 'lat': 13.0731, 'lng': -59.5379}
                ],
                'distance_km': 12.5,
                'estimated_duration_minutes': 25
            },
            'route_2': {
                'route_id': 'route_2',
                'route_name': 'Bridgetown to Speightstown',
                'origin': 'Bridgetown Terminal',
                'destination': 'Speightstown Terminal',
                'coordinates': [
                    (13.0969, -59.6145),  # Bridgetown
                    (13.1500, -59.6200),  # Intermediate
                    (13.2500, -59.6300)   # Speightstown
                ],
                'stops': [
                    {'name': 'Bridgetown Terminal', 'lat': 13.0969, 'lng': -59.6145},
                    {'name': 'St. Michael', 'lat': 13.1200, 'lng': -59.6180},
                    {'name': 'St. James', 'lat': 13.1800, 'lng': -59.6250},
                    {'name': 'Speightstown Terminal', 'lat': 13.2500, 'lng': -59.6300}
                ],
                'distance_km': 18.2,
                'estimated_duration_minutes': 35
            }
        }
        
    def notify_vehicle_full(self, vehicle_id: str, passenger_count: int, capacity: int) -> bool:
        """Mock notification that immediately responds with route"""
        logger.info(f"📡 🎭 MOCK: Vehicle {vehicle_id} full notification ({passenger_count}/{capacity})")
        
        # Simulate route assignment
        import random
        route_id = random.choice(list(self.mock_routes.keys()))
        route_data = self.mock_routes[route_id].copy()
        
        # Trigger route dispatch
        self._handle_route_dispatch(vehicle_id, route_data)
        return True
    
    def request_route_assignment(self, vehicle_id: str, vehicle_type: str = "zr_van") -> Optional[Dict[str, Any]]:
        """Mock route assignment"""
        import random
        route_id = random.choice(list(self.mock_routes.keys()))
        route_data = self.mock_routes[route_id].copy()
        
        logger.info(f"📡 🎭 MOCK: Route {route_id} assigned to vehicle {vehicle_id}")
        self._handle_route_dispatch(vehicle_id, route_data)
        return route_data
    
    def update_vehicle_state(self, vehicle_id: str, state: str, **kwargs) -> bool:
        """Mock state update"""
        logger.info(f"📡 🎭 MOCK: Vehicle {vehicle_id} state updated to {state}")
        return True
    
    def notify_journey_completed(self, vehicle_id: str, journey_data: Dict[str, Any]) -> bool:
        """Mock journey completion"""
        logger.info(f"📡 🎭 MOCK: Vehicle {vehicle_id} journey completed")
        return True
    
    def get_available_routes(self) -> Optional[List[Dict[str, Any]]]:
        """Mock available routes"""
        return list(self.mock_routes.values())
