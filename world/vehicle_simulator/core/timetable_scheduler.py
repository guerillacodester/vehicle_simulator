"""
Timetable Scheduler
------------------
Real-time scheduler that manages fleet operations based on timetables and schedules.
Monitors time and dispatches vehicles according to their scheduled service times.
Replaces manual vehicle startup with automated, schedule-driven operations.
"""

import logging
import threading
import time as time_module
import random
from datetime import datetime, time, timedelta
from typing import Dict, List, Callable, Any, Optional
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class CapacityBasedOperation:
    """Represents a capacity-based vehicle operation (ZR van style)"""
    
    def __init__(self, vehicle_id: str, operation: str, capacity_threshold: int,
                 route_id: str = None, driver_id: str = None, **kwargs):
        self.vehicle_id = vehicle_id
        self.operation = operation  # 'start_service', 'end_service', 'change_route'
        self.capacity_threshold = capacity_threshold  # Number of passengers to trigger departure
        self.current_passengers = 0
        self.route_id = route_id
        self.driver_id = driver_id
        self.params = kwargs
        self.executed = False
        self.boarding_start_time = None
        self.max_wait_time = kwargs.get('max_wait_time', 1800)  # 30 minutes max wait
    
    def add_passenger(self, passenger_count: int = 1):
        """Add passengers to the vehicle"""
        self.current_passengers += passenger_count
        if self.boarding_start_time is None:
            self.boarding_start_time = datetime.now()
    
    def is_ready_to_depart(self) -> bool:
        """Check if vehicle is ready to depart based on capacity or max wait time"""
        # Depart when full
        if self.current_passengers >= self.capacity_threshold:
            return True
        
        # Depart after max wait time even if not full
        if (self.boarding_start_time and 
            (datetime.now() - self.boarding_start_time).total_seconds() >= self.max_wait_time):
            return True
            
        return False
    
    def get_departure_reason(self) -> str:
        """Get reason for departure"""
        if self.current_passengers >= self.capacity_threshold:
            return f"FULL ({self.current_passengers}/{self.capacity_threshold} passengers)"
        else:
            return f"MAX_WAIT_TIME ({self.current_passengers}/{self.capacity_threshold} passengers)"
    
    def __str__(self):
        return f"CapacityBasedOperation({self.vehicle_id}, {self.current_passengers}/{self.capacity_threshold}, {self.operation})"


class ScheduledOperation:
    """Represents a scheduled vehicle operation"""
    
    def __init__(self, vehicle_id: str, operation: str, scheduled_time: time, 
                 route_id: str = None, driver_id: str = None, **kwargs):
        self.vehicle_id = vehicle_id
        self.operation = operation  # 'start_service', 'end_service', 'change_route'
        self.scheduled_time = scheduled_time
        self.route_id = route_id
        self.driver_id = driver_id
        self.params = kwargs
        self.executed = False
    
    def __str__(self):
        return f"ScheduledOperation({self.vehicle_id}, {self.operation}, {self.scheduled_time})"


