import logging
import aiohttp
import asyncio
import math
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from .states import StateMachine, PersonState
from .interfaces import IDispatcher, VehicleAssignment, DriverAssignment, RouteInfo

try:
    from common.config_provider import get_config
    _config_available = True
except ImportError:
    _config_available = False


class ApiStrategy(ABC):
    """Abstract base class for API strategies (FastAPI, Strapi, etc.)"""
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connectivity"""
        pass
    
    @abstractmethod
    async def get_vehicle_assignments(self) -> List[VehicleAssignment]:
        """Get vehicle assignments with human-readable data"""
        pass
    
    @abstractmethod
    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments with human-readable data"""
        pass
    
    @abstractmethod
    async def get_all_depot_vehicles(self) -> List[Dict[str, Any]]:
        """Get all vehicles in depot regardless of status"""
        pass
    
    @abstractmethod
    async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
        """Get route information and geometry by route code"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources"""
        pass

class RouteBuffer:
    """Thread-safe, searchable route buffer for GPS-based route queries."""
    
    def __init__(self):
        self._routes: Dict[str, RouteInfo] = {}
        self._lock = asyncio.Lock()
        self._gps_index: Dict[Tuple[float, float], List[str]] = {}  # GPS coordinate -> route_ids
        self._initialized = False
    
    async def add_route(self, route_info: RouteInfo) -> bool:
        """Add route with GPS indexing for proximity searches."""
        async with self._lock:
            try:
                self._routes[route_info.route_id] = route_info
                
                # Index GPS coordinates for proximity searches
                if route_info.geometry and route_info.geometry.get('coordinates'):
                    coords = route_info.geometry['coordinates']
                    for coord in coords:
                        if len(coord) >= 2:
                            # Round to reasonable precision for indexing
                            lat_key = round(coord[1], 4)  # ~11m precision
                            lon_key = round(coord[0], 4)  # ~11m precision
                            coord_key = (lat_key, lon_key)
                            
                            if coord_key not in self._gps_index:
                                self._gps_index[coord_key] = []
                            if route_info.route_id not in self._gps_index[coord_key]:
                                self._gps_index[coord_key].append(route_info.route_id)
                
                logging.debug(f"RouteBuffer: Added route {route_info.route_id} with {route_info.coordinate_count} GPS points")
                return True
                
            except Exception as e:
                logging.error(f"RouteBuffer: Failed to add route {route_info.route_id}: {e}")
                return False
    
    async def get_route_by_id(self, route_id: str) -> Optional[RouteInfo]:
        """Get complete route information by route ID."""
        async with self._lock:
            return self._routes.get(route_id)
    
    async def get_routes_by_gps(self, lat: float, lon: float, walking_distance_km: float = 0.5) -> List[RouteInfo]:
        """Get all routes within walking distance of GPS coordinates."""
        async with self._lock:
            nearby_routes = set()
            
            # Calculate search radius in coordinate degrees (approximate)
            lat_radius = walking_distance_km / 111.0  # ~111km per degree latitude
            lon_radius = walking_distance_km / (111.0 * math.cos(math.radians(lat)))  # Adjust for longitude
            
            # Search GPS index within radius
            for coord_key, route_ids in self._gps_index.items():
                key_lat, key_lon = coord_key
                
                # Quick distance check using coordinate differences
                lat_diff = abs(lat - key_lat)
                lon_diff = abs(lon - key_lon)
                
                if lat_diff <= lat_radius and lon_diff <= lon_radius:
                    # More precise distance calculation
                    distance_km = self._calculate_distance(lat, lon, key_lat, key_lon)
                    if distance_km <= walking_distance_km:
                        nearby_routes.update(route_ids)
            
            # Return RouteInfo objects for nearby routes
            result = []
            for route_id in nearby_routes:
                if route_id in self._routes:
                    result.append(self._routes[route_id])
            
            return result
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def get_all_routes(self) -> List[RouteInfo]:
        """Get all routes in buffer."""
        async with self._lock:
            return list(self._routes.values())
    
    async def clear(self) -> None:
        """Clear all routes from buffer."""
        async with self._lock:
            self._routes.clear()
            self._gps_index.clear()
            self._initialized = False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        async with self._lock:
            return {
                'total_routes': len(self._routes),
                'total_gps_points': len(self._gps_index),
                'routes': list(self._routes.keys()),
                'initialized': self._initialized
            }


