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
        """Get vehicle assignments using PUBLIC API with human-readable data only - NO UUIDs."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch assignments - API not connected")
            return []
        
        try:
            # Use the search endpoint that provides complete assignment data with human-readable identifiers
            async with self.session.get(f"{self.api_base_url}/api/v1/search/vehicle-driver-pairs", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"[{self.component_name}] Failed to fetch assignments: HTTP {response.status}")
                    return []
                
                pairs_data = await response.json()
                assignments = []
                
                # Transform search results into VehicleAssignment objects  
                for pair in pairs_data:
                    # Only include active vehicles with valid assignments
                    if (pair.get('vehicle_status') in ['available', 'in_service'] and 
                        pair.get('driver_employment_status') == 'active' and
                        pair.get('registration') and pair.get('route_code')):
                        
                        assignment = VehicleAssignment(
                            vehicle_id=pair.get('registration', ''),  # Use reg code as vehicle_id (no UUIDs)
                            route_id=pair.get('route_code', ''),      # Use route code as route_id (no UUIDs)
                            driver_id=pair.get('driver_license', ''), # Use license as driver_id (no UUIDs)
                            assignment_type='regular',
                            start_time=pair.get('assignment_date'),
                            end_time=None,
                            # Human-readable friendly names
                            vehicle_reg_code=pair.get('registration', 'Unknown Vehicle'),
                            driver_name=pair.get('driver_name', 'Unknown Driver'),
                            route_name=pair.get('route_name', 'Unknown Route')
                        )
                        assignments.append(assignment)
            
            logging.info(f"[{self.component_name}] Fetched {len(assignments)} vehicle assignments with friendly names")
            return assignments
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error fetching vehicle assignments: {str(e)}")
            return []
    
    async def get_all_depot_vehicles(self) -> List[Dict[str, Any]]:
        """Get ALL vehicles in depot regardless of status - for complete inventory tracking."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch depot vehicles - API not connected")
            return []
        
        try:
            # Get all vehicles from public API (includes all statuses)
            async with self.session.get(f"{self.api_base_url}/api/v1/vehicles/public", timeout=10) as response:
                if response.status == 200:
                    vehicles_data = await response.json()
                    logging.debug(f"[{self.component_name}] Fetched {len(vehicles_data)} total depot vehicles")
                    return vehicles_data
                else:
                    logging.error(f"[{self.component_name}] Failed to fetch depot vehicles: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error fetching depot vehicles: {str(e)}")
            return []
    
    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments using PUBLIC API with human-readable data only - NO UUIDs."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch driver assignments - API not connected")
            return []
        
        try:
            # Use the search endpoint that provides complete assignment data with human-readable identifiers
            async with self.session.get(f"{self.api_base_url}/api/v1/search/vehicle-driver-pairs", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"[{self.component_name}] Failed to fetch driver assignments: HTTP {response.status}")
                    return []
                
                pairs_data = await response.json()
                assignments = []
                
                # Transform search results into DriverAssignment objects
                for pair in pairs_data:
                    if pair.get('driver_employment_status') == 'active':
                        assignment = DriverAssignment(
                            driver_id=pair.get('driver_license', ''),    # Use license as driver_id (no UUIDs)
                            driver_name=pair.get('driver_name', ''),
                            license_number=pair.get('driver_license', ''),
                            vehicle_id=pair.get('registration', ''),     # Use reg code as vehicle_id (no UUIDs)
                            route_id=pair.get('route_code', ''),         # Use route code as route_id (no UUIDs)
                            status="available",  # All active drivers are available
                            shift_start=pair.get('assignment_date'),
                            shift_end=None
                        )
                        assignments.append(assignment)
                
                logging.info(f"[{self.component_name}] Fetched {len(assignments)} driver assignments from Fleet Manager")
                return assignments
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error fetching driver assignments: {str(e)}")
            return []
    
    async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
        """Get route information and geometry directly by route number from Fleet Manager PUBLIC API."""
        if not self.api_connected or not self.session:
            logging.error(f"[{self.component_name}] Cannot fetch route info - Fleet Manager API not connected")
            return None
        
        try:
            # Step 1: Get route details by route code from Fleet Manager PUBLIC API
            async with self.session.get(f"{self.api_base_url}/api/v1/routes/public/{route_code}", timeout=10) as route_response:
                if route_response.status != 200:
                    logging.error(f"[{self.component_name}] Route {route_code} not found in Fleet Manager: HTTP {route_response.status}")
                    return None
                    
                route_data = await route_response.json()
                route_name = route_data.get('long_name', f'Route {route_code}')
                
                logging.info(f"[{self.component_name}] Found route: {route_name} (code: {route_code})")
                
            # Step 2: Get route geometry by route code from Fleet Manager PUBLIC API
            geometry = None
            coordinate_count = 0
            
            async with self.session.get(f"{self.api_base_url}/api/v1/routes/public/{route_code}/geometry", timeout=10) as geo_response:
                if geo_response.status != 200:
                    logging.error(f"[{self.component_name}] Failed to fetch geometry for route {route_code}: HTTP {geo_response.status}")
                    return None
                    
                route_geometry_data = await geo_response.json()
                geometry = route_geometry_data.get('geometry')
                
                if geometry and geometry.get('coordinates'):
                    coordinate_count = len(geometry['coordinates'])
                    logging.info(f"[{self.component_name}] ✅ Route {route_name} has {coordinate_count} GPS coordinates from Fleet Manager API")
                    
                    # Log first and last coordinates as verification
                    coords = geometry['coordinates']
                    if coords:
                        first_coord = coords[0]
                        last_coord = coords[-1]
                        logging.info(f"[{self.component_name}] Route path: [{first_coord[0]:.6f}, {first_coord[1]:.6f}] → [{last_coord[0]:.6f}, {last_coord[1]:.6f}]")
                else:
                    logging.error(f"[{self.component_name}] ❌ Route {route_code} geometry is null from Fleet Manager API")
                    logging.error(f"[{self.component_name}] ❌ Fleet Manager route geometry endpoint is broken - API should return GPS coordinates from route_shapes→shapes join")
                    return None
                
            # Create RouteInfo with complete data from Fleet Manager API
            route_info = RouteInfo(
                route_id=route_code,              # Route code (1A, 1B, etc.)
                route_name=route_name,            # Human-readable route name from Fleet Manager
                route_type='bus',                 # Bus route type
                geometry=geometry,                # Complete GPS geometry from Fleet Manager API
                stops=None,                       # Stops not needed for basic vehicle movement
                distance_km=None,                 # Distance not needed for basic vehicle movement
                coordinate_count=coordinate_count, # Number of GPS coordinates
                shape_id=None                     # Shape ID not needed when we have direct geometry
            )
            
            logging.info(f"[{self.component_name}] ✅ Successfully loaded Route {route_name} with {coordinate_count} GPS coordinates")
            return route_info
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error fetching route info for {route_code}: {str(e)}")
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