#!/usr/bin/env python3
"""
Route Coordinator
-----------------
Utility to load route coordinates from various sources (database, files)
and provide them in the format expected by Navigator.

This maintains compatibility for legacy code while keeping Navigator clean.
"""

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def get_route_coordinates(
    route_id: Optional[str] = None,
    route_file: Optional[str] = None,
    direction: str = "outbound"
) -> List[Tuple[float, float]]:
    """
    Load route coordinates from database or file.
    
    Args:
        route_id: Route identifier for database lookup
        route_file: Path to GeoJSON route file
        direction: "outbound" or "inbound" (reverses coordinates)
    
    Returns:
        List of (longitude, latitude) coordinate pairs
    
    Raises:
        ValueError: If no valid route source provided or route not found
    """
    coordinates = []
    
    # Try database first if route_id provided
    if route_id:
        try:
            from world.vehicle_simulator.providers.database_route_provider import DatabaseRouteProvider
            provider = DatabaseRouteProvider()
            coordinates = provider.get_route_coordinates(route_id)
            logger.info(f"Loaded route {route_id} from database ({len(coordinates)} coordinates)")
        except Exception as e:
            logger.warning(f"Failed to load route {route_id} from database: {e}")
            # Fall back to file if available
            if route_file:
                logger.info(f"Falling back to file route: {route_file}")
            else:
                raise ValueError(f"Route '{route_id}' not found in database and no file fallback provided")
    
    # Load from file if no database coordinates or if only file provided
    if not coordinates and route_file:
        try:
            from world.vehicle_simulator.utils.routes.route_loader import load_route_coordinates
            coordinates = load_route_coordinates(route_file)
            logger.info(f"Loaded route from file {route_file} ({len(coordinates)} coordinates)")
        except Exception as e:
            logger.error(f"Failed to load route file {route_file}: {e}")
            raise ValueError(f"Could not load route from file: {route_file}")
    
    # Check if we have coordinates
    if not coordinates:
        raise ValueError("No route coordinates could be loaded from any source")
    
    # Reverse for inbound direction
    if direction == "inbound":
        coordinates = list(reversed(coordinates))
        logger.debug(f"Route coordinates reversed for inbound direction")
    
    return coordinates


def create_navigator_with_route(
    vehicle_id: str,
    route_id: Optional[str] = None,
    route_file: Optional[str] = None,
    engine_buffer=None,
    tick_time: float = 0.1,
    mode: str = "geodesic",
    direction: str = "outbound"
):
    """
    Convenience function to create Navigator with route coordinates loaded from database or file.
    
    This provides backward compatibility for code that was using the old Navigator interface.
    """
    from world.vehicle_simulator.vehicle.driver.navigation.navigator import Navigator
    
    # Load route coordinates
    coordinates = get_route_coordinates(route_id, route_file, direction)
    
    # Create Navigator with coordinates
    return Navigator(
        vehicle_id=vehicle_id,
        route_coordinates=coordinates,
        engine_buffer=engine_buffer,
        tick_time=tick_time,
        mode=mode,
        direction=direction
    )
