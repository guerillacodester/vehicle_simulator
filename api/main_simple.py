"""
Simple Fleet Management API - Testing Version
============================================
A simplified version to test basic functionality without file uploads initially
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Vehicle Simulator API starting up...")
    yield
    logger.info("🛑 Vehicle Simulator API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Vehicle Simulator API",
    description="Remote interface for fleet management and simulator control",
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates
templates = Jinja2Templates(directory="api/templates")

# Serve static files for uploads and assets  
app.mount("/static", StaticFiles(directory="api/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Vehicle Simulator API</title></head>
        <body>
            <h1>🚀 Vehicle Simulator API</h1>
            <p>API is running successfully!</p>
            <ul>
                <li><a href="/fleet-management">Fleet Management Interface</a></li>
                <li><a href="/docs">API Documentation</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/fleet-management", response_class=HTMLResponse)
async def fleet_management_interface(request: Request):
    """Professional fleet management interface"""
    return templates.TemplateResponse("fleet-management.html", {"request": request})

@app.get("/fleet/countries")
async def list_countries():
    """Get list of countries with fleet data - simplified version"""
    try:
        # Return mock data for now to test the interface
        return [
            {
                "country": "barbados",
                "routes_count": 3,
                "vehicles_count": 8,
                "timetables_count": 0,
                "last_updated": "2025-09-07T15:45:00"
            },
            {
                "country": "jamaica", 
                "routes_count": 5,
                "vehicles_count": 12,
                "timetables_count": 2,
                "last_updated": "2025-09-07T15:30:00"
            }
        ]
    except Exception as e:
        logger.error(f"❌ Error getting countries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fleet/countries/{country}/routes")
async def get_country_routes(country: str):
    """Get routes for a specific country - simplified version"""
    if country == "barbados":
        return {
            "country": country,
            "routes": [
                {
                    "route_id": "barbados_route_1",
                    "name": "Bridgetown to Speightstown",
                    "has_geometry": True,
                    "vehicle_count": 3
                },
                {
                    "route_id": "barbados_route_2", 
                    "name": "Bridgetown to Oistins",
                    "has_geometry": True,
                    "vehicle_count": 2
                },
                {
                    "route_id": "barbados_route_3",
                    "name": "Cross-Island Express", 
                    "has_geometry": True,
                    "vehicle_count": 3
                }
            ]
        }
    else:
        return {"country": country, "routes": []}

@app.get("/fleet/countries/{country}/vehicles")
async def get_country_vehicles(country: str):
    """Get vehicles for a specific country - simplified version"""
    if country == "barbados":
        return {
            "country": country,
            "vehicles": [
                {
                    "vehicle_id": "barbados_bus_001",
                    "status": "available", 
                    "route_id": "barbados_route_1",
                    "route_name": "Bridgetown to Speightstown"
                },
                {
                    "vehicle_id": "barbados_bus_002",
                    "status": "in_service",
                    "route_id": "barbados_route_1", 
                    "route_name": "Bridgetown to Speightstown"
                },
                {
                    "vehicle_id": "barbados_bus_003",
                    "status": "available",
                    "route_id": "barbados_route_2",
                    "route_name": "Bridgetown to Oistins"
                },
                {
                    "vehicle_id": "barbados_bus_004",
                    "status": "maintenance",
                    "route_id": None,
                    "route_name": None
                }
            ]
        }
    else:
        return {"country": country, "vehicles": []}

if __name__ == "__main__":
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=False)
