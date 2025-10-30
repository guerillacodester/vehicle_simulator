"""
Route Spawner Service
====================

FastAPI service that streams spawned passengers in real-time from routes.
Provides async generator-based streaming endpoint for route passenger spawning.

Endpoint:
  GET /spawn/route/{route_id}?time=HH:MM:SS&day=Monday&window=60

Response: NDJSON stream of SpawnRequest objects (1 JSON object per line)

Example:
  curl "http://localhost:4000/spawn/route/gg3pv3z19hhm117v9xth5ezq?time=09:00:00&day=Monday"
  
  Output:
  {"passenger_id":"PASS_ABC12345","spawn_location":[13.32661,-59.61552],...}
  {"passenger_id":"PASS_DEF67890","spawn_location":[13.32750,-59.61480],...}
  ...
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from commuter_simulator.core.domain.spawner_engine.route_spawner import RouteSpawner
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader
from commuter_simulator.infrastructure.geospatial.client import GeospatialClient
from commuter_simulator.infrastructure.database import PassengerRepository


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class SpawnRequestDTO(BaseModel):
    """DTO for streaming spawn requests"""
    passenger_id: str
    spawn_location: tuple  # (lat, lon)
    destination_location: tuple  # (lat, lon)
    route_id: str
    spawn_time: str
    spawn_context: str
    priority: float
    generation_method: str


class SpawnStats(BaseModel):
    """Statistics about a spawn operation"""
    route_id: str
    requested_time: str
    day_of_week: str
    spawn_window_minutes: int
    total_spawned: int
    success_count: int
    failed_count: int
    elapsed_seconds: float


# Create FastAPI app
app = FastAPI(
    title="Route Spawner Service",
    description="Stream-based route passenger spawning service",
    version="1.0.0"
)


class RouteSpawnerServiceManager:
    """Manages RouteSpawner instances and streaming"""
    
    def __init__(
        self,
        strapi_url: str = "http://localhost:1337",
        geo_url: str = "http://localhost:6000"
    ):
        self.strapi_url = strapi_url
        self.geo_url = geo_url
        self.logger = logging.getLogger(__name__)
        
        # Initialize infrastructure clients
        self.config_loader = SpawnConfigLoader(api_base_url=f"{strapi_url}/api")
        self.geo_client = GeospatialClient(base_url=geo_url)
        self.passenger_repo = None
        
    async def initialize(self):
        """Initialize repository connection"""
        try:
            self.passenger_repo = PassengerRepository(
                strapi_url=self.strapi_url,
                logger=self.logger
            )
            await self.passenger_repo.connect()
            self.logger.info("✅ RouteSpawnerService initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize: {e}")
            return False
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.passenger_repo:
            await self.passenger_repo.disconnect()
    
    async def spawn_route_stream(
        self,
        route_id: str,
        current_time: datetime,
        time_window_minutes: int = 60
    ) -> AsyncGenerator[str, None]:
        """
        Stream spawned passengers for a route as NDJSON.
        
        Yields one JSON line per passenger as they are generated.
        
        Args:
            route_id: Strapi route document ID
            current_time: Simulation time
            time_window_minutes: Spawn window in minutes
            
        Yields:
            NDJSON lines (one SpawnRequestDTO per line)
        """
        if not self.passenger_repo:
            raise RuntimeError("Service not initialized")
        
        try:
            # Create spawner instance for this route
            spawner = RouteSpawner(
                reservoir=None,  # We're just generating, not storing
                config={},
                route_id=route_id,
                config_loader=self.config_loader,
                geo_client=self.geo_client
            )
            
            self.logger.info(f"🎯 Spawning route {route_id} at {current_time}")
            
            # Generate spawn requests
            spawn_requests = await spawner.spawn(
                current_time=current_time,
                time_window_minutes=time_window_minutes
            )
            
            if not spawn_requests:
                self.logger.warning(f"No spawn requests generated for route {route_id}")
                return
            
            # Stream each spawn request as NDJSON
            for i, spawn_req in enumerate(spawn_requests, 1):
                try:
                    # Convert SpawnRequest to JSON
                    dto = SpawnRequestDTO(
                        passenger_id=spawn_req.passenger_id,
                        spawn_location=spawn_req.spawn_location,
                        destination_location=spawn_req.destination_location,
                        route_id=spawn_req.route_id,
                        spawn_time=spawn_req.spawn_time.isoformat() if hasattr(spawn_req.spawn_time, 'isoformat') else str(spawn_req.spawn_time),
                        spawn_context=spawn_req.spawn_context.name if hasattr(spawn_req.spawn_context, 'name') else str(spawn_req.spawn_context),
                        priority=spawn_req.priority,
                        generation_method=spawn_req.generation_method
                    )
                    
                    # Yield as NDJSON (newline-delimited JSON)
                    yield dto.model_dump_json() + "\n"
                    
                    self.logger.debug(f"  [{i}/{len(spawn_requests)}] Streamed {spawn_req.passenger_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error streaming spawn request {i}: {e}")
                    continue
            
            self.logger.info(f"✅ Spawning complete: {len(spawn_requests)} passengers streamed for route {route_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error spawning route {route_id}: {e}", exc_info=True)
            # Yield error as JSON
            error_dto = {"error": str(e), "route_id": route_id}
            yield json.dumps(error_dto) + "\n"


# Global service manager
service_manager: Optional[RouteSpawnerServiceManager] = None


@app.on_event("startup")
async def startup():
    """Initialize service on startup"""
    global service_manager
    service_manager = RouteSpawnerServiceManager(
        strapi_url="http://localhost:1337",
        geo_url="http://localhost:6000"
    )
    await service_manager.initialize()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global service_manager
    if service_manager:
        await service_manager.shutdown()


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RouteSpawnerService",
        "version": "1.0.0"
    }


@app.get("/spawn/route/{route_id}")
async def spawn_route(
    route_id: str,
    time: str = Query("09:00:00", description="Spawn time as HH:MM:SS"),
    day: str = Query("Monday", description="Day of week (Monday, Tuesday, ...)"),
    window: int = Query(60, description="Spawn window in minutes")
):
    """
    Stream passengers spawned for a route.
    
    Args:
        route_id: Strapi route document ID
        time: Spawn time (HH:MM:SS format)
        day: Day of week
        window: Time window in minutes
        
    Returns:
        NDJSON stream of SpawnRequest objects
    """
    if not service_manager:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        # Parse time
        time_parts = time.split(":")
        if len(time_parts) != 3:
            raise ValueError("Invalid time format, use HH:MM:SS")
        
        hour, minute, second = map(int, time_parts)
        
        # Get current date, then adjust to requested day
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        # Map day name to weekday
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        target_day = days.get(day.lower())
        if target_day is None:
            raise ValueError(f"Invalid day: {day}")
        
        # Calculate target date
        current_day = today.weekday()
        days_ahead = target_day - current_day
        if days_ahead < 0:
            days_ahead += 7
        spawn_date = today + timedelta(days=days_ahead)
        
        # Create datetime
        current_time = datetime.combine(spawn_date, datetime.min.time()).replace(
            hour=hour, minute=minute, second=second
        )
        
        logger.info(f"📊 Spawning route {route_id} on {spawn_date} at {time} (window={window}min)")
        
        # Return streaming response
        return StreamingResponse(
            service_manager.spawn_route_stream(
                route_id=route_id,
                current_time=current_time,
                time_window_minutes=window
            ),
            media_type="application/x-ndjson"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in spawn_route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           ROUTE SPAWNER SERVICE                           ║
    ║                                                           ║
    ║  Streaming endpoint for route passenger spawning         ║
    ║  Listening on http://localhost:4000                      ║
    ║                                                           ║
    ║  Example request:                                         ║
    ║  GET /spawn/route/gg3pv3z19hhm117v9xth5ezq             ║
    ║      ?time=09:00:00&day=Monday                           ║
    ║                                                           ║
    ║  Returns: NDJSON stream of SpawnRequest objects          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=4000,
        log_level="info"
    )
