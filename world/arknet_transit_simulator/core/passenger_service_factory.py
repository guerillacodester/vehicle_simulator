"""
Passenger Service Factory for Depot-Level Integration

This factory creates and manages the DynamicPassengerService at the depot level,
integrating with the dispatcher's route buffer for GPS-aware passenger spawning.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from ..passenger_modeler.passenger_service import DynamicPassengerService
from ..passenger_modeler.passenger_events import PassengerBuffer
from .interfaces import IDispatcher
from ..config.config_loader import ConfigLoader

class PassengerServiceFactory:
    """Factory for creating depot-level passenger services with dispatcher integration."""
    
    def __init__(self, component_name: str = "PassengerServiceFactory"):
        self.component_name = component_name
        self.config = ConfigLoader()
        self.passenger_service: Optional[DynamicPassengerService] = None
        self.dispatcher: Optional[IDispatcher] = None
        self.initialized = False
        
    def set_dispatcher(self, dispatcher: IDispatcher):
        """Set dispatcher for route buffer queries."""
        self.dispatcher = dispatcher
        
    async def create_passenger_service(self, route_ids: List[str]) -> bool:
        """Create passenger service after routes have been assigned to vehicles."""
        if not self.dispatcher:
            logging.error(f"[{self.component_name}] No dispatcher configured")
            return False
            
        try:
            # Get passenger service configuration
            config = self._load_passenger_config()
            
            # Verify route buffer is populated
            stats = await self.dispatcher.get_route_buffer_stats()
            if stats.get('total_routes', 0) == 0:
                logging.warning(f"[{self.component_name}] Route buffer is empty, populating with {len(route_ids)} routes")
                success = await self.dispatcher.populate_route_buffer(route_ids)
                if not success:
                    logging.error(f"[{self.component_name}] Failed to populate route buffer")
                    return False
            
            # Create passenger buffer with configuration
            passenger_buffer = PassengerBuffer(
                max_size=config['max_events_buffer'],
                enable_priority=True
            )
            
            # Create passenger service with depot-level integration
            self.passenger_service = DynamicPassengerService(
                route_ids=route_ids,
                max_memory_mb=config['memory_limit_mb'],  # Use correct parameter name
                dispatcher=self.dispatcher,  # NEW: Pass dispatcher for route queries
                walking_distance_km=config['walking_distance_km']  # NEW: GPS proximity
            )
            
            # Start the passenger service
            await self.passenger_service.start_service()
            self.initialized = True
            
            # Log service creation
            buffer_stats = await self.dispatcher.get_route_buffer_stats()
            logging.info(f"[{self.component_name}] Passenger service created for {len(route_ids)} routes")
            logging.info(f"[{self.component_name}] Route buffer: {buffer_stats['total_routes']} routes, {buffer_stats['total_gps_points']} GPS points")
            logging.info(f"[{self.component_name}] Walking distance: {config['walking_distance_km']}km, Max passengers: {config['max_passengers_total']}")
            
            return True
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Failed to create passenger service: {str(e)}")
            return False
    
    async def stop_passenger_service(self) -> bool:
        """Stop the passenger service gracefully."""
        try:
            if self.passenger_service:
                await self.passenger_service.stop_service()
                self.passenger_service = None
                self.initialized = False
                logging.info(f"[{self.component_name}] Passenger service stopped")
            return True
        except Exception as e:
            logging.error(f"[{self.component_name}] Error stopping passenger service: {str(e)}")
            return False
    
    def _load_passenger_config(self) -> Dict[str, Any]:
        """Load passenger service configuration from config.ini."""
        try:
            # Load passenger service specific configuration using correct ConfigLoader methods
            max_passengers_per_route = int(self.config.get_config_value('passenger_service', 'max_passengers_per_route', 50))
            memory_limit_mb = int(self.config.get_config_value('passenger_service', 'memory_limit_mb', 1))
            walking_distance_km = float(self.config.get_config_value('passenger_service', 'walking_distance_km', 0.5))
            max_concurrent_spawns = int(self.config.get_config_value('passenger_service', 'max_concurrent_spawns', 3))
            
            # Calculate total passengers based on route count (will be set when service is created)
            # For now, use a reasonable default
            max_passengers_total = max_passengers_per_route * 10  # Assume max 10 routes initially
            
            config = {
                'max_passengers_per_route': max_passengers_per_route,
                'max_passengers_total': max_passengers_total,
                'memory_limit_mb': memory_limit_mb,
                'walking_distance_km': walking_distance_km,
                'max_concurrent_spawns': max_concurrent_spawns,
                'max_events_buffer': max_concurrent_spawns * 5  # Buffer for events
            }
            
            logging.debug(f"[{self.component_name}] Loaded configuration: {config}")
            return config
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Error loading configuration: {str(e)}")
            # Return safe defaults
            return {
                'max_passengers_per_route': 20,
                'max_passengers_total': 100,
                'memory_limit_mb': 1,
                'walking_distance_km': 0.5,
                'max_concurrent_spawns': 3,
                'max_events_buffer': 15
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get passenger service status for monitoring."""
        try:
            if not self.passenger_service:
                return {
                    'initialized': False,
                    'running': False,
                    'passengers': 0,
                    'routes': 0
                }
            
            # Get basic status from passenger service
            return {
                'initialized': self.initialized,
                'running': self.passenger_service.is_running,
                'passengers': len(self.passenger_service.active_passengers),
                'routes': len(self.passenger_service.route_ids),
                'memory_usage_mb': self.passenger_service.stats.memory_usage_mb,
                'dispatcher_connected': self.dispatcher is not None
            }
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Error getting service status: {str(e)}")
            return {'error': str(e)}

    async def query_passengers_near_gps(self, lat: float, lon: float, radius_km: float = None) -> List[Dict[str, Any]]:
        """Query passengers near GPS coordinates using dispatcher route buffer."""
        if not self.dispatcher or not self.passenger_service:
            return []
        
        try:
            # Use configured walking distance if not specified
            if radius_km is None:
                config = self._load_passenger_config()
                radius_km = config['walking_distance_km']
            
            # Query dispatcher for nearby routes
            nearby_routes = await self.dispatcher.query_routes_by_gps(lat, lon, radius_km)
            
            # Get passengers from those routes
            passengers = []
            for route_info in nearby_routes:
                # Filter active passengers by route
                route_passengers = [
                    p for p in self.passenger_service.active_passengers.values() 
                    if p.get('route_id') == route_info.route_id
                ]
                passengers.extend(route_passengers)
            
            logging.debug(f"[{self.component_name}] Found {len(passengers)} passengers near ({lat:.6f}, {lon:.6f}) within {radius_km}km")
            return passengers
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Error querying passengers near GPS: {str(e)}")
            return []