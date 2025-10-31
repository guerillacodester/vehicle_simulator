"""
Route Spawner - Generates commuters along transit routes using Poisson distribution.

Responsible for:
1. Loading route spawn configuration
2. Querying buildings near route
3. Calculating Poisson-distributed spawn count
4. Generating spatially distributed commuter positions
5. Pushing to reservoir

Does NOT handle:
- Persistence (that's the reservoir)
- Route movement (that's the vehicle simulator)
- Pickup logic (that's the conductor)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

from commuter_simulator.core.domain.spawner_engine.base_spawner import SpawnerInterface, SpawnRequest, ReservoirInterface
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient


class RouteSpawner(SpawnerInterface):
    """
    Generates commuters along a transit route using Poisson distribution.
    
    Configuration comes from spawn-config in Strapi. Queries buildings near route
    to determine population density, then uses Poisson distribution to calculate
    how many passengers to spawn in the time window.
    """
    
    def __init__(
        self, 
        reservoir: ReservoirInterface, 
        config: Dict[str, Any],
        route_id: str,
        config_loader: SpawnConfigLoader,
        geo_client: GeospatialClient
    ):
        """
        Initialize route spawner.
        
        Args:
            reservoir: Where to store spawned commuters
            config: Base configuration dict
            route_id: Strapi route document ID
            config_loader: For loading route spawn configuration
            geo_client: For querying buildings near route
        """
        super().__init__(reservoir, config)
        self.route_id = route_id
        self.config_loader = config_loader
        self.geo_client = geo_client
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Cache for route data
        self._route_geometry_cache = None
        self._spawn_config_cache = None
        self._buildings_cache = None
    
    async def spawn(self, current_time: datetime, time_window_minutes: int = 60) -> List[SpawnRequest]:
        """
        Generate commuters for this route in the time window.
        
        Algorithm:
        1. Load route geometry and spawn config
        2. Query buildings near route (population density)
        3. Calculate base spawn count using Poisson distribution
        4. Apply day-of-week and hourly multipliers
        5. Spatially distribute passengers along route
        6. Generate random boarding/alighting pairs
        
        Args:
            current_time: Current simulation time
            time_window_minutes: Time window for this spawn cycle
            
        Returns:
            List[SpawnRequest]: Generated spawn requests
        """
        try:
            # Load configuration
            spawn_config = await self._load_spawn_config()
            if not spawn_config:
                self.logger.warning(f"No spawn config for route {self.route_id}")
                return []
            
            route_geometry = await self._load_route_geometry()
            if not route_geometry:
                self.logger.error(f"No route geometry for {self.route_id}")
                return []
            
            # Query buildings
            buildings = await self._get_buildings_near_route(route_geometry, spawn_config)
            
            # Calculate spawn count
            spawn_count = await self._calculate_spawn_count(
                spawn_config=spawn_config,
                building_count=len(buildings),
                current_time=current_time,
                time_window_minutes=time_window_minutes
            )
            
            self.logger.info(f"Route {self.route_id}: spawning {spawn_count} passengers")
            
            # Generate spawn requests
            spawn_requests = await self._generate_spawn_requests(
                spawn_count=spawn_count,
                route_geometry=route_geometry,
                current_time=current_time
            )
            
            return spawn_requests
            
        except Exception as e:
            self.logger.error(f"Error spawning for route {self.route_id}: {e}", exc_info=True)
            self.spawn_errors += 1
            return []
    
    async def _load_spawn_config(self) -> Optional[Dict[str, Any]]:
        """Load spawn configuration from Strapi"""
        if self._spawn_config_cache:
            return self._spawn_config_cache
        
        try:
            # Query spawn-config by route document_id
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config_loader.api_base_url}/spawn-configs?"
                    f"populate=*&filters[route][documentId][$eq]={self.route_id}"
                )
                data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                raw_config = data['data'][0]
                # Extract config JSON field (production schema)
                # Supports both old (components) and new (JSON) formats
                if 'config' in raw_config:
                    self._spawn_config_cache = raw_config['config']
                else:
                    # Fallback for old component-based schema
                    self._spawn_config_cache = raw_config
                return self._spawn_config_cache
            
            return None
        except Exception as e:
            self.logger.error(f"Error loading spawn config: {e}")
            return None
    
    async def _load_route_geometry(self) -> Optional[Dict[str, Any]]:
        """Load route geometry from geospatial service"""
        if self._route_geometry_cache:
            return self._route_geometry_cache
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.geo_client.base_url}/spatial/route-geometry/{self.route_id}"
                )
                response.raise_for_status()
                self._route_geometry_cache = response.json()
                return self._route_geometry_cache
        except Exception as e:
            self.logger.error(f"Error loading route geometry: {e}")
            return None
    
    async def _get_buildings_near_route(
        self, 
        route_geometry: Dict[str, Any], 
        spawn_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get buildings near route using geospatial service"""
        try:
            # Get spawn radius from config
            dist_params = spawn_config.get('distribution_params', {})
            if isinstance(dist_params, list) and len(dist_params) > 0:
                dist_params = dist_params[0]
            
            spawn_radius = dist_params.get('spawn_radius_meters', 500)
            
            # Get route coordinates
            route_coords = route_geometry.get('coordinates', [])
            if not route_coords:
                return []
            
            # Query buildings (no artificial limit - get all buildings within radius)
            self.logger.info(f"Querying buildings within {spawn_radius}m of route...")
            result = self.geo_client.buildings_along_route(
                route_coordinates=route_coords,
                buffer_meters=spawn_radius,
                limit=5000  # Match PostGIS default, allow getting all buildings
            )
            
            buildings = result.get('buildings', [])
            self.logger.info(f"Found {len(buildings)} buildings near route")
            return buildings
            
        except Exception as e:
            self.logger.error(f"Error querying buildings: {e}")
            return []
    
    async def _calculate_spawn_count(
        self,
        spawn_config: Dict[str, Any],
        building_count: int,
        current_time: datetime,
        time_window_minutes: int
    ) -> int:
        """
        Calculate Poisson lambda from ACTUAL GeoJSON data weighted by spawn config.
        Each route has unique spawn characteristics based on:
        - Real building counts along route
        - Building types (residential vs commercial weights)
        - POI density and types  
        - Land use patterns
        """
        try:
            dist_params = spawn_config.get('distribution_params', {})
            if isinstance(dist_params, list) and len(dist_params) > 0:
                dist_params = dist_params[0]
            
            # Get passengers per building per hour from config
            passengers_per_building = dist_params.get('passengers_per_building_per_hour', 0.3)
            
            # Calculate spatial factor from actual building count
            # This uses REAL GeoJSON data queried from PostGIS
            spatial_factor = building_count * passengers_per_building
            
            # TODO: Add POI and landuse factors using weights from spawn_config
            # poi_weights = spawn_config.get('poi_weights', {})
            # landuse_weights = spawn_config.get('landuse_weights', {})
            # building_weights = spawn_config.get('building_weights', {})
            
            # Hourly rate from config (peak hours = higher rate)
            hourly_rates = spawn_config.get('hourly_rates', {})
            hour_str = str(current_time.hour)
            hourly_rate = float(hourly_rates.get(hour_str, 0.5))
            
            # Day multiplier from config (weekday vs weekend)
            day_multipliers = spawn_config.get('day_multipliers', {})
            day_str = str(current_time.weekday())
            day_mult = float(day_multipliers.get(day_str, 1.0))
            
            # Calculate lambda: spatial × hourly × day × time_window
            # This gives expected passenger count for this specific time window
            lambda_param = spatial_factor * hourly_rate * day_mult * (time_window_minutes / 60.0)
            
            # Generate Poisson-distributed count
            import numpy as np
            spawn_count = np.random.poisson(lambda_param) if lambda_param > 0 else 0
            
            self.logger.info(
                f"Spawn calculation: buildings={building_count} × pass/bldg={passengers_per_building} × "
                f"hourly={hourly_rate} × day={day_mult} × window={time_window_minutes/60:.2f}h "
                f"= lambda={lambda_param:.2f} → count={spawn_count}"
            )
            
            return spawn_count
            
        except Exception as e:
            self.logger.error(f"Error calculating spawn count: {e}")
            return 0
    
    async def _generate_spawn_requests(
        self,
        spawn_count: int,
        route_geometry: Dict[str, Any],
        current_time: datetime
    ) -> List[SpawnRequest]:
        """Generate individual spawn requests with random positions along route"""
        spawn_requests = []
        route_coords = route_geometry.get('coordinates', [])
        
        for i in range(spawn_count):
            try:
                # Random boarding position along route
                board_idx = random.randint(0, len(route_coords) - 1)
                board_lon, board_lat = route_coords[board_idx]
                
                # Random alighting position further along route
                alight_idx = random.randint(board_idx, len(route_coords) - 1)
                alight_lon, alight_lat = route_coords[alight_idx]
                
                # Generate unique passenger ID
                passenger_id = f"PASS_{i:08X}"
                
                # Create spawn request with all required fields
                spawn_req = SpawnRequest(
                    passenger_id=passenger_id,
                    spawn_location=(board_lat, board_lon),
                    destination_location=(alight_lat, alight_lon),
                    route_id=self.route_id,
                    spawn_time=current_time,
                    spawn_context="ROUTE",
                    generation_method="poisson"
                )
                
                spawn_requests.append(spawn_req)
                
                # Log individual spawn event
                self.logger.info(
                    f"🚶 Passenger {passenger_id} spawned at {current_time.strftime('%H:%M:%S')} | "
                    f"Type: ROUTE | Board: ({board_lat:.4f}, {board_lon:.4f}) | "
                    f"Alight: ({alight_lat:.4f}, {alight_lon:.4f})"
                )
                
            except Exception as e:
                self.logger.debug(f"Error generating spawn request {i}: {e}")
                continue
        
        return spawn_requests
