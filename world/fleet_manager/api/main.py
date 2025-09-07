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
)

# Initialize database
try:
    init_engine()
    print("✅ Database connection established")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="Fleet Management API",
    description="Comprehensive CRUD API for vehicle fleet management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Fleet Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "countries": "/api/v1/countries",
            "depots": "/api/v1/depots", 
            "vehicles": "/api/v1/vehicles",
            "drivers": "/api/v1/drivers",
            "stops": "/api/v1/stops",
            "trips": "/api/v1/trips",
            "services": "/api/v1/services",
            "blocks": "/api/v1/blocks"
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
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
