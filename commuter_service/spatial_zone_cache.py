"""
Spatial Zone Cache - Background Zone Loading with Spatial Filtering

This module provides background, multithreaded zone loading with spatial filtering
to prevent blocking the main event loop. Zones are loaded only within a buffer
distance of active routes and depots.

Architecture:
- Background thread for zone loading
- Spatial filtering using bounding box + distance checks
- LRU caching of filtered zones
- Async interface for main thread
- Thread-safe zone access

Usage:
    cache = SpatialZoneCache(
        api_client=strapi_client,
        country_id=1,
        buffer_km=5.0  # Only load zones within 5km of route
    )
    
    await cache.initialize_for_route(route_coordinates)
    zones = await cache.get_cached_zones()  # Non-blocking
"""

import asyncio
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import math

from shapely.geometry import Point, Polygon, MultiPolygon, LineString, shape
from shapely.ops import unary_union


class SpatialZoneCache:
    """
    Background zone loader with spatial filtering.
    
    Loads zones in a separate thread to avoid blocking the main event loop.
    Only loads zones within buffer distance of active routes/depots.
    """
    
    def __init__(
        self,
        api_client: Any,  # StrapiApiClient instance
        country_id: int,
        buffer_km: float = 5.0,
        cache_ttl_minutes: int = 60,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize spatial zone cache.
        
        Args:
            api_client: StrapiApiClient for fetching zone data
            country_id: Country ID to filter zones
            buffer_km: Buffer distance in kilometers around routes/depots
            cache_ttl_minutes: How long to cache zones before refresh
            logger: Logger instance
        """
        self.api_client = api_client
        self.country_id = country_id
        self.buffer_km = buffer_km
        self.cache_ttl_minutes = cache_ttl_minutes
        self.logger = logger or logging.getLogger(__name__)
        
        # Thread-safe zone storage
        self._zones_lock = threading.Lock()
        self._population_zones: List[Dict[str, Any]] = []
        self._amenity_zones: List[Dict[str, Any]] = []
        self._last_loaded: Optional[datetime] = None
        
        # Spatial filter
        self._route_buffer: Optional[Polygon] = None
        self._route_coordinates: List[List[float]] = []
        self._depot_points: List[Tuple[float, float]] = []
        
        # Background loading
        self._loading_thread: Optional[threading.Thread] = None
        self._stop_loading = threading.Event()
        self._loading_complete = threading.Event()
        
    def _calculate_bounding_box_buffer(
        self,
        coordinates: List[List[float]],
        buffer_km: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box with buffer around coordinates.
        
        Args:
            coordinates: List of [lon, lat] coordinate pairs
            buffer_km: Buffer distance in kilometers
        
        Returns:
            (min_lon, min_lat, max_lon, max_lat) tuple
        """
        if not coordinates:
            return (0, 0, 0, 0)
        
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        # Convert km to degrees (approximate)
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        avg_lat = sum(lats) / len(lats)
        buffer_deg_lat = buffer_km / 111.0
        buffer_deg_lon = buffer_km / (111.0 * math.cos(math.radians(avg_lat)))
        
        min_lon = min(lons) - buffer_deg_lon
        max_lon = max(lons) + buffer_deg_lon
        min_lat = min(lats) - buffer_deg_lat
        max_lat = max(lats) + buffer_deg_lat
        
        return (min_lon, min_lat, max_lon, max_lat)
    
    def _create_route_buffer(
        self,
        coordinates: List[List[float]],
        buffer_km: float
    ) -> Polygon:
        """
        Create a buffer polygon around route coordinates.
        
        Args:
            coordinates: List of [lon, lat] coordinate pairs
            buffer_km: Buffer distance in kilometers
        
        Returns:
            Shapely Polygon representing buffered route area
        """
        if not coordinates:
            return Polygon()
        
        # Create LineString from coordinates
        line = LineString([(coord[0], coord[1]) for coord in coordinates])
        
        # Buffer in degrees (approximate)
        avg_lat = sum(coord[1] for coord in coordinates) / len(coordinates)
        buffer_deg = buffer_km / (111.0 * math.cos(math.radians(avg_lat)))
        
        # Create buffer polygon
        buffer_poly = line.buffer(buffer_deg)
        
        return buffer_poly
    
    def _point_in_buffer(self, lon: float, lat: float) -> bool:
        """
        Check if a point is within the route buffer.
        
        Args:
            lon: Longitude
            lat: Latitude
        
        Returns:
            True if point is within buffer, False otherwise
        """
        if not self._route_buffer:
            return True  # No filter, accept all
        
        point = Point(lon, lat)
        return self._route_buffer.contains(point) or self._route_buffer.intersects(point)
    
    def _zone_intersects_buffer(self, zone_geometry: Dict) -> bool:
        """
        Check if a zone's geometry intersects with the route buffer.
        
        Args:
            zone_geometry: GeoJSON geometry dict
        
        Returns:
            True if zone intersects buffer, False otherwise
        """
        if not self._route_buffer:
            return True  # No filter, accept all
        
        try:
            # Convert GeoJSON to Shapely geometry
            zone_shape = shape(zone_geometry)
            
            # Check intersection
            return self._route_buffer.intersects(zone_shape)
            
        except Exception as e:
            self.logger.warning(f"Failed to check zone intersection: {e}")
            return False  # Exclude malformed geometries
    
    def _filter_zones_by_buffer(
        self,
        zones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter zones to only those within the route buffer.
        
        Args:
            zones: List of zone dictionaries
        
        Returns:
            Filtered list of zones
        """
        if not self._route_buffer:
            return zones  # No filter
        
        filtered = []
        
        for zone in zones:
            try:
                # Get geometry from zone data
                geometry = zone.get('geometry_geojson') or zone.get('geometry')
                
                if not geometry:
                    continue
                
                # Check if zone intersects buffer
                if self._zone_intersects_buffer(geometry):
                    filtered.append(zone)
                    
            except Exception as e:
                self.logger.warning(f"Failed to filter zone: {e}")
                continue
        
        return filtered
    
    def _background_load_zones(self):
        """
        Background thread function to load zones from API.
        Runs in separate thread to avoid blocking main event loop.
        
        IMPORTANT: Creates its own async context to avoid event loop conflicts.
        """
        import asyncio
        import httpx
        
        async def _async_load():
            """Actual async loading logic with independent HTTP client"""
            # Create a NEW HTTP client for this thread
            async with httpx.AsyncClient(timeout=30.0) as session:
                try:
                    # Load zones from API (using our own HTTP client)
                    all_zones = await self._fetch_landuse_zones(session)
                    places = await self._fetch_places(session)
                    
                    self.logger.info(
                        f"🌍 Background thread loaded {len(all_zones)} zones, "
                        f"{len(places)} places from API"
                    )
                    
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
                    
                    # Add places as amenity zones
                    amenity_zones_raw.extend(places)
                    
                    self.logger.info(
                        f"📊 Categorized: {len(population_zones_raw)} population zones, "
                        f"{len(amenity_zones_raw)} amenity zones (before filtering)"
                    )
                    
                    # Apply spatial filtering
                    population_zones_filtered = self._filter_zones_by_buffer(population_zones_raw)
                    amenity_zones_filtered = self._filter_zones_by_buffer(amenity_zones_raw)
                    
                    self.logger.info(
                        f"🎯 Spatial filter (±{self.buffer_km}km): "
                        f"{len(population_zones_filtered)} population zones, "
                        f"{len(amenity_zones_filtered)} amenity zones"
                    )
                    
                    # Store filtered zones (thread-safe)
                    with self._zones_lock:
                        self._population_zones = population_zones_filtered
                        self._amenity_zones = amenity_zones_filtered
                        self._last_loaded = datetime.now()
                    
                    self.logger.info("✅ Background zone loading complete")
                    
                except Exception as e:
                    self.logger.error(f"❌ Background zone loading failed: {e}", exc_info=True)
        
        try:
            # Create NEW event loop for this thread (critical!)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run async loading
            loop.run_until_complete(_async_load())
            
        except Exception as e:
            self.logger.error(f"❌ Background thread error: {e}", exc_info=True)
        finally:
            # Unblock waiters
            self._loading_complete.set()
            
            # Cleanup
            try:
                loop.close()
            except:
                pass
    
    async def _fetch_landuse_zones(self, session: Any) -> List[Dict[str, Any]]:
        """Fetch landuse zones using independent HTTP client"""
        all_zones = []
        page = 1
        page_size = 100
        
        # Get base_url from api_client
        base_url = self.api_client.base_url
        
        while True:
            response = await session.get(
                f"{base_url}/api/landuse-zones",
                params={
                    "filters[country][id][$eq]": self.country_id,
                    "pagination[page]": page,
                    "pagination[pageSize]": page_size,
                    "sort": "zone_type:asc"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            zones = data.get('data', [])
            all_zones.extend(zones)
            
            # Check if there are more pages
            pagination = data.get('meta', {}).get('pagination', {})
            total_pages = pagination.get('pageCount', 1)
            
            if page >= total_pages:
                break
                
            page += 1
        
        return all_zones
    
    async def _fetch_places(self, session: Any) -> List[Dict[str, Any]]:
        """Fetch places using independent HTTP client"""
        # Get base_url from api_client
        base_url = self.api_client.base_url
        
        response = await session.get(
            f"{base_url}/api/places",
            params={
                "filters[country][id][$eq]": self.country_id,
                "pagination[pageSize]": 10000,
                "sort": "name:asc"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return data.get('data', [])
    
    async def initialize_for_route(
        self,
        route_coordinates: List[List[float]],
        depot_locations: Optional[List[Tuple[float, float]]] = None
    ):
        """
        Initialize spatial cache for a specific route.
        
        Starts background thread to load zones within buffer distance
        of the route and depots.
        
        Args:
            route_coordinates: List of [lon, lat] coordinate pairs
            depot_locations: Optional list of (lat, lon) depot positions
        """
        self.logger.info(
            f"🚀 Initializing spatial zone cache for route "
            f"({len(route_coordinates)} points, buffer={self.buffer_km}km)"
        )
        
        # Store route data
        self._route_coordinates = route_coordinates
        self._depot_points = depot_locations or []
        
        # Create spatial buffer
        all_points = route_coordinates.copy()
        for lat, lon in self._depot_points:
            all_points.append([lon, lat])
        
        if all_points:
            self._route_buffer = self._create_route_buffer(all_points, self.buffer_km)
            bbox = self._calculate_bounding_box_buffer(all_points, self.buffer_km)
            self.logger.info(
                f"📍 Route buffer created: bbox={bbox}, "
                f"area={self._route_buffer.area:.6f} sq deg"
            )
        
        # Start background loading thread
        self._loading_complete.clear()
        self._stop_loading.clear()
        self._loading_thread = threading.Thread(
            target=self._background_load_zones,
            daemon=True,
            name="ZoneLoader"
        )
        self._loading_thread.start()
        
        self.logger.info("⏳ Background zone loading started...")
    
    async def wait_for_initial_load(self, timeout: float = 30.0) -> bool:
        """
        Wait for initial zone load to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if loaded successfully, False if timeout
        """
        loop = asyncio.get_event_loop()
        
        # Wait for loading to complete (non-blocking)
        await loop.run_in_executor(
            None,
            lambda: self._loading_complete.wait(timeout)
        )
        
        return self._loading_complete.is_set()
    
    async def get_cached_zones(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get cached zones (non-blocking).
        
        Returns:
            Tuple of (population_zones, amenity_zones)
        """
        with self._zones_lock:
            return (
                self._population_zones.copy(),
                self._amenity_zones.copy()
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._zones_lock:
            return {
                'population_zones': len(self._population_zones),
                'amenity_zones': len(self._amenity_zones),
                'last_loaded': self._last_loaded.isoformat() if self._last_loaded else None,
                'buffer_km': self.buffer_km,
                'loading_complete': self._loading_complete.is_set(),
                'route_points': len(self._route_coordinates),
                'depot_points': len(self._depot_points)
            }
    
    async def shutdown(self):
        """
        Shutdown background loading and cleanup resources.
        """
        self._stop_loading.set()
        
        if self._loading_thread and self._loading_thread.is_alive():
            self._loading_thread.join(timeout=5.0)
        
        self.logger.info("🛑 Spatial zone cache shutdown complete")
