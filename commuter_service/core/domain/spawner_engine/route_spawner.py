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
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import random

from commuter_service.core.domain.spawner_engine.base_spawner import SpawnerInterface, SpawnRequest, ReservoirInterface
from commuter_service.infrastructure.spawn.config_loader import SpawnConfigLoader
from commuter_service.infrastructure.geospatial.client import GeospatialClient


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
            
            self.logger.info(
                f"Route {self.route_id} at {current_time.strftime('%Y-%m-%d %H:%M')}: "
                f"spawning {spawn_count} passengers (buildings={len(buildings)})"
            )
            
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
        """Get depot information from geospatial service."""
        try:
            import httpx
            
            # Use geospatial service to query depot by documentId
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.geo_client.base_url}/routes/by-document-id/{self.route_id}/depot"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('depot')
                elif response.status_code == 404:
                    error_detail = response.json().get('detail', 'Unknown error')
                    self.logger.warning(f"Depot lookup failed: {error_detail}")
                    return None
                else:
                    self.logger.warning(f"Depot query returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error fetching depot info from geospatial service: {e}")
            return None
    
    async def _get_depot_catchment_buildings(self, spawn_config: Dict[str, Any]) -> int:
        """
        Get count of buildings in depot catchment area.
        This represents the terminal population available for all routes.
        """
        if self._depot_catchment_cache is not None:
            return self._depot_catchment_cache
        
        depot = await self._get_depot_info(spawn_config)
        if not depot:
            raise ValueError(
                f"No depot associated with route {self.route_id}. "
                f"Cannot spawn passengers without depot configuration. "
                f"Please create route-depot association in database."
            )
        
        # Get depot location
        depot_lat = depot.get('latitude')
        depot_lon = depot.get('longitude')
        
        if depot_lat is None or depot_lon is None:
            raise ValueError(
                f"Depot missing coordinates: {depot}. "
                f"Cannot calculate depot catchment without valid lat/lon."
            )
        
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
    
    # DEPRECATED: No longer needed with independent additive spawning model
    # Each route spawns independently, not competitively
    async def _get_total_buildings_all_routes(self, spawn_config: Dict[str, Any]) -> int:
        """
        [DEPRECATED - ZERO-SUM MODEL]
        Get total count of buildings across all routes at this depot.
        This was needed for calculating route attractiveness (zero-sum distribution).
        
        Now unused: Routes spawn independently, not competitively.
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
        Calculate spawn count for ROUTE PASSENGERS ONLY.
        
        RouteSpawner creates passengers along the route (pickup anywhere along route).
        DepotSpawner creates passengers at depot (pickup at terminal).
        
        This method only calculates route passengers based on buildings along route.
        """
        try:
            from commuter_service.core.domain.spawner_engine.spawn_calculator import SpawnCalculator

            # Extract temporal multipliers
            base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
                spawn_config=spawn_config,
                current_time=current_time,
                spawner_type='route'  # Use route-specific base rate
            )
            
            effective_rate = SpawnCalculator.calculate_effective_rate(
                base_rate=base_rate,
                hourly_multiplier=hourly_mult,
                day_multiplier=day_mult
            )
            
            # Calculate ROUTE passengers only (buildings along route)
            route_passengers_per_hour = building_count * effective_rate
            
            # Convert to lambda for time window
            lambda_param = route_passengers_per_hour * (time_window_minutes / 60.0)
            
            # Generate Poisson-distributed count
            import numpy as np
            spawn_count = np.random.poisson(lambda_param) if lambda_param > 0 else 0
            
            # Log breakdown for observability
            self.logger.info(
                f"Spawn ROUTE passengers [route={self.route_id}]: "
                f"route_buildings={building_count} | "
                f"base={base_rate:.4f}, hourly={hourly_mult:.2f}, day={day_mult:.2f}, "
                f"effective_rate={effective_rate:.4f} | "
                f"route_pass/hr={route_passengers_per_hour:.2f} | "
                f"lambda={lambda_param:.2f}, spawn_count={spawn_count}"
            )

            return int(spawn_count)

        except Exception as e:
            self.logger.error(f"Error calculating spawn count: {e}", exc_info=True)
            return 0
    
    async def _generate_spawn_requests(
        self,
        spawn_count: int,
        route_geometry: Dict[str, Any],
        current_time: datetime
    ) -> List[SpawnRequest]:
        """
        Generate individual spawn requests with realistic commute distances.
        
        OPTIMIZED: 
        1. Fetch config once
        2. Shared distance cache with on-demand fetching
        3. Batch all passengers in single asyncio.gather
        """
        route_coords = route_geometry.get('coordinates', [])
        num_coords = len(route_coords)
        
        if num_coords < 4:
            self.logger.warning(f"Route has only {num_coords} stops, skipping spawn")
            return []
        
        # OPTIMIZATION 1: Fetch minimum commute distance ONCE
        try:
            min_distance_config = await self.geo_client.get(f"/spatial/minimum-commute-distance")
            min_stops = min_distance_config.get('min_stops', 3)
            min_distance_meters = min_distance_config.get('min_distance_meters', 1000)
        except Exception as e:
            self.logger.error(f"Failed to fetch min distance config: {e}")
            raise  # Fail fast - no silent fallbacks!

        # Fetch DB-driven distribution policy (end-to-end settings)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.config_loader.api_base_url}/operational-configurations",
                    params={
                        "filters[section][$eq]": "passenger_spawning.distribution",
                        "pagination[pageSize]": 10
                    }
                )
                resp.raise_for_status()
                data = resp.json()

            configs = data.get('data', [])
            if not configs or len(configs) == 0:
                raise ValueError("Distribution policy not found in operational-configurations")

            # Parse values into a simple dict
            policy = {}
            for c in configs:
                param = c.get('parameter') or c.get('attributes', {}).get('parameter')
                val = c.get('value') or c.get('attributes', {}).get('value')
                if param and val is not None:
                    policy[param] = val

            # Required params
            if 'end_to_end_probability' not in policy or 'end_to_end_terminal_only' not in policy:
                raise ValueError("Required distribution parameters missing: end_to_end_probability or end_to_end_terminal_only")

            # Normalize types
            try:
                end_to_end_probability = float(policy.get('end_to_end_probability'))
            except Exception:
                end_to_end_probability = float(str(policy.get('end_to_end_probability')))

            raw_terminal_only = policy.get('end_to_end_terminal_only')
            if isinstance(raw_terminal_only, bool):
                end_to_end_terminal_only = raw_terminal_only
            else:
                end_to_end_terminal_only = str(raw_terminal_only).lower() in ('1', 'true', 'yes')

        except Exception as e:
            self.logger.error(f"Failed to fetch distribution policy from DB: {e}")
            raise
        
        # OPTIMIZATION 2: Shared cache for on-demand distance fetching
        # Only fetches distances as needed, but caches to avoid duplicates
        distance_cache = {}
        
        # OPTIMIZATION 3: Generate all passengers with shared cache
        import asyncio
        tasks = [
            self._generate_single_passenger(
                i, route_coords, num_coords, min_stops, min_distance_meters,
                current_time, distance_cache, end_to_end_probability, end_to_end_terminal_only
            )
            for i in range(spawn_count)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        spawn_requests = []
        for result in results:
            if isinstance(result, SpawnRequest):
                spawn_requests.append(result)
            elif isinstance(result, Exception):
                self.logger.debug(f"Passenger generation failed: {result}")
        
        return spawn_requests
    
    async def _generate_single_passenger(
        self,
        passenger_num: int,
        route_coords: List[List[float]],
        num_coords: int,
        min_stops: int,
        min_distance_meters: int,
        current_time: datetime,
        distance_cache: Dict[Tuple[int, int], float],
        end_to_end_probability: float = 0.0,
        end_to_end_terminal_only: bool = False
    ) -> SpawnRequest:
        """
        Generate a single passenger spawn request with distance validation.
        
        Uses pre-computed distance cache for O(1) lookups instead of API calls.
        """
        import random as rand
        import uuid
        
        # Generate boarding and alighting indices with realistic distribution
        trip_type = rand.choices(
            ['short', 'medium', 'long'],
            weights=[0.2, 0.5, 0.3],
            k=1
        )[0]
        
        # Pick random boarding position
        board_idx = rand.randint(0, num_coords - 1)
        
        # Calculate valid alighting range based on trip type
        max_attempts = 10
        alight_idx = None
        actual_distance = 0
        
        for attempt in range(max_attempts):
            if trip_type == 'short':
                # Short trip: min_stops to 30% of route length
                max_span = max(min_stops + 1, int(num_coords * 0.3))
                span = rand.randint(min_stops, max_span)
            elif trip_type == 'medium':
                # Medium trip: 30% to 70% of route length
                min_span = int(num_coords * 0.3)
                max_span = int(num_coords * 0.7)
                span = rand.randint(max(min_stops, min_span), max_span)
            else:  # long
                # Long trip: 70% to 100% of route length (end-to-end)
                min_span = int(num_coords * 0.7)
                max_span = num_coords - 1
                span = rand.randint(max(min_stops, min_span), max_span)
                # DB-driven decision: sometimes make long trips explicit end-to-end
                try:
                    # If probability triggers, make this a terminal-to-terminal trip
                    if rand.random() < end_to_end_probability:
                        # If terminal_only configured, force both board and alight to terminals
                        if end_to_end_terminal_only:
                            if rand.random() < 0.5:
                                board_idx = 0
                                alight_idx = num_coords - 1
                            else:
                                board_idx = num_coords - 1
                                alight_idx = 0
                            # Compute actual_distance via cache/API below and break out of attempts
                            cache_key = (board_idx, alight_idx)
                            if cache_key in distance_cache:
                                actual_distance = distance_cache[cache_key]
                            else:
                                try:
                                    distance_result = await self.geo_client.get(
                                        f"/spatial/route-segment-distance/{self.route_id}",
                                        params={"from_index": board_idx, "to_index": alight_idx}
                                    )
                                    actual_distance = distance_result.get('distance_meters', 0)
                                    distance_cache[cache_key] = actual_distance
                                    distance_cache[(alight_idx, board_idx)] = actual_distance
                                except Exception as e:
                                    self.logger.debug(f"Distance fetch failed for end-to-end: {e}")
                                    actual_distance = 0

                            # If this meets minimum, accept
                            if actual_distance >= min_distance_meters:
                                break
                            else:
                                # If failed, continue attempts to find a regular long trip
                                alight_idx = None
                                continue
                        else:
                            # Not terminal-only: make alight the far terminal but allow boarding anywhere
                            if rand.random() < 0.5:
                                alight_idx = num_coords - 1
                            else:
                                alight_idx = 0
                            # proceed to distance check below
                        
                except Exception:
                    # On any error when applying policy, fall back to normal long-trip logic
                    pass
            # Determine direction (forward or backward along route)
            if rand.random() < 0.5 and board_idx >= span:
                # Backward direction
                alight_idx = board_idx - span
            elif board_idx + span < num_coords:
                # Forward direction
                alight_idx = board_idx + span
            else:
                # Can't go forward, try backward
                alight_idx = max(0, board_idx - span)
            
            # OPTIMIZATION: Check cache first, fetch on-demand if not cached
            cache_key = (board_idx, alight_idx)
            if cache_key in distance_cache:
                actual_distance = distance_cache[cache_key]
            else:
                # Fetch and cache
                try:
                    distance_result = await self.geo_client.get(
                        f"/spatial/route-segment-distance/{self.route_id}",
                        params={"from_index": board_idx, "to_index": alight_idx}
                    )
                    actual_distance = distance_result.get('distance_meters', 0)
                    distance_cache[cache_key] = actual_distance
                    # Cache reverse too
                    distance_cache[(alight_idx, board_idx)] = actual_distance
                except Exception as e:
                    self.logger.debug(f"Distance fetch failed: {e}")
                    actual_distance = 0
            
            # Accept if meets minimum distance (strict enforcement)
            if actual_distance >= min_distance_meters:
                break
            else:
                self.logger.debug(f"Rejected trip: {actual_distance}m < {min_distance_meters}m minimum")
                alight_idx = None  # Try again
        
        # If we couldn't find a valid pair, raise exception
        if alight_idx is None or alight_idx == board_idx:
            raise ValueError(f"Could not generate valid commute for passenger {passenger_num} after {max_attempts} attempts")
        
        board_lon, board_lat = route_coords[board_idx]
        alight_lon, alight_lat = route_coords[alight_idx]
        
        # Generate unique passenger ID using UUID
        passenger_id = f"PASS_{uuid.uuid4().hex.upper()}"
        
        # Randomize spawn time within the hour (0-59 minutes, 0-59 seconds)
        random_minutes = rand.randint(0, 59)
        random_seconds = rand.randint(0, 59)
        actual_spawn_time = current_time.replace(minute=random_minutes, second=random_seconds, microsecond=0)
        
        # Create spawn request with all required fields
        spawn_req = SpawnRequest(
            passenger_id=passenger_id,
            spawn_location=(board_lat, board_lon),
            destination_location=(alight_lat, alight_lon),
            route_id=self.route_id,
            spawn_time=actual_spawn_time,
            spawn_context="ROUTE",
            generation_method="poisson"
        )
        
        # Log individual spawn event with distance
        distance_km = actual_distance / 1000 if actual_distance > 0 else 0
        self.logger.info(
            f"🚶 Passenger {passenger_id} spawned at {actual_spawn_time.strftime('%H:%M:%S')} | "
            f"Type: ROUTE ({trip_type}) | Board: Stop {board_idx} | Alight: Stop {alight_idx} | "
            f"Distance: {distance_km:.2f}km"
        )
        
        return spawn_req
