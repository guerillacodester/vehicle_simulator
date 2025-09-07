"""
Mock Fleet Management Database Service
====================================
Simplified version without SSH tunnel dependency
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MockFleetDatabaseService:
    """Mock database service for demonstration"""
    
    def __init__(self):
        self._countries_data = {
            "barbados": {
                "routes": [
                    {"route_id": "barbados_route_1", "name": "Bridgetown to Speightstown", "has_geometry": True, "vehicle_count": 3},
                    {"route_id": "barbados_route_2", "name": "Bridgetown to Oistins", "has_geometry": True, "vehicle_count": 2}
                ],
                "vehicles": [
                    {"vehicle_id": "barbados_bus_001", "status": "available", "route_id": "barbados_route_1", "route_name": "Bridgetown to Speightstown"},
                    {"vehicle_id": "barbados_bus_002", "status": "in_service", "route_id": "barbados_route_1", "route_name": "Bridgetown to Speightstown"},
                    {"vehicle_id": "barbados_bus_003", "status": "available", "route_id": "barbados_route_2", "route_name": "Bridgetown to Oistins"}
                ]
            }
        }
    
    async def initialize(self):
        """Mock initialization"""
        logger.info("🔌 Mock database initialized")
        
    async def cleanup(self):
        """Mock cleanup"""
        logger.info("🔌 Mock database cleaned up")
    
    async def save_routes_from_geojson(self, geojson_data: Dict, country: str, source_file: str) -> int:
        """Mock save routes"""
        features = geojson_data.get('features', [])
        logger.info(f"📍 Mock: Would save {len(features)} routes for {country}")
        
        # Add to mock data
        if country not in self._countries_data:
            self._countries_data[country] = {"routes": [], "vehicles": []}
        
        for feature in features:
            props = feature.get('properties', {})
            route_id = props.get('route_id', f"{country}_route_{len(self._countries_data[country]['routes']) + 1}")
            route_name = props.get('name', f"Route {route_id}")
            
            self._countries_data[country]['routes'].append({
                "route_id": route_id,
                "name": route_name,
                "has_geometry": True,
                "vehicle_count": 0
            })
        
        return len(features)
    
    async def save_vehicles_from_json(self, vehicle_data: List[Dict], country: str, source_file: str) -> int:
        """Mock save vehicles"""
        logger.info(f"🚌 Mock: Would save {len(vehicle_data)} vehicles for {country}")
        
        # Add to mock data
        if country not in self._countries_data:
            self._countries_data[country] = {"routes": [], "vehicles": []}
        
        for vehicle in vehicle_data:
            vehicle_id = vehicle.get('vehicle_id', f"{country}_vehicle_{len(self._countries_data[country]['vehicles']) + 1}")
            
            self._countries_data[country]['vehicles'].append({
                "vehicle_id": vehicle_id,
                "status": vehicle.get('status', 'available'),
                "route_id": vehicle.get('route_id'),
                "route_name": vehicle.get('route_name', 'Unknown Route')
            })
        
        return len(vehicle_data)
    
    async def get_countries_with_data(self) -> List[Dict[str, Any]]:
        """Mock get countries"""
        countries = []
        for country, data in self._countries_data.items():
            countries.append({
                "country": country,
                "name": country.title(),
                "routes": len(data['routes']),
                "vehicles": len(data['vehicles'])
            })
        return countries
    
    async def get_country_routes(self, country: str) -> List[Dict]:
        """Mock get country routes"""
        return self._countries_data.get(country, {}).get('routes', [])
    
    async def get_country_vehicles(self, country: str) -> List[Dict]:
        """Mock get country vehicles"""
        return self._countries_data.get(country, {}).get('vehicles', [])
    
    async def delete_country_data(self, country: str) -> Dict[str, int]:
        """Mock delete country data"""
        if country in self._countries_data:
            routes_count = len(self._countries_data[country]['routes'])
            vehicles_count = len(self._countries_data[country]['vehicles'])
            del self._countries_data[country]
            
            return {
                "vehicles": vehicles_count,
                "routes": routes_count,
                "timetables": 0
            }
        return {"vehicles": 0, "routes": 0, "timetables": 0}

# Global mock database service instance
db_service = MockFleetDatabaseService()
