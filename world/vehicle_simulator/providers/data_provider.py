"""
Unified Data Provider
--------------------
Unified provider that uses fleet_manager API endpoints to get all fleet data:
routes, timetables, schedules, vehicles, drivers, services, etc.
Includes real-time Socket.IO monitoring of API availability.
Replaces the specific database_route_provider with a comprehensive solution.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time
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
        
        # Try initial connection
        self._initialize_fleet_manager()
        
        logger.info(f"Fleet data provider initialized with Socket.IO monitoring for {server_url}")

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
        """Initialize fleet manager connection when API is available"""
        if not self.api_monitor.is_api_available():
            logger.warning("Cannot initialize fleet manager - API not available")
            return
            
        try:
            # Import here to avoid circular dependencies
            from world.fleet_manager.manager import FleetManager
            self._fleet_manager = FleetManager()
            logger.info("✅ Fleet manager connection established")
        except ImportError as e:
            logger.error(f"Fleet manager not available: {e}")
            raise RuntimeError("FleetDataProvider requires fleet_manager to be available")
        except Exception as e:
            logger.error(f"Failed to initialize fleet manager: {e}")
            self._fleet_manager = None

    def _cleanup_fleet_manager(self):
        """Clean up fleet manager connection"""
        if self._fleet_manager:
            try:
                self._fleet_manager.close()
            except Exception as e:
                logger.warning(f"Error closing fleet manager: {e}")
            finally:
                self._fleet_manager = None
    
    def __del__(self):
        """Clean up connections"""
        if self.api_monitor:
            self.api_monitor.stop_monitoring()
        self._cleanup_fleet_manager()
    
    def is_api_available(self) -> bool:
        """Check if fleet manager API is currently available"""
        return self._api_available and self._fleet_manager is not None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API connection status"""
        return self.api_monitor.get_status().to_dict()
    
    def force_reconnect(self):
        """Force API reconnection attempt"""
        logger.info("Forcing API reconnection")
        self.api_monitor.force_reconnect()
    
    def _ensure_api_available(self):
        """Ensure API is available before making calls"""
        if not self.is_api_available():
            status = self.api_monitor.get_status()
            error_msg = f"Fleet Manager API not available: {status.error or 'Connection lost'}"
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
            from world.fleet_manager.models import Vehicle
            
            vehicles = []
            db_vehicles = self._fleet_manager.db.query(Vehicle).all()
            
            for vehicle in db_vehicles:
                vehicle_data = {
                    'id': vehicle.vehicle_id,
                    'license_plate': vehicle.reg_code,
                    'capacity': None,  # Vehicle model doesn't have capacity field
                    'fuel_type': None,  # Vehicle model doesn't have fuel_type field
                    'status': vehicle.status,
                    'depot_id': vehicle.home_depot_id,
                    'model': None,  # Vehicle model doesn't have model field
                    'year': None,  # Vehicle model doesn't have year field
                    'active': vehicle.status == 'active',
                    'current_assignment': self._get_vehicle_current_assignment(vehicle.vehicle_id)
                }
                vehicles.append(vehicle_data)
            
            return vehicles
            
        except Exception as e:
            logger.error(f"Failed to get vehicles: {e}")
            return []
    
    def _get_vehicle_current_assignment(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get current operational assignment for vehicle"""
        try:
            from world.fleet_manager.models import VehicleAssignment
            
            assignment = (
                self._fleet_manager.db.query(VehicleAssignment)
                .filter(VehicleAssignment.vehicle_id == vehicle_id)
                .filter(VehicleAssignment.assigned_at.cast(Date) == datetime.now().date())
                .first()
            )
            
            if assignment:
                return {
                    'route_id': assignment.route_id,
                    'driver_id': assignment.driver_id,
                    'block_id': assignment.block_id,
                    'start_time': assignment.start_time,
                    'end_time': assignment.end_time,
                    'service_id': assignment.service_id
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vehicle assignment for {vehicle_id}: {e}")
            return None
    
    # ==================== ROUTE DATA ====================
    
    def get_routes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all routes with coordinates and metadata.
        Replaces file_route_provider with database data.
        """
        try:
            from world.fleet_manager.models import Route
            routes = {}
            db_routes = self._fleet_manager.db.query(Route).all()
            
            for route in db_routes:
                route_data = {
                    'id': route.route_id,
                    'short_name': route.short_name,
                    'long_name': route.long_name,
                    'description': route.description,
                    'color': route.color,
                    'coordinates': self.get_route_coordinates(route.short_name),
                    'stops': self._get_route_stops(route.route_id)
                }
                routes[route.short_name] = route_data
            
            return routes
            
        except Exception as e:
            logger.error(f"Failed to get routes: {e}")
            return {}
    
    def get_route_coordinates(self, route_identifier: str) -> List[Tuple[float, float]]:
        """
        Get coordinates from database using fleet manager.
        Maintains compatibility with existing Navigator interface.
        """
        self._ensure_api_available()
        
        try:
            return self._fleet_manager.routes.get_route_coordinates(route_identifier)
        except Exception as e:
            logger.error(f"Failed to get route coordinates for {route_identifier}: {e}")
            raise ValueError(f"Route '{route_identifier}' not found in database")
    
    def _get_route_stops(self, route_id: str) -> List[Dict[str, Any]]:
        """Get stops for a specific route"""
        try:
            from world.fleet_manager.models import Stop, StopTime
            
            stops = []
            stop_times = (
                self._fleet_manager.db.query(StopTime)
                .join(Stop)
                .filter(StopTime.route_id == route_id)
                .order_by(StopTime.stop_sequence)
                .all()
            )
            
            for stop_time in stop_times:
                stop_data = {
                    'stop_id': stop_time.stop.stop_id,
                    'name': stop_time.stop.name,
                    'lat': float(stop_time.stop.lat),
                    'lon': float(stop_time.stop.lon),
                    'sequence': stop_time.stop_sequence,
                    'arrival_time': stop_time.arrival_time,
                    'departure_time': stop_time.departure_time
                }
                stops.append(stop_data)
            
            return stops
            
        except Exception as e:
            logger.error(f"Failed to get stops for route {route_id}: {e}")
            return []
    
    # ==================== SCHEDULE DATA ====================
    
    def get_timetables(self) -> List[Dict[str, Any]]:
        """Get all service timetables"""
        try:
            from world.fleet_manager.models import Timetable
            
            timetables = []
            db_timetables = self._fleet_manager.db.query(Timetable).all()
            
            for timetable in db_timetables:
                timetable_data = {
                    'id': timetable.timetable_id,
                    'service_id': timetable.service_id,
                    'route_id': timetable.route_id,
                    'direction': timetable.direction,
                    'start_time': timetable.start_time,
                    'end_time': timetable.end_time,
                    'frequency_minutes': timetable.frequency_minutes,
                    'active_days': timetable.active_days
                }
                timetables.append(timetable_data)
            
            return timetables
            
        except Exception as e:
            logger.error(f"Failed to get timetables: {e}")
            return []
    
    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get vehicle-specific schedules for today"""
        try:
            from world.fleet_manager.models import VehicleAssignment
            
            schedules = []
            today = datetime.now().date()
            
            assignments = (
                self._fleet_manager.db.query(VehicleAssignment)
                .filter(VehicleAssignment.assigned_at.cast(Date) == today)
                .all()
            )
            
            for assignment in assignments:
                schedule_data = {
                    'vehicle_id': assignment.vehicle_id,
                    'route_id': assignment.route_id,
                    'driver_id': assignment.driver_id,
                    'start_time': assignment.start_time,
                    'end_time': assignment.end_time,
                    'block_id': assignment.block_id,
                    'service_id': assignment.service_id
                }
                schedules.append(schedule_data)
            
            return schedules
            
        except Exception as e:
            logger.error(f"Failed to get schedules: {e}")
            return []
    
    # ==================== PERSONNEL DATA ====================
    
    def get_drivers(self) -> List[Dict[str, Any]]:
        """Get all drivers and their assignments"""
        try:
            from world.fleet_manager.models import Driver
            
            drivers = []
            db_drivers = self._fleet_manager.db.query(Driver).all()
            
            for driver in db_drivers:
                driver_data = {
                    'id': driver.driver_id,
                    'name': driver.name,
                    'license_number': driver.license_no,
                    'status': driver.employment_status,
                    'depot_id': driver.home_depot_id
                }
                drivers.append(driver_data)
            
            return drivers
            
        except Exception as e:
            logger.error(f"Failed to get drivers: {e}")
            return []
    
    # ==================== SERVICE DATA ====================
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get all service definitions"""
        try:
            from world.fleet_manager.models import Service
            
            services = []
            db_services = self._fleet_manager.db.query(Service).all()
            
            for service in db_services:
                service_data = {
                    'id': service.service_id,
                    'name': service.name,
                    'description': service.description,
                    'type': service.service_type,
                    'start_date': service.start_date,
                    'end_date': service.end_date
                }
                services.append(service_data)
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to get services: {e}")
            return []
    
    def get_depots(self) -> List[Dict[str, Any]]:
        """Get all depot locations"""
        try:
            from world.fleet_manager.models import Depot
            
            depots = []
            db_depots = self._fleet_manager.db.query(Depot).all()
            
            for depot in db_depots:
                depot_data = {
                    'id': depot.depot_id,
                    'name': depot.name,
                    'location': depot.location,
                    'capacity': depot.capacity,
                    'active': True  # All depots are considered active
                }
                depots.append(depot_data)
            
            return depots
            
        except Exception as e:
            logger.error(f"Failed to get depots: {e}")
            return []
    
    # ==================== OPERATIONAL QUERIES ====================
    
    def get_active_schedules_for_time(self, current_time: time) -> List[Dict[str, Any]]:
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
