"""
Fleet Management Services
========================
Business logic for fleet management operations using GTFS API endpoints
Platform-agnostic and designed for distributed deployment
"""

import os
import json
import shutil
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .models import CountryData, VehicleData, RouteData
from .gtfs_api_client import GTFSAPIClient

logger = logging.getLogger(__name__)

class FleetService:
    """Service class for fleet management operations using GTFS API endpoints"""
    
    def __init__(self, api_base_url: Optional[str] = None):
        # Platform-agnostic upload directory
        self.upload_base_path = Path("uploads")
        self.upload_base_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        for subdir in ["routes", "vehicles", "timetables"]:
            (self.upload_base_path / subdir).mkdir(exist_ok=True)
            
        # Initialize API client with configurable base URL
        self.api_client = GTFSAPIClient(api_base_url)
        
    async def _ensure_country_exists(self, country_name: str) -> Dict[str, Any]:
        """Ensure country exists in database, create if not"""
        try:
            # Try to find existing country by name
            countries = await self.api_client.get_countries()
            for country in countries:
                if country.get("name", "").lower() == country_name.lower():
                    return country
            
            # Country doesn't exist, create it
            country_data = {
                "name": country_name,
                "iso_code": country_name[:3].upper()  # Simple ISO code generation
            }
            return await self.api_client.create_country(country_data)
            
        except Exception as e:
            logger.error(f"Error ensuring country exists: {e}")
            raise
    
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
        """Process uploaded route files and save via API"""
        try:
            logger.info(f"🔄 Processing {len(file_paths)} route files for {country}")
            
            # Ensure country exists
            country_record = await self._ensure_country_exists(country)
            country_id = country_record["country_id"]
            
            total_routes_saved = 0
            routes_to_create = []
            
            for file_path in file_paths:
                with open(file_path, 'r') as f:
                    try:
                        route_data = json.load(f)
                        # Validate GeoJSON structure
                        if 'features' in route_data:
                            logger.info(f"✅ Valid GeoJSON with {len(route_data['features'])} features")
                            
                            # Convert GeoJSON features to route data
                            for feature in route_data['features']:
                                properties = feature.get('properties', {})
                                geometry = feature.get('geometry', {})
                                
                                route_entry = {
                                    "country_id": country_id,
                                    "short_name": properties.get('name', f"Route {len(routes_to_create) + 1}"),
                                    "long_name": properties.get('description', properties.get('name', '')),
                                    "parishes": properties.get('parishes', []),
                                    "is_active": True
                                }
                                routes_to_create.append(route_entry)
                        else:
                            logger.warning(f"⚠️ Invalid GeoJSON structure in {file_path}")
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON in {file_path}: {str(e)}")
            
            # Bulk create routes via API
            if routes_to_create:
                created_routes = await self.api_client.bulk_create_routes(routes_to_create)
                total_routes_saved = len(created_routes)
            
            logger.info(f"🎯 Total routes processed for {country}: {total_routes_saved}")
                        
        except Exception as e:
            logger.error(f"❌ Error processing routes: {str(e)}")
            raise e
    
    async def process_vehicles(self, file_paths: List[str], country: str):
        """Process uploaded vehicle files and save via API"""
        try:
            logger.info(f"🔄 Processing {len(file_paths)} vehicle files for {country}")
            
            # Ensure country exists
            country_record = await self._ensure_country_exists(country)
            country_id = country_record["country_id"]
            
            total_vehicles_saved = 0
            vehicles_to_create = []
            
            for file_path in file_paths:
                with open(file_path, 'r') as f:
                    try:
                        vehicle_data = json.load(f)
                        vehicles_list = []
                        
                        # Normalize vehicle data structure
                        if isinstance(vehicle_data, list):
                            vehicles_list = vehicle_data
                        elif isinstance(vehicle_data, dict) and 'vehicles' in vehicle_data:
                            vehicles_list = vehicle_data['vehicles']
                        else:
                            logger.warning(f"⚠️ Invalid vehicle data structure in {file_path}")
                            continue
                            
                        logger.info(f"✅ Valid vehicle data with {len(vehicles_list)} vehicles")
                        
                        # Convert to API format
                        for vehicle in vehicles_list:
                            vehicle_entry = {
                                "country_id": country_id,
                                "reg_code": vehicle.get('reg_code', vehicle.get('registration', '')),
                                "status": vehicle.get('status', 'available'),
                                "notes": vehicle.get('notes', '')
                            }
                            vehicles_to_create.append(vehicle_entry)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Invalid JSON in {file_path}: {str(e)}")
            
            # Bulk create vehicles via API
            if vehicles_to_create:
                created_vehicles = await self.api_client.bulk_create_vehicles(vehicles_to_create)
                total_vehicles_saved = len(created_vehicles)
                
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
        """Get list of all countries with fleet data via API"""
        try:
            # Get countries from API
            countries_response = await self.api_client.get_countries()
            
            # Convert to CountryData objects
            countries = []
            for country_info in countries_response:
                # Get counts for each country
                routes = await self.api_client.get_routes(country_id=country_info["country_id"])
                vehicles = await self.api_client.get_vehicles(country_id=country_info["country_id"])
                timetables = await self.api_client.get_timetables()  # TODO: filter by country
                
                countries.append(CountryData(
                    country=country_info["name"],
                    routes_count=len(routes),
                    vehicles_count=len(vehicles),
                    timetables_count=len(timetables),
                    last_updated=datetime.fromisoformat(country_info["created_at"].replace('Z', '+00:00'))
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
        """Get all routes for a specific country via API"""
        try:
            # Find country first
            countries = await self.api_client.get_countries()
            country_id = None
            for c in countries:
                if c["name"].lower() == country.lower():
                    country_id = c["country_id"]
                    break
            
            if not country_id:
                logger.warning(f"Country {country} not found")
                return []
                
            routes = await self.api_client.get_routes(country_id=country_id)
            return routes
        except Exception as e:
            logger.error(f"❌ Error getting routes for {country}: {str(e)}")
            return []
    
    async def get_country_vehicles(self, country: str) -> List[Dict]:
        """Get all vehicles for a specific country via API"""
        try:
            # Find country first
            countries = await self.api_client.get_countries()
            country_id = None
            for c in countries:
                if c["name"].lower() == country.lower():
                    country_id = c["country_id"]
                    break
            
            if not country_id:
                logger.warning(f"Country {country} not found")
                return []
                
            vehicles = await self.api_client.get_vehicles(country_id=country_id)
            return vehicles
        except Exception as e:
            logger.error(f"❌ Error getting vehicles for {country}: {str(e)}")
            return []
    
    async def delete_country_data(self, country: str) -> Dict[str, int]:
        """Delete all fleet data for a specific country via API"""
        try:
            # Find country first
            countries = await self.api_client.get_countries()
            country_id = None
            for c in countries:
                if c["name"].lower() == country.lower():
                    country_id = c["country_id"]
                    break
            
            if not country_id:
                logger.warning(f"Country {country} not found")
                return {"routes": 0, "vehicles": 0, "timetables": 0}
            
            # Note: For now, we don't implement DELETE endpoints in the API
            # This would require adding DELETE endpoints to the GTFS API
            logger.warning("Delete functionality not yet implemented in API")
            
            # Delete uploaded files
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
                "database": {"routes": 0, "vehicles": 0, "timetables": 0},  # Placeholder until DELETE API is implemented
                "files": file_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting data for {country}: {str(e)}")
            raise e