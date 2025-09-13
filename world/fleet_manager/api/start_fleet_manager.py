"""
FastAPI application for Fleet Management CRUD operations
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn
from typing import List
import sys
from pathlib import Path
import socketio

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from world.fleet_manager.database import get_session, init_engine
from world.fleet_manager.models import *
from world.fleet_manager.api.routers import (
    countries_router,
    depots_router,
    vehicles_router,
    drivers_router,
    stops_router,
    trips_router,
    services_router,
    blocks_router,
    routes_router,
    shapes_router,
    route_shapes_router,
    search_router,
)

# Initialize database
try:
    init_engine()
    print("✅ Database connection established")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Create Socket.io server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(
    title="Fleet Management API",
    description="Comprehensive CRUD API for vehicle fleet management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount Socket.io
socket_app = socketio.ASGIApp(sio, app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(countries_router, prefix="/api/v1")
app.include_router(depots_router, prefix="/api/v1") 
app.include_router(vehicles_router, prefix="/api/v1")
app.include_router(drivers_router, prefix="/api/v1")
app.include_router(stops_router, prefix="/api/v1")
app.include_router(trips_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(blocks_router, prefix="/api/v1")
app.include_router(routes_router, prefix="/api/v1")
app.include_router(shapes_router, prefix="/api/v1")
app.include_router(route_shapes_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")

# Socket.io event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"🔌 Client connected: {sid}")
    await sio.emit('connection_status', {'status': 'connected', 'server': 'online'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"🔌 Client disconnected: {sid}")

@sio.event
async def ping(sid, data):
    """Handle ping requests from clients"""
    await sio.emit('pong', {'timestamp': data.get('timestamp', None)}, room=sid)

@app.get("/")
async def root():
    """API root endpoint - Only public endpoints available"""
    return {
        "message": "Fleet Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "note": "Only public endpoints are available - all private endpoints have been removed",
        "public_endpoints": {
            "routes": "/api/v1/routes/public/",
            "route_geometry": "/api/v1/routes/public/{route_code}/geometry",
            "vehicles": "/api/v1/vehicles/public/",
            "vehicle_performance": "/api/v1/vehicles/public/{reg_code}/performance",
            "drivers": "/api/v1/drivers/public/",
            "shapes": "/api/v1/shapes/public/"
        },
        "deprecated": {
            "countries": "removed - was /api/v1/countries",
            "depots": "removed - was /api/v1/depots", 
            "stops": "removed - was /api/v1/stops",
            "trips": "removed - was /api/v1/trips",
            "services": "removed - was /api/v1/services",
            "blocks": "removed - was /api/v1/blocks"
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        result = db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "failed", "error": str(e)}

@app.get("/api/v1/simulator/status")
async def simulator_status():
    """Simulator status endpoint (placeholder for external monitoring)"""
    return {
        "status": "running",
        "service": "fleet_management_api",
        "version": "1.0.0",
        "simulator_active": False,
        "message": "This is the Fleet Management API, not a vehicle simulator"
    }

if __name__ == "__main__":
    # Run the app directly instead of using uvicorn.run() to avoid reload issues
    import uvicorn
    uvicorn.run(
        socket_app,  # Use socket_app instead of app for Socket.io support
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
