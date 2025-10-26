"""
Simplified Spatial Zone Cache - Async-only implementation

Loads zones asynchronously without background threads to avoid event loop conflicts.
Uses spatial filtering to load only zones near active routes.

This version is simpler and more reliable than the threaded version.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import math

from shapely.geometry import Point, Polygon, LineString, shape


class SimpleSpatialZoneCache:
    """
    Async-only spatial zone cache (no threading).
    
    Loads zones with spatial filtering, all in the main event loop.
    Simpler and more reliable than threaded version.
    """
    
    def __init__(
        self,
        api_client: Any,
        country_id: int,
        buffer_km: float = 5.0,
        logger: Optional[logging.Logger] = None
    ):
        self.api_client = api_client
        self.country_id = country_id
        self.buffer_km = buffer_km
        self.logger = logger or logging.getLogger(__name__)
        
        # Zone storage
        self._population_zones: List[Dict[str, Any]] = []
        self._amenity_zones: List[Dict[str, Any]] = []
        self._last_loaded: Optional[datetime] = None
        
        # Spatial filter
        self._route_buffer: Optional[Polygon] = None
        
    def _create_route_buffer(
        self,
        coordinates: List[List[float]],
        buffer_km: float
    ) -> Polygon:
        """Create a buffer polygon around route coordinates"""
        if not coordinates:
            return Polygon()
        
        line = LineString([(coord[0], coord[1]) for coord in coordinates])
        
        # Buffer in degrees (approximate)
        avg_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        buffer_deg = buffer_km / (111.0 * math.cos(math.radians(avg_lat)))
        
        return line.buffer(buffer_deg)
    
    def _zone_intersects_buffer(self, zone_geometry: Dict) -> bool:
        """Check if zone intersects with route buffer"""
        if not self._route_buffer:
            return True
        
        try:
            zone_shape = shape(zone_geometry)
            return self._route_buffer.intersects(zone_shape)
        except Exception as e:
            self.logger.warning(f"Failed to check zone intersection: {e}")
            return False
    
    def _filter_zones_by_buffer(
        self,
        zones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter zones to only those within the route buffer"""
        if not self._route_buffer:
            return zones
        
        filtered = []
        for zone in zones:
            try:
                geometry = zone.get('geometry_geojson') or zone.get('geometry')
                if not geometry:
                    continue
                
                if self._zone_intersects_buffer(geometry):
                    filtered.append(zone)
            except Exception:
                continue
        
        return filtered
    
    async def initialize_for_route(
        self,
        route_coordinates: List[List[float]],
        depot_locations: Optional[List[Tuple[float, float]]] = None
    ):
        """Initialize and load zones for a specific route (async)"""
        self.logger.info(
            f"🚀 Loading zones with spatial filtering "
            f"({len(route_coordinates)} route points, buffer={self.buffer_km}km)"
        )
        
        # Create spatial buffer
        all_points = route_coordinates.copy()
        for lat, lon in (depot_locations or []):
            all_points.append([lon, lat])
        
        if all_points:
            self._route_buffer = self._create_route_buffer(all_points, self.buffer_km)
            self.logger.info(f"📍 Route buffer created (area={self._route_buffer.area:.6f} sq deg)")
        
        # Load zones from API (async, in main event loop)
        self.logger.info("⏳ Loading zones from API...")
        all_zones = await self.api_client.get_landuse_zones_by_country(self.country_id)
        places = await self.api_client.get_places_by_country(self.country_id)
        
        self.logger.info(f"🌍 Loaded {len(all_zones)} zones, {len(places)} places from API")
        
        # Categorize zones
        population_zones_raw = [
            z for z in all_zones
            if z.get('zone_type') in [
                'residential', 'commercial', 'industrial',
                'mixed_use', 'institutional'
            ]
        ]
        
        amenity_zones_raw = [
            z for z in all_zones
            if z.get('zone_type') in [
                'retail', 'education', 'healthcare',
                'recreation', 'transport'
            ]
        ]
        amenity_zones_raw.extend(places)
        
        self.logger.info(
            f"📊 Categorized: {len(population_zones_raw)} population, "
            f"{len(amenity_zones_raw)} amenity zones (before filtering)"
        )
        
        # Apply spatial filtering
        self._population_zones = self._filter_zones_by_buffer(population_zones_raw)
        self._amenity_zones = self._filter_zones_by_buffer(amenity_zones_raw)
        self._last_loaded = datetime.now()
        
        self.logger.info(
            f"🎯 Spatial filter (±{self.buffer_km}km): "
            f"{len(self._population_zones)} population zones, "
            f"{len(self._amenity_zones)} amenity zones"
        )
        
        self.logger.info("✅ Zone loading complete")
    
    async def get_cached_zones(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get cached zones"""
        return (self._population_zones.copy(), self._amenity_zones.copy())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'population_zones': len(self._population_zones),
            'amenity_zones': len(self._amenity_zones),
            'last_loaded': self._last_loaded.isoformat() if self._last_loaded else None,
            'buffer_km': self.buffer_km,
            'loading_complete': self._last_loaded is not None
        }
    
    async def shutdown(self):
        """Cleanup"""
        self.logger.info("🛑 Spatial zone cache shutdown")
