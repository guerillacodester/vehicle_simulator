"""
File-Based Route Provider
------------------------
Implementation of route provider that reads from GeoJSON files,
completely independent of fleet_manager database.
"""

import json
import os
import glob
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import logging

from world.vehicle_simulator.interfaces.route_provider import IRouteProvider

logger = logging.getLogger(__name__)


class FileRouteProvider(IRouteProvider):
    """
    Route provider that reads from GeoJSON files in data/routes directory.
    No database dependencies.
    """
    
    def __init__(self, routes_directory: str = "data/routes"):
        self.routes_directory = self._resolve_routes_directory(routes_directory)
        self._route_cache = {}
        self._load_routes()
    
    def _resolve_routes_directory(self, routes_directory: str) -> Path:
        """Resolve routes directory path relative to project root"""
        # Try as absolute path first
        path = Path(routes_directory)
        if path.is_absolute() and path.exists():
            return path
        
        # Try relative to current working directory
        if path.exists():
            return path.resolve()
        
        # Try relative to project root (go up from this file location)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Go up 4 levels to project root
        project_path = project_root / routes_directory
        if project_path.exists():
            return project_path.resolve()
        
        # Try alternative paths
        for alternative in ["../../data/routes", "../../../data/routes", "../../../../data/routes"]:
            alt_path = current_file.parent / alternative
            if alt_path.exists():
                return alt_path.resolve()
        
        # Default to original path (will show warning in _load_routes)
        return Path(routes_directory)
    
    def _load_routes(self):
        """Load all route files from directory"""
        if not self.routes_directory.exists():
            logger.warning(f"Routes directory not found: {self.routes_directory}")
            # Also log what we tried
            logger.debug(f"Attempted to find routes at: {self.routes_directory.absolute()}")
            return
        
        # Look for GeoJSON files
        for route_file in self.routes_directory.glob("*.geojson"):
            try:
                with open(route_file, 'r') as f:
                    route_data = json.load(f)
                
                # Extract route identifier from filename
                route_id = route_file.stem
                
                self._route_cache[route_id] = {
                    'file_path': str(route_file),
                    'data': route_data,
                    'name': route_data.get('properties', {}).get('name', route_id)
                }
                
                logger.debug(f"Loaded route: {route_id}")
                
            except Exception as e:
                logger.error(f"Failed to load route file {route_file}: {e}")
        
        logger.info(f"Loaded {len(self._route_cache)} routes from files")
    
    def get_route_coordinates(self, route_identifier: str) -> List[Tuple[float, float]]:
        """
        Get coordinates from GeoJSON file.
        
        Args:
            route_identifier: Route filename (without extension) or full path
            
        Returns:
            List of (longitude, latitude) coordinate tuples
        """
        # Handle full file path
        if route_identifier.endswith('.geojson'):
            route_identifier = Path(route_identifier).stem
        
        if route_identifier not in self._route_cache:
            # Try to load dynamically
            route_file = self.routes_directory / f"{route_identifier}.geojson"
            if route_file.exists():
                try:
                    with open(route_file, 'r') as f:
                        route_data = json.load(f)
                    self._route_cache[route_identifier] = {
                        'file_path': str(route_file),
                        'data': route_data,
                        'name': route_data.get('properties', {}).get('name', route_identifier)
                    }
                except Exception as e:
                    logger.error(f"Failed to load route {route_identifier}: {e}")
                    raise ValueError(f"Route '{route_identifier}' not found or invalid")
            else:
                raise ValueError(f"Route '{route_identifier}' not found")
        
        route_data = self._route_cache[route_identifier]['data']
        
        # Extract coordinates from GeoJSON
        coordinates = []
        
        if route_data.get('type') == 'FeatureCollection':
            # Multiple features
            for feature in route_data.get('features', []):
                coords = self._extract_coordinates(feature.get('geometry', {}))
                coordinates.extend(coords)
        elif route_data.get('type') == 'Feature':
            # Single feature
            coordinates = self._extract_coordinates(route_data.get('geometry', {}))
        else:
            # Direct geometry
            coordinates = self._extract_coordinates(route_data)
        
        return coordinates
    
    def _extract_coordinates(self, geometry: Dict) -> List[Tuple[float, float]]:
        """Extract coordinates from GeoJSON geometry"""
        geom_type = geometry.get('type', '')
        coords = geometry.get('coordinates', [])
        
        if geom_type == 'LineString':
            return [(lon, lat) for lon, lat in coords]
        elif geom_type == 'MultiLineString':
            result = []
            for line in coords:
                result.extend([(lon, lat) for lon, lat in line])
            return result
        elif geom_type == 'Point':
            return [(coords[0], coords[1])]
        else:
            logger.warning(f"Unsupported geometry type: {geom_type}")
            return []
    
    def get_route_info(self, route_identifier: str) -> Optional[Dict[str, Any]]:
        """Get route metadata"""
        if route_identifier.endswith('.geojson'):
            route_identifier = Path(route_identifier).stem
        
        if route_identifier not in self._route_cache:
            return None
        
        route_info = self._route_cache[route_identifier]
        properties = route_info['data'].get('properties', {})
        
        return {
            'id': route_identifier,
            'name': properties.get('name', route_identifier),
            'description': properties.get('description', ''),
            'file_path': route_info['file_path'],
            'properties': properties
        }
    
    def list_available_routes(self) -> List[str]:
        """List all available route identifiers"""
        return list(self._route_cache.keys())
