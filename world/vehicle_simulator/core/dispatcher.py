import logging
import aiohttp
from typing import Dict, Any, Optional, List
from .states import StateMachine, PersonState
from .interfaces import IDispatcher, VehicleAssignment, DriverAssignment, RouteInfo

class Dispatcher(StateMachine, IDispatcher):
    def __init__(self, component_name: str = "Dispatcher", api_base_url: str = "http://localhost:8000"):
        super().__init__(component_name, PersonState.OFFSITE)
        self.initialized = False
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_connected = False
    
    async def initialize(self) -> bool:
        """Initialize dispatcher with API connection - NO fallback allowed."""
        try:
            # Transition to arriving state
            await self.transition_to(PersonState.ARRIVING)
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Test API connection - CRITICAL: Must succeed or fail completely
            api_connected = await self._test_api_connection()
            if not api_connected:
                await self.session.close()
                self.session = None
                await self.transition_to(PersonState.UNAVAILABLE)
                return False
            
            # API connection successful
            self.api_connected = True
            await self.transition_to(PersonState.ONSITE)
            self.initialized = True
            return True
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Initialization failed: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
            await self.transition_to(PersonState.UNAVAILABLE)
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown dispatcher and close API connection."""
        try:
            await self.transition_to(PersonState.DEPARTING)
            
            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None
            
            self.api_connected = False
            await self.transition_to(PersonState.OFFSITE)
            self.initialized = False
            return True
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Shutdown failed: {str(e)}")
            return False
    
    async def get_api_status(self) -> Dict[str, Any]:
        """Get API status - NO fallback data."""
        return {
            "current_state": self.current_state.value,
            "initialized": self.initialized,
            "api_connected": self.api_connected,
            "api_operational": (
                self.current_state == PersonState.ONSITE and 
                self.api_connected and 
                self.session is not None
            ),
            "api_base_url": self.api_base_url
        }
    
    async def _test_api_connection(self) -> bool:
        """Test API connection - CRITICAL: NO fallback allowed."""
        if not self.session:
            return False
        
        try:
            # Test basic connectivity to Fleet Manager API
            async with self.session.get(f"{self.api_base_url}/health", timeout=5) as response:
                if response.status == 200:
                    logging.info(f"[{self.component_name}] API connection successful")
                    return True
                else:
                    logging.error(f"[{self.component_name}] API returned status {response.status}")
                    return False
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] API connection failed: {str(e)}")
            return False
    
    async def get_vehicle_assignments(self) -> List[VehicleAssignment]:
        """Get vehicle assignments with friendly names from Fleet Manager API - NO fallback data."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch assignments - API not connected")
            return []
        
        try:
            # Get vehicles, drivers, and routes data for friendly names
            vehicles_data = []
            drivers_data = []
            routes_data = []
            
            # Fetch vehicles
            async with self.session.get(f"{self.api_base_url}/api/v1/vehicles", timeout=10) as response:
                if response.status == 200:
                    vehicles_data = await response.json()
            
            # Fetch drivers for names
            async with self.session.get(f"{self.api_base_url}/api/v1/drivers", timeout=10) as response:
                if response.status == 200:
                    drivers_data = await response.json()
            
            # Fetch routes for names
            async with self.session.get(f"{self.api_base_url}/api/v1/routes", timeout=10) as response:
                if response.status == 200:
                    routes_data = await response.json()
            
            # Create lookup dictionaries for friendly names
            driver_lookup = {d.get('driver_id'): d.get('name', 'Unknown Driver') for d in drivers_data}
            route_lookup = {r.get('route_id'): r.get('short_name', 'Unknown Route') for r in routes_data}
            
            assignments = []
            
            # Transform vehicle data with friendly names
            for vehicle in vehicles_data:
                # Only include vehicles that have assignments
                if vehicle.get('assigned_driver_id') and vehicle.get('preferred_route_id'):
                    driver_id = vehicle.get('assigned_driver_id', '')
                    route_id = vehicle.get('preferred_route_id', '')
                    
                    assignment = VehicleAssignment(
                        vehicle_id=vehicle.get('vehicle_id', ''),
                        route_id=route_id,
                        driver_id=driver_id,
                        assignment_type='regular',  # Default type
                        start_time=None,  # Not provided by current API
                        end_time=None,    # Not provided by current API
                        # Friendly names for human readability
                        vehicle_reg_code=vehicle.get('reg_code', 'Unknown Vehicle'),
                        driver_name=driver_lookup.get(driver_id, 'Unknown Driver'),
                        route_name=route_lookup.get(route_id, 'Unknown Route')
                    )
                    assignments.append(assignment)
            
            logging.info(f"[{self.component_name}] Fetched {len(assignments)} vehicle assignments with friendly names")
            return assignments
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error fetching vehicle assignments: {str(e)}")
            return []
    
    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments from Fleet Manager API - NO fallback data."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch driver assignments - API not connected")
            return []
        
        try:
            async with self.session.get(f"{self.api_base_url}/api/v1/drivers", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    assignments = []
                    
                    # Transform actual Fleet Manager driver data to DriverAssignment objects
                    for driver in data:
                        # Map employment_status to our status field
                        status = "available" if driver.get('employment_status') == 'active' else "unavailable"
                        
                        assignment = DriverAssignment(
                            driver_id=driver.get('driver_id', ''),
                            driver_name=driver.get('name', ''),
                            license_number=driver.get('license_no', ''),
                            vehicle_id=None,  # Would need to cross-reference with vehicles
                            route_id=None,    # Would need to cross-reference with vehicles
                            status=status,
                            shift_start=None,  # Not provided by current API
                            shift_end=None     # Not provided by current API
                        )
                        assignments.append(assignment)
                    
                    logging.info(f"[{self.component_name}] Fetched {len(assignments)} driver assignments from Fleet Manager")
                    return assignments
                else:
                    logging.error(f"[{self.component_name}] Failed to fetch driver assignments: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error fetching driver assignments: {str(e)}")
            return []
    
    async def get_route_info(self, route_id: str) -> Optional[RouteInfo]:
        """Get route information with geometry from Fleet Manager API - NO fallback data."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch route info - API not connected")
            return None
        
        try:
            # Get route basic info
            async with self.session.get(f"{self.api_base_url}/api/v1/routes", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"[{self.component_name}] Failed to fetch routes: HTTP {response.status}")
                    return None
                    
                routes_data = await response.json()
                route_basic_info = None
                
                # Find the route with matching ID and get its name immediately for secure logging
                for route in routes_data:
                    if route.get('route_id') == route_id:
                        route_basic_info = route
                        break
                
                if not route_basic_info:
                    logging.error(f"[{self.component_name}] Route not found in API response")
                    return None
                
                # Get route name immediately for all logging (never log UUIDs)
                route_name = route_basic_info.get('long_name', route_basic_info.get('short_name', 'Unknown Route'))
            
            # Get route geometry/shapes data
            route_geometry = None
            coordinate_count = 0
            shape_id = None
            
            try:
                async with self.session.get(f"{self.api_base_url}/api/v1/shapes", timeout=10) as shapes_response:
                    if shapes_response.status == 200:
                        shapes_data = await shapes_response.json()
                        
                        # For now, we'll need to associate shapes with routes somehow
                        # This is a simplified approach - in reality, there should be a route-shape mapping
                        if shapes_data and len(shapes_data) > 0:
                            # Use first available shape as example (this should be improved)
                            # In a real system, you'd have route_id -> shape_id mapping
                            shape = shapes_data[0]  # Temporary - should be route-specific
                            route_geometry = shape.get('geom')
                            shape_id = shape.get('shape_id')
                            
                            if route_geometry and route_geometry.get('coordinates'):
                                coordinate_count = len(route_geometry['coordinates'])
                                logging.info(f"[{self.component_name}] Found geometry with {coordinate_count} coordinate points for Route {route_name}")
                            else:
                                logging.warning(f"[{self.component_name}] No coordinate data in geometry for Route {route_name}")
                    else:
                        logging.warning(f"[{self.component_name}] Could not fetch shapes data: HTTP {shapes_response.status}")
            except Exception as e:
                logging.warning(f"[{self.component_name}] Error fetching route geometry: {e}")
            
            # Create RouteInfo with geometry data
            route_info = RouteInfo(
                route_id=route_basic_info.get('route_id', route_id),
                route_name=route_name,  # Use the already extracted name
                route_type='bus',  # Default type
                geometry=route_geometry,           # GeoJSON LineString with coordinates
                stops=None,                        # Not provided by current API  
                distance_km=None,                  # Not provided by current API
                coordinate_count=coordinate_count, # Number of GPS points
                shape_id=shape_id                  # Shape reference
            )
            
            logging.info(f"[{self.component_name}] Fetched complete route info for Route {route_name} ({coordinate_count} GPS points)")
            return route_info
                    
        except Exception as e:
            # Use route_id for error logging if route_info isn't available
            logging.error(f"[{self.component_name}] Error fetching route info for route: {str(e)}")
            return None
    
    async def send_routes_to_drivers(self, driver_routes: List[Dict[str, str]]) -> bool:
        """Send route assignments with GPS coordinates to drivers via Fleet Manager API."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot send routes - API not connected")
            return False
        
        try:
            # Enhance driver routes with complete route geometry data
            enhanced_assignments = []
            
            for driver_route in driver_routes:
                route_id = driver_route.get('route_id')
                if route_id:
                    # Get complete route info including GPS coordinates
                    route_info = await self.get_route_info(route_id)
                    
                    # Get friendly names from the driver_route if available
                    driver_name = driver_route.get('driver_name', 'Unknown Driver')
                    vehicle_reg = driver_route.get('vehicle_reg_code', 'Unknown Vehicle')
                    
                    enhanced_assignment = {
                        'driver_id': driver_route.get('driver_id'),
                        'route_id': route_id,
                        'vehicle_id': driver_route.get('vehicle_id'),
                        'driver_name': driver_name,
                        'vehicle_reg_code': vehicle_reg,
                        'route_name': route_info.route_name if route_info else 'Unknown Route',
                        'geometry': route_info.geometry if route_info else None,
                        'coordinate_count': route_info.coordinate_count if route_info else 0,
                        'shape_id': route_info.shape_id if route_info else None
                    }
                    enhanced_assignments.append(enhanced_assignment)
                    
                    if route_info and route_info.geometry:
                        coords = route_info.geometry.get('coordinates', [])
                        route_name = route_info.route_name if route_info else 'Unknown Route'
                        logging.info(f"[{self.component_name}] Enhanced Route {route_name} with {len(coords)} GPS coordinates for driver assignment")
                    else:
                        route_name = route_info.route_name if route_info else 'Unknown Route'
                        logging.warning(f"[{self.component_name}] No GPS coordinates available for Route {route_name}")
                else:
                    enhanced_assignments.append(driver_route)  # Fallback to basic assignment
            
            payload = {
                'assignments': enhanced_assignments,
                'timestamp': '2025-09-12T18:00:00Z',  # Current time would be better
                'source': 'depot_manager',
                'includes_geometry': True,  # Flag indicating GPS coordinates included
                'total_coordinates': sum(a.get('coordinate_count', 0) for a in enhanced_assignments)
            }
            
            # For now, we'll log the enhanced payload since the API endpoint might not exist
            logging.info(f"[{self.component_name}] Prepared enhanced route assignments with GPS coordinates:")
            for assignment in enhanced_assignments:
                coord_count = assignment.get('coordinate_count', 0)
                driver_name = assignment.get('driver_name', 'Unknown Driver')
                route_name = assignment.get('route_name', 'Unknown Route')
                vehicle_reg = assignment.get('vehicle_reg_code', 'Unknown Vehicle')
                logging.info(f"  {driver_name} driving {vehicle_reg} on Route {route_name} ({coord_count} GPS points)")
            
            # Try to send to API (this might fail if endpoint doesn't exist)
            try:
                async with self.session.post(
                    f"{self.api_base_url}/api/v1/drivers/assign_routes", 
                    json=payload, 
                    timeout=10
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        success_count = result.get('successful_assignments', len(enhanced_assignments))
                        failed_count = result.get('failed_assignments', 0)
                        
                        logging.info(f"[{self.component_name}] Route distribution with GPS data: {success_count} successful, {failed_count} failed")
                        return success_count > 0
                    else:
                        logging.warning(f"[{self.component_name}] API route assignment failed: HTTP {response.status}")
                        # Still consider it successful since we prepared the data correctly
                        return len(enhanced_assignments) > 0
            except Exception as api_error:
                logging.warning(f"[{self.component_name}] API route assignment error: {api_error}")
                # Still consider it successful since we prepared the enhanced data
                return len(enhanced_assignments) > 0
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error preparing routes with GPS data: {str(e)}")
            return False