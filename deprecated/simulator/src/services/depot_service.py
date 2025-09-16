"""
Depot service for managing fleet data from Strapi
"""

import logging
from typing import Dict, List, Optional
from services.strapi_client import StrapiClient

logger = logging.getLogger(__name__)


class DepotService:
    """Service for managing depot and fleet operations"""
    
    def __init__(self, strapi_client: StrapiClient):
        self.strapi_client = strapi_client
        self.vehicles: List[Dict] = []
        self.drivers: List[Dict] = []
        self.routes: List[Dict] = []
        self.loaded = False
    
    async def load_fleet_data(self) -> bool:
        """Load all fleet data from Strapi"""
        logger.info("📦 Loading fleet data from Strapi...")
        
        try:
            # Load vehicles, drivers, and routes in parallel
            import asyncio
            
            vehicles_task = self.strapi_client.get_vehicles()
            drivers_task = self.strapi_client.get_drivers()
            routes_task = self.strapi_client.get_routes()
            
            self.vehicles, self.drivers, self.routes = await asyncio.gather(
                vehicles_task, drivers_task, routes_task
            )
            
            logger.info(f"✅ Loaded {len(self.vehicles)} vehicles, {len(self.drivers)} drivers, {len(self.routes)} routes")
            
            self.loaded = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load fleet data: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """Check if fleet data is loaded"""
        return self.loaded
    
    def get_active_vehicles(self) -> List[Dict]:
        """Get vehicles with active status"""
        return [
            vehicle for vehicle in self.vehicles
            if vehicle.get("attributes", {}).get("status") in ["available", "in_service"]
        ]
    
    def get_available_drivers(self) -> List[Dict]:
        """Get drivers with available status"""
        return [
            driver for driver in self.drivers
            if driver.get("attributes", {}).get("employment_status") == "active"
        ]
    
    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict]:
        """Get vehicle by ID"""
        for vehicle in self.vehicles:
            if vehicle.get("id") == vehicle_id:
                return vehicle
        return None
    
    def get_driver_by_id(self, driver_id: str) -> Optional[Dict]:
        """Get driver by ID"""
        for driver in self.drivers:
            if driver.get("id") == driver_id:
                return driver
        return None
    
    def get_route_by_id(self, route_id: str) -> Optional[Dict]:
        """Get route by ID"""
        for route in self.routes:
            if route.get("id") == route_id:
                return route
        return None
    
    def get_vehicle_assignments(self) -> List[Dict]:
        """Get vehicle-driver assignments"""
        assignments = []
        
        for vehicle in self.get_active_vehicles():
            vehicle_attrs = vehicle.get("attributes", {})
            assigned_driver_id = vehicle_attrs.get("assigned_driver_id")
            
            if assigned_driver_id:
                driver = self.get_driver_by_id(str(assigned_driver_id))
                
                if driver:
                    assignment = {
                        "vehicle_id": vehicle.get("id"),
                        "vehicle_reg": vehicle_attrs.get("reg_code"),
                        "driver_id": driver.get("id"),
                        "driver_name": driver.get("attributes", {}).get("name"),
                        "route_id": vehicle_attrs.get("preferred_route_id"),
                        "status": vehicle_attrs.get("status", "unknown")
                    }
                    
                    # Add route information if available
                    route_id = vehicle_attrs.get("preferred_route_id")
                    if route_id:
                        route = self.get_route_by_id(str(route_id))
                        if route:
                            assignment["route_name"] = route.get("attributes", {}).get("long_name")
                            assignment["route_geometry"] = route.get("attributes", {}).get("geometry")
                    
                    assignments.append(assignment)
        
        return assignments
    
    async def update_vehicle_status(self, vehicle_id: str, status: str, additional_data: Optional[Dict] = None) -> bool:
        """Update vehicle status in Strapi"""
        update_data = {"status": status}
        
        if additional_data:
            update_data.update(additional_data)
        
        success = await self.strapi_client.update_vehicle_status(vehicle_id, update_data)
        
        if success:
            # Update local cache
            vehicle = self.get_vehicle_by_id(vehicle_id)
            if vehicle:
                vehicle["attributes"].update(update_data)
        
        return success
    
    def get_depot_summary(self) -> Dict:
        """Get depot operational summary"""
        active_vehicles = self.get_active_vehicles()
        available_drivers = self.get_available_drivers()
        assignments = self.get_vehicle_assignments()
        
        return {
            "total_vehicles": len(self.vehicles),
            "active_vehicles": len(active_vehicles),
            "total_drivers": len(self.drivers),
            "available_drivers": len(available_drivers),
            "active_assignments": len(assignments),
            "total_routes": len(self.routes),
            "operational_status": "active" if assignments else "inactive"
        }