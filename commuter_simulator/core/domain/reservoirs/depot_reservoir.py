"""
Depot Reservoir - DB-backed with optional Redis caching for depot-spawned commuters.

This is a DB-backed adapter similar to RouteReservoir. DepotReservoir stores
spawned passengers in Strapi with a depot_id and can query waiting passengers
for that depot. Redis can be used as an optional L1 cache; TTL or explicit
invalidations should be used when state changes occur.
"""

import logging
import uuid
from typing import List, Dict, Optional, Tuple

from commuter_simulator.core.domain.spawner_engine import ReservoirInterface, SpawnRequest
from commuter_simulator.infrastructure.database.passenger_repository import PassengerRepository


class DepotReservoir(ReservoirInterface):
    """DB-backed depot reservoir with optional Redis cache."""

    def __init__(
        self,
        depot_id: str,
        passenger_repository: PassengerRepository,
        redis_client: Optional[object] = None,
        cache_ttl_seconds: int = 60,
        enable_redis_cache: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.depot_id = depot_id
        self.passenger_repo = passenger_repository
        self.redis_client = redis_client if enable_redis_cache else None
        self.cache_ttl = cache_ttl_seconds
        self.enable_cache = enable_redis_cache and redis_client is not None
        self.logger = logger or logging.getLogger(__name__)

        cache_type = "Redis-backed" if self.enable_cache else "DB-backed (Redis disabled)"
        self.logger.info(f"[DepotReservoir] Initialized for depot {depot_id} as {cache_type} adapter")

    async def push(self, spawn_request: SpawnRequest) -> str:
        """Persist a single spawned passenger to Strapi with depot_id set."""
        if not spawn_request.passenger_id:
            spawn_request.passenger_id = f"PASS_{uuid.uuid4().hex[:8].upper()}"

        # Build a human-friendly destination name when none is provided
        dest_name = f"Depot {self.depot_id}"

        success = await self.passenger_repo.insert_passenger(
            passenger_id=spawn_request.passenger_id,
            route_id=spawn_request.route_id or "",
            latitude=spawn_request.spawn_location[0],
            longitude=spawn_request.spawn_location[1],
            destination_lat=spawn_request.destination_location[0],
            destination_lon=spawn_request.destination_location[1],
            destination_name=dest_name,
            depot_id=self.depot_id,
            spawned_at=spawn_request.spawn_time,
        )

        if success:
            # invalidate cache for this depot if using redis
            if self.enable_cache:
                try:
                    await self.redis_client.delete(f"depot_reservoir:{self.depot_id}:passengers")
                except Exception:
                    self.logger.debug("Failed to invalidate redis cache for depot")

            self.logger.debug(f"✅ Inserted passenger {spawn_request.passenger_id} at depot {self.depot_id}")
        else:
            self.logger.error(f"❌ Failed to insert passenger {spawn_request.passenger_id} at depot {self.depot_id}")

        return spawn_request.passenger_id

    async def push_batch(self, spawn_requests: List[SpawnRequest]) -> Tuple[int, int]:
        """Persist multiple spawned passengers using bulk insert for performance."""
        if not spawn_requests:
            return (0, 0)

        dest_name = f"Depot {self.depot_id}"
        passengers = []
        for req in spawn_requests:
            if not req.passenger_id:
                req.passenger_id = f"PASS_{uuid.uuid4().hex[:8].upper()}"

            passengers.append({
                "passenger_id": req.passenger_id,
                "route_id": req.route_id or "",
                "depot_id": self.depot_id,
                "latitude": req.spawn_location[0],
                "longitude": req.spawn_location[1],
                "destination_name": dest_name,
                "destination_lat": req.destination_location[0],
                "destination_lon": req.destination_location[1],
                "spawned_at": req.spawn_time,
            })

        successful, failed = await self.passenger_repo.bulk_insert_passengers(passengers)

        if successful > 0 and self.enable_cache:
            try:
                await self.redis_client.delete(f"depot_reservoir:{self.depot_id}:passengers")
            except Exception:
                self.logger.debug("Failed to invalidate redis cache for depot after batch insert")

        self.logger.info(f"✅ Depot batch push: {successful} inserted, {failed} failed for depot {self.depot_id}")
        return (successful, failed)

    async def available(self, route_id: str = None, limit: int = 100) -> List[Dict]:
        """Return waiting passengers for this depot. Optionally filter by destination route."""
        # For depot-level queries, get WAITING passengers with depot_id filter
        results = await self.passenger_repo.get_waiting_passengers_by_depot(self.depot_id, limit=limit)

        if route_id:
            results = [r for r in results if r.get("route_id") == route_id]

        return results[:limit]

    async def mark_picked_up(self, passenger_id: str, vehicle_id: Optional[str] = None) -> bool:
        """Mark passenger as boarded in Strapi (and invalidate cache)."""
        success = await self.passenger_repo.mark_boarded(passenger_id)
        if success and self.enable_cache:
            try:
                await self.redis_client.delete(f"depot_reservoir:{self.depot_id}:passengers")
            except Exception:
                self.logger.debug("Failed to invalidate redis cache for depot after pickup")

        return success

    async def mark_dropped_off(self, passenger_id: str) -> bool:
        """Mark passenger as alighted in Strapi."""
        return await self.passenger_repo.mark_alighted(passenger_id)

    async def get_stats(self) -> Dict:
        return {
            "type": "DepotReservoir",
            "depot_id": self.depot_id,
            "source": "Strapi API (DB-backed)",
        }
