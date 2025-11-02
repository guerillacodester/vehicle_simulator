"""
Depot Spawner - Generates commuters at depot locations using Poisson distribution.

Responsible for:
1. Loading depot spawn configuration
2. Querying buildings near depot (population density)
3. Calculating Poisson-distributed spawn count
4. Generating commuters at depot with random destination routes
5. Pushing to depot reservoir

Key differences from RouteSpawner:
- Spawns at SINGLE depot location (not distributed along route)
- Passengers wait for ANY route (assigned randomly at spawn)
- Uses depot_id instead of route_id for spatial context
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import uuid

from commuter_simulator.core.domain.spawner_engine.base_spawner import SpawnerInterface, SpawnRequest, ReservoirInterface
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient


class DepotSpawner(SpawnerInterface):
    """
    Generates commuters at a depot location using Poisson distribution.
    
    Depot passengers wait at a central location for any available route.
    Configuration comes from depot-spawn-config in Strapi.
    """
    
    def __init__(
        self,
        reservoir: ReservoirInterface,
        config: Dict[str, Any],
        depot_id: str,
        depot_location: tuple,  # (lat, lon)
        available_routes: Optional[List[str]] = None,
        depot_document_id: Optional[str] = None,
        strapi_url: str = "http://localhost:1337",
        config_loader: Optional[SpawnConfigLoader] = None,
        geo_client: Optional[GeospatialClient] = None
    ):
        """
        Initialize depot spawner.
        
        Args:
            reservoir: DepotReservoir to store spawned commuters
            config: Base configuration dict
            depot_id: Unique depot identifier
            depot_location: (lat, lon) of depot
            available_routes: List of route IDs passengers can board (optional - will query if None)
            depot_document_id: Strapi v5 documentId for querying associated routes (optional)
            strapi_url: Base URL for Strapi API (default: http://localhost:1337)
            config_loader: For loading depot spawn configuration (optional)
            geo_client: For querying buildings near depot (optional)
        """
        super().__init__(reservoir, config)
        self.depot_id = depot_id
        self.depot_location = depot_location  # (lat, lon)
        self.available_routes = available_routes  # Can be None - will query from DB
        self.depot_document_id = depot_document_id
        self.strapi_url = strapi_url
        self.config_loader = config_loader
        self.geo_client = geo_client
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Cache for depot data
        self._spawn_config_cache = None
        self._buildings_cache = None
        self._associated_routes_cache = None
    
    async def spawn(self, current_time: datetime, time_window_minutes: int = 60) -> List[SpawnRequest]:
        """
        Generate commuters at depot for the time window.
        
        Algorithm:
        1. Load depot spawn config (or use defaults)
        2. Load associated routes from database (if not provided in constructor)
        3. Query buildings near depot (population density - optional)
        4. Calculate spawn count using Poisson distribution
        5. Apply day-of-week and hourly multipliers
        6. Generate passengers at depot location
        7. Assign random destination routes from associated routes
        
        Args:
            current_time: Current simulation time
            time_window_minutes: Time window for this spawn cycle
            
        Returns:
            List[SpawnRequest]: Generated spawn requests
        """
        try:
            # Load configuration (optional - can use defaults)
            spawn_config = await self._load_spawn_config()
            
            # Load associated routes if not provided in constructor
            if self.available_routes is None:
                self.available_routes = await self._load_associated_routes()
            
            # Query buildings near depot (for population density)
            depot_buildings = await self._get_depot_buildings(spawn_config)
            
            # Calculate spawn count
            spawn_count = await self._calculate_spawn_count(
                spawn_config=spawn_config,
                building_count=depot_buildings,
                current_time=current_time,
                time_window_minutes=time_window_minutes
            )
            
            self.logger.info(f"Depot {self.depot_id}: spawning {spawn_count} passengers")
            
            # Generate spawn requests
            spawn_requests = await self._generate_spawn_requests(
                spawn_count=spawn_count,
                current_time=current_time
            )
            
            return spawn_requests
            
        except Exception as e:
            self.logger.error(f"Error spawning at depot {self.depot_id}: {e}", exc_info=True)
            self.spawn_errors += 1
            return []
    
    async def _load_spawn_config(self) -> Dict[str, Any]:
        """
        Load spawn configuration from Strapi or return defaults.
        
        Since spawn config is stored per route (not per depot), we query the first
        available route's config. All routes at the same depot share the same spawn config.
        """
        if self._spawn_config_cache:
            return self._spawn_config_cache
        
        # Try to load config from one of the available routes
        if self.available_routes and len(self.available_routes) > 0:
            try:
                import httpx
                route_id = self.available_routes[0]
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{self.config_loader.api_base_url}/spawn-configs?"
                        f"populate=*&filters[route][documentId][$eq]={route_id}"
                    )
                    data = response.json()
                
                if data.get('data') and len(data['data']) > 0:
                    raw_config = data['data'][0]
                    # Extract config JSON field
                    if 'config' in raw_config:
                        self._spawn_config_cache = raw_config['config']
                    else:
                        self._spawn_config_cache = raw_config
                    self.logger.info(f"Loaded spawn config from route {route_id}")
                    return self._spawn_config_cache
            except Exception as e:
                self.logger.warning(f"Error loading spawn config from route: {e}")
        
        # Fallback to default config if no route config found
        self.logger.warning(f"No spawn config found, using defaults for depot {self.depot_id}")
        
        default_config = {
            'distribution_params': {
                'depot_passengers_per_building_per_hour': 0.3,
                'route_passengers_per_building_per_hour': 0.012
            },
            'hourly_rates': {
                '0': 0, '1': 0, '2': 0, '3': 0, '4': 0,
                '5': 0.15, '6': 0.35, '7': 0.75, '8': 1.0,
                '9': 0.45, '10': 0.25, '11': 0.2, '12': 0.3,
                '13': 0.25, '14': 0.3, '15': 0.4, '16': 0.55,
                '17': 0.85, '18': 0.4, '19': 0.2, '20': 0.1,
                '21': 0.05, '22': 0, '23': 0
            },
            'day_multipliers': {
                '0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0,
                '4': 1.0, '5': 1.0, '6': 0.6
            }
        }
        self._spawn_config_cache = default_config
        return default_config
    
    async def _load_associated_routes(self) -> List[str]:
        """
        Load associated routes from Strapi route-depot junction table.
        
        Returns:
            List of route short_names that serve this depot.
            Returns empty list if no associations found or on error.
        """
        if self._associated_routes_cache:
            return self._associated_routes_cache
        
        if not self.depot_document_id:
            self.logger.warning(
                f"No depot_document_id provided for depot {self.depot_id}, cannot query associated routes"
            )
            return []
        
        try:
            import httpx
            
            # Query route-depots where depot matches this depot's documentId
            # MUST populate route relation to get route data
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = (
                    f"{self.strapi_url}/api/route-depots?"
                    f"filters[depot][documentId][$eq]={self.depot_document_id}&"
                    f"populate=route&"
                    f"pagination[pageSize]=100"
                )
                
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            associations = data.get('data', [])
            
            if not associations:
                self.logger.warning(
                    f"No associated routes found for depot {self.depot_id} (documentId={self.depot_document_id})"
                )
                return []
            
            # Extract route short names or IDs from populated route relation
            route_names = []
            for assoc in associations:
                # Get the populated route object
                route = assoc.get('route')
                if route:
                    # Prefer route_short_name, fallback to ID
                    route_short_name = route.get('route_short_name') or str(route.get('id', ''))
                if route and route_short_name:
                    route_names.append(route_short_name)
            
            self._associated_routes_cache = route_names
            self.logger.info(
                f"Loaded {len(route_names)} associated routes for depot {self.depot_id}: {route_names}"
            )
            
            return route_names
            
        except Exception as e:
            self.logger.error(f"Error loading associated routes for depot {self.depot_id}: {e}")
            return []
    
    async def _get_depot_buildings(self, spawn_config: Dict[str, Any]) -> int:
        """
        Query buildings near depot using geospatial service.
        Similar to RouteSpawner's building query but for depot catchment area.
        """
        try:
            if not self.geo_client:
                self.logger.warning("No geo_client available, using default building count")
                return 200  # Default fallback
            
            # Get depot catchment radius from config
            dist_params = spawn_config.get('distribution_params', {})
            catchment_radius = dist_params.get('depot_catchment_radius_meters', 800)
            
            # Query buildings near depot
            depot_lat, depot_lon = self.depot_location
            result = self.geo_client.depot_catchment_area(
                depot_latitude=depot_lat,
                depot_longitude=depot_lon,
                catchment_radius_meters=catchment_radius
            )
            
            buildings = result.get('buildings', [])
            building_count = len(buildings)
            
            self.logger.info(
                f"Depot {self.depot_id}: Found {building_count} buildings within {catchment_radius}m"
            )
            
            return building_count
            
        except Exception as e:
            self.logger.error(f"Error querying depot buildings: {e}")
            return 200  # Fallback default
    
    async def _calculate_spawn_count(
        self,
        spawn_config: Dict[str, Any],
        building_count: int,
        current_time: datetime,
        time_window_minutes: int
    ) -> int:
        """
        Calculate how many passengers to spawn using Poisson distribution.
        
        Formula: lambda = (building_count × base_rate) × hourly_mult × day_mult × (time_window / 60)
        This matches RouteSpawner's approach for consistency.
        """
        try:
            from commuter_simulator.core.domain.spawner_engine.spawn_calculator import SpawnCalculator
            
            dist_params = spawn_config.get('distribution_params', {})
            
            # Extract temporal multipliers using kernel helper for consistency
            # Pass spawner_type='depot' to get depot-specific base rate
            base_rate, hourly_rate, day_mult = SpawnCalculator.extract_temporal_multipliers(
                spawn_config=spawn_config,
                current_time=current_time,
                spawner_type='depot'  # Use depot-specific base rate
            )
            
            # Calculate effective rate
            effective_rate = SpawnCalculator.calculate_effective_rate(
                base_rate=base_rate,
                hourly_multiplier=hourly_rate,
                day_multiplier=day_mult
            )
            
            # Calculate depot passengers per hour (same formula as RouteSpawner)
            depot_passengers_per_hour = building_count * effective_rate
            
            # Calculate lambda (expected value) for Poisson
            lambda_param = depot_passengers_per_hour * (time_window_minutes / 60.0)
            
            # Generate Poisson-distributed count
            import numpy as np
            spawn_count = np.random.poisson(lambda_param) if lambda_param > 0 else 0
            
            self.logger.info(
                f"Depot spawn [depot={self.depot_id}]: "
                f"buildings={building_count}, base_rate={base_rate:.4f}, "
                f"hourly={hourly_rate:.2f}, day={day_mult:.2f}, "
                f"effective_rate={effective_rate:.4f}, "
                f"depot_pass/hr={depot_passengers_per_hour:.2f}, "
                f"lambda={lambda_param:.2f}, spawn_count={spawn_count}"
            )
            
            return spawn_count
            
        except Exception as e:
            self.logger.error(f"Error calculating spawn count: {e}")
            return 0
    
    async def _calculate_route_attractiveness(
        self,
        spawn_config: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate attractiveness-weighted distribution of passengers across routes.
        
        Simplified: Use equal distribution for all routes.
        (In future, could weight by building density along each route)
        
        Returns:
            Dict mapping route_id -> attractiveness (0.0 - 1.0, sum = 1.0)
        """
        if not self.available_routes:
            return {}
        
        # Equal distribution across all routes
        equal_weight = 1.0 / len(self.available_routes)
        attractiveness = {route: equal_weight for route in self.available_routes}
        
        self.logger.info(
            f"Depot {self.depot_id} route attractiveness (equal distribution): {attractiveness}"
        )
        
        return attractiveness
    
    async def _get_depot_info(self, spawn_config: Dict[str, Any]) -> Optional[Dict]:
        """Get depot information from spawn config or API"""
        # Try to get from spawn config first
        depot_info = spawn_config.get('depot')
        if depot_info:
            return depot_info
        
        # Query from API if depot_document_id available
        if self.depot_document_id and self.config_loader:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"{self.strapi_url}/api/depots/{self.depot_document_id}?populate=*"
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    return data.get('data')
            except Exception as e:
                self.logger.warning(f"Could not fetch depot info: {e}")
        
        return None
    
    async def _get_route_buildings(self, route_id: str, spawn_config: Dict[str, Any]) -> int:
        """Get building count for a specific route"""
        try:
            if not self.config_loader:
                return 0
            
            # Query route's spawn config
            route_config = await self.config_loader.load_spawn_config(route_id)
            if not route_config:
                return 0
            
            # Get building count from route spawn config
            # This should come from the geospatial query for that route
            buildings = route_config.get('building_count', 0)
            
            self.logger.debug(f"Route {route_id} has {buildings} buildings")
            return buildings
            
        except Exception as e:
            self.logger.error(f"Error getting buildings for route {route_id}: {e}")
            return 0
    
    def _weighted_route_assignment(
        self,
        spawn_count: int,
        attractiveness: Dict[str, float]
    ) -> Dict[str, int]:
        """
        Distribute passengers across routes based on attractiveness weights.
        
        Args:
            spawn_count: Total number of passengers to assign
            attractiveness: Dict of route_id -> attractiveness weight (0.0-1.0)
            
        Returns:
            Dict of route_id -> passenger count
        """
        import numpy as np
        
        if not attractiveness or sum(attractiveness.values()) == 0:
            # If no attractiveness data, distribute evenly
            routes = self.available_routes or []
            if not routes:
                return {}
            
            passengers_per_route = spawn_count // len(routes)
            remainder = spawn_count % len(routes)
            
            assignments = {route: passengers_per_route for route in routes}
            # Distribute remainder to first routes
            for i, route in enumerate(routes[:remainder]):
                assignments[route] += 1
            
            return assignments
        
        # Normalize attractiveness to probabilities
        total_attractiveness = sum(attractiveness.values())
        probabilities = {
            route: weight / total_attractiveness 
            for route, weight in attractiveness.items()
        }
        
        # Use multinomial distribution to assign passengers
        routes = list(probabilities.keys())
        probs = [probabilities[r] for r in routes]
        
        # Generate assignments
        assignments = np.random.multinomial(spawn_count, probs)
        
        return {route: int(count) for route, count in zip(routes, assignments)}
    
    async def _generate_spawn_requests(
        self,
        spawn_count: int,
        current_time: datetime
    ) -> List[SpawnRequest]:
        """
        Generate individual spawn requests at depot location.
        
        Uses attractiveness-weighted distribution to assign passengers to routes
        based on building density along each route (zero-sum model).
        """
        # If no routes available, cannot spawn passengers
        if not self.available_routes:
            self.logger.warning(
                f"Depot {self.depot_id} has no available routes - cannot spawn passengers"
            )
            return []
        
        # Calculate route attractiveness distribution
        spawn_config = await self._load_spawn_config()
        attractiveness = await self._calculate_route_attractiveness(spawn_config)
        
        # Distribute passengers across routes based on attractiveness
        route_assignments = self._weighted_route_assignment(spawn_count, attractiveness)
        
        spawn_requests = []
        
        for route_id, passenger_count in route_assignments.items():
            for i in range(passenger_count):
                try:
                    # All passengers spawn at depot location
                    spawn_lat, spawn_lon = self.depot_location
                    
                    # Assign to route based on attractiveness weighting
                    destination_route = route_id
                    
                    # Generate unique passenger ID using full UUID
                    import uuid
                    passenger_id = f"PASS_{uuid.uuid4().hex.upper()}"
                    
                    # Destination is unknown until route is assigned by conductor
                    # For now, use depot location as placeholder
                    dest_lat, dest_lon = self.depot_location
                    
                    # Create spawn request
                    spawn_req = SpawnRequest(
                        passenger_id=passenger_id,
                        spawn_location=(spawn_lat, spawn_lon),
                        destination_location=(dest_lat, dest_lon),  # Updated by conductor
                        route_id=destination_route,
                        spawn_time=current_time,
                        spawn_context="DEPOT",
                        priority=1.0,
                        generation_method="poisson_depot"
                    )
                    
                    spawn_requests.append(spawn_req)
                    
                    # Log individual spawn event
                    self.logger.info(
                        f"🚶 Passenger {passenger_id} spawned at {current_time.strftime('%H:%M:%S')} | "
                        f"Type: DEPOT ({self.depot_id}) | Location: ({spawn_lat:.4f}, {spawn_lon:.4f}) | "
                        f"Route: {destination_route}"
                    )
                    
                except Exception as e:
                    self.logger.debug(f"Error generating depot spawn request {i}: {e}")
                    continue
        
        return spawn_requests
