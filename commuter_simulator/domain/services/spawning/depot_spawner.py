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

from commuter_simulator.domain.services.spawning.base_spawner import SpawnerInterface, SpawnRequest, ReservoirInterface
from commuter_simulator.infrastructure.config.spawn_config_loader import SpawnConfigLoader
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
            
            # Calculate spawn count
            spawn_count = await self._calculate_spawn_count(
                spawn_config=spawn_config,
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
        """Load spawn configuration from Strapi or return defaults"""
        if self._spawn_config_cache:
            return self._spawn_config_cache
        
        # If no config loader, use default config
        if not self.config_loader:
            default_config = {
                'distribution_params': {
                    'spatial_base': 2.0,  # Base spawn rate for depots (higher than routes)
                    'hourly_rates': {
                        '6': 0.8, '7': 1.2, '8': 1.5,  # Morning rush
                        '9': 1.0, '10': 0.6, '11': 0.5,
                        '12': 0.7, '13': 0.6, '14': 0.5,
                        '15': 0.6, '16': 0.8, '17': 1.3,  # Evening rush
                        '18': 1.2, '19': 0.9, '20': 0.5,
                    },
                    'day_multipliers': {
                        '0': 1.2,  # Monday
                        '1': 1.1,  # Tuesday
                        '2': 1.1,  # Wednesday
                        '3': 1.1,  # Thursday
                        '4': 1.3,  # Friday
                        '5': 0.4,  # Saturday
                        '6': 0.3,  # Sunday
                    }
                }
            }
            self._spawn_config_cache = default_config
            self.logger.info(f"Using default spawn config for depot {self.depot_id}")
            return default_config
        
        try:
            # Query depot-spawn-config by depot_id
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.config_loader.api_base_url}/depot-spawn-configs?"
                    f"populate=*&filters[depot_id][$eq]={self.depot_id}"
                )
                data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                self._spawn_config_cache = data['data'][0]
                self.logger.info(f"Loaded spawn config for depot {self.depot_id}")
                return self._spawn_config_cache
            
            # Fallback to default
            return await self._load_spawn_config()
            
        except Exception as e:
            self.logger.warning(f"Error loading depot spawn config: {e}, using defaults")
            return await self._load_spawn_config()
    
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
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = (
                    f"{self.strapi_url}/api/route-depots?"
                    f"filters[depot][documentId][$eq]={self.depot_document_id}&"
                    f"fields[0]=route_short_name&"
                    f"fields[1]=distance_from_route_m&"
                    f"fields[2]=is_start_terminus&"
                    f"fields[3]=is_end_terminus&"
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
            
            # Extract route short names from cached labels
            route_names = []
            for assoc in associations:
                attrs = assoc.get('attributes', assoc)
                route_short_name = attrs.get('route_short_name')
                if route_short_name:
                    route_names.append(route_short_name)
            
            self._associated_routes_cache = route_names
            self.logger.info(
                f"Loaded {len(route_names)} associated routes for depot {self.depot_id}: {route_names}"
            )
            
            return route_names
            
        except Exception as e:
            self.logger.error(f"Error loading associated routes for depot {self.depot_id}: {e}")
            return []
    
    async def _calculate_spawn_count(
        self,
        spawn_config: Dict[str, Any],
        current_time: datetime,
        time_window_minutes: int
    ) -> int:
        """Calculate how many passengers to spawn using Poisson distribution"""
        try:
            dist_params = spawn_config.get('distribution_params', {})
            
            # Base spawn rate from config
            spatial_base = dist_params.get('spatial_base', 2.0)
            
            # Hourly rate based on time of day
            hourly_rates = dist_params.get('hourly_rates', {})
            hour_str = str(current_time.hour)
            hourly_rate = float(hourly_rates.get(hour_str, 0.5))
            
            # Day multiplier (Monday=0, Sunday=6)
            day_multipliers = dist_params.get('day_multipliers', {})
            day_str = str(current_time.weekday())
            day_mult = float(day_multipliers.get(day_str, 1.0))
            
            # Calculate lambda (expected value) for Poisson
            # lambda = spatial_base × hourly_rate × day_multiplier × (time_window / 60 min)
            lambda_param = spatial_base * hourly_rate * day_mult * (time_window_minutes / 60.0)
            
            # Generate Poisson-distributed count
            import numpy as np
            spawn_count = np.random.poisson(lambda_param) if lambda_param > 0 else 0
            
            self.logger.info(
                f"Depot spawn calculation: spatial={spatial_base} × hourly={hourly_rate} × day={day_mult} "
                f"= lambda={lambda_param:.2f} → count={spawn_count}"
            )
            
            return spawn_count
            
        except Exception as e:
            self.logger.error(f"Error calculating spawn count: {e}")
            return 0
    
    async def _generate_spawn_requests(
        self,
        spawn_count: int,
        current_time: datetime
    ) -> List[SpawnRequest]:
        """Generate individual spawn requests at depot location"""
        # If no routes available, cannot spawn passengers
        if not self.available_routes:
            self.logger.warning(
                f"Depot {self.depot_id} has no available routes - cannot spawn passengers"
            )
            return []
        
        spawn_requests = []
        
        for i in range(spawn_count):
            try:
                # All passengers spawn at depot location
                spawn_lat, spawn_lon = self.depot_location
                
                # Randomly assign destination route from associated routes
                destination_route = random.choice(self.available_routes)
                
                # Generate unique passenger ID
                passenger_id = f"DEPOT_{self.depot_id}_{uuid.uuid4().hex[:8].upper()}"
                
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
                
            except Exception as e:
                self.logger.debug(f"Error generating depot spawn request {i}: {e}")
                continue
        
        return spawn_requests
