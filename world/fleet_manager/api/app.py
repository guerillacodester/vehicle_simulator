#!/usr/bin/env python3
# world/fleet_manager/api/app.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Routers
from world.fleet_manager.api.routers import routes as routes_router
from world.fleet_manager.api.routers import countries as countries_router
from world.fleet_manager.api.routers import depots as depots_router
from world.fleet_manager.api.routers import vehicles as vehicles_router
from world.fleet_manager.api.routers import shapes as shapes_router
from world.fleet_manager.api.routers import admin as admin_router
from world.fleet_manager.api.routers import timetables as timetables_router

# DB init
from world.fleet_manager.database import init_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Initialize engine + SSH tunnel ONCE at startup
    engine = init_engine()
    app.state.engine = engine
    try:
        yield
    finally:
        # optional: close engine/tunnel if you add stop handles in database.py
        pass

def create_app() -> FastAPI:
    """
    FastAPI application factory.
    Registers modular routers and shared middleware.
    """
    app = FastAPI(
        title="ArkNet FleetManager API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,   # ✅ attach lifespan
    )

    # CORS (adjust for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health probe
    @app.get("/healthz", tags=["meta"])
    def healthz() -> str:
        return "ok"

    # Register routers
    app.include_router(countries_router.router)
    app.include_router(depots_router.router)
    app.include_router(vehicles_router.router)
    app.include_router(routes_router.router)
    app.include_router(shapes_router.router)
    app.include_router(admin_router.router)
    app.include_router(timetables_router.router)
    
    return app

# Uvicorn entrypoint
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("world.fleet_manager.api.app:app", host="127.0.0.1", port=8000, reload=True)
