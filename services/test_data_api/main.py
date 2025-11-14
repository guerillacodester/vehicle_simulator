"""
Standalone test data API service for vehicle simulator.
Provides vehicles, drivers, and routes without requiring Strapi.
Can be used for autonomous testing and demonstrations.

Usage:
    python -m services.test_data_api --port 5002
    
Then configure simulator to use: http://localhost:5002
"""
import sys
from pathlib import Path
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class VehicleData(BaseModel):
    """Vehicle data model"""
    vehicle_reg_code: str
    vehicle_id: str
    route_id: str
    vehicle_status: str = "available"


class DriverData(BaseModel):
    """Driver data model"""
    driver_id: str
    driver_name: str
    assigned_route_id: str


class RouteData(BaseModel):
    """Route data model"""
    route_code: str
    route_id: str
    route_name: str
    geometry: Dict[str, Any]


# ============================================================================
# TEST DATA
# ============================================================================

TEST_VEHICLES = [
    {
        "vehicle_id": "vehicle-1",
        "vehicle_reg_code": "ZR102",
        "route_id": "route-1",
        "vehicle_status": "available"
    },
    {
        "vehicle_id": "vehicle-2",
        "vehicle_reg_code": "ZR103",
        "route_id": "route-1",
        "vehicle_status": "available"
    },
]

TEST_DRIVERS = [
    {
        "driver_id": "driver-1",
        "driver_name": "Alice Johnson",
        "assigned_route_id": "route-1"
    },
    {
        "driver_id": "driver-2",
        "driver_name": "Bob Smith",
        "assigned_route_id": "route-1"
    },
]

TEST_ROUTES = [
    {
        "route_code": "route-1",
        "route_id": "route-1",
        "route_name": "Demo Route 1",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-74.0050, 40.7128],
                [-74.0040, 40.7140],
                [-74.0030, 40.7140],
                [-74.0020, 40.7130],
                [-74.0010, 40.7120],
                [-74.0020, 40.7110],
                [-74.0030, 40.7110],
                [-74.0040, 40.7120],
                [-74.0050, 40.7128],
            ]
        }
    }
]


# ============================================================================
# APP
# ============================================================================

app = FastAPI(
    title="Test Data API",
    description="Lightweight data service for vehicle simulator testing",
    version="1.0.0"
)


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "test-data-api"
    }


@app.get("/vehicles", response_model=Dict[str, Any])
async def get_vehicles():
    """Get test vehicles"""
    return {
        "data": TEST_VEHICLES,
        "count": len(TEST_VEHICLES)
    }


@app.get("/vehicles/{vehicle_id}", response_model=Dict[str, Any])
async def get_vehicle(vehicle_id: str):
    """Get specific vehicle"""
    for v in TEST_VEHICLES:
        if v["vehicle_id"] == vehicle_id or v["vehicle_reg_code"] == vehicle_id:
            return {"data": v}
    raise HTTPException(status_code=404, detail="Vehicle not found")


@app.get("/drivers", response_model=Dict[str, Any])
async def get_drivers():
    """Get test drivers"""
    return {
        "data": TEST_DRIVERS,
        "count": len(TEST_DRIVERS)
    }


@app.get("/drivers/{driver_id}", response_model=Dict[str, Any])
async def get_driver(driver_id: str):
    """Get specific driver"""
    for d in TEST_DRIVERS:
        if d["driver_id"] == driver_id:
            return {"data": d}
    raise HTTPException(status_code=404, detail="Driver not found")


@app.get("/routes", response_model=Dict[str, Any])
async def get_routes():
    """Get test routes"""
    return {
        "data": TEST_ROUTES,
        "count": len(TEST_ROUTES)
    }


@app.get("/routes/{route_id}", response_model=Dict[str, Any])
async def get_route(route_id: str):
    """Get specific route"""
    for r in TEST_ROUTES:
        if r["route_id"] == route_id or r["route_code"] == route_id:
            return {"data": r}
    raise HTTPException(status_code=404, detail="Route not found")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Data API")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5002, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()
    
    uvicorn.run(
        "services.test_data_api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
