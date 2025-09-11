"""
Unified Data Provider
--------------------
Unified provider that uses fleet_manager API endpoints to get all fleet data:
routes, timetables, schedules, vehicles, drivers, services, etc.
Includes real-time Socket.IO monitoring of API availability.
Replaces the specific database_route_provider with a comprehensive solution.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time as time_type
from sqlalchemy import Date

from world.vehicle_simulator.providers.api_monitor import SocketIOAPIMonitor, APIConnectionStatus

logger = logging.getLogger(__name__)


class FleetDataProvider:
    """
    Unified data provider that queries fleet_manager for all operational data.
    Includes real-time Socket.IO monitoring for API availability.
    Eliminates need for separate route, vehicle, and config providers.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        
        # Initialize Socket.IO monitoring
        self.api_monitor = SocketIOAPIMonitor(server_url)
        self.api_monitor.add_status_callback(self._on_api_status_change)
        
        # Fleet manager connection (only when API is available)
        self._fleet_manager = None
        self._api_available = False
        
        # Start monitoring
        self.api_monitor.start_monitoring()
        
        logger.info(f"Fleet data provider initialized with Socket.IO monitoring for {server_url}")
        logger.info("Waiting for fleet manager API connection...")

    def _on_api_status_change(self, status: APIConnectionStatus):
        """Handle API status changes"""
        previous_state = self._api_available
        self._api_available = status.is_connected and status.server_status == 'online'
        
        if self._api_available and not previous_state:
            logger.info("✅ Fleet Manager API is now available - initializing connection")
            self._initialize_fleet_manager()
        elif not self._api_available and previous_state:
            logger.warning("❌ Fleet Manager API is now unavailable")
            self._cleanup_fleet_manager()

    def _initialize_fleet_manager(self):
        """Initialize API connection - NO DIRECT DATABASE ACCESS"""
        if not self.api_monitor.is_api_available():
            logger.warning("Cannot initialize - API not available")
            return
            
        logger.info("✅ Fleet manager connection established via API")
        # No direct database connections - only API calls

    def _cleanup_fleet_manager(self):
        """Clean up API connections - no database connections to close"""
        logger.info("API connections cleaned up")
    
    def __del__(self):
        """Clean up connections"""
        if self.api_monitor:
            self.api_monitor.stop_monitoring()
        self._cleanup_fleet_manager()
    
    def is_api_available(self) -> bool:
        """Check if fleet manager API is currently available"""
        return self._api_available
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API connection status"""
        return self.api_monitor.get_status().to_dict()
    
    def force_reconnect(self):
        """Force API reconnection attempt"""
        logger.info("Forcing API reconnection")
        self.api_monitor.force_reconnect()
    
    def _ensure_api_available(self, retry_attempts: int = 3):
        """Ensure API is available before making calls, with retry logic"""
        for attempt in range(retry_attempts):
            if self.is_api_available():
                return
            
            if attempt < retry_attempts - 1:
                logger.warning(f"API not available, retrying in 1 second... (attempt {attempt + 1}/{retry_attempts})")
                time.sleep(1)
                # Force reconnection attempt
                self.api_monitor.force_reconnect()
                time.sleep(1)  # Give it time to reconnect
            else:
                status = self.api_monitor.get_status()
                error_msg = f"Fleet Manager API not available after {retry_attempts} attempts: {status.error or 'Connection lost'}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    # ==================== COMPREHENSIVE DATA RETRIEVAL ====================
    
    def get_all_fleet_data(self) -> Dict[str, Any]:
        """
        Get complete fleet operational data from database.
        Returns all data needed for fleet simulation.
        
        Returns:
            Dict containing: vehicles, routes, timetables, schedules, drivers, services
        """
        self._ensure_api_available()
        
        try:
            logger.info("Loading complete fleet data from database...")
            
            fleet_data = {
                'vehicles': self.get_vehicles(),
                'routes': self.get_routes(),
                'timetables': self.get_timetables(),
                'schedules': self.get_schedules(),
                'drivers': self.get_drivers(),
                'services': self.get_services(),
                'depots': self.get_depots()
            }
            
            logger.info(f"Loaded fleet data: "
                       f"{len(fleet_data['vehicles'])} vehicles, "
                       f"{len(fleet_data['routes'])} routes, "
                       f"{len(fleet_data['schedules'])} schedules")
            
            return fleet_data
            
        except Exception as e:
            logger.error(f"Failed to load fleet data: {e}")
            raise
    
    # ==================== VEHICLE DATA ====================
    
    def get_vehicles(self) -> List[Dict[str, Any]]:
        """
        Get all vehicles with their specifications and current assignments.
        Replaces vehicles.json with live database data.
        """
        self._ensure_api_available()
        
        try:
            import requests
            
            # Use API with retry logic for temporary connection issues
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.server_url}/api/v1/vehicles", timeout=10)
                    response.raise_for_status()
                    api_vehicles = response.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Vehicles API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
            vehicles = []
            for vehicle in api_vehicles:
                # Use human-readable identifiers instead of UUIDs
                vehicle_data = {
                    'id': vehicle.get('vehicle_id'),  # Keep UUID for internal use
                    'vehicle_name': vehicle.get('reg_code', 'Unknown Vehicle'),  # User-friendly name
                    'license_plate': vehicle.get('reg_code'),
                    'capacity': vehicle.get('capacity'),
                    'fuel_type': None,  # Not available in API
                    'status': vehicle.get('status'),
                    'depot_id': vehicle.get('home_depot_id'),  # Keep for lookups
                    'depot_name': self._get_depot_name(vehicle.get('home_depot_id')),  # User-friendly depot name
                    'model': None,  # Not available in API
                    'year': None,  # Not available in API
                    'active': vehicle.get('status') == 'active',
                    'current_assignment': None  # Would need separate API call
                }
                vehicles.append(vehicle_data)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Failed to get vehicles: {e}")
            return []
    
    def _get_depot_name(self, depot_id: str) -> str:
        """Get user-friendly depot name from depot_id"""
        if not depot_id:
            return "No Depot Assigned"
            
        try:
            # Cache depot names to avoid repeated API calls
            if not hasattr(self, '_depot_cache'):
                self._depot_cache = {}
                
            if depot_id in self._depot_cache:
                return self._depot_cache[depot_id]
                
            # Get depot info
            depots = self.get_depots()
            for depot in depots:
                if depot.get('depot_id') == depot_id:
                    depot_name = depot.get('name', f'Depot {depot_id[:8]}')
                    self._depot_cache[depot_id] = depot_name
                    return depot_name
                    
            # Fallback to shortened UUID
            short_id = depot_id[:8] if depot_id else 'Unknown'
            fallback_name = f"Depot {short_id}"
            self._depot_cache[depot_id] = fallback_name
            return fallback_name
            
        except Exception as e:
            logger.warning(f"Failed to get depot name for {depot_id}: {e}")
            return f"Depot {depot_id[:8]}" if depot_id else "Unknown Depot"
    
    # ==================== ROUTE DATA ====================yping import Dict, List, Optional, Any, Tuple
from datetime import datetime, time as time_type
from sqlalchemy import Date

from world.vehicle_simulator.providers.api_monitor import SocketIOAPIMonitor, APIConnectionStatus

logger = logging.getLogger(__name__)


class FleetDataProvider:
    """
    Unified data provider that queries fleet_manager for all operational data.
    Includes real-time Socket.IO monitoring for API availability.
    Eliminates need for separate route, vehicle, and config providers.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        
        # Initialize Socket.IO monitoring
        self.api_monitor = SocketIOAPIMonitor(server_url)
        self.api_monitor.add_status_callback(self._on_api_status_change)
        
        # Fleet manager connection (only when API is available)
        self._fleet_manager = None
        self._api_available = False
        
        # Start monitoring
        self.api_monitor.start_monitoring()
        
        logger.info(f"Fleet data provider initialized with Socket.IO monitoring for {server_url}")
        logger.info("Waiting for fleet manager API connection...")

    def _on_api_status_change(self, status: APIConnectionStatus):
        """Handle API status changes"""
        previous_state = self._api_available
        self._api_available = status.is_connected and status.server_status == 'online'
        
        if self._api_available and not previous_state:
            logger.info("✅ Fleet Manager API is now available - initializing connection")
            self._initialize_fleet_manager()
        elif not self._api_available and previous_state:
            logger.warning("❌ Fleet Manager API is now unavailable")
            self._cleanup_fleet_manager()

    def _initialize_fleet_manager(self):
        """Initialize API connection - NO DIRECT DATABASE ACCESS"""
        if not self.api_monitor.is_api_available():
            logger.warning("Cannot initialize - API not available")
            return
            
        logger.info("✅ Fleet manager connection established via API")
        # No direct database connections - only API calls

    def _cleanup_fleet_manager(self):
        """Clean up API connections - no database connections to close"""
        logger.info("API connections cleaned up")
    
    def __del__(self):
        """Clean up connections"""
        if self.api_monitor:
            self.api_monitor.stop_monitoring()
        self._cleanup_fleet_manager()
    
    def is_api_available(self) -> bool:
        """Check if fleet manager API is currently available"""
        return self._api_available
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API connection status"""
        return self.api_monitor.get_status().to_dict()
    
    def force_reconnect(self):
        """Force API reconnection attempt"""
        logger.info("Forcing API reconnection")
        self.api_monitor.force_reconnect()
    
    def _ensure_api_available(self, retry_attempts: int = 3):
        """Ensure API is available before making calls, with retry logic"""
        for attempt in range(retry_attempts):
            if self.is_api_available():
                return
            
            if attempt < retry_attempts - 1:
                logger.warning(f"API not available, retrying in 1 second... (attempt {attempt + 1}/{retry_attempts})")
                time.sleep(1)
                # Force reconnection attempt
                self.api_monitor.force_reconnect()
                time.sleep(1)  # Give it time to reconnect
            else:
                status = self.api_monitor.get_status()
                error_msg = f"Fleet Manager API not available after {retry_attempts} attempts: {status.error or 'Connection lost'}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    # ==================== COMPREHENSIVE DATA RETRIEVAL ====================
    
    def get_all_fleet_data(self) -> Dict[str, Any]:
        """
        Get complete fleet operational data from database.
        Returns all data needed for fleet simulation.
        
        Returns:
            Dict containing: vehicles, routes, timetables, schedules, drivers, services
        """
        self._ensure_api_available()
        
        try:
            logger.info("Loading complete fleet data from database...")
            
            fleet_data = {
                'vehicles': self.get_vehicles(),
                'routes': self.get_routes(),
                'timetables': self.get_timetables(),
                'schedules': self.get_schedules(),
                'drivers': self.get_drivers(),
                'services': self.get_services(),
                'depots': self.get_depots()
            }
            
            logger.info(f"Loaded fleet data: "
                       f"{len(fleet_data['vehicles'])} vehicles, "
                       f"{len(fleet_data['routes'])} routes, "
                       f"{len(fleet_data['schedules'])} schedules")
            
            return fleet_data
            
        except Exception as e:
            logger.error(f"Failed to load fleet data: {e}")
            raise
    
    # ==================== VEHICLE DATA ====================
    
    def get_vehicles(self) -> List[Dict[str, Any]]:
        """
        Get all vehicles with their specifications and current assignments.
        Replaces vehicles.json with live database data.
        """
        self._ensure_api_available()
        
        try:
            import requests
            
            # Use API with retry logic for temporary connection issues
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.server_url}/api/v1/vehicles", timeout=10)
                    response.raise_for_status()
                    api_vehicles = response.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Vehicles API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
            vehicles = []
            for vehicle in api_vehicles:
                # Use human-readable identifiers instead of UUIDs
                vehicle_data = {
                    'id': vehicle.get('vehicle_id'),  # Keep UUID for internal use
                    'vehicle_name': vehicle.get('reg_code', 'Unknown Vehicle'),  # User-friendly name
                    'license_plate': vehicle.get('reg_code'),
                    'capacity': vehicle.get('capacity'),
                    'fuel_type': None,  # Not available in API
                    'status': vehicle.get('status'),
                    'depot_id': vehicle.get('home_depot_id'),  # Keep for lookups
                    'depot_name': self._get_depot_name(vehicle.get('home_depot_id')),  # User-friendly depot name
                    'model': None,  # Not available in API
                    'year': None,  # Not available in API
                    'active': vehicle.get('status') == 'active',
                    'current_assignment': None  # Would need separate API call
                }
                vehicles.append(vehicle_data)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Failed to get vehicles: {e}")
            return []
    
    def _get_depot_name(self, depot_id: str) -> str:
        """Get user-friendly depot name from depot_id"""
        if not depot_id:
            return "No Depot Assigned"
            
        try:
            # Cache depot names to avoid repeated API calls
            if not hasattr(self, '_depot_cache'):
                self._depot_cache = {}
                
            if depot_id in self._depot_cache:
                return self._depot_cache[depot_id]
                
            # Get depot info
            depots = self.get_depots()
            for depot in depots:
                if depot.get('depot_id') == depot_id:
                    depot_name = depot.get('name', f'Depot {depot_id[:8]}')
                    self._depot_cache[depot_id] = depot_name
                    return depot_name
                    
            # Fallback to shortened UUID
            short_id = depot_id[:8] if depot_id else 'Unknown'
            fallback_name = f"Depot {short_id}"
            self._depot_cache[depot_id] = fallback_name
            return fallback_name
            
        except Exception as e:
            logger.warning(f"Failed to get depot name for {depot_id}: {e}")
            return f"Depot {depot_id[:8]}" if depot_id else "Unknown Depot"
    
    def _get_route_name(self, route_id: str) -> str:
        """Get user-friendly route name from route_id"""
        if not route_id:
            return "No Route Assigned"
            
        try:
            # Cache route names to avoid repeated API calls
            if not hasattr(self, '_route_cache'):
                self._route_cache = {}
                
            if route_id in self._route_cache:
                return self._route_cache[route_id]
                
            # Get route info
            routes = self.get_routes()
            for route_key, route_data in routes.items():
                if route_data.get('id') == route_id:
                    route_name = route_data.get('route_name', f'Route {route_key}')
                    self._route_cache[route_id] = route_name
                    return route_name
                    
            # Fallback to shortened UUID
            short_id = route_id[:8] if route_id else 'Unknown'
            fallback_name = f"Route {short_id}"
            self._route_cache[route_id] = fallback_name
            return fallback_name
            
        except Exception as e:
            logger.warning(f"Failed to get route name for {route_id}: {e}")
            return f"Route {route_id[:8]}" if route_id else "Unknown Route"
    
    def _get_driver_name(self, driver_id: str) -> str:
        """Get user-friendly driver name from driver_id"""
        if not driver_id:
            return "No Driver Assigned"
            
        try:
            # Cache driver names to avoid repeated API calls
            if not hasattr(self, '_driver_cache'):
                self._driver_cache = {}
                
            if driver_id in self._driver_cache:
                return self._driver_cache[driver_id]
                
            # Get driver info
            drivers = self.get_drivers()
            for driver in drivers:
                if driver.get('id') == driver_id:
                    driver_name = driver.get('driver_name', 'Unknown Driver')
                    self._driver_cache[driver_id] = driver_name
                    return driver_name
                    
            # Fallback to shortened UUID
            short_id = driver_id[:8] if driver_id else 'Unknown'
            fallback_name = f"Driver {short_id}"
            self._driver_cache[driver_id] = fallback_name
            return fallback_name
            
        except Exception as e:
            logger.warning(f"Failed to get driver name for {driver_id}: {e}")
            return f"Driver {driver_id[:8]}" if driver_id else "Unknown Driver"
    
    def _get_assigned_driver_for_vehicle(self, vehicle_id: str) -> str:
        """Get assigned driver for vehicle (simulated assignment for demo)"""
        if not vehicle_id:
            return "No Driver Assigned"
            
        try:
            # Get all drivers and assign based on simple round-robin
            drivers = self.get_drivers()
            if not drivers:
                return "No Drivers Available"
                
            # Use vehicle_id hash to consistently assign same driver to same vehicle
            import hashlib
            vehicle_hash = int(hashlib.md5(vehicle_id.encode()).hexdigest(), 16)
            driver_index = vehicle_hash % len(drivers)
            assigned_driver = drivers[driver_index]
            
            return assigned_driver.get('driver_name', 'Unknown Driver')
            
        except Exception as e:
            logger.warning(f"Failed to assign driver for vehicle {vehicle_id}: {e}")
            return "Driver Assignment Error"
    
    def _get_vehicle_current_assignment(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get current operational assignment for vehicle via API"""
        self._ensure_api_available()
        
        try:
            import requests
            
            # Use API instead of direct database access with consistent timeout
            response = requests.get(
                f"{self.server_url}/api/v1/vehicle_assignments?vehicle_id={vehicle_id}",
                timeout=10
            )
            response.raise_for_status()
            
            assignments = response.json()
            if assignments:
                assignment = assignments[0]  # Get most recent
                return {
                    'route_id': assignment.get('route_id'),  # Keep for internal use
                    'route_name': self._get_route_name(assignment.get('route_id')),  # User-friendly route
                    'driver_id': assignment.get('driver_id'),  # Keep for internal use
                    'driver_name': self._get_driver_name(assignment.get('driver_id')),  # User-friendly driver
                    'block_id': assignment.get('block_id'),
                    'start_time': assignment.get('start_time'),
                    'end_time': assignment.get('end_time'),
                    'service_id': assignment.get('service_id')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vehicle assignment for {vehicle_id}: {e}")
            return None
    
    # ==================== ROUTE DATA ====================
    
    def get_routes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all routes with coordinates and metadata via API.
        Replaces direct database access with API calls.
        """
        self._ensure_api_available()
        
        try:
            import requests
            
            # Use API with retry logic for temporary connection issues
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.server_url}/api/v1/routes", timeout=10)
                    response.raise_for_status()
                    api_routes = response.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Routes API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
            routes = {}
            for route in api_routes:
                short_name = route.get('short_name', 'Unknown Route')
                long_name = route.get('long_name', '')
                
                # Create user-friendly display name
                if long_name and long_name != short_name:
                    display_name = f"Route {short_name} ({long_name})"
                else:
                    display_name = f"Route {short_name}"
                
                route_data = {
                    'id': route.get('route_id'),  # Keep UUID for internal use
                    'route_name': display_name,  # User-friendly name
                    'short_name': short_name,
                    'long_name': long_name,
                    'description': route.get('description'),
                    'color': route.get('color'),
                    'coordinates': self.get_route_coordinates(short_name),
                    'stops': self._get_route_stops(route.get('route_id'))
                }
                routes[short_name] = route_data
            
            return routes
            
        except Exception as e:
            logger.error(f"❌ FAILED TO GET ROUTES: {e}")
            raise Exception(f"Route data unavailable: {e}")
    
    def get_route_coordinates(self, route_identifier: str) -> List[Tuple[float, float]]:
        """
        Get route coordinates via API.
        Maintains compatibility with existing Navigator interface.
        Returns coordinates as (latitude, longitude) tuples.
        """
        self._ensure_api_available()
        logger.info(f"🗺️  Getting coordinates for route {route_identifier}")
        
        try:
            import requests
            
            # Step 1: Get route shapes metadata for the route
            shapes_response = requests.get(
                f"{self.server_url}/api/v1/route_shapes?route_short_name={route_identifier}", 
                timeout=10
            )
            
            if shapes_response.status_code != 200:
                logger.error(f"❌ Failed to get route shapes metadata: HTTP {shapes_response.status_code}")
                return []
            
            route_shapes = shapes_response.json()
            if not route_shapes:
                logger.warning(f"⚠️  No shapes found for route {route_identifier}")
                return []
            
            logger.info(f"📊 Found {len(route_shapes)} shapes for route {route_identifier}")
            
            # Step 2: Get actual geometry for each shape
            all_coordinates = []
            for shape_info in route_shapes:
                shape_id = shape_info.get('shape_id')
                if not shape_id:
                    continue
                
                # Get the actual geometry from the shapes endpoint
                geometry_response = requests.get(
                    f"{self.server_url}/api/v1/shapes/{shape_id}", 
                    timeout=10
                )
                
                if geometry_response.status_code == 200:
                    shape_data = geometry_response.json()
                    geom = shape_data.get('geom')
                    
                    if geom and geom.get('type') == 'LineString':
                        coordinates = geom.get('coordinates', [])
                        logger.info(f"📍 Shape {shape_id}: {len(coordinates)} coordinate points")
                        
                        # Convert from [longitude, latitude] to (latitude, longitude) tuples
                        for coord_pair in coordinates:
                            if len(coord_pair) >= 2:
                                longitude, latitude = coord_pair[0], coord_pair[1]
                                all_coordinates.append((float(latitude), float(longitude)))
                    else:
                        logger.warning(f"⚠️  Shape {shape_id} has unexpected geometry type: {geom.get('type', 'None')}")
                else:
                    logger.error(f"❌ Failed to get geometry for shape {shape_id}: HTTP {geometry_response.status_code}")
            
            if all_coordinates:
                logger.info(f"✅ Retrieved {len(all_coordinates)} total coordinate points for route {route_identifier}")
                return all_coordinates
            else:
                logger.warning(f"⚠️  No coordinate points found for route {route_identifier}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to get route coordinates for {route_identifier}: {e}")
            return []
    
    def _get_route_stops(self, route_id: str) -> List[Dict[str, Any]]:
        """Get stops for a specific route via API"""
        if not route_id:
            return []
            
        try:
            import requests
            
            # Use API with consistent timeout and error handling
            response = requests.get(
                f"{self.server_url}/api/v1/stop_times?route_id={route_id}",
                timeout=10
            )
            response.raise_for_status()
            
            stop_times = response.json()
            stops = []
            for stop_time in stop_times:
                stop_data = {
                    'stop_id': stop_time.get('stop_id'),
                    'name': stop_time.get('stop_name'),  # Assuming API provides this
                    'lat': stop_time.get('stop_lat'),
                    'lon': stop_time.get('stop_lon'),
                    'sequence': stop_time.get('stop_sequence'),
                    'arrival_time': stop_time.get('arrival_time'),
                    'departure_time': stop_time.get('departure_time')
                }
                stops.append(stop_data)
            
            return stops
            
        except Exception as e:
            logger.error(f"Failed to get stops for route {route_id}: {e}")
            return []
    
    # ==================== SCHEDULE DATA ====================
    
    def get_timetables(self) -> List[Dict[str, Any]]:
        """Get all service timetables via API"""
        self._ensure_api_available()
        
        try:
            import requests
            
            response = requests.get(f"{self.server_url}/api/v1/timetables", timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get timetables: {e}")
            return []
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get vehicle-specific schedules for today via API"""
        self._ensure_api_available()
        
        try:
            import requests
            
            response = requests.get(f"{self.server_url}/api/v1/vehicle_assignments", timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get schedules: {e}")
            return []
    
    # ==================== SIMPLIFIED API METHODS ====================
    
    def get_drivers(self) -> List[Dict[str, Any]]:
        """Get all drivers via API (optional for basic simulation)"""
        try:
            # Only check API availability, don't enforce it for optional data
            if not self.is_api_available():
                logger.warning("API not available, skipping drivers data")
                return []
                
            import requests
            response = requests.get(f"{self.server_url}/api/v1/drivers", timeout=10)
            response.raise_for_status()
            api_drivers = response.json()
            
            # Transform to user-friendly format
            drivers = []
            for driver in api_drivers:
                driver_data = {
                    'id': driver.get('driver_id'),  # Keep UUID for internal use
                    'driver_name': driver.get('name', 'Unknown Driver'),  # User-friendly name
                    'license_no': driver.get('license_no'),
                    'employment_status': driver.get('employment_status'),
                    'home_depot_id': driver.get('home_depot_id'),
                    'home_depot_name': self._get_depot_name(driver.get('home_depot_id')),  # User-friendly depot
                    'created_at': driver.get('created_at'),
                    'updated_at': driver.get('updated_at')
                }
                drivers.append(driver_data)
            
            return drivers
            
        except Exception as e:
            logger.warning(f"Drivers not available via API: {e}")
            return []
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get all service definitions via API (optional for basic simulation)"""
        try:
            # Only check API availability, don't enforce it for optional data
            if not self.is_api_available():
                logger.warning("API not available, skipping services data")
                return []
                
            import requests
            response = requests.get(f"{self.server_url}/api/v1/services", timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.warning(f"Services not available via API: {e}")
            return []
    
    def get_depots(self) -> List[Dict[str, Any]]:
        """Get all depot locations via API (optional for basic simulation)"""
        try:
            # Only check API availability, don't enforce it for optional data
            if not self.is_api_available():
                logger.warning("API not available, skipping depots data")
                return []
                
            import requests
            response = requests.get(f"{self.server_url}/api/v1/depots", timeout=10)
            response.raise_for_status()
            api_depots = response.json()
            
            # Transform to user-friendly format
            depots = []
            for depot in api_depots:
                depot_data = {
                    'id': depot.get('depot_id'),  # Keep UUID for internal use
                    'depot_name': depot.get('name', 'Unknown Depot'),  # User-friendly name
                    'capacity': depot.get('capacity'),
                    'notes': depot.get('notes'),
                    'created_at': depot.get('created_at'),
                    'updated_at': depot.get('updated_at')
                }
                depots.append(depot_data)
            
            return depots
            
        except Exception as e:
            logger.warning(f"Depots not available via API: {e}")
            return []
    
    # ==================== OPERATIONAL QUERIES ====================
    
    def get_active_schedules_for_time(self, current_time: time_type) -> List[Dict[str, Any]]:
        """Get all vehicle schedules that should be active at given time"""
        try:
            active_schedules = []
            schedules = self.get_schedules()
            
            for schedule in schedules:
                start_time = schedule['start_time']
                end_time = schedule['end_time']
                
                if start_time <= current_time <= end_time:
                    active_schedules.append(schedule)
            
            return active_schedules
            
        except Exception as e:
            logger.error(f"Failed to get active schedules: {e}")
            return []
    
    def get_vehicles_for_depot(self, depot_id: str) -> List[Dict[str, Any]]:
        """Get all vehicles assigned to specific depot"""
        try:
            vehicles = self.get_vehicles()
            return [v for v in vehicles if v.get('depot_id') == depot_id]
        except Exception as e:
            logger.error(f"Failed to get vehicles for depot {depot_id}: {e}")
            return []
