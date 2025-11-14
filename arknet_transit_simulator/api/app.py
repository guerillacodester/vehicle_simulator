"""FastAPI application factory for fleet management."""

from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_simulator
from .models import HealthResponse
from .events import get_event_bus

# Import routers
from .routes import vehicles, conductors, control, websockets, simulator


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ArkNet Fleet Management API",
        description="Real-time fleet management and observability",
        version="0.1.0"
    )
    
    # Enable CORS for web clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(vehicles.router)
    app.include_router(conductors.router)
    app.include_router(control.router)
    app.include_router(simulator.router)
    app.include_router(websockets.router)
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        sim = get_simulator()
        bus = get_event_bus()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            simulator_running=sim._running,
            active_vehicles=len(sim.active_drivers),
            event_bus_stats=bus.get_stats()
        )
    
    return app
