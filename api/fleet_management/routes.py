"""
Fleet Management Routes
======================
Handle uploading and managing routes, timetables, vehicles by country
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Optional
import json
import os
import shutil
from datetime import datetime
import logging

from .services import FleetService
from .models import UploadResponse, CountryData, VehicleData

logger = logging.getLogger(__name__)
router = APIRouter()
fleet_service = FleetService()

@router.post("/upload/routes", response_model=UploadResponse)
async def upload_routes(
    background_tasks: BackgroundTasks,
    country: str = Form(...),
    route_files: List[UploadFile] = File(...)
):
    """
    Upload GeoJSON route files for a specific country
    
    - **country**: Country code (e.g., 'barbados', 'jamaica')
    - **route_files**: One or more .geojson files containing route data
    """
    try:
        logger.info(f"📍 Uploading {len(route_files)} route files for {country}")
        
        # Validate files
        for file in route_files:
            if not file.filename.endswith('.geojson'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be a .geojson file")
        
        # Save files and process in background
        uploaded_files = []
        for file in route_files:
            file_path = await fleet_service.save_upload_file(file, "routes", country)
            uploaded_files.append(file_path)
        
        # Process routes in background
        background_tasks.add_task(
            fleet_service.process_routes,
            uploaded_files,
            country
        )
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {len(route_files)} route files for {country}",
            files_processed=len(route_files),
            country=country,
            upload_type="routes"
        )
        
    except Exception as e:
        logger.error(f"❌ Error uploading routes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/timetables", response_model=UploadResponse)
async def upload_timetables(
    background_tasks: BackgroundTasks,
    country: str = Form(...),
    timetable_files: List[UploadFile] = File(...)
):
    """
    Upload JSON timetable files for a specific country
    
    - **country**: Country code
    - **timetable_files**: One or more .json files containing timetable data
    """
    try:
        logger.info(f"📅 Uploading {len(timetable_files)} timetable files for {country}")
        
        # Validate files
        for file in timetable_files:
            if not file.filename.endswith('.json'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be a .json file")
        
        # Save files and process in background
        uploaded_files = []
        for file in timetable_files:
            file_path = await fleet_service.save_upload_file(file, "timetables", country)
            uploaded_files.append(file_path)
        
        # Process timetables in background
        background_tasks.add_task(
            fleet_service.process_timetables,
            uploaded_files,
            country
        )
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {len(timetable_files)} timetable files for {country}",
            files_processed=len(timetable_files),
            country=country,
            upload_type="timetables"
        )
        
    except Exception as e:
        logger.error(f"❌ Error uploading timetables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/vehicles", response_model=UploadResponse)
async def upload_vehicles(
    background_tasks: BackgroundTasks,
    country: str = Form(...),
    vehicle_files: List[UploadFile] = File(...)
):
    """
    Upload JSON vehicle files for a specific country
    
    - **country**: Country code
    - **vehicle_files**: One or more .json files containing vehicle data
    """
    try:
        logger.info(f"🚌 Uploading {len(vehicle_files)} vehicle files for {country}")
        
        # Validate files
        for file in vehicle_files:
            if not file.filename.endswith('.json'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be a .json file")
        
        # Save files and process in background
        uploaded_files = []
        for file in vehicle_files:
            file_path = await fleet_service.save_upload_file(file, "vehicles", country)
            uploaded_files.append(file_path)
        
        # Process vehicles in background
        background_tasks.add_task(
            fleet_service.process_vehicles,
            uploaded_files,
            country
        )
        
        return UploadResponse(
            success=True,
            message=f"Successfully uploaded {len(vehicle_files)} vehicle files for {country}",
            files_processed=len(vehicle_files),
            country=country,
            upload_type="vehicles"
        )
        
    except Exception as e:
        logger.error(f"❌ Error uploading vehicles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries", response_model=List[CountryData])
async def list_countries():
    """
    List all countries with fleet data
    """
    try:
        countries = await fleet_service.get_countries()
        return countries
    except Exception as e:
        logger.error(f"❌ Error getting countries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries/{country}/routes")
async def get_country_routes(country: str):
    """
    Get all routes for a specific country
    """
    try:
        routes = await fleet_service.get_country_routes(country)
        return {"country": country, "routes": routes}
    except Exception as e:
        logger.error(f"❌ Error getting routes for {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/countries/{country}/vehicles")
async def get_country_vehicles(country: str):
    """
    Get all vehicles for a specific country
    """
    try:
        vehicles = await fleet_service.get_country_vehicles(country)
        return {"country": country, "vehicles": vehicles}
    except Exception as e:
        logger.error(f"❌ Error getting vehicles for {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/countries/{country}")
async def delete_country_data(country: str):
    """
    Delete all fleet data for a specific country
    """
    try:
        result = await fleet_service.delete_country_data(country)
        return {"message": f"Successfully deleted data for {country}", "deleted": result}
    except Exception as e:
        logger.error(f"❌ Error deleting data for {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
