"""
Fleet Management Services
========================
Business logic for fleet management operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import os
import json
import shutil
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path

from .models import CountryData, VehicleData, RouteData
from .database import db_service

logger = logging.getLogger(__name__)

class FleetService:
    """Service class for fleet management operations"""
    
    def __init__(self):
        self.upload_base_path = Path("uploads")
        self.upload_base_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        for subdir in ["routes", "vehicles", "timetables"]:
            (self.upload_base_path / subdir).mkdir(exist_ok=True)
    
    async def save_upload_file(self, file, file_type: str, country: str) -> str:
        """Save uploaded file to appropriate directory"""
        try:
            # Create country-specific directory
            country_dir = self.upload_base_path / file_type / country
            country_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = country_dir / filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"💾 Saved {file_type} file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Error saving file: {str(e)}")
            raise e
    
    async def process_routes(self, file_paths: List[str], country: str):
        """Process uploaded route files and save to database"""
        try:
            logger.info(f"🔄 Processing {len(file_paths)} route files for {country}")
            
            total_routes_saved = 0
            for file_path in file_paths:
                with open(file_path, 'r') as f:
                    try:
                        route_data = json.load(f)
                        # Validate GeoJSON structure
                        if 'features' in route_data:
                            logger.info(f"✅ Valid GeoJSON with {len(route_data['features'])} features")
                            # Save to database
                            routes_saved = await db_service.save_routes_from_geojson(route_data, country, file_path)
                            total_routes_saved += routes_saved
                        else:
                            logger.warning(f"⚠️ Invalid GeoJSON structure in {file_path}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON in {file_path}: {str(e)}")
            
            logger.info(f"🎯 Total routes processed for {country}: {total_routes_saved}")
                        
        except Exception as e:
            logger.error(f"❌ Error processing routes: {str(e)}")
            raise e
    
    async def process_vehicles(self, file_paths: List[str], country: str):
        """Process uploaded vehicle files and save to database"""
        try:
            logger.info(f"🔄 Processing {len(file_paths)} vehicle files for {country}")
            
            total_vehicles_saved = 0
            for file_path in file_paths:
                with open(file_path, 'r') as f:
                    try:
                        vehicle_data = json.load(f)
                        # Validate vehicle data structure
                        if isinstance(vehicle_data, list):
                            logger.info(f"✅ Valid vehicle list with {len(vehicle_data)} vehicles")
                            vehicles_saved = await db_service.save_vehicles_from_json(vehicle_data, country, file_path)
                            total_vehicles_saved += vehicles_saved
                        elif isinstance(vehicle_data, dict) and 'vehicles' in vehicle_data:
                            vehicles = vehicle_data['vehicles']
                            logger.info(f"✅ Valid vehicle data with {len(vehicles)} vehicles")
                            vehicles_saved = await db_service.save_vehicles_from_json(vehicles, country, file_path)
                            total_vehicles_saved += vehicles_saved
                        else:
                            logger.warning(f"⚠️ Invalid vehicle data structure in {file_path}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON in {file_path}: {str(e)}")
            
            logger.info(f"🎯 Total vehicles processed for {country}: {total_vehicles_saved}")
                        
        except Exception as e:
            logger.error(f"❌ Error processing vehicles: {str(e)}")
            raise e
    
    async def process_timetables(self, file_paths: List[str], country: str):
        """Process uploaded timetable files and save to database"""
        try:
            logger.info(f"🔄 Processing {len(file_paths)} timetable files for {country}")
            
            for file_path in file_paths:
                with open(file_path, 'r') as f:
                    try:
                        timetable_data = json.load(f)
                        # Validate timetable data structure
                        logger.info(f"✅ Processing timetable data from {file_path}")
                        # TODO: Save to database
                        await self._save_timetables_to_db(timetable_data, country, file_path)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON in {file_path}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"❌ Error processing timetables: {str(e)}")
    
    async def get_countries(self) -> List[CountryData]:
        """Get list of all countries with fleet data from database"""
        try:
            # Get data from database
            countries_data = await db_service.get_countries_with_data()
            
            # Convert to CountryData objects
            countries = []
            for country_info in countries_data:
                countries.append(CountryData(
                    country=country_info["country"],
                    routes_count=country_info["routes"],
                    vehicles_count=country_info["vehicles"],
                    timetables_count=0,  # TODO: implement timetables
                    last_updated=datetime.now()
                ))
            
            return countries
            
        except Exception as e:
            logger.error(f"❌ Error getting countries: {str(e)}")
            # Return default data if database fails
            return [CountryData(
                country="barbados",
                routes_count=0,
                vehicles_count=0,
                timetables_count=0,
                last_updated=datetime.now()
            )]
    
    async def get_country_routes(self, country: str) -> List[Dict]:
        """Get all routes for a specific country from database"""
        try:
            routes = await db_service.get_country_routes(country)
            return routes
        except Exception as e:
            logger.error(f"❌ Error getting routes for {country}: {str(e)}")
            return []
    
    async def get_country_vehicles(self, country: str) -> List[Dict]:
        """Get all vehicles for a specific country from database"""
        try:
            vehicles = await db_service.get_country_vehicles(country)
            return vehicles
        except Exception as e:
            logger.error(f"❌ Error getting vehicles for {country}: {str(e)}")
            return []
    
    async def delete_country_data(self, country: str) -> Dict[str, int]:
        """Delete all fleet data for a specific country"""
        try:
            # Delete from database
            db_result = await db_service.delete_country_data(country)
            
            # Also delete uploaded files
            file_result = {"routes": 0, "vehicles": 0, "timetables": 0}
            for file_type in ["routes", "vehicles", "timetables"]:
                country_dir = self.upload_base_path / file_type / country
                if country_dir.exists():
                    files = list(country_dir.glob("*"))
                    file_result[file_type] = len(files)
                    shutil.rmtree(country_dir)
                    logger.info(f"🗑️ Deleted {len(files)} {file_type} files for {country}")
            
            # Combine results
            return {
                "database": db_result,
                "files": file_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting data for {country}: {str(e)}")
            raise e