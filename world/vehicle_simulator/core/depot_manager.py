import logging
from typing import Dict, Any, Optional, List
from .states import StateMachine, DepotState
from .interfaces import IDepotManager, IDispatcher, VehicleAssignment, DriverAssignment

class DepotManager(StateMachine, IDepotManager):
    def __init__(self, component_name: str = "DepotManager"):
        super().__init__(component_name, DepotState.CLOSED)
        self.dispatcher: Optional[IDispatcher] = None
        self.initialized = False
    
    def set_dispatcher(self, dispatcher: IDispatcher):
        self.dispatcher = dispatcher
    
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
        
        # Coordinate route distribution to drivers
        route_distribution = await self._coordinate_route_distribution()
        if not route_distribution:
            logging.warning(f"[{self.component_name}] Route distribution failed - continuing with limited operation")
        
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
    
    async def shutdown(self) -> bool:
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