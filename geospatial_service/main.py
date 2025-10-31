"""
Geospatial Services API - FastAPI
High-performance spatial query service for vehicle and passenger simulators

Provides:
- Reverse geocoding (lat/lon → address)
- Geofence detection (is point inside zone?)
- Route buildings query (buildings near transit routes)
- Depot catchment query (buildings near depot)

Performance targets:
- Reverse geocoding: <50ms
- Geofence check: <30ms
- Route buildings: <100ms
- Depot catchment: <150ms
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from api import geocoding_router, geofence_router, spatial_router
from api.spawn import router as spawn_router
from api.routes import router as routes_router
from api.depots import router as depots_router
from api.buildings import router as buildings_router
from api.analytics import router as analytics_router
from api.metadata import router as metadata_router
from services.postgis_client import postgis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Geospatial Services API...")
    await postgis_client.connect()
    
    stats = await postgis_client.get_stats()
    print(f"📊 Database stats:")
    print(f"   - Buildings: {stats['buildings']:,}")
    print(f"   - Highways: {stats['highways']:,}")
    print(f"   - POIs: {stats['pois']:,}")
    print(f"   - Landuse zones: {stats['landuse_zones']:,}")
    print(f"   - Regions: {stats['regions']:,}")
    print("✅ Geospatial Services API ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Geospatial Services API...")
    await postgis_client.disconnect()
    print("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Geospatial Services API",
    description="High-performance spatial queries for ArkNet Transit Simulator",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(geocoding_router)
app.include_router(geofence_router)
app.include_router(spatial_router)
app.include_router(spawn_router)
app.include_router(routes_router)
app.include_router(depots_router)
app.include_router(buildings_router)
app.include_router(analytics_router)
app.include_router(metadata_router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Geospatial Services API",
        "version": "2.0.0",
        "description": "Production-grade geospatial query and analysis API",
        "status": "operational",
        "endpoints": {
            "geocoding": "/geocode - Address resolution and reverse geocoding",
            "geofencing": "/geofence - Zone membership and boundary detection",
            "spatial": "/spatial - Core spatial queries and operations",
            "routes": "/routes - Route geometry, buildings, and metrics",
            "depots": "/depots - Depot catchments and service areas",
            "buildings": "/buildings - Building queries and density analysis",
            "spawn_analysis": "/spawn - Passenger spawn rate calculations",
            "analytics": "/analytics - Reporting and data visualization",
            "metadata": "/meta - Service metadata and dataset information",
            "documentation": "/docs - Interactive API documentation",
            "health": "/health - Health check endpoint"
        },
        "features": {
            "total_endpoints": "50+ endpoints",
            "solid_principles": "Applied - Single Responsibility, Separation of Concerns",
            "coverage": "Complete spectrum of geospatial operations",
            "production_ready": True
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    start_time = time.time()
    
    try:
        stats = await postgis_client.get_stats()
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "database": "connected",
            "features": stats,
            "latency_ms": round(latency_ms, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    import configparser
    from pathlib import Path
    
    # Load port from config.ini
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent.parent / "config.ini"
    config.read(config_path, encoding='utf-8')
    
    # Extract port from geospatial_url (e.g., "http://localhost:6000" -> 6000)
    geospatial_url = config.get('infrastructure', 'geospatial_url', fallback='http://localhost:6000')
    port = int(geospatial_url.split(':')[-1])
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
