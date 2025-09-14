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
            
            # Safety Check: Verify route buffer for assigned routes only
            stats = await self.dispatcher.get_route_buffer_stats()
            if stats.get('total_routes', 0) == 0:
                logging.info(f"[{self.component_name}] 🛡️ SAFETY: Route buffer empty - populating only with vehicle-assigned routes")
                logging.info(f"[{self.component_name}] This ensures passengers spawn only for operational routes: {route_ids}")
                success = await self.dispatcher.populate_route_buffer(route_ids)
                if not success:
                    logging.error(f"[{self.component_name}] ❌ Failed to populate route buffer - no passengers will spawn")
                    return False
                else:
                    # Verify population was successful
                    new_stats = await self.dispatcher.get_route_buffer_stats()
                    logging.info(f"[{self.component_name}] ✅ Route buffer populated: {new_stats['total_routes']} routes, {new_stats['total_gps_points']} GPS points")
            else:
                logging.info(f"[{self.component_name}] ✅ Route buffer already populated: {stats['total_routes']} routes, {stats['total_gps_points']} GPS points")
            
            # Additional Safety: Validate that all requested routes are available in buffer
            # Re-fetch stats after potential population
            final_stats = await self.dispatcher.get_route_buffer_stats()
            available_routes = final_stats.get('routes', [])
            missing_routes = [route_id for route_id in route_ids if route_id not in available_routes]
            if missing_routes:
                logging.warning(f"[{self.component_name}] ⚠️ SAFETY: Some routes missing from buffer: {missing_routes}")
                logging.info(f"[{self.component_name}] Available routes in buffer: {available_routes}")
                logging.info(f"[{self.component_name}] Passengers will only spawn for available routes: {[r for r in route_ids if r in available_routes]}")
            else:
                logging.info(f"[{self.component_name}] ✅ All assigned routes ({len(route_ids)}) validated in buffer")
            
            # Final safety validation
            safety_report = await self.validate_route_safety(route_ids)
            if not safety_report['safe_to_spawn']:
                logging.error(f"[{self.component_name}] 🚨 SAFETY VIOLATION: Cannot spawn passengers")
                logging.error(f"[{self.component_name}] Missing routes: {safety_report['missing_routes']}")
                return False
            
            logging.info(f"[{self.component_name}] 🛡️ SAFETY VALIDATED: {safety_report['routes_in_buffer']}/{safety_report['total_requested_routes']} routes ready")
            
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

    async def validate_route_safety(self, route_ids: List[str]) -> Dict[str, Any]:
        """Validate that passenger service is only using routes with assigned vehicles."""
        try:
            safety_report = {
                'total_requested_routes': len(route_ids),
                'routes_in_buffer': 0,
                'missing_routes': [],
                'safe_to_spawn': False,
                'gps_points_available': 0
            }
            
            if not self.dispatcher:
                safety_report['error'] = 'No dispatcher available'
                return safety_report
            
            # Check route buffer status
            buffer_stats = await self.dispatcher.get_route_buffer_stats()
            available_routes = buffer_stats.get('routes', [])
            
            safety_report['routes_in_buffer'] = len(available_routes)
            safety_report['missing_routes'] = [r for r in route_ids if r not in available_routes]
            
            # Log safety status with clear indicators
            if len(safety_report['missing_routes']) == 0:
                logging.info(f"✅ SAFETY: All driver routes available in buffer: {route_ids}")
            else:
                logging.warning(f"⚠️ SAFETY: Some routes missing from buffer: {safety_report['missing_routes']}")
                logging.info(f"🛡️ SAFETY: Available routes in buffer: {available_routes}")
                logging.info(f"🛡️ SAFETY: Requested routes: {route_ids}")
            safety_report['gps_points_available'] = buffer_stats.get('total_gps_points', 0)
            safety_report['safe_to_spawn'] = len(safety_report['missing_routes']) == 0
            
            return safety_report
            
        except Exception as e:
            return {'error': str(e), 'safe_to_spawn': False}

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