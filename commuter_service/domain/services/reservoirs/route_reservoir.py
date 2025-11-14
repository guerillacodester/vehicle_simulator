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

# Import WebSocket event emitter (will be imported dynamically to avoid circular deps)
_emit_passenger_event = None


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
            spawn_request.passenger_id = f"PASS_{uuid.uuid4().hex[:8].upper()}"
        
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
                req.passenger_id = f"PASS_{uuid.uuid4().hex[:8].upper()}"
            
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
            
            # Emit WebSocket events for spawned passengers
            await self._emit_spawn_events(spawn_requests)
        
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

    async def _emit_spawn_events(self, spawn_requests: List[SpawnRequest]):
        """Emit websocket events for spawned passengers.

        This dynamically imports the emitter to avoid circular imports when the
        HTTP interface registers the global ConnectionManager.
        """
        try:
            # Import emitter dynamically to avoid import cycles
            from commuter_service.interfaces.http.commuter_manifest import emit_passenger_event
        except Exception as e:
            self.logger.debug(f"WebSocket emitter not available: {e}")
            return

        # Fire-and-forget emission for each spawned passenger
        for req in spawn_requests:
            try:
                passenger_data = {
                    'passenger_id': req.passenger_id,
                    'route_id': req.route_id,
                    'spawned_at': req.spawn_time.isoformat() if hasattr(req.spawn_time, 'isoformat') else str(req.spawn_time),
                    'latitude': req.spawn_location[0],
                    'longitude': req.spawn_location[1],
                    'destination_lat': req.destination_location[0],
                    'destination_lon': req.destination_location[1],
                    'status': 'WAITING'
                }

                # Don't await to avoid slowing down DB writes; schedule on loop
                asyncio.create_task(emit_passenger_event('spawned', passenger_data, route_id=req.route_id))
            except Exception as e:
                self.logger.debug(f"Failed to emit spawn event for {req.passenger_id}: {e}")

    
    
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
        success = await self.passenger_repo.mark_boarded(passenger_id, vehicle_id=vehicle_id)
        
        if success:
            # Invalidate cache for this route
            # (Note: we'd need route_id - could fetch passenger first)
            
            self.logger.debug(f"✅ Marked {passenger_id} as boarded/picked up")
            
            # Emit boarded event
            try:
                # Get passenger details for event
                passengers = await self.passenger_repo.get_waiting_passengers_by_route(
                    route_id=None,  # Will search all routes
                    limit=1
                )
                # Find our passenger
                passenger_data = None
                for p in passengers:
                    if p.get('passenger_id') == passenger_id:
                        passenger_data = p
                        break
                
                if passenger_data:
                    await self._emit_state_change_event(
                        'boarded',
                        passenger_data,
                        vehicle_id=vehicle_id
                    )
            except Exception as e:
                self.logger.debug(f"Failed to emit boarded event: {e}")
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
        # Get passenger data before marking alighted (for event emission)
        try:
            passenger_data = None
            passengers = await self.passenger_repo.get_waiting_passengers_by_route(
                route_id=None,
                limit=1000
            )
            for p in passengers:
                if p.get('passenger_id') == passenger_id:
                    passenger_data = p
                    break
        except:
            passenger_data = None
        
        # Update status in database via PassengerRepository
        success = await self.passenger_repo.mark_alighted(passenger_id)
        
        if success:
            self.logger.debug(f"✅ Marked {passenger_id} as alighted/dropped off")
            
            # Emit alighted event
            if passenger_data:
                try:
                    await self._emit_state_change_event(
                        'alighted',
                        passenger_data
                    )
                except Exception as e:
                    self.logger.debug(f"Failed to emit alighted event: {e}")
        else:
            self.logger.warning(f"❌ Failed to mark {passenger_id} as alighted")
        
        return success
    
    async def _emit_state_change_event(self, event_type: str, passenger_data: dict, vehicle_id: Optional[str] = None):
        """Emit state change event (boarded/alighted)"""
        try:
            from commuter_service.interfaces.http.commuter_manifest import emit_passenger_event
        except Exception as e:
            self.logger.debug(f"WebSocket emitter not available: {e}")
            return
        
        # Build event payload
        event_payload = {
            'passenger_id': passenger_data.get('passenger_id'),
            'route_id': passenger_data.get('route_id'),
            'latitude': passenger_data.get('latitude'),
            'longitude': passenger_data.get('longitude'),
            'destination_lat': passenger_data.get('destination_lat'),
            'destination_lon': passenger_data.get('destination_lon'),
            'status': passenger_data.get('status')
        }
        
        if event_type == 'boarded' and vehicle_id:
            event_payload['vehicle_id'] = vehicle_id
            event_payload['boarded_at'] = passenger_data.get('boarded_at')
        elif event_type == 'alighted':
            event_payload['vehicle_id'] = passenger_data.get('vehicle_id')
            event_payload['alighted_at'] = passenger_data.get('alighted_at')
        
        # Schedule emission
        asyncio.create_task(emit_passenger_event(
            event_type,
            event_payload,
            route_id=passenger_data.get('route_id')
        ))
    
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
