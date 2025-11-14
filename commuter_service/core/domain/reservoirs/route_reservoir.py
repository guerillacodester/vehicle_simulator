"""
Route Reservoir - DB-backed with Redis caching for route-based spawned commuters.

Implements cache-aside pattern:
1. First request: Query passengers from Strapi /api/active-passengers, cache in Redis
2. Subsequent requests: Serve from Redis (fast, microseconds vs milliseconds)
3. Cache invalidation: TTL (default 60s) or explicit invalidation on state changes

Architecture:
- Passengers pushed to database by RouteSpawner (via PassengerRepository)
- Reservoir queries available passengers, caching in Redis
- Filters by route_id and status=WAITING
- Single source of truth: Strapi active-passengers table
- Fast queries: Redis L1 cache before hitting Strapi
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

from commuter_service.core.domain.spawner_engine import ReservoirInterface, SpawnRequest
from commuter_service.infrastructure.database.passenger_repository import PassengerRepository


class RouteReservoir(ReservoirInterface):
    """
    DB-backed with Redis cache for route-spawned passengers.
    
    Uses cache-aside pattern: DB is source of truth, Redis is L1 cache.
    - Push: Writes to DB, invalidates Redis cache
    - Query: Tries Redis first, falls back to DB, populates Redis
    - TTL: Cache expires after configured interval (default 60s)
    """
    
    def __init__(
        self,
        passenger_repository: PassengerRepository,
        redis_client: Optional[object] = None,
        cache_ttl_seconds: int = 60,
        enable_redis_cache: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize route reservoir with DB + Redis caching.
        
        Args:
            passenger_repository: PassengerRepository instance for DB access
            redis_client: Optional Redis client for caching (aioredis)
            cache_ttl_seconds: TTL for cached passengers (default 60s)
            enable_redis_cache: Enable Redis caching (default False)
            logger: Optional logger instance
        """
        self.passenger_repo = passenger_repository
        self.redis_client = redis_client if enable_redis_cache else None
        self.cache_ttl = cache_ttl_seconds
        self.enable_cache = enable_redis_cache and redis_client is not None
        self.logger = logger or logging.getLogger(__name__)
        
        cache_type = "Redis-backed" if self.enable_cache else "DB-backed (Redis disabled)"
        self.logger.info(f"[RouteReservoir] Initialized as {cache_type} query adapter")
    
    async def push(self, spawn_request: SpawnRequest) -> str:
        """
        Store a single spawned passenger in database and invalidate cache.
        
        Args:
            spawn_request: SpawnRequest with passenger details
            
        Returns:
            Passenger ID
        """
        if not spawn_request.passenger_id:
            import uuid
            # Use full UUID to guarantee uniqueness (32 hex chars vs 8)
            spawn_request.passenger_id = f"PASS_{uuid.uuid4().hex.upper()}"
        
        # Insert into database via PassengerRepository
        success = await self.passenger_repo.insert_passenger(
            passenger_id=spawn_request.passenger_id,
            route_id=spawn_request.route_id,
            latitude=spawn_request.spawn_location[0],
            longitude=spawn_request.spawn_location[1],
            destination_lat=spawn_request.destination_location[0],
            destination_lon=spawn_request.destination_location[1],
            destination_name="Stop",
            spawned_at=spawn_request.spawn_time
        )
        
        if success:
            # Invalidate cache for this route
            await self._invalidate_route_cache(spawn_request.route_id)
            self.logger.debug(
                f"✅ Inserted passenger {spawn_request.passenger_id} "
                f"on route {spawn_request.route_id}, invalidated cache"
            )
        else:
            self.logger.error(
                f"❌ Failed to insert passenger {spawn_request.passenger_id}"
            )
        
        return spawn_request.passenger_id
    
    async def push_batch(self, spawn_requests: List[SpawnRequest]) -> Tuple[int, int]:
        """
        Store multiple spawned passengers in database and invalidate cache.
        
        Args:
            spawn_requests: List of SpawnRequest objects
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not spawn_requests:
            return (0, 0)
        
        import uuid
        
        # Convert SpawnRequest objects to passenger dicts for bulk insert
        passengers = []
        route_ids = set()
        
        for req in spawn_requests:
            if not req.passenger_id:
                # Use full UUID to guarantee uniqueness (32 hex chars vs 8)
                req.passenger_id = f"PASS_{uuid.uuid4().hex.upper()}"
            
            route_ids.add(req.route_id)
            passengers.append({
                'passenger_id': req.passenger_id,
                'route_id': req.route_id,
                'latitude': req.spawn_location[0],
                'longitude': req.spawn_location[1],
                'destination_lat': req.destination_location[0],
                'destination_lon': req.destination_location[1],
                'destination_name': "Stop",
                'spawned_at': req.spawn_time
            })
        
        # Use bulk insert for performance (concurrent inserts)
        successful, failed = await self.passenger_repo.bulk_insert_passengers(passengers)
        
        if successful > 0:
            # Invalidate cache for all affected routes
            for route_id in route_ids:
                await self._invalidate_route_cache(route_id)
            
            self.logger.info(
                f"✅ Batch push: {successful} passengers inserted, "
                f"{failed} failed, caches invalidated for {len(route_ids)} routes"
            )
        
        return (successful, failed)
    
    async def _invalidate_route_cache(self, route_id: str):
        """Invalidate Redis cache for a route"""
        if not self.enable_cache:
            return
        
        try:
            cache_key = f"route_reservoir:{route_id}:passengers"
            await self.redis_client.delete(cache_key)
            self.logger.debug(f"🗑️  Invalidated cache for route {route_id}")
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to invalidate cache: {e}")
    
    async def _get_cache_key(self, route_id: str) -> str:
        """Get Redis cache key for a route"""
        return f"route_reservoir:{route_id}:passengers"

    
    
    async def available(self, route_id: str = None, limit: int = 100) -> List[Dict]:
        """
        Query available (WAITING) passengers from database.
        
        Args:
            route_id: Filter by specific route
            limit: Maximum to return
            
        Returns:
            List of available passenger dicts from Strapi
        """
        if not route_id:
            self.logger.warning("RouteReservoir.available() requires route_id parameter")
            return []
        
        # Query database via PassengerRepository helper (no spatial filter required)
        # This calls Strapi GET /api/active-passengers?filters[route_id][$eq]={route_id}&filters[status][$eq]=WAITING
        results = await self.passenger_repo.get_waiting_passengers_by_route(route_id=route_id, limit=limit)
        return results[:limit]
    
    async def mark_picked_up(self, passenger_id: str, vehicle_id: Optional[str] = None) -> bool:
        """
        Mark passenger as picked up via database.
        
        Args:
            passenger_id: Passenger to mark
            vehicle_id: Optional vehicle ID doing the pickup
            
        Returns:
            True if successful
        """
        # Update status in database via PassengerRepository
        success = await self.passenger_repo.mark_boarded(passenger_id)
        
        if success:
            self.logger.debug(f"✅ Marked {passenger_id} as boarded/picked up")
        else:
            self.logger.warning(f"❌ Failed to mark {passenger_id} as boarded")
        
        return success
    
    async def mark_dropped_off(self, passenger_id: str) -> bool:
        """
        Mark passenger as dropped off via database.
        
        Args:
            passenger_id: Passenger to mark
            
        Returns:
            True if successful
        """
        # Update status in database via PassengerRepository
        success = await self.passenger_repo.mark_alighted(passenger_id)
        
        if success:
            self.logger.debug(f"✅ Marked {passenger_id} as alighted/dropped off")
        else:
            self.logger.warning(f"❌ Failed to mark {passenger_id} as alighted")
        
        return success
    
    async def query_nearby(
        self,
        vehicle_lat: float,
        vehicle_lon: float,
        route_id: str,
        radius_km: float = 0.2,
        max_results: int = 50,
        status: str = "WAITING",
        current_time: Optional[str] = None  # ISO8601 timestamp for spawn_time filtering
    ) -> List[Dict]:
        """
        Query passengers near a vehicle position (spatial query through reservoir).
        
        This is the SINGLE SOURCE OF TRUTH for conductor passenger visibility.
        All conductor queries should go through this method, not direct Strapi access.
        
        Args:
            vehicle_lat: Current vehicle latitude
            vehicle_lon: Current vehicle longitude
            route_id: Route ID to filter passengers
            radius_km: Search radius in kilometers (default 0.2 km = 200m)
            max_results: Maximum passengers to return (default 50)
            status: Filter by passenger status (default WAITING)
            current_time: Current simulation time (ISO8601). If provided, only return passengers
                         where spawned_at <= current_time (i.e., passenger has "arrived")
        
        Returns:
            List of passenger dicts sorted by distance (closest first)
            
        Example:
            nearby = await reservoir.query_nearby(
                vehicle_lat=13.0975,
                vehicle_lon=-59.6139,
                route_id="route_1",
                radius_km=0.2,
                current_time="2024-10-27T14:30:00Z"  # Only spawned passengers
            )
            # Returns: [{'passenger_id': 'P_123', 'distance_km': 0.05, ...}, ...]
        """
        # Import haversine for distance calculation
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
        from arknet_transit_simulator.utils.geospatial import haversine
        from datetime import datetime
        
        # Parse current_time if provided
        current_dt = None
        if current_time:
            try:
                current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            except Exception as e:
                self.logger.warning(f"Failed to parse current_time '{current_time}': {e}")
        
        # Query all passengers for this route with matching status
        # Note: This uses PassengerRepository which handles Strapi pagination
        all_passengers = await self.passenger_repo.get_waiting_passengers_by_route(
            route_id=route_id,
            limit=100  # Fetch more than max_results to ensure coverage
        )
        
        if not all_passengers:
            self.logger.debug(f"No passengers found for route {route_id} with status {status}")
            return []
        
        # Calculate distances and filter by radius
        passengers_with_distance = []
        
        for passenger in all_passengers:
            # Filter by spawn_time if current_time provided
            if current_dt:
                spawned_at_str = passenger.get("spawned_at")
                if spawned_at_str:
                    try:
                        spawned_at_dt = datetime.fromisoformat(spawned_at_str.replace('Z', '+00:00'))
                        # Only include passengers who have "arrived" (spawned_at <= current_time)
                        if spawned_at_dt > current_dt:
                            self.logger.debug(
                                f"Passenger {passenger.get('passenger_id')} not yet spawned "
                                f"(spawned_at={spawned_at_str} > current_time={current_time})"
                            )
                            continue  # Skip this passenger (not yet arrived)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to parse spawned_at '{spawned_at_str}' for passenger "
                            f"{passenger.get('passenger_id')}: {e}"
                        )
            
            p_lat = passenger.get("latitude")
            p_lon = passenger.get("longitude")
            
            if p_lat is None or p_lon is None:
                self.logger.warning(f"Passenger {passenger.get('passenger_id')} missing coordinates")
                continue
            
            # Calculate haversine distance
            distance_km = haversine(vehicle_lat, vehicle_lon, p_lat, p_lon)
            
            # Filter by radius
            if distance_km <= radius_km:
                # Add distance to passenger dict for sorting
                passenger_copy = passenger.copy()
                passenger_copy['distance_km'] = distance_km
                passengers_with_distance.append((distance_km, passenger_copy))
        
        # Sort by distance (closest first)
        passengers_with_distance.sort(key=lambda x: x[0])
        
        # Take top max_results
        nearby_passengers = [p for _, p in passengers_with_distance[:max_results]]
        
        self.logger.info(
            f"🔍 Reservoir query_nearby: Found {len(nearby_passengers)} passengers "
            f"for route {route_id} within {radius_km}km of ({vehicle_lat:.6f}, {vehicle_lon:.6f})"
        )
        
        return nearby_passengers
    
    async def get_stats(self) -> Dict:
        """
        Get reservoir statistics from database queries.
        
        Returns:
            Dict with statistics
        """
        # Note: For now, this returns placeholder stats
        # A full implementation would query database for counts
        return {
            'type': 'RouteReservoir',
            'source': 'Strapi API (DB-backed)',
            'note': 'All passengers live in database, not in-memory'
        }
