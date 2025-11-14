"""
Unified Data Provider - FIXED VERSION
------------------------------------
Fixed version with:
1. Proper capacity handling (16 for all ZR vans)
2. Race condition fixes with API stabilization
3. Enhanced vehicle assignment display with route and driver info
4. Proper depot name resolution (Bridgetown instead of UUID)
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time as time_type
from sqlalchemy import Date

from arknet_transit_simulator.providers.api_monitor import SocketIOAPIMonitor, APIConnectionStatus

logger = logging.getLogger(__name__)


class FleetDataProvider:
    """
    Unified data provider that queries fleet_manager for all operational data.
    FIXED VERSION with proper capacity, depot names, and route assignments.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        
        # Initialize Socket.IO monitoring
        self.api_monitor = SocketIOAPIMonitor(server_url)
        self.api_monitor.add_status_callback(self._on_api_status_change)
        
        # Fleet manager connection (only when API is available)
        self._fleet_manager = None
        self._api_available = False
        
        # Comprehensive data caches
        self._route_coordinates_cache = {}  # Cache for route coordinates
        self._vehicles_cache = None
        self._routes_cache = None
        self._drivers_cache = None
        self._depots_cache = None
        self._cache_loaded = False
        
        # Start monitoring
        self.api_monitor.start_monitoring()
        
        logger.info(f"Fleet data provider initialized with Socket.IO monitoring for {server_url}")
        logger.info("Waiting for fleet manager API connection...")

    def _preload_all_data(self):
        """Pre-cache all data for faster subsequent access"""
        if self._cache_loaded or not self._api_available:
            return
            
        try:
            import requests
            import concurrent.futures
            
            logger.info("🚀 Pre-caching all fleet data for faster access...")
            
            # Define all API endpoints to cache (using public endpoints)
            cache_tasks = [
                ("vehicles", f"{self.server_url}/api/v1/vehicles/public"),
                ("routes", f"{self.server_url}/api/v1/routes/public"),
                ("drivers", f"{self.server_url}/api/v1/drivers/public"),
                ("depots", f"{self.server_url}/api/v1/depots/public"),
            ]
            
            def fetch_data(name, url):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        return name, response.json()
                except:
                    pass
                return name, []
            
            # Fetch all basic data concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_endpoint = {executor.submit(fetch_data, name, url): name for name, url in cache_tasks}
                
                for future in concurrent.futures.as_completed(future_to_endpoint):
                    name, data = future.result()
                    if name == "vehicles":
                        self._vehicles_cache = data
                    elif name == "routes":
                        self._routes_cache = data
                    elif name == "drivers":
                        self._drivers_cache = data
                    elif name == "depots":
                        self._depots_cache = data
            
            # Pre-cache route coordinates for all routes
            if self._routes_cache:
                route_tasks = []
                for route in self._routes_cache:
                    route_identifier = route.get('short_name')
                    if route_identifier and route_identifier not in self._route_coordinates_cache:
                        route_tasks.append(route_identifier)
                
                if route_tasks:
                    # Cache route coordinates concurrently
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        future_to_route = {executor.submit(self._load_route_coordinates_internal, route_id): route_id for route_id in route_tasks}
                        for future in concurrent.futures.as_completed(future_to_route):
                            pass  # Results are cached internally
            
            self._cache_loaded = True
            logger.info("✅ All fleet data cached successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to pre-cache data: {e}")

    def _on_api_status_change(self, status: APIConnectionStatus):
        """Handle API status changes with stabilization delay"""
        previous_state = self._api_available
        self._api_available = status.is_connected and status.server_status == 'online'
        
        if self._api_available and not previous_state:
            logger.info("✅ Fleet Manager API is now available - waiting for stabilization...")
            # Add delay to allow API endpoints to fully stabilize and prevent race conditions
            time.sleep(2)
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
        
        # Pre-cache all data in background
        import threading
        cache_thread = threading.Thread(target=self._preload_all_data, daemon=True)
        cache_thread.start()

    def _cleanup_fleet_manager(self):
        """Clean up API connections"""
        logger.info("API connections cleaned up")
    
    def __del__(self):
        """Clean up connections"""
        if self.api_monitor:
            self.api_monitor.stop_monitoring()
        self._cleanup_fleet_manager()
    
    def is_api_available(self) -> bool:
        """Check if fleet manager API is currently available"""
        # First check Socket.IO status (preferred)
        if self._api_available:
            return True
            
        # If Socket.IO says not available, do a quick direct HTTP check
        # This prevents race conditions where HTTP API is ready but Socket.IO isn't connected yet
        try:
            import requests
            response = requests.get(f"{self.server_url}/api/v1/vehicles/public", timeout=2)
            if response.status_code == 200:
                logger.debug("Direct HTTP API check successful (Socket.IO still connecting)")
                return True
        except:
            pass
            
        return False
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API connection status"""
        return self.api_monitor.get_status().to_dict()
    
    def force_reconnect(self):
        """Force API reconnection attempt"""
        logger.info("Forcing API reconnection")
        self.api_monitor.force_reconnect()
    
    def _ensure_api_available(self, retry_attempts: int = 3):
        """Ensure API is available before making calls, with improved logic"""
        for attempt in range(retry_attempts):
            if self.is_api_available():
                return
            
            if attempt < retry_attempts - 1:
                logger.warning(f"API not available, retrying in 1 second... (attempt {attempt + 1}/{retry_attempts})")
                time.sleep(1)
                # Only force Socket.IO reconnection if direct HTTP also fails
                try:
                    import requests
                    requests.get(f"{self.server_url}/api/v1/vehicles/public", timeout=2)
                    # If direct HTTP works, don't worry about Socket.IO for now
                    logger.debug("Direct HTTP works, continuing despite Socket.IO status")
                    return
                except:
                    # Force Socket.IO reconnection only if HTTP also fails
                    self.api_monitor.force_reconnect()
                    time.sleep(1)
            else:
                status = self.api_monitor.get_status()
                error_msg = f"Fleet Manager API not available after {retry_attempts} attempts: {status.error or 'Connection lost'}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    # ==================== VEHICLE DATA - FIXED VERSION ====================
    
    def get_vehicles(self) -> List[Dict[str, Any]]:
        """
        Get all vehicles with proper capacity, depot names, and route assignments.
        FIXED VERSION with 16-commuter capacity and user-friendly data.
        """
        self._ensure_api_available()
        
        # Use cached data if available
        if self._vehicles_cache is not None:
            api_vehicles = self._vehicles_cache
        else:
            try:
                import requests
                
                # Use API with retry logic for temporary connection issues
                for attempt in range(3):
                    try:
                        response = requests.get(f"{self.server_url}/api/v1/vehicles/public", timeout=10)
                        response.raise_for_status()
                        api_vehicles = response.json()
                        self._vehicles_cache = api_vehicles  # Cache the result
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt < 2:
                            logger.warning(f"Vehicles API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                            time.sleep(1)
                        else:
                            raise
            except Exception as e:
                logger.error(f"Failed to get vehicles: {e}")
                return []
        
        try:
            
            vehicles = []
            for vehicle in api_vehicles:
                # Use human-readable identifiers instead of UUIDs
                vehicle_data = {
                    'id': vehicle.get('vehicle_id'),  # Keep UUID for internal use
                    'vehicle_name': vehicle.get('reg_code', 'Unknown Vehicle'),  # User-friendly name
                    'license_plate': vehicle.get('reg_code'),
                    'capacity': 16,  # FIXED: All ZR vans in Barbados have 16-commuter capacity
                    'fuel_type': None,  # Not available in API
                    'status': vehicle.get('status'),
                    'depot_id': vehicle.get('home_depot_id'),  # Keep for lookups
                    'depot_name': self._get_depot_name(vehicle.get('home_depot_id')),  # User-friendly depot name
                    'model': None,  # Not available in API
                    'year': None,  # Not available in API
                    'active': vehicle.get('status') == 'active',
                    'current_assignment': None,  # Would need separate API call
                    # Route assignment information
                    'preferred_route_id': vehicle.get('preferred_route_id'),  # Keep for internal use
                    'assigned_route': self._get_route_name(vehicle.get('preferred_route_id')),  # User-friendly route name
                    # Driver assignment (from database relationship)
                    'assigned_driver_id': vehicle.get('assigned_driver_id'),  # UUID from database
                    'assigned_driver': self._get_driver_name(vehicle.get('assigned_driver_id'))
                }
                vehicles.append(vehicle_data)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Failed to get vehicles: {e}")
            return []
    
    def _get_depot_name(self, depot_id: str) -> str:
        """Get user-friendly depot name from depot_id - FIXED VERSION"""
        if not depot_id:
            return "No Depot Assigned"
            
        try:
            # Cache depot names to avoid repeated API calls
            if not hasattr(self, '_depot_cache'):
                self._depot_cache = {}
                
            if depot_id in self._depot_cache:
                return self._depot_cache[depot_id]
                
            # Get depot info from transformed data
            depots = self.get_depots()
            for depot in depots:
                # Use the correct field mapping for transformed depot data
                if depot.get('id') == depot_id:  # Use 'id' field from transformed data
                    depot_name = depot.get('depot_name', f'Depot {depot_id[:8]}')  # Use 'depot_name' from transformed data
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
        """Get user-friendly route name from route_id - SIMPLIFIED to avoid cascade failures"""
        if not route_id:
            return "No Route Assigned"
            
        try:
            # Cache route names to avoid repeated API calls
            if not hasattr(self, '_route_cache'):
                self._route_cache = {}
                
            if route_id in self._route_cache:
                return self._route_cache[route_id]
                
            # Get route info directly from routes API (avoid full route loading with coordinates/stops)
            import requests
            response = requests.get(f"{self.server_url}/api/v1/routes/public", timeout=10)
            
            if response.status_code == 200:
                api_routes = response.json()
                for route in api_routes:
                    if route.get('route_id') == route_id:
                        short_name = route.get('short_name', 'Unknown')
                        long_name = route.get('long_name', '')
                        
                        # Create user-friendly display name
                        if long_name and long_name != short_name:
                            display_name = f"Route {short_name} ({long_name})"
                        else:
                            display_name = f"Route {short_name}"
                        
                        self._route_cache[route_id] = display_name
                        return display_name
                        
            # Fallback to shortened UUID
            short_id = route_id[:8] if route_id else 'Unknown'
            fallback_name = f"Route {short_id}"
            self._route_cache[route_id] = fallback_name
            return fallback_name
            
        except Exception as e:
            logger.warning(f"Failed to get route name for {route_id}: {e}")
            return f"Route {route_id[:8]}" if route_id else "Unknown Route"
    
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
                
            # Get driver info from API
            import requests
            response = requests.get(f"{self.server_url}/api/v1/drivers/public", timeout=10)
            
            if response.status_code == 200:
                api_drivers = response.json()
                for driver in api_drivers:
                    if driver.get('driver_id') == driver_id:
                        driver_name = driver.get('name', 'Unknown Driver')
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
    
    # ==================== DATA RETRIEVAL METHODS ====================
    
    def get_all_fleet_data(self) -> Dict[str, Any]:
        """Get complete fleet operational data"""
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
    
    def get_routes(self) -> Dict[str, Dict[str, Any]]:
        """Get all routes with coordinates and metadata via API"""
        self._ensure_api_available()
        
        # Use cached data if available
        if self._routes_cache is not None:
            api_routes = self._routes_cache
        else:
            try:
                import requests
                
                # Use API with retry logic for temporary connection issues
                for attempt in range(3):
                    try:
                        response = requests.get(f"{self.server_url}/api/v1/routes/public", timeout=10)
                        response.raise_for_status()
                        api_routes = response.json()
                        self._routes_cache = api_routes  # Cache the result
                        break
                    except requests.exceptions.RequestException as e:
                        if attempt < 2:
                            logger.warning(f"Routes API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                            time.sleep(1)
                        else:
                            raise
            except Exception as e:
                logger.error(f"Failed to get routes: {e}")
                return {}
        
        try:
            
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
    
    def _load_route_coordinates_internal(self, route_identifier: str) -> List[Tuple[float, float]]:
        """Internal method to load route coordinates (used by caching)"""
        try:
            import requests
            
            # Step 1: Get route shapes metadata
            shapes_response = requests.get(
                f"{self.server_url}/api/v1/route_shapes?route_short_name={route_identifier}", 
                timeout=10
            )
            
            if shapes_response.status_code != 200:
                return []
            
            route_shapes = shapes_response.json()
            if not route_shapes:
                return []
            
            # Step 2: Get actual geometry for each shape - use concurrent requests
            import concurrent.futures
            all_coordinates = []
            
            def fetch_shape_geometry(shape_info):
                shape_id = shape_info.get('shape_id')
                if not shape_id:
                    return []
                
                try:
                    geometry_response = requests.get(
                        f"{self.server_url}/api/v1/shapes/{shape_id}", 
                        timeout=10
                    )
                    
                    if geometry_response.status_code == 200:
                        shape_data = geometry_response.json()
                        geom = shape_data.get('geom')
                        
                        if geom and geom.get('type') == 'LineString':
                            coordinates = geom.get('coordinates', [])
                            # Convert from [longitude, latitude] to (latitude, longitude) tuples
                            result = []
                            for coord_pair in coordinates:
                                if len(coord_pair) >= 2:
                                    longitude, latitude = coord_pair[0], coord_pair[1]
                                    result.append((float(latitude), float(longitude)))
                            return result
                except:
                    pass  # Silent error handling
                return []
            
            # Use ThreadPoolExecutor to fetch shapes concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_shape = {executor.submit(fetch_shape_geometry, shape_info): shape_info for shape_info in route_shapes}
                for future in concurrent.futures.as_completed(future_to_shape):
                    coordinates = future.result()
                    all_coordinates.extend(coordinates)
            
            # Cache the result and return
            result = all_coordinates if all_coordinates else []
            self._route_coordinates_cache[route_identifier] = result
            return result
                
        except Exception as e:
            # Silent error handling - cache empty result
            self._route_coordinates_cache[route_identifier] = []
            return []

    def get_route_coordinates(self, route_identifier: str) -> List[Tuple[float, float]]:
        """Get route coordinates via API with caching"""
        self._ensure_api_available()
        
        # Check cache first
        if route_identifier in self._route_coordinates_cache:
            return self._route_coordinates_cache[route_identifier]
        
        # Load and cache if not in cache
        return self._load_route_coordinates_internal(route_identifier)
    
    def _get_route_stops(self, route_id: str) -> List[Dict[str, Any]]:
        """Get stops for a specific route via API"""
        if not route_id:
            return []
            
        try:
            import requests
            
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
                    'name': stop_time.get('stop_name'),
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
    
    def get_drivers(self) -> List[Dict[str, Any]]:
        """Get all drivers via API - FIXED with retry logic"""
        try:
            import requests
            
            # Use retry logic to prevent race conditions
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.server_url}/api/v1/drivers/public", timeout=10)
                    response.raise_for_status()
                    api_drivers = response.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Drivers API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
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
        """Get all service definitions via API - FIXED with retry logic"""
        try:
            import requests
            
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.server_url}/api/v1/services", timeout=10)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Services API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
        except Exception as e:
            logger.warning(f"Services not available via API: {e}")
            return []
    
    def get_depots(self) -> List[Dict[str, Any]]:
        """Get all depot locations via API - FIXED with retry logic"""
        try:
            import requests
            
            # Use retry logic to prevent race conditions
            for attempt in range(3):
                try:
                    response = requests.get(f"{self.server_url}/api/v1/depots", timeout=10)
                    response.raise_for_status()
                    api_depots = response.json()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < 2:
                        logger.warning(f"Depots API request failed, retrying... (attempt {attempt + 1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
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