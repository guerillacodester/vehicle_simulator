"""
High-performance depot-centric passenger system coordinator.

Main entry point for setting up and managing efficient passenger simulation
optimized for 1200+ concurrent vehicles on resource-constrained hardware.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .depot_passenger_manager import DepotPassengerManager
from .passenger_integration import PassengerIntegrationService, initialize_passenger_integration
from .people import PeopleSimulatorConfig
from .people_models.poisson import PoissonDistributionModel


class DepotPassengerCoordinator:
    """
    Main coordinator for high-performance depot-centric passenger operations.
    
    Orchestrates:
    - Depot passenger pool management
    - Vehicle position tracking
    - Passenger-vehicle matching
    - Performance monitoring and optimization
    
    Designed for:
    - 1200+ concurrent vehicles
    - Low CPU and memory usage
    - Rock-solid stability on low-end hardware
    """
    
    def __init__(self, config: Optional[PeopleSimulatorConfig] = None):
        self.config = config or PeopleSimulatorConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Core components
        self.passenger_manager = DepotPassengerManager(self.config)
        self.integration_service: Optional[PassengerIntegrationService] = None
        self.distribution_model = PoissonDistributionModel(
            config=self.config,
            base_lambda=10.0,  # Reduced for efficiency
            peak_multiplier=2.0,  # Lower peaks for stability
            weekend_multiplier=0.7
        )
        
        # Background tasks
        self.passenger_generation_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Performance settings optimized for 1200 vehicles
        self.generation_interval = 45  # Generate passengers every 45 seconds
        self.cleanup_interval = 300    # Cleanup every 5 minutes
        self.monitoring_interval = 60  # Monitor performance every minute
        
        # System state
        self.is_running = False
        self.start_time = None
        
        self.logger.info("DepotPassengerCoordinator initialized for high-performance operation")
    
    async def initialize(self, system_config: Dict[str, Any]) -> None:
        """
        Initialize the entire depot passenger system.
        
        Args:
            system_config: Configuration containing:
                - depots: List of depot configurations
                - routes: Dictionary of route polylines  
                - performance_limits: System performance constraints
        """
        try:
            self.start_time = datetime.now()
            
            # Extract configuration
            depots = system_config.get('depots', [])
            routes = system_config.get('routes', {})
            performance_limits = system_config.get('performance_limits', {})
            
            # Apply performance limits
            self._apply_performance_limits(performance_limits)
            
            # Initialize passenger manager
            await self.passenger_manager.initialize_depots(depots)
            await self.passenger_manager.load_route_polylines(routes)
            
            # Initialize integration service
            depot_zones = {
                depot['depot_id']: {
                    'lat': depot['lat'],
                    'lon': depot['lon'],
                    'boarding_radius': depot.get('boarding_radius', 0.001)
                }
                for depot in depots
            }
            
            self.integration_service = initialize_passenger_integration(
                self.passenger_manager, 
                depot_zones
            )
            
            self.logger.info(
                f"System initialized: {len(depots)} depots, {len(routes)} routes, "
                f"performance mode: {performance_limits.get('mode', 'standard')}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize depot passenger system: {e}")
            raise
    
    def _apply_performance_limits(self, limits: Dict[str, Any]) -> None:
        """Apply performance constraints based on hardware capabilities."""
        mode = limits.get('mode', 'standard')
        
        if mode == 'ultra_low_resource':
            # Optimizations for very constrained hardware
            self.generation_interval = 60
            self.passenger_manager.max_passengers_per_depot = 100
            self.passenger_manager.batch_size = 25
            self.distribution_model.base_lambda = 5.0
            
        elif mode == 'high_performance':
            # Settings for more powerful hardware
            self.generation_interval = 30
            self.passenger_manager.max_passengers_per_depot = 300
            self.passenger_manager.batch_size = 75
            self.distribution_model.base_lambda = 15.0
        
        # Apply custom limits if specified
        if 'max_passengers_per_depot' in limits:
            self.passenger_manager.max_passengers_per_depot = limits['max_passengers_per_depot']
        
        if 'generation_interval' in limits:
            self.generation_interval = limits['generation_interval']
        
        self.logger.info(f"Applied performance mode: {mode}")
    
    async def start(self) -> None:
        """Start all background processes for passenger management."""
        if self.is_running:
            self.logger.warning("System already running")
            return
        
        try:
            self.is_running = True
            
            # Start background tasks
            self.passenger_generation_task = asyncio.create_task(
                self._passenger_generation_loop()
            )
            
            self.cleanup_task = asyncio.create_task(
                self._cleanup_loop()
            )
            
            self.monitoring_task = asyncio.create_task(
                self._monitoring_loop()
            )
            
            self.logger.info("Depot passenger system started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop all background processes gracefully."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel background tasks
        tasks = [
            self.passenger_generation_task,
            self.cleanup_task,
            self.monitoring_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        for task in tasks:
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Shutdown integration service
        if self.integration_service:
            await self.integration_service.shutdown()
        
        self.logger.info("Depot passenger system stopped")
    
    async def _passenger_generation_loop(self) -> None:
        """Background loop for generating passengers at depots."""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Generate passengers at all depots
                await self.passenger_manager.generate_depot_passengers(
                    self.distribution_model,
                    current_time
                )
                
                # Wait for next generation cycle
                await asyncio.sleep(self.generation_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in passenger generation loop: {e}")
                await asyncio.sleep(10)  # Brief pause before retry
    
    async def _cleanup_loop(self) -> None:
        """Background loop for system cleanup and optimization."""
        while self.is_running:
            try:
                # Clean up stale passengers and optimize memory
                await self.passenger_manager.cleanup_stale_data()
                
                # Wait for next cleanup cycle
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(30)
    
    async def _monitoring_loop(self) -> None:
        """Background loop for performance monitoring."""
        while self.is_running:
            try:
                # Collect performance statistics
                passenger_stats = self.passenger_manager.get_performance_stats()
                integration_stats = self.integration_service.get_stats() if self.integration_service else {}
                
                # Log performance metrics
                self.logger.info(
                    f"Performance: {passenger_stats['active_vehicles']} vehicles, "
                    f"{passenger_stats['total_waiting_passengers']} waiting passengers, "
                    f"{integration_stats.get('telemetry_packets_processed', 0)} telemetry packets processed"
                )
                
                # Check for performance warnings
                if passenger_stats['total_waiting_passengers'] > 2000:
                    self.logger.warning("High passenger count detected - consider increasing generation interval")
                
                if integration_stats.get('performance_warnings', 0) > 100:
                    self.logger.warning("Performance warnings detected - system may be overloaded")
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    def register_vehicle(self, vehicle_id: str, route_id: str, 
                        initial_lat: float, initial_lon: float) -> None:
        """Register a vehicle for passenger tracking."""
        self.passenger_manager.register_vehicle(vehicle_id, route_id, initial_lat, initial_lon)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        passenger_stats = self.passenger_manager.get_performance_stats()
        integration_stats = self.integration_service.get_stats() if self.integration_service else {}
        
        return {
            'system_status': 'running' if self.is_running else 'stopped',
            'uptime_seconds': uptime.total_seconds(),
            'passenger_stats': passenger_stats,
            'integration_stats': integration_stats,
            'config': {
                'generation_interval': self.generation_interval,
                'cleanup_interval': self.cleanup_interval,
                'max_passengers_per_depot': self.passenger_manager.max_passengers_per_depot
            }
        }
    
    async def simulate_load_test(self, num_vehicles: int = 1200, duration_minutes: int = 10) -> Dict[str, Any]:
        """
        Simulate load test with specified number of vehicles.
        
        Returns performance metrics for validation.
        """
        self.logger.info(f"Starting load test: {num_vehicles} vehicles for {duration_minutes} minutes")
        
        start_time = datetime.now()
        
        # Register test vehicles
        test_routes = list(self.passenger_manager.route_polylines.keys())[:10]  # Use up to 10 routes
        for i in range(num_vehicles):
            route_id = test_routes[i % len(test_routes)] if test_routes else 'route1'
            self.register_vehicle(f"test_vehicle_{i}", route_id, 37.7749, -122.4194)
        
        # Run simulation
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            await asyncio.sleep(1)
        
        # Collect final statistics
        final_stats = self.get_system_stats()
        
        self.logger.info(f"Load test completed: {final_stats}")
        
        return final_stats


# Convenience function for easy setup
async def setup_depot_passenger_system(depots: List[Dict], routes: Dict[str, List], 
                                      performance_mode: str = 'standard') -> DepotPassengerCoordinator:
    """
    Quick setup function for depot-centric passenger system.
    
    Args:
        depots: List of depot configurations with lat, lon, depot_id
        routes: Dictionary of route_id -> list of (lat, lon) coordinates
        performance_mode: 'ultra_low_resource', 'standard', or 'high_performance'
    
    Returns:
        Configured and started DepotPassengerCoordinator
    """
    config = PeopleSimulatorConfig()
    coordinator = DepotPassengerCoordinator(config)
    
    system_config = {
        'depots': depots,
        'routes': routes,
        'performance_limits': {'mode': performance_mode}
    }
    
    await coordinator.initialize(system_config)
    await coordinator.start()
    
    return coordinator