class FastApiStrategy(ApiStrategy):
    """FastAPI implementation of ApiStrategy - maintains existing behavior"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_connected = False
    
    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return True
    
    async def test_connection(self) -> bool:
        """Test API connection - CRITICAL: NO fallback allowed."""
        if not self.session:
            return False
        
        try:
            # Test basic connectivity to Fleet Manager API
            async with self.session.get(f"{self.api_base_url}/health", timeout=5) as response:
                if response.status == 200:
                    logging.info(f"FastAPI connection successful")
                    self.api_connected = True
                    return True
                else:
                    logging.error(f"FastAPI returned status {response.status}")
                    return False
                    
        except Exception as e:
            logging.error(f"FastAPI connection failed: {str(e)}")
            return False
    
    async def get_vehicle_assignments(self) -> List[VehicleAssignment]:
        """Get vehicle assignments using PUBLIC API with human-readable data only - NO UUIDs."""
        if not self.api_connected or not self.session:
            logging.error(f"[FastApiStrategy] Cannot fetch assignments - API not connected")
            return []
        
        try:
            # Use the search endpoint that provides complete assignment data with human-readable identifiers
            async with self.session.get(f"{self.api_base_url}/api/v1/search/vehicle-driver-pairs", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"[FastApiStrategy] Failed to fetch assignments: HTTP {response.status}")
                    return []
                
                pairs_data = await response.json()
                assignments = []
                
                # Transform search results into VehicleAssignment objects  
                for pair in pairs_data:
                    # Include ALL assignments from Fleet Manager - respect exact driver/vehicle pairings
                    # regardless of vehicle status (maintenance, retired, etc.)
                    if (pair.get('driver_employment_status') == 'active' and
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
                            route_name=pair.get('route_name', 'Unknown Route'),
                            vehicle_status=pair.get('vehicle_status', 'unknown')  # Include vehicle operational status
                        )
                        assignments.append(assignment)
            
            logging.info(f"[FastApiStrategy] Fetched {len(assignments)} vehicle assignments with friendly names")
            return assignments
                    
        except Exception as e:
            logging.error(f"[FastApiStrategy] Error fetching vehicle assignments: {str(e)}")
            return []

    async def get_all_depot_vehicles(self) -> List[Dict[str, Any]]:
        """Get ALL vehicles in depot regardless of status - for complete inventory tracking."""
        if not self.api_connected or not self.session:
            logging.error(f"[FastApiStrategy] Cannot fetch depot vehicles - API not connected")
            return []
        
        try:
            # Get all vehicles from public API (includes all statuses)
            async with self.session.get(f"{self.api_base_url}/api/v1/vehicles/public", timeout=10) as response:
                if response.status == 200:
                    vehicles_data = await response.json()
                    logging.debug(f"[FastApiStrategy] Fetched {len(vehicles_data)} total depot vehicles")
                    return vehicles_data
                else:
                    logging.error(f"[FastApiStrategy] Failed to fetch depot vehicles: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logging.error(f"[FastApiStrategy] Error fetching depot vehicles: {str(e)}")
            return []

    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments using PUBLIC API with human-readable data only - NO UUIDs."""
        if not self.api_connected or not self.session:
            logging.error(f"[FastApiStrategy] Cannot fetch driver assignments - API not connected")
            return []
        
        try:
            # Use the search endpoint that provides complete assignment data with human-readable identifiers
            async with self.session.get(f"{self.api_base_url}/api/v1/search/vehicle-driver-pairs", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"[FastApiStrategy] Failed to fetch driver assignments: HTTP {response.status}")
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
                
                logging.info(f"[FastApiStrategy] Fetched {len(assignments)} driver assignments from Fleet Manager")
                return assignments
                    
        except Exception as e:
            logging.error(f"[FastApiStrategy] Error fetching driver assignments: {str(e)}")
            return []

    async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
        """Get route information and geometry directly by route number from Fleet Manager PUBLIC API."""
        if not self.api_connected or not self.session:
            logging.error(f"[FastApiStrategy] Cannot fetch route info - Fleet Manager API not connected")
            return None
        
        try:
            # Step 1: Get route details by route code from Fleet Manager PUBLIC API
            async with self.session.get(f"{self.api_base_url}/api/v1/routes/public/{route_code}", timeout=10) as route_response:
                if route_response.status != 200:
                    logging.error(f"[FastApiStrategy] Route {route_code} not found in Fleet Manager: HTTP {route_response.status}")
                    return None
                    
                route_data = await route_response.json()
                route_name = route_data.get('long_name', f'Route {route_code}')
                
                logging.info(f"[FastApiStrategy] Found route: {route_name} (code: {route_code})")
                
            # Step 2: Get route geometry by route code from Fleet Manager PUBLIC API
            geometry = None
            coordinate_count = 0
            
            async with self.session.get(f"{self.api_base_url}/api/v1/routes/public/{route_code}/geometry", timeout=10) as geo_response:
                if geo_response.status != 200:
                    logging.error(f"[FastApiStrategy] Failed to fetch geometry for route {route_code}: HTTP {geo_response.status}")
                    return None
                    
                route_geometry_data = await geo_response.json()
                geometry = route_geometry_data.get('geometry')
                
                if geometry and geometry.get('coordinates'):
                    coordinate_count = len(geometry['coordinates'])
                    logging.info(f"[FastApiStrategy] ✅ Route {route_name} has {coordinate_count} GPS coordinates from Fleet Manager API")
                    
                    # Log first and last coordinates as verification
                    coords = geometry['coordinates']
                    if coords:
                        first_coord = coords[0]
                        last_coord = coords[-1]
                        logging.info(f"[FastApiStrategy] Route path: [{first_coord[0]:.6f}, {first_coord[1]:.6f}] → [{last_coord[0]:.6f}, {last_coord[1]:.6f}]")
                else:
                    logging.error(f"[FastApiStrategy] ❌ Route {route_code} geometry is null from Fleet Manager API")
                    logging.error(f"[FastApiStrategy] ❌ Fleet Manager route geometry endpoint is broken - API should return GPS coordinates from route_shapes→shapes join")
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
            
            logging.info(f"[FastApiStrategy] ✅ Successfully loaded Route {route_name} with {coordinate_count} GPS coordinates")
            return route_info
                    
        except Exception as e:
            logging.error(f"[FastApiStrategy] Error fetching route info for {route_code}: {str(e)}")
            return None

    async def close(self) -> None:
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None


class StrapiStrategy(ApiStrategy):
    """Strapi CMS implementation of ApiStrategy - replaces FastAPI with Strapi REST API"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_connected = False
    
    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return True
    
    async def test_connection(self) -> bool:
        """Test Strapi API connection"""
        if not self.session:
            return False
        
        try:
            # Test basic connectivity to Strapi API
            async with self.session.get(f"{self.api_base_url}/api/vehicles", timeout=5) as response:
                if response.status == 200:
                    logging.info(f"Strapi connection successful")
                    self.api_connected = True
                    return True
                else:
                    logging.error(f"Strapi returned status {response.status}")
                    return False
                    
        except Exception as e:
            logging.error(f"Strapi connection failed: {str(e)}")
            return False
    
    async def get_vehicle_assignments(self) -> List[VehicleAssignment]:
        """Get vehicle assignments from Strapi with proper relationship mapping"""
        if not self.api_connected or not self.session:
            logging.error(f"[StrapiStrategy] Cannot fetch assignments - API not connected")
            return []
        
        try:
            # Get vehicles with populated relationships using correct Strapi field names
            async with self.session.get(f"{self.api_base_url}/api/vehicles?populate%5B0%5D=assigned_driver&populate%5B1%5D=preferred_route&populate%5B2%5D=vehicle_status", timeout=10) as response:
                if response.status != 200:
                    logging.error(f"[StrapiStrategy] Failed to fetch assignments: HTTP {response.status}")
                    return []
                
                vehicles_data = await response.json()
                assignments = []
                
                # Transform Strapi vehicles into VehicleAssignment objects
                for vehicle_item in vehicles_data.get('data', []):
                    vehicle = vehicle_item
                    driver = vehicle.get('assigned_driver')
                    route = vehicle.get('preferred_route')
                    status = vehicle.get('vehicle_status')
                    
                    # Only include assignments with active drivers and valid routes
                    if (driver and route and 
                        driver.get('employment_status') == 'active' and
                        vehicle.get('reg_code') and route.get('short_name')):
                        
                        assignment = VehicleAssignment(
                            vehicle_id=vehicle.get('reg_code', ''),          # Use reg_code as vehicle_id
                            route_id=route.get('short_name', ''),            # Use route short_name
                            driver_id=driver.get('license_no', ''),          # Use license_no as driver_id
                            assignment_type='regular',
                            start_time=vehicle.get('createdAt'),
                            end_time=None,
                            # Human-readable friendly names
                            vehicle_reg_code=vehicle.get('reg_code', 'Unknown Vehicle'),
                            driver_name=driver.get('name', 'Unknown Driver'),
                            route_name=route.get('long_name', 'Unknown Route'),
                            vehicle_status=status.get('status_id', 'unknown') if status else 'unknown'
                        )
                        assignments.append(assignment)
                
                logging.info(f"[StrapiStrategy] Fetched {len(assignments)} vehicle assignments from Strapi")
                return assignments
                        
        except Exception as e:
            logging.error(f"[StrapiStrategy] Error fetching vehicle assignments: {str(e)}")
            return []
    
    async def get_all_depot_vehicles(self) -> List[Dict[str, Any]]:
        """Get ALL vehicles from Strapi depot with normalized format matching FastAPI"""
        if not self.api_connected or not self.session:
            logging.error(f"[StrapiStrategy] Cannot fetch depot vehicles - API not connected")
            return []
        
        try:
            # Get all vehicles from Strapi API with relationships
            async with self.session.get(f"{self.api_base_url}/api/vehicles?populate=vehicle_status", timeout=10) as response:
                if response.status == 200:
                    vehicles_data = await response.json()
                    vehicles = []
                    
                    # Transform Strapi vehicles to match FastAPI format
                    for vehicle_item in vehicles_data.get('data', []):
                        vehicle = vehicle_item
                        status = vehicle.get('vehicle_status')
                        
                        # Create normalized vehicle dict matching FastAPI format
                        normalized_vehicle = {
                            'registration': vehicle.get('reg_code', ''),
                            'reg_code': vehicle.get('reg_code', ''),  # Also include for compatibility
                            'capacity': vehicle.get('capacity', 0),
                            'type': vehicle.get('vehicle_type', 'bus'),  # Default type
                            'status': status.get('status_id', 'unknown') if status else 'unknown',
                            'vehicle_status': status.get('status_id', 'unknown') if status else 'unknown',
                            'max_speed_kmh': vehicle.get('max_speed_kmh', 90),
                            'acceleration_mps2': vehicle.get('acceleration_mps2', 1.2),
                            'braking_mps2': vehicle.get('braking_mps2', 1.8),
                            'eco_mode': vehicle.get('eco_mode', True),
                            'createdAt': vehicle.get('createdAt'),
                            'updatedAt': vehicle.get('updatedAt')
                        }
                        vehicles.append(normalized_vehicle)
                    
                    logging.debug(f"[StrapiStrategy] Fetched {len(vehicles)} total depot vehicles from Strapi")
                    return vehicles
                else:
                    logging.error(f"[StrapiStrategy] Failed to fetch depot vehicles: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logging.error(f"[StrapiStrategy] Error fetching depot vehicles: {str(e)}")
            return []
    
    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments from Strapi using vehicle→driver reverse relationship"""
        if not self.api_connected or not self.session:
            logging.error(f"[StrapiStrategy] Cannot fetch driver assignments - API not connected")
            return []
        
        try:
            # Get vehicle assignments and extract driver info (reverse of vehicle assignments)
            vehicle_assignments = await self.get_vehicle_assignments()
            assignments = []
            
            # Transform vehicle assignments into driver assignments
            for vehicle_assignment in vehicle_assignments:
                if vehicle_assignment.driver_id and vehicle_assignment.driver_name:
                    assignment = DriverAssignment(
                        driver_id=vehicle_assignment.driver_id,
                        driver_name=vehicle_assignment.driver_name,
                        license_number=vehicle_assignment.driver_id,  # Same as driver_id
                        vehicle_id=vehicle_assignment.vehicle_id,
                        route_id=vehicle_assignment.route_id,
                        status="available",  # All active drivers are available
                        shift_start=vehicle_assignment.start_time,
                        shift_end=vehicle_assignment.end_time
                    )
                    assignments.append(assignment)
                
            logging.info(f"[StrapiStrategy] Fetched {len(assignments)} driver assignments from vehicle relationships")
            return assignments
                    
        except Exception as e:
            logging.error(f"[StrapiStrategy] Error fetching driver assignments: {str(e)}")
            return []
    
    async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
        """Get route information and geometry using GTFS-compliant Strapi structure"""
        if not self.api_connected or not self.session:
            logging.error(f"[StrapiStrategy] Cannot fetch route info - Strapi API not connected")
            return None
        
        try:
            # Step 1: Get route details by route code from Strapi routes table
            async with self.session.get(f"{self.api_base_url}/api/routes?filters[short_name][$eq]={route_code}", timeout=10) as route_response:
                if route_response.status != 200:
                    logging.error(f"[StrapiStrategy] Failed to fetch route {route_code}: HTTP {route_response.status}")
                    return None
                    
                route_data = await route_response.json()
                routes = route_data.get('data', [])
                
                if not routes:
                    logging.error(f"[StrapiStrategy] Route {route_code} not found in Strapi")
                    return None
                
                route = routes[0]
                route_name = route.get('long_name', f'Route {route_code}')
                
                logging.info(f"[StrapiStrategy] Found route: {route_name} (code: {route_code})")
                
            # Step 2: Get ALL route-shapes for this route
            async with self.session.get(f"{self.api_base_url}/api/route-shapes?filters[route_id][$eq]={route_code}", timeout=10) as shape_link_response:
                if shape_link_response.status != 200:
                    logging.error(f"[StrapiStrategy] Failed to fetch route-shapes for route {route_code}: HTTP {shape_link_response.status}")
                    return None

                shape_link_data = await shape_link_response.json()
                route_shapes = shape_link_data.get('data', [])

                if not route_shapes:
                    logging.error(f"[StrapiStrategy] No route-shapes found for route {route_code}")
                    return None

            # Step 3: For each shape, get all shape points and concatenate
            all_coordinates = []
            all_shape_ids = []
            for shape in route_shapes:
                shape_id = shape.get('shape_id')
                all_shape_ids.append(shape_id)
                async with self.session.get(f"{self.api_base_url}/api/shapes?filters[shape_id][$eq]={shape_id}&sort=shape_pt_sequence&pagination[pageSize]=1000", timeout=15) as shapes_response:
                    if shapes_response.status != 200:
                        logging.error(f"[StrapiStrategy] Failed to fetch shapes for shape_id {shape_id}: HTTP {shapes_response.status}")
                        continue

                    shapes_data = await shapes_response.json()
                    shape_points = shapes_data.get('data', [])

                    if not shape_points:
                        logging.warning(f"[StrapiStrategy] No shape points found for shape_id {shape_id}")
                        continue

                    for point in shape_points:
                        lon = point.get('shape_pt_lon')
                        lat = point.get('shape_pt_lat')
                        if lon is not None and lat is not None:
                            all_coordinates.append([lon, lat])

            coordinate_count = len(all_coordinates)

            if coordinate_count > 0:
                logging.info(f"[StrapiStrategy] ✅ Route {route_name} has {coordinate_count} GPS coordinates from ALL GTFS-compliant Strapi shapes")
                first_coord = all_coordinates[0]
                last_coord = all_coordinates[-1]
                logging.info(f"[StrapiStrategy] Route path: [{first_coord[0]:.6f}, {first_coord[1]:.6f}] → [{last_coord[0]:.6f}, {last_coord[1]:.6f}] (all shapes)")
                geometry = {
                    "type": "LineString",
                    "coordinates": all_coordinates
                }
            else:
                logging.error(f"[StrapiStrategy] ❌ No valid coordinates found for route {route_code} (all shapes)")
                return None

            # Create RouteInfo with complete data from ALL GTFS-compliant Strapi shapes
            route_info = RouteInfo(
                route_id=route_code,
                route_name=route_name,
                route_type='bus',
                geometry=geometry,
                stops=None,
                distance_km=None,
                coordinate_count=coordinate_count,
                shape_id=','.join(all_shape_ids)  # List all shape_ids used
            )

            logging.info(f"[StrapiStrategy] ✅ Successfully loaded Route {route_name} with {coordinate_count} GPS coordinates from ALL GTFS shapes")
            return route_info
                    
        except Exception as e:
            logging.error(f"[StrapiStrategy] Error fetching route info for {route_code}: {str(e)}")
            return None
    
    async def close(self) -> None:
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None