class TimetableScheduler:
    """
    Real-time scheduler for fleet operations supporting both time-based and capacity-based scheduling.
    - Time-based: Traditional fixed schedule departures
    - Capacity-based: ZR van style - depart when full or after max wait time
    """
    
    def __init__(self, data_provider, precision_seconds: int = 30, 
                 default_mode: str = 'capacity', default_capacity: int = 11):
        self.data_provider = data_provider
        self.precision_seconds = precision_seconds
        self.default_mode = default_mode  # 'capacity' or 'time'
        self.default_capacity = default_capacity  # Default ZR van capacity
        
        # Operation queues
        self.operations_queue = Queue()
        self.scheduled_operations: List[ScheduledOperation] = []
        self.capacity_operations: List[CapacityBasedOperation] = []
        
        self.vehicle_handlers: Dict[str, Any] = {}  # vehicle_id -> vehicle handler
        self.running = False
        self.scheduler_thread = None
        
        # Passenger simulation for capacity-based operations
        self.passenger_simulation_enabled = True
        self.passenger_arrival_rate = 0.3  # Passengers per second
        
        # Callbacks for vehicle operations
        self.operation_callbacks: Dict[str, Callable] = {}
        
        logger.info(f"Timetable scheduler initialized with {precision_seconds}s precision")
    
    def register_vehicle_handler(self, vehicle_id: str, handler: Any):
        """Register a vehicle handler for operations"""
        self.vehicle_handlers[vehicle_id] = handler
        logger.debug(f"Registered handler for vehicle {vehicle_id}")
    
    def register_operation_callback(self, operation: str, callback: Callable):
        """Register callback for specific operation type"""
        self.operation_callbacks[operation] = callback
        logger.debug(f"Registered callback for operation: {operation}")
    
    def load_today_schedule(self, force_mode: str = None):
        """
        Load today's schedule from database and create operations based on mode.
        
        Args:
            force_mode: Override default mode ('time' or 'capacity')
        """
        try:
            mode = force_mode or self.default_mode
            logger.info(f"Loading today's vehicle schedules in {mode} mode...")
            
            schedules = self.data_provider.get_schedules()
            routes = self.data_provider.get_routes()
            vehicles = self.data_provider.get_vehicles()
            
            if mode == 'capacity':
                self._load_capacity_based_operations(schedules, routes, vehicles)
            else:
                self._load_time_based_operations(schedules, routes)
                
        except Exception as e:
            logger.error(f"Failed to load schedule: {e}")
            raise
    
    def _load_time_based_operations(self, schedules, routes):
        """Load traditional time-based scheduled operations"""
        for schedule in schedules:
            vehicle_id = schedule['vehicle_id']
            route_id = schedule['route_id']
            start_time = schedule['start_time']
            end_time = schedule['end_time']
            driver_id = schedule.get('driver_id')
            
            # Create start service operation
            start_op = ScheduledOperation(
                vehicle_id=vehicle_id,
                operation='start_service',
                scheduled_time=start_time,
                route_id=route_id,
                driver_id=driver_id,
                route_data=routes.get(route_id)
            )
            self.scheduled_operations.append(start_op)
            
            # Create end service operation
            end_op = ScheduledOperation(
                vehicle_id=vehicle_id,
                operation='end_service',
                scheduled_time=end_time,
                route_id=route_id,
                driver_id=driver_id
            )
            self.scheduled_operations.append(end_op)
        
        # Sort operations by time
        self.scheduled_operations.sort(key=lambda op: op.scheduled_time)
        
        logger.info(f"Loaded {len(self.scheduled_operations)} time-based scheduled operations")
        
        # Log upcoming operations
        for op in self.scheduled_operations[:5]:  # Show first 5
            logger.info(f"Scheduled: {op}")
    
    def _load_capacity_based_operations(self, schedules, routes, vehicles):
        """Load ZR van style capacity-based operations"""
        for schedule in schedules:
            vehicle_id = schedule['vehicle_id']
            route_id = schedule['route_id']
            driver_id = schedule.get('driver_id')
            
            # Get vehicle capacity
            vehicle_info = vehicles.get(vehicle_id, {})
            capacity = vehicle_info.get('capacity', self.default_capacity)
            
            # Create capacity-based start operation
            capacity_op = CapacityBasedOperation(
                vehicle_id=vehicle_id,
                operation='start_service',
                capacity_threshold=capacity,
                route_id=route_id,
                driver_id=driver_id,
                route_data=routes.get(route_id),
                max_wait_time=schedule.get('max_wait_time', 1800)  # 30 min default
            )
            self.capacity_operations.append(capacity_op)
        
        logger.info(f"Loaded {len(self.capacity_operations)} capacity-based operations")
        
        # Log capacity operations
        for op in self.capacity_operations:
            logger.info(f"Capacity Operation: {op}")
    
    def simulate_passenger_arrival(self, vehicle_id: str, passenger_count: int = None):
        """Simulate passengers arriving for a specific vehicle"""
        if not self.passenger_simulation_enabled:
            return
        
        # Find the capacity operation for this vehicle
        for op in self.capacity_operations:
            if op.vehicle_id == vehicle_id and not op.executed:
                if passenger_count is None:
                    # Random passenger arrival (1-3 passengers)
                    passenger_count = random.randint(1, 3)
                
                op.add_passenger(passenger_count)
                logger.info(f"🚶 {passenger_count} passengers boarded {vehicle_id} "
                          f"({op.current_passengers}/{op.capacity_threshold})")
                
                # Check if ready to depart
                if op.is_ready_to_depart():
                    logger.info(f"🚐 Vehicle {vehicle_id} ready to depart: {op.get_departure_reason()}")
                    self._execute_capacity_operation(op)
                break
    
    def _execute_capacity_operation(self, operation: CapacityBasedOperation):
        """Execute a capacity-based operation"""
        try:
            operation.executed = True
            self._execute_operation_common(operation)
            logger.info(f"Executed capacity operation: {operation}")
        except Exception as e:
            logger.error(f"Failed to execute capacity operation: {e}")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Timetable scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Timetable scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - monitors both time-based and capacity-based operations"""
        logger.info(f"Scheduler monitoring loop started in {self.default_mode} mode")
        
        while self.running:
            try:
                current_time = datetime.now().time()
                
                # Handle time-based operations
                due_operations = self._get_due_operations(current_time)
                for operation in due_operations:
                    try:
                        self._execute_operation(operation)
                        operation.executed = True
                        logger.info(f"Executed: {operation}")
                    except Exception as e:
                        logger.error(f"Failed to execute operation {operation}: {e}")
                
                # Handle capacity-based operations (simulate passenger arrivals)
                if self.default_mode == 'capacity':
                    self._simulate_passenger_arrivals()
                
                # Check capacity operations for max wait time expiry
                self._check_capacity_timeouts()
                
                # Sleep for precision interval
                time_module.sleep(self.precision_seconds)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time_module.sleep(5)  # Longer sleep on error
    
    def _get_due_operations(self, current_time: time) -> List[ScheduledOperation]:
        """Get operations that are due for execution"""
        due_operations = []
        
        for operation in self.scheduled_operations:
            if operation.executed:
                continue
            
            # Check if operation time has passed (within precision window)
            if self._is_time_due(operation.scheduled_time, current_time):
                due_operations.append(operation)
        
        return due_operations
    
    def _is_time_due(self, scheduled_time: time, current_time: time) -> bool:
        """Check if scheduled time is due (within precision window)"""
        # Convert times to seconds for comparison
        scheduled_seconds = scheduled_time.hour * 3600 + scheduled_time.minute * 60 + scheduled_time.second
        current_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        
        # Account for precision window
        time_diff = current_seconds - scheduled_seconds
        
        # Operation is due if current time is at or past scheduled time (within precision)
        return 0 <= time_diff <= self.precision_seconds
    
    def _execute_operation(self, operation: ScheduledOperation):
        """Execute a scheduled operation"""
        vehicle_id = operation.vehicle_id
        operation_type = operation.operation
        
        # Get vehicle handler
        vehicle_handler = self.vehicle_handlers.get(vehicle_id)
        if not vehicle_handler:
            logger.warning(f"No handler registered for vehicle {vehicle_id}")
            return
        
        # Execute based on operation type
        if operation_type == 'start_service':
            self._start_vehicle_service(vehicle_handler, operation)
        elif operation_type == 'end_service':
            self._end_vehicle_service(vehicle_handler, operation)
        elif operation_type == 'change_route':
            self._change_vehicle_route(vehicle_handler, operation)
        else:
            logger.warning(f"Unknown operation type: {operation_type}")
    
    def _start_vehicle_service(self, vehicle_handler: Any, operation: ScheduledOperation):
        """Start vehicle service - turn on systems and assign route"""
        try:
            logger.info(f"Starting service for vehicle {operation.vehicle_id} on route {operation.route_id}")
            
            # Turn on vehicle systems
            if hasattr(vehicle_handler, '_engine'):
                vehicle_handler._engine.on()
                logger.debug(f"Engine started for {operation.vehicle_id}")
            
            if hasattr(vehicle_handler, '_gps'):
                vehicle_handler._gps.on()
                logger.debug(f"GPS started for {operation.vehicle_id}")
            
            # Assign route to navigator
            if hasattr(vehicle_handler, '_navigator') and operation.route_id:
                route_data = operation.params.get('route_data')
                if route_data and 'coordinates' in route_data:
                    # Set route coordinates
                    vehicle_handler._navigator.route = route_data['coordinates']
                    vehicle_handler._navigator.on()
                    logger.debug(f"Navigator started for {operation.vehicle_id} with route {operation.route_id}")
                else:
                    logger.warning(f"No route coordinates available for {operation.route_id}")
            
            # Execute custom callback if registered
            if 'start_service' in self.operation_callbacks:
                self.operation_callbacks['start_service'](vehicle_handler, operation)
            
            logger.info(f"✅ Vehicle {operation.vehicle_id} service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start service for vehicle {operation.vehicle_id}: {e}")
            raise
    
    def _end_vehicle_service(self, vehicle_handler: Any, operation: ScheduledOperation):
        """End vehicle service - turn off systems"""
        try:
            logger.info(f"Ending service for vehicle {operation.vehicle_id}")
            
            # Turn off vehicle systems
            if hasattr(vehicle_handler, '_navigator'):
                vehicle_handler._navigator.off()
                logger.debug(f"Navigator stopped for {operation.vehicle_id}")
            
            if hasattr(vehicle_handler, '_engine'):
                vehicle_handler._engine.off()
                logger.debug(f"Engine stopped for {operation.vehicle_id}")
            
            if hasattr(vehicle_handler, '_gps'):
                vehicle_handler._gps.off()
                logger.debug(f"GPS stopped for {operation.vehicle_id}")
            
            # Execute custom callback if registered
            if 'end_service' in self.operation_callbacks:
                self.operation_callbacks['end_service'](vehicle_handler, operation)
            
            logger.info(f"✅ Vehicle {operation.vehicle_id} service ended successfully")
            
        except Exception as e:
            logger.error(f"Failed to end service for vehicle {operation.vehicle_id}: {e}")
            raise
    
    def _change_vehicle_route(self, vehicle_handler: Any, operation: ScheduledOperation):
        """Change vehicle route during service"""
        try:
            logger.info(f"Changing route for vehicle {operation.vehicle_id} to {operation.route_id}")
            
            if hasattr(vehicle_handler, '_navigator') and operation.route_id:
                route_data = operation.params.get('route_data')
                if route_data and 'coordinates' in route_data:
                    vehicle_handler._navigator.route = route_data['coordinates']
                    logger.debug(f"Route changed for {operation.vehicle_id}")
                else:
                    logger.warning(f"No route coordinates available for {operation.route_id}")
            
            # Execute custom callback if registered
            if 'change_route' in self.operation_callbacks:
                self.operation_callbacks['change_route'](vehicle_handler, operation)
            
            logger.info(f"✅ Vehicle {operation.vehicle_id} route changed successfully")
            
        except Exception as e:
            logger.error(f"Failed to change route for vehicle {operation.vehicle_id}: {e}")
            raise
    
    def get_active_vehicles(self) -> List[str]:
        """Get list of vehicles that should currently be in service"""
        current_time = datetime.now().time()
        active_vehicles = set()
        
        for operation in self.scheduled_operations:
            if (operation.operation == 'start_service' and 
                operation.executed and 
                operation.scheduled_time <= current_time):
                active_vehicles.add(operation.vehicle_id)
            elif (operation.operation == 'end_service' and 
                  operation.executed and 
                  operation.scheduled_time <= current_time):
                active_vehicles.discard(operation.vehicle_id)
        
        return list(active_vehicles)
    
    def get_next_operations(self, limit: int = 10) -> List[ScheduledOperation]:
        """Get next upcoming operations"""
        current_time = datetime.now().time()
        upcoming = [op for op in self.scheduled_operations 
                   if not op.executed and op.scheduled_time >= current_time]
        return upcoming[:limit]
    
    def _simulate_passenger_arrivals(self):
        """Simulate passengers arriving at depot for capacity-based operations"""
        for op in self.capacity_operations:
            if not op.executed and op.boarding_start_time is None:
                # Start boarding for vehicles that haven't started yet
                if random.random() < 0.1:  # 10% chance per tick to start boarding
                    op.boarding_start_time = datetime.now()
                    logger.info(f"🚶 Passengers started boarding vehicle {op.vehicle_id}")
            
            elif not op.executed and op.boarding_start_time:
                # Continue boarding for vehicles already boarding
                if random.random() < self.passenger_arrival_rate:
                    passenger_count = random.randint(1, 2)
                    op.add_passenger(passenger_count)
                    logger.info(f"🚶 {passenger_count} passengers boarded {op.vehicle_id} "
                              f"({op.current_passengers}/{op.capacity_threshold})")
                    
                    # Check if ready to depart
                    if op.is_ready_to_depart():
                        logger.info(f"🚐 Vehicle {op.vehicle_id} ready to depart: {op.get_departure_reason()}")
                        self._execute_capacity_operation(op)
    
    def _check_capacity_timeouts(self):
        """Check for capacity operations that have exceeded max wait time"""
        for op in self.capacity_operations:
            if not op.executed and op.boarding_start_time:
                if op.is_ready_to_depart():
                    reason = op.get_departure_reason()
                    if "MAX_WAIT_TIME" in reason:
                        logger.info(f"⏰ Vehicle {op.vehicle_id} departing due to max wait time: {reason}")
                        self._execute_capacity_operation(op)
    
    def _execute_operation_common(self, operation):
        """Common execution logic for both operation types"""
        vehicle_id = operation.vehicle_id
        operation_type = operation.operation
        
        # Get vehicle handler
        vehicle_handler = self.vehicle_handlers.get(vehicle_id)
        if not vehicle_handler:
            logger.warning(f"No handler registered for vehicle {vehicle_id}")
            return
        
        # Execute based on operation type
        if operation_type == 'start_service':
            self._start_vehicle_service(vehicle_handler, operation)
        elif operation_type == 'end_service':
            self._end_vehicle_service(vehicle_handler, operation)
        else:
            logger.warning(f"Unknown operation type: {operation_type}")
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Get comprehensive schedule status with countdowns for both operation types"""
        current_time = datetime.now().time()
        current_datetime = datetime.now()
        
        # Handle different operation modes
        if self.default_mode == 'capacity':
            return self._get_capacity_status()
        else:
            return self._get_time_based_status(current_time, current_datetime)
    
    def _get_capacity_status(self) -> Dict[str, Any]:
        """Get status for capacity-based operations"""
        total_capacity_ops = len(self.capacity_operations)
        completed_capacity_ops = len([op for op in self.capacity_operations if op.executed])
        boarding_vehicles = [op for op in self.capacity_operations 
                           if not op.executed and op.boarding_start_time]
        
        # Find next vehicle ready to depart
        next_departure_info = None
        for op in self.capacity_operations:
            if not op.executed and op.boarding_start_time:
                boarding_time = (datetime.now() - op.boarding_start_time).total_seconds()
                time_remaining = max(0, op.max_wait_time - boarding_time)
                
                next_departure_info = {
                    'vehicle_id': op.vehicle_id,
                    'route_id': op.route_id,
                    'mode': 'capacity',
                    'passengers': f"{op.current_passengers}/{op.capacity_threshold}",
                    'boarding_time': f"{int(boarding_time)}s",
                    'max_wait_remaining': f"{int(time_remaining)}s",
                    'ready_to_depart': op.is_ready_to_depart(),
                    'departure_reason': op.get_departure_reason() if op.is_ready_to_depart() else None
                }
                break
        
        return {
            'mode': 'capacity',
            'timetable_loaded': total_capacity_ops > 0,
            'total_operations': total_capacity_ops,
            'completed_operations': completed_capacity_ops,
            'pending_operations': total_capacity_ops - completed_capacity_ops,
            'boarding_vehicles': len(boarding_vehicles),
            'next_departure': next_departure_info,
            'capacity_operations': [
                {
                    'vehicle_id': op.vehicle_id,
                    'route_id': op.route_id,
                    'passengers': f"{op.current_passengers}/{op.capacity_threshold}",
                    'boarding': op.boarding_start_time is not None,
                    'ready': op.is_ready_to_depart(),
                    'executed': op.executed
                } for op in self.capacity_operations[:5]
            ]
        }
    
    def _get_time_based_status(self, current_time, current_datetime) -> Dict[str, Any]:
        """Get status for time-based operations"""
        # Get next upcoming operations
        upcoming = self.get_next_operations(5)
        
        # Calculate countdown for next departure
        next_departure = None
        countdown_seconds = None
        
        for op in upcoming:
            if op.operation == 'start_service':
                next_departure = op
                # Calculate time until departure
                target_datetime = datetime.combine(current_datetime.date(), op.scheduled_time)
                if target_datetime < current_datetime:
                    # If time has passed today, it's tomorrow
                    target_datetime += timedelta(days=1)
                
                countdown_seconds = int((target_datetime - current_datetime).total_seconds())
                break
        
        # Get resource availability
        available_vehicles = len([v for v in self.vehicle_handlers.keys() if v])
        total_operations = len(self.scheduled_operations)
        completed_operations = len([op for op in self.scheduled_operations if op.executed])
        active_vehicles = self.get_active_vehicles()
        
        return {
            'mode': 'time',
            'timetable_loaded': total_operations > 0,
            'total_operations': total_operations,
            'completed_operations': completed_operations,
            'pending_operations': total_operations - completed_operations,
            'active_vehicles': len(active_vehicles),
            'available_vehicles': available_vehicles,
            'next_departure': {
                'vehicle_id': next_departure.vehicle_id if next_departure else None,
                'route_id': next_departure.route_id if next_departure else None,
                'scheduled_time': next_departure.scheduled_time.strftime('%H:%M:%S') if next_departure else None,
                'countdown_seconds': countdown_seconds,
                'countdown_display': self._format_countdown(countdown_seconds) if countdown_seconds else None
            } if next_departure else None,
            'upcoming_operations': [
                {
                    'vehicle_id': op.vehicle_id,
                    'operation': op.operation,
                    'route_id': op.route_id,
                    'scheduled_time': op.scheduled_time.strftime('%H:%M:%S'),
                    'countdown_seconds': int((datetime.combine(current_datetime.date(), op.scheduled_time) - current_datetime).total_seconds())
                } for op in upcoming
            ]
        }
    
    def _format_countdown(self, seconds: int) -> str:
        """Format countdown seconds into human-readable format"""
        if seconds < 0:
            return "OVERDUE"
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def get_resource_availability(self) -> Dict[str, Any]:
        """Check availability of vehicles, routes, and drivers for operations"""
        try:
            vehicles = self.data_provider.get_vehicles() if self.data_provider else {}
            routes = self.data_provider.get_routes() if self.data_provider else {}
            drivers = self.data_provider.get_drivers() if self.data_provider else {}
            
            return {
                'vehicles_available': len(vehicles),
                'routes_available': len(routes),
                'drivers_available': len(drivers),
                'fleet_manager_connected': self.data_provider.is_api_available() if self.data_provider else False,
                'resource_status': 'ready' if (len(vehicles) > 0 and len(routes) > 0) else 'insufficient_resources'
            }
        except Exception as e:
            logger.error(f"Failed to check resource availability: {e}")
            return {
                'vehicles_available': 0,
                'routes_available': 0,
                'drivers_available': 0,
                'fleet_manager_connected': False,
                'resource_status': 'error',
                'error': str(e)
            }
    
    def force_execute_operation(self, vehicle_id: str, operation_type: str, **kwargs):
        """Manually force execution of an operation (for testing/debugging)"""
        try:
            operation = ScheduledOperation(
                vehicle_id=vehicle_id,
                operation=operation_type,
                scheduled_time=datetime.now().time(),
                **kwargs
            )
            
            self._execute_operation(operation)
            logger.info(f"Force executed: {operation}")
            
        except Exception as e:
            logger.error(f"Failed to force execute operation: {e}")
            raise
