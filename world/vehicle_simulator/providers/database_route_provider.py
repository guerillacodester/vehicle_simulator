"""
Database Route Provider
----------------------
Implementation that uses fleet_manager database for route data.
This maintains compatibility with existing fleet_manager functionality.
"""

from typing import List, Tuple, Optional, Dict, Any
import logging

from interfaces.route_provider import IRouteProvider

logger = logging.getLogger(__name__)


class DatabaseRouteProvider(IRouteProvider):
    """
    Route provider that uses fleet_manager database.
    This is a wrapper around the existing FleetManager functionality.
    """
    
    def __init__(self):
        # Import here to avoid circular dependencies
        try:
            from world.fleet_manager.manager import FleetManager
            self._fleet_manager = FleetManager()
        except ImportError as e:
            logger.error(f"Fleet manager not available: {e}")
            raise RuntimeError("DatabaseRouteProvider requires fleet_manager to be available")
    
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, '_fleet_manager') and self._fleet_manager:
            self._fleet_manager.close()
    
    def get_route_coordinates(self, route_identifier: str) -> List[Tuple[float, float]]:
        """
        Get coordinates from database using fleet manager.
        
        Args:
            route_identifier: Route short_name in database
            
        Returns:
            List of (longitude, latitude) coordinate tuples
        """
        try:
            return self._fleet_manager.routes.get_route_coordinates(route_identifier)
        except Exception as e:
            logger.error(f"Failed to get route coordinates for {route_identifier}: {e}")
            raise ValueError(f"Route '{route_identifier}' not found in database")
    
    def get_route_info(self, route_identifier: str) -> Optional[Dict[str, Any]]:
        """Get route metadata from database"""
        try:
            # Query route information from database
            from world.fleet_manager.models import Route
            route = (
                self._fleet_manager.db.query(Route)
                .filter(Route.short_name == route_identifier)
                .first()
            )
            
            if not route:
                return None
            
            return {
                'id': route.route_id,
                'short_name': route.short_name,
                'name': route.name,
                'description': route.description,
                'agency_id': route.agency_id,
                'route_type': route.route_type,
                'color': route.color,
                'text_color': route.text_color
            }
            
        except Exception as e:
            logger.error(f"Failed to get route info for {route_identifier}: {e}")
            return None
    
    def list_available_routes(self) -> List[str]:
        """List all available route short_names from database"""
        try:
            from world.fleet_manager.models import Route
            routes = self._fleet_manager.db.query(Route.short_name).all()
            return [route.short_name for route in routes if route.short_name]
        except Exception as e:
            logger.error(f"Failed to list routes: {e}")
            return []