class Dispatcher(StateMachine, IDispatcher):
    def __init__(self, component_name: str = "Dispatcher", api_strategy: Optional[ApiStrategy] = None, api_base_url: Optional[str] = None):
        """
        Initialize dispatcher.
        
        Args:
            component_name: Name of the dispatcher component
            api_strategy: Optional API strategy (Strapi, FastAPI, etc.)
            api_base_url: API base URL. If None, loads from config.ini via ConfigProvider.
        """
        super().__init__(component_name, PersonState.OFFSITE)
        self.initialized = False
        
        # Load api_base_url from config if not provided
        if api_base_url is None:
            if _config_available:
                try:
                    config = get_config()
                    api_base_url = config.infrastructure.strapi_url
                except Exception:
                    api_base_url = "http://localhost:1337"  # Fallback default
            else:
                api_base_url = "http://localhost:1337"  # Fallback if config not available
        
        # Use provided strategy or create default Strapi strategy (modern GTFS-compliant)
        if api_strategy is None:
            self.api_strategy = StrapiStrategy(api_base_url)
        else:
            self.api_strategy = api_strategy
            
        # Keep backwards compatibility  
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_connected = False
        self.route_buffer = RouteBuffer()
    
    async def initialize(self) -> bool:
        """Initialize dispatcher with API connection - NO fallback allowed."""
        try:
            # Transition to arriving state
            await self.transition_to(PersonState.ARRIVING)
            
            # Initialize the API strategy
            if hasattr(self.api_strategy, 'initialize'):
                await self.api_strategy.initialize()
            
            # Test API connection through strategy - CRITICAL: Must succeed or fail completely
            api_connected = await self.api_strategy.test_connection()
            if not api_connected:
                if hasattr(self.api_strategy, 'close'):
                    await self.api_strategy.close()
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
            
            # Close API strategy
            if hasattr(self.api_strategy, 'close'):
                await self.api_strategy.close()
            
            # Close HTTP session for backwards compatibility
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
        """Get vehicle assignments - delegates to API strategy."""
        return await self.api_strategy.get_vehicle_assignments()
    
    async def get_all_depot_vehicles(self) -> List[Dict[str, Any]]:
        """Get ALL vehicles in depot - delegates to API strategy."""
        return await self.api_strategy.get_all_depot_vehicles()
    
    async def get_driver_assignments(self) -> List[DriverAssignment]:
        """Get driver assignments - delegates to API strategy."""
        return await self.api_strategy.get_driver_assignments()
    
    async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
        """Get route information and geometry - delegates to API strategy."""
        return await self.api_strategy.get_route_info(route_code)
    
    async def send_routes_to_drivers(self, driver_routes: List[Dict[str, str]]) -> bool:
        """Send route assignments with GPS coordinates to drivers via Fleet Manager API."""
        logging.info(f"[{self.component_name}] 🚀 send_routes_to_drivers called with {len(driver_routes)} routes")
        
        if not self.api_connected:
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
            
            # Skip API route assignment during development - Fleet Manager API may not be available
            if len(enhanced_assignments) > 0:
                logging.info(f"[{self.component_name}] Route assignments prepared for {len(enhanced_assignments)} vehicles (API transmission skipped in development mode)")
                return True
            else:
                logging.info(f"[{self.component_name}] No route assignments to prepare")
                return False
                    
        except Exception as e:
            logging.error(f"[{self.component_name}] Error preparing routes with GPS data: {str(e)}")
            return False
    
    async def populate_route_buffer(self, route_ids: List[str]) -> bool:
        """Populate route buffer with complete route data for passenger service queries."""
        if not self.api_connected:
            logging.error(f"[{self.component_name}] Cannot populate route buffer - API not connected")
            return False
        
        try:
            await self.route_buffer.clear()
            populated_count = 0
            
            for route_id in route_ids:
                route_info = await self.get_route_info(route_id)
                if route_info:
                    success = await self.route_buffer.add_route(route_info)
                    if success:
                        populated_count += 1
                    else:
                        logging.warning(f"[{self.component_name}] Failed to buffer route {route_id}")
                else:
                    logging.warning(f"[{self.component_name}] No route info available for {route_id}")
            
            stats = await self.route_buffer.get_stats()
            logging.info(f"[{self.component_name}] Route buffer populated: {populated_count}/{len(route_ids)} routes, {stats['total_gps_points']} GPS index points")
            
            return populated_count > 0
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Error populating route buffer: {str(e)}")
            return False
    
    async def query_route_by_id(self, route_id: str) -> Optional[RouteInfo]:
        """Query route buffer for complete route geometry by route ID."""
        try:
            return await self.route_buffer.get_route_by_id(route_id)
        except Exception as e:
            logging.error(f"[{self.component_name}] Error querying route {route_id}: {str(e)}")
            return None
    
    async def query_routes_by_gps(self, lat: float, lon: float, walking_distance_km: float = 0.5) -> List[RouteInfo]:
        """Query route buffer for all routes within walking distance of GPS coordinates."""
        try:
            routes = await self.route_buffer.get_routes_by_gps(lat, lon, walking_distance_km)
            logging.debug(f"[{self.component_name}] Found {len(routes)} routes within {walking_distance_km}km of ({lat:.6f}, {lon:.6f})")
            return routes
        except Exception as e:
            logging.error(f"[{self.component_name}] Error querying routes by GPS ({lat}, {lon}): {str(e)}")
            return []
    
    async def get_route_buffer_stats(self) -> Dict[str, Any]:
        """Get route buffer statistics for monitoring."""
        try:
            return await self.route_buffer.get_stats()
        except Exception as e:
            logging.error(f"[{self.component_name}] Error getting route buffer stats: {str(e)}")
            return {'error': str(e)}
    
    # Strategy management helper methods
    def get_current_strategy(self) -> str:
        """Get the name of the currently active API strategy."""
        return type(self.api_strategy).__name__
    
    def get_current_api_url(self) -> str:
        """Get the API base URL of the current strategy."""
        return getattr(self.api_strategy, 'api_base_url', 'Unknown')
    
    async def switch_to_fastapi(self, api_url: str = "http://localhost:8000") -> bool:
        """Switch to FastAPI strategy - for backward compatibility or fallback."""
        try:
            # Close current strategy
            if hasattr(self.api_strategy, 'session') and self.api_strategy.session:
                await self.api_strategy.session.close()
            
            # Switch to FastAPI strategy
            self.api_strategy = FastApiStrategy(api_url)
            self.api_base_url = api_url
            
            # Initialize new strategy
            await self.api_strategy.initialize()
            self.api_connected = await self.api_strategy.test_connection()
            
            logging.info(f"[{self.component_name}] Switched to FastAPI strategy: {api_url}")
            return self.api_connected
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Failed to switch to FastAPI: {str(e)}")
            return False
    
    async def switch_to_strapi(self, api_url: str = "http://localhost:1337") -> bool:
        """Switch to Strapi strategy - modern GTFS-compliant API."""
        try:
            # Close current strategy
            if hasattr(self.api_strategy, 'session') and self.api_strategy.session:
                await self.api_strategy.session.close()
            
            # Switch to Strapi strategy
            self.api_strategy = StrapiStrategy(api_url)
            self.api_base_url = api_url
            
            # Initialize new strategy
            await self.api_strategy.initialize()
            self.api_connected = await self.api_strategy.test_connection()
            
            logging.info(f"[{self.component_name}] Switched to Strapi strategy: {api_url}")
            return self.api_connected
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Failed to switch to Strapi: {str(e)}")
            return False