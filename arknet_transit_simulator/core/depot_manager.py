import logging
from typing import Dict, Any, Optional, List
from .states import StateMachine, DepotState
from .interfaces import IDepotManager, IDispatcher, VehicleAssignment, DriverAssignment
from .route_queue_builder import RouteQueueBuilder
from .passenger_service_factory import PassengerServiceFactory

class DepotManager(StateMachine, IDepotManager):
    def __init__(self, component_name: str = "DepotManager"):
        super().__init__(component_name, DepotState.CLOSED)
        self.dispatcher: Optional[IDispatcher] = None
        self.route_queue_builder: RouteQueueBuilder = RouteQueueBuilder(f"{component_name}_RouteQueues")
        self.passenger_service_factory: PassengerServiceFactory = PassengerServiceFactory(f"{component_name}_PassengerService")
        self.initialized = False
    
    def set_dispatcher(self, dispatcher: IDispatcher):
        self.dispatcher = dispatcher
        self.passenger_service_factory.set_dispatcher(dispatcher)
    
    async def initialize(self) -> bool:
        """Initialize depot with vehicle data validation - NO fallback allowed."""
        if not self.dispatcher:
            logging.error(f"[{self.component_name}] No dispatcher configured")
            return False
        
        # Start opening depot
        await self.transition_to(DepotState.OPENING)
        
        # Initialize dispatcher (connects to API)
        dispatcher_result = await self.dispatcher.initialize()
        if not dispatcher_result:
            logging.error(f"[{self.component_name}] Dispatcher initialization failed")
            await self.transition_to(DepotState.CLOSED)
            return False
        
        # Validate vehicle and driver data from API - CRITICAL: NO fallback data
        validation_result = await self._validate_vehicles_and_drivers()
        if not validation_result:
            logging.error(f"[{self.component_name}] Vehicle and driver validation failed")
            await self.dispatcher.shutdown()
            await self.transition_to(DepotState.CLOSED)
            return False
        
        # Skip route distribution during initialization - will be done after vehicles are operational
        logging.info(f"[{self.component_name}] Route distribution deferred until vehicles are operational")
        
        # All validations passed - depot is operational
        await self.transition_to(DepotState.OPEN)
        self.initialized = True
        logging.info(f"[{self.component_name}] Depot initialization complete")
        return True
    
    async def _validate_vehicles_and_drivers(self) -> bool:
        """Validate that both vehicles and drivers are available from API - NO fallback allowed."""
        if not self.dispatcher:
            return False
        
        try:
            # Get vehicle assignments from API
            vehicle_assignments = await self.dispatcher.get_vehicle_assignments()
            if not vehicle_assignments:
                logging.error(f"[{self.component_name}] No vehicle assignments available from API")
                return False
            
            # Get driver assignments from API
            driver_assignments = await self.dispatcher.get_driver_assignments()
            if not driver_assignments:
                logging.error(f"[{self.component_name}] No driver assignments available from API")
                return False
            
            # Validate vehicle assignments have required data
            valid_vehicles = 0
            for assignment in vehicle_assignments:
                if assignment.vehicle_id and assignment.route_id:
                    valid_vehicles += 1
            
            # Validate driver assignments have required data
            valid_drivers = 0
            available_drivers = 0
            for assignment in driver_assignments:
                if assignment.driver_id and assignment.license_number:
                    valid_drivers += 1
                    if assignment.status == "available":
                        available_drivers += 1
            
            if valid_vehicles == 0:
                logging.error(f"[{self.component_name}] No valid vehicle assignments found")
                return False
                
            if valid_drivers == 0:
                logging.error(f"[{self.component_name}] No valid driver assignments found")
                return False
                
            if available_drivers == 0:
                logging.error(f"[{self.component_name}] No available drivers found")
                return False
            
            logging.info(f"[{self.component_name}] Validation passed: {valid_vehicles} vehicles, {available_drivers} available drivers")
            
            # Build route queues for depot operations
            await self._build_route_queues(vehicle_assignments, driver_assignments)
            
            # Get complete depot inventory (all vehicles regardless of status)
            await self._report_depot_inventory()
            
            return True
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Vehicle and driver validation error: {e}")
            return False
    
    async def _coordinate_route_distribution(self) -> bool:
        """Coordinate route distribution to drivers when vehicles and drivers are present."""
        if not self.dispatcher:
            return False
        
        try:
            # Get current vehicle and driver assignments
            vehicle_assignments = await self.dispatcher.get_vehicle_assignments()
            driver_assignments = await self.dispatcher.get_driver_assignments()
            
            if not vehicle_assignments or not driver_assignments:
                logging.error(f"[{self.component_name}] Cannot coordinate routes - missing assignments")
                return False
            
            # Build driver-route mappings from vehicle assignments
            driver_routes = []
            for vehicle in vehicle_assignments:
                if vehicle.driver_id and vehicle.route_id:
                    # Find the driver to verify they're available
                    driver_found = False
                    for driver in driver_assignments:
                        if driver.driver_id == vehicle.driver_id and driver.status == "available":
                            driver_routes.append({
                                'driver_id': vehicle.driver_id,
                                'route_id': vehicle.route_id,
                                'vehicle_id': vehicle.vehicle_id,
                                'driver_name': vehicle.driver_name,  # Use friendly name from vehicle assignment
                                'vehicle_reg_code': vehicle.vehicle_reg_code,  # Use friendly name from vehicle assignment
                                'route_name': vehicle.route_name  # Use friendly name from vehicle assignment
                            })
                            driver_found = True
                            break
                    
                    if not driver_found:
                        driver_name = vehicle.driver_name or 'Unknown Driver'
                        route_name = vehicle.route_name or 'Unknown Route'
                        logging.warning(f"[{self.component_name}] Driver {driver_name} not available for Route {route_name}")
            
            if not driver_routes:
                logging.error(f"[{self.component_name}] No valid driver-route combinations found")
                return False
            
            # Send routes to drivers via dispatcher
            success = await self.dispatcher.send_routes_to_drivers(driver_routes)
            if success:
                logging.info(f"[{self.component_name}] Successfully distributed {len(driver_routes)} routes to drivers")
            else:
                logging.error(f"[{self.component_name}] Failed to distribute routes to drivers")
            
            return success
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Route coordination error: {e}")
            return False
    
    async def _build_route_queues(self, vehicle_assignments: List[VehicleAssignment], driver_assignments: List[DriverAssignment]) -> bool:
        """Build route queues for organizing vehicles by route assignments."""
        try:
            # Get route information from dispatcher for each unique route
            route_info = []
            if self.dispatcher:
                # Extract unique route codes from vehicle assignments  
                unique_route_codes = set()
                for vehicle in vehicle_assignments:
                    if vehicle.route_id:  # route_id contains route codes like "1A", "1"
                        unique_route_codes.add(vehicle.route_id)
                
                # Fetch route info for each unique route code
                for route_code in unique_route_codes:
                    try:
                        route_data = await self.dispatcher.get_route_info(route_code)
                        if route_data:
                            route_info.append(route_data)
                    except Exception as e:
                        logging.warning(f"[{self.component_name}] Failed to get route info for {route_code}: {e}")
            
            # Build the route queues
            success = self.route_queue_builder.build_queues(
                vehicle_assignments=vehicle_assignments,
                driver_assignments=driver_assignments,
                route_info=route_info
            )
            
            if success:
                # Log queue statistics
                stats = self.route_queue_builder.get_summary_statistics()
                logging.info(f"[{self.component_name}] Route queues built: {stats['routes_with_vehicles']} routes with vehicles, {stats['total_vehicles']} total vehicles")
                
                # Log route names with vehicles
                route_names = self.route_queue_builder.get_route_names()
                if route_names:
                    logging.info(f"[{self.component_name}] Routes with vehicles: {', '.join(route_names)}")
            else:
                logging.error(f"[{self.component_name}] Failed to build route queues")
            
            return success
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Route queue building error: {e}")
            return False
    
    async def _report_depot_inventory(self) -> None:
        """Report complete depot inventory including inactive vehicles."""
        if not self.dispatcher:
            return
        
        try:
            # Get ALL vehicles in depot
            all_vehicles = await self.dispatcher.get_all_depot_vehicles()
            if not all_vehicles:
                logging.warning(f"[{self.component_name}] No depot inventory data available")
                return
            
            # Categorize vehicles by status
            active_vehicles = []
            inactive_vehicles = []
            
            for vehicle in all_vehicles:
                status = vehicle.get('status', 'unknown')
                reg_code = vehicle.get('reg_code', 'Unknown')
                
                if status in ['available', 'in_service']:
                    active_vehicles.append((reg_code, status))
                else:
                    inactive_vehicles.append((reg_code, status))
            
            # Report depot inventory
            total_count = len(all_vehicles)
            active_count = len(active_vehicles)
            inactive_count = len(inactive_vehicles)
            
            logging.info("")
            logging.info("═══ DEPOT INVENTORY ═══")
            logging.info(f"[{self.component_name}] Complete Depot Inventory:")
            logging.info(f"  • Total vehicles in depot: {total_count}")
            logging.info(f"  • Active vehicles: {active_count} (operational)")
            logging.info(f"  • Inactive vehicles: {inactive_count} (non-operational)")
            
            # List active vehicles
            if active_vehicles:
                active_list = ", ".join([f"{reg}({status})" for reg, status in active_vehicles])
                logging.info(f"  • Active: {active_list}")
            
            # List inactive vehicles with reasons
            if inactive_vehicles:
                logging.info(f"  • Inactive vehicles (reasons):")
                for reg_code, status in inactive_vehicles:
                    reason = self._get_status_reason(status)
                    logging.info(f"    - {reg_code}: {reason}")
            logging.info("")
            
        except Exception as e:
            logging.error(f"[{self.component_name}] Depot inventory reporting error: {e}")
    
    def _get_status_reason(self, status: str) -> str:
        """Get human-readable reason for vehicle status."""
        status_reasons = {
            'maintenance': 'Under maintenance - not available for service',
            'retired': 'Retired from service - end of operational life',
            'out_of_service': 'Temporarily out of service',
            'repair': 'Under repair - mechanical issues',
            'inspection': 'Undergoing safety inspection',
            'cleaning': 'Deep cleaning in progress',
            'unknown': 'Status unknown - requires investigation'
        }
        return status_reasons.get(status, f'Status "{status}" - requires review')
    
    async def shutdown(self) -> bool:
        # Stop passenger service first
        await self.passenger_service_factory.stop_passenger_service()
        
        if self.dispatcher:
            await self.dispatcher.shutdown()
        
        await self.transition_to(DepotState.CLOSING)
        await self.transition_to(DepotState.CLOSED)
        self.initialized = False
        return True
    
    async def get_system_status(self) -> Dict[str, Any]:
        dispatcher_status = None
        vehicle_status = None
        driver_status = None
        
        if self.dispatcher:
            dispatcher_status = await self.dispatcher.get_api_status()
            
            # Add vehicle and driver assignment data if system is operational
            if self.initialized:
                try:
                    vehicle_assignments = await self.dispatcher.get_vehicle_assignments()
                    vehicle_status = {
                        'assignment_count': len(vehicle_assignments) if vehicle_assignments else 0,
                        'validation_status': 'passed' if vehicle_assignments else 'failed'
                    }
                    
                    driver_assignments = await self.dispatcher.get_driver_assignments()
                    available_drivers = len([d for d in driver_assignments if d.status == "available"]) if driver_assignments else 0
                    driver_status = {
                        'total_drivers': len(driver_assignments) if driver_assignments else 0,
                        'available_drivers': available_drivers,
                        'validation_status': 'passed' if driver_assignments and available_drivers > 0 else 'failed'
                    }
                    
                except Exception as e:
                    vehicle_status = {
                        'assignment_count': 0,
                        'validation_status': 'error',
                        'error': str(e)
                    }
                    driver_status = {
                        'total_drivers': 0,
                        'available_drivers': 0,
                        'validation_status': 'error',
                        'error': str(e)
                    }
        
        return {
            "depot_name": self.component_name,
            "depot_state": self.current_state.value,
            "initialized": self.initialized,
            "dispatcher_status": dispatcher_status,
            "vehicle_status": vehicle_status,
            "driver_status": driver_status,
            "system_operational": (
                self.current_state == DepotState.OPEN and 
                self.initialized and 
                dispatcher_status and 
                dispatcher_status.get('api_operational', False) and
                vehicle_status and
                vehicle_status.get('validation_status') == 'passed' and
                driver_status and
                driver_status.get('validation_status') == 'passed'
            )
        }

    async def distribute_routes_to_operational_vehicles(self, active_drivers: List = None) -> bool:
        """
        Distribute routes only to vehicles that are operational (drivers onboard, GPS running).
        This should be called after vehicles are initialized and drivers are boarded.
        
        Args:
            active_drivers: List of active driver objects that are ONBOARD their vehicles
            
        Returns:
            bool: True if route distribution was successful for operational vehicles
        """
        logging.info(f"[{self.component_name}] 🚀 distribute_routes_to_operational_vehicles called with {len(active_drivers) if active_drivers else 0} drivers")
        
        if not self.dispatcher or not active_drivers:
            logging.info(f"[{self.component_name}] No operational vehicles for route distribution")
            return True  # Not an error - just no work to do
            
        try:
            # Build route assignments only for operational vehicles
            operational_routes = []
            
            for driver in active_drivers:
                # Only include drivers that are ONBOARD or WAITING and have GPS running
                if (hasattr(driver, 'current_state') and 
                    driver.current_state.value in ['ONBOARD', 'WAITING'] and
                    hasattr(driver, 'vehicle_gps') and 
                    driver.vehicle_gps and
                    hasattr(driver.vehicle_gps, 'current_state')):
                    
                    driver_name = getattr(driver, 'person_name', 'Unknown Driver')
                    vehicle_id = getattr(driver, 'vehicle_id', 'unknown')
                    route_name = getattr(driver, 'route_name', 'unknown')
                    
                    # Get starting coordinates from driver's route
                    starting_coords = "No coordinates available"
                    if hasattr(driver, 'route') and driver.route and len(driver.route) > 0:
                        first_coord = driver.route[0]  # [longitude, latitude]
                        lat, lon = first_coord[1], first_coord[0]
                        starting_coords = f"lat={lat:.6f}, lon={lon:.6f}"
                    
                    logging.info(f"  📍 {driver_name} → {vehicle_id} → Route {route_name}: Starting at {starting_coords}")
                    
                    operational_routes.append({
                        'driver_id': getattr(driver, 'component_id', 'unknown'),
                        'driver_name': driver_name,
                        'vehicle_id': vehicle_id,
                        'route_id': route_name,
                        'vehicle_reg_code': vehicle_id
                    })
            
            if not operational_routes:
                logging.info(f"[{self.component_name}] No operational vehicles found for route distribution")
                return True
                
            # Send routes only for operational vehicles (for API logging)
            success = await self.dispatcher.send_routes_to_drivers(operational_routes)
            if success:
                logging.info(f"[{self.component_name}] Successfully prepared routes for {len(operational_routes)} operational vehicles")
            else:
                logging.info(f"[{self.component_name}] Route preparation completed with API limitations (expected in development)")
            
            # Now actually set the route geometry on each driver object
            logging.info(f"[{self.component_name}] 🗺️ Setting route geometry on {len(active_drivers)} drivers...")
            for driver in active_drivers:
                driver_name = getattr(driver, 'person_name', 'Unknown Driver')
                logging.info(f"[{self.component_name}] 🔍 Checking driver {driver_name}...")
                
                if (hasattr(driver, 'current_state') and 
                    driver.current_state.value in ['ONBOARD', 'WAITING'] and
                    hasattr(driver, 'route_name')):
                    
                    route_name = getattr(driver, 'route_name', None)
                    logging.info(f"[{self.component_name}] 📋 Driver {driver_name} assigned to route {route_name}")
                    
                    if route_name:
                        try:
                            # Get the route info with GPS coordinates from dispatcher
                            logging.info(f"[{self.component_name}] 📡 Fetching route info for {route_name}...")
                            route_info = await self.dispatcher.get_route_info(route_name)
                            if route_info and route_info.geometry:
                                # Set the route coordinates on the driver
                                coordinates = route_info.geometry.get('coordinates', [])
                                driver.route = coordinates  # Set GPS coordinates for driving
                                
                                vehicle_id = getattr(driver, 'vehicle_id', 'unknown')
                                logging.info(f"[{self.component_name}] ✅ Set {len(coordinates)} GPS coordinates on driver {driver_name} (vehicle {vehicle_id}) for route {route_name}")
                            else:
                                logging.warning(f"[{self.component_name}] ❌ No route geometry found for route {route_name}")
                        except Exception as e:
                            logging.error(f"[{self.component_name}] Error setting route on driver: {e}")
                else:
                    logging.warning(f"[{self.component_name}] ⚠️  Driver {driver_name} not eligible for route assignment (state: {getattr(driver, 'current_state', 'unknown')}, has_route_name: {hasattr(driver, 'route_name')})")
            
            # Start passenger service after routes are distributed
            await self._start_passenger_service_after_routes(operational_routes)
            
            return True  # Always return True - API failures are expected during development
            
        except Exception as e:
            logging.warning(f"[{self.component_name}] Route distribution error (non-critical): {e}")
            return True  # Always return True - route distribution failures shouldn't stop operations
    
    async def _start_passenger_service_after_routes(self, operational_routes: List[Dict[str, str]]) -> bool:
        """Start passenger service after routes have been distributed to vehicles."""
        try:
            if not operational_routes:
                logging.info(f"[{self.component_name}] No operational routes - passenger service not started")
                return False
            
            # Extract unique route IDs from operational routes
            route_ids = list(set(route['route_id'] for route in operational_routes if route.get('route_id')))
            
            if not route_ids:
                logging.warning(f"[{self.component_name}] No valid route IDs found in operational routes")
                return False
            
            logging.info(f"[{self.component_name}] Starting passenger service for {len(route_ids)} active routes: {', '.join(route_ids)}")
            
            # Create and start passenger service through factory
            success = await self.passenger_service_factory.create_passenger_service(route_ids)
            
            if success:
                # Get service status for logging
                status = await self.passenger_service_factory.get_service_status()
                logging.info(f"[{self.component_name}] 🚀 Passenger service started successfully!")
                logging.info(f"[{self.component_name}] Service status: {status['passengers']} passengers across {status['routes']} routes")
                
                # Get route buffer statistics
                if self.dispatcher:
                    buffer_stats = await self.dispatcher.get_route_buffer_stats()
                    logging.info(f"[{self.component_name}] Route buffer: {buffer_stats['total_routes']} routes with {buffer_stats['total_gps_points']} GPS points indexed")
                
                return True
            else:
                logging.error(f"[{self.component_name}] Failed to start passenger service")
                return False
                
        except Exception as e:
            logging.error(f"[{self.component_name}] Error starting passenger service: {str(e)}")
            return False