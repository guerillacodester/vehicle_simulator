#!/usr/bin/env python3
# world/fleet_manager/api/app.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from world.fleet_manager.api.routers import countries as countries_router


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

    return app


# Uvicorn entrypoint
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("world.fleet_manager.api.app:app", host="127.0.0.1", port=8000, reload=True)
