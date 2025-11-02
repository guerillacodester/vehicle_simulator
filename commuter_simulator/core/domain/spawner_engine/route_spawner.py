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
        self._depot_catchment_cache = None
        self._total_buildings_all_routes_cache = None
    
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
    
    async def _get_depot_info(self, spawn_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get depot information from spawn config."""
        try:
            import httpx
            
            # First, get the spawn-config entry with depot relationship populated
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config_loader.api_base_url}/spawn-configs?"
                    f"populate=depot&filters[route][documentId][$eq]={self.route_id}"
                )
                data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                depot = data['data'][0].get('depot')
                return depot
            
            return None
        except Exception as e:
            self.logger.error(f"Error fetching depot info: {e}")
            return None
    
    async def _get_depot_catchment_buildings(self, spawn_config: Dict[str, Any]) -> int:
        """
        Get count of buildings in depot catchment area.
        This represents the terminal population available for all routes.
        """
        if self._depot_catchment_cache is not None:
            return self._depot_catchment_cache
        
        try:
            depot = await self._get_depot_info(spawn_config)
            if not depot:
                self.logger.warning("No depot found for route, using route buildings as fallback")
                return 0  # Will trigger fallback behavior
            
            # Get depot location
            depot_lat = depot.get('latitude')
            depot_lon = depot.get('longitude')
            
            if depot_lat is None or depot_lon is None:
                self.logger.warning(f"Depot missing coordinates: {depot}")
                return 0
            
            # Get catchment radius from config (default 800m to match route buffer)
            dist_params = spawn_config.get('distribution_params', {})
            if isinstance(dist_params, list) and len(dist_params) > 0:
                dist_params = dist_params[0]
            catchment_radius = dist_params.get('depot_catchment_radius_meters', 800)
            
            # Query depot catchment
            result = self.geo_client.depot_catchment_area(
                depot_latitude=depot_lat,
                depot_longitude=depot_lon,
                catchment_radius_meters=catchment_radius
            )
            
            buildings = result.get('buildings', [])
            building_count = len(buildings)
            self._depot_catchment_cache = building_count
            
            self.logger.info(
                f"Depot catchment: {building_count} buildings within {catchment_radius}m "
                f"of depot at ({depot_lat:.4f}, {depot_lon:.4f})"
            )
            
            return building_count
            
        except Exception as e:
            self.logger.error(f"Error querying depot catchment: {e}")
            return 0
    
    async def _get_total_buildings_all_routes(self, spawn_config: Dict[str, Any]) -> int:
        """
        Get total count of buildings across all routes at this depot.
        This is needed for calculating route attractiveness (zero-sum distribution).
        """
        if self._total_buildings_all_routes_cache is not None:
            return self._total_buildings_all_routes_cache
        
        try:
            depot = await self._get_depot_info(spawn_config)
            if not depot:
                self.logger.warning("No depot found, using single route as fallback")
                return 0  # Will trigger fallback behavior
            
            depot_doc_id = depot.get('documentId')
            if not depot_doc_id:
                self.logger.warning("Depot missing documentId")
                return 0
            
            import httpx
            
            # Query route-depots junction to get all routes at this depot
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config_loader.api_base_url}/route-depots",
                    params={
                        'filters[depot][documentId][$eq]': depot_doc_id,
                        'populate': 'route'
                    }
                )
                data = response.json()
            
            route_depots = data.get('data', [])
            
            if not route_depots:
                self.logger.warning(f"No routes found for depot {depot_doc_id}")
                return 0
            
            # Get building count for each route
            total_buildings = 0
            route_count = 0
            
            for assoc in route_depots:
                route = assoc.get('route')
                if not route:
                    continue
                
                route_doc_id = route.get('documentId')
                if not route_doc_id:
                    continue
                
                route_count += 1
                
                # Get route geometry
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(
                            f"{self.geo_client.base_url}/spatial/route-geometry/{route_doc_id}"
                        )
                        route_geometry = response.json()
                    
                    # Get buildings along this route
                    route_coords = route_geometry.get('coordinates', [])
                    if route_coords:
                        # Get spawn radius from config
                        dist_params = spawn_config.get('distribution_params', {})
                        if isinstance(dist_params, list) and len(dist_params) > 0:
                            dist_params = dist_params[0]
                        spawn_radius = dist_params.get('spawn_radius_meters', 500)
                        
                        result = self.geo_client.buildings_along_route(
                            route_coordinates=route_coords,
                            buffer_meters=spawn_radius,
                            limit=5000
                        )
                        buildings = result.get('buildings', [])
                        total_buildings += len(buildings)
                
                except Exception as e:
                    self.logger.warning(f"Error getting buildings for route {route_doc_id}: {e}")
                    continue
            
            self._total_buildings_all_routes_cache = total_buildings
            
            self.logger.info(
                f"Total buildings across {route_count} routes at depot: {total_buildings}"
            )
            
            return total_buildings
            
        except Exception as e:
            self.logger.error(f"Error calculating total buildings for all routes: {e}")
            return 0
    
    async def _calculate_spawn_count(
        self,
        spawn_config: Dict[str, Any],
        building_count: int,
        current_time: datetime,
        time_window_minutes: int
    ) -> int:
        """
        Calculate spawn count using hybrid model (terminal population × route attractiveness).
        
        Uses centralized spawn calculation kernel for consistency.
        Queries depot catchment and aggregates buildings across all routes to enable
        zero-sum route attractiveness calculation.
        
        Fallback: If depot data unavailable, uses route buildings only (attractiveness=1.0).
        """
        try:
            from commuter_simulator.core.domain.spawner_engine.spawn_calculator import SpawnCalculator

            # Try to get depot catchment and total buildings across all routes
            depot_catchment = await self._get_depot_catchment_buildings(spawn_config)
            total_buildings = await self._get_total_buildings_all_routes(spawn_config)
            
            # Fallback: if depot data unavailable, use route-only mode
            if depot_catchment == 0 or total_buildings == 0:
                self.logger.info(
                    "Depot data unavailable, using route-only mode (attractiveness=1.0)"
                )
                buildings_near_depot = building_count
                buildings_along_route = building_count
                total_buildings_all_routes = building_count
            else:
                buildings_near_depot = depot_catchment
                buildings_along_route = building_count
                total_buildings_all_routes = total_buildings

            result = SpawnCalculator.calculate_hybrid_spawn(
                buildings_near_depot=buildings_near_depot,
                buildings_along_route=buildings_along_route,
                total_buildings_all_routes=total_buildings_all_routes,
                spawn_config=spawn_config,
                current_time=current_time,
                time_window_minutes=time_window_minutes,
                seed=None
            )

            # Log kernel breakdown for observability
            self.logger.info(
                f"Spawn kernel [route={self.route_id}]: "
                f"depot_buildings={buildings_near_depot}, route_buildings={buildings_along_route}, "
                f"total_all_routes={total_buildings_all_routes} | "
                f"base={result.get('base_rate')}, hourly={result.get('hourly_mult'):.2f}, "
                f"day={result.get('day_mult'):.2f}, effective_rate={result.get('effective_rate'):.4f}, "
                f"terminal_pop={result.get('terminal_population'):.2f} pass/hr, "
                f"attractiveness={result.get('route_attractiveness'):.3f}, "
                f"passengers/hr={result.get('passengers_per_hour'):.2f}, "
                f"lambda={result.get('lambda_param'):.2f}, spawn_count={result.get('spawn_count')}"
            )

            return int(result.get('spawn_count', 0))

        except Exception as e:
            self.logger.error(f"Error calculating spawn count with kernel: {e}", exc_info=True)
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
