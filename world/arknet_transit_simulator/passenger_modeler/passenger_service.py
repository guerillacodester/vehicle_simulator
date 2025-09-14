#!/usr/bin/env python3
"""
Dynamic Passenger Service
========================

Background service that manages dynamic passenger lifecycle for active routes.
Optimized for embedded deployment on Radxa Rock S0 (512MB RAM).

Features:
- Async architecture with asyncio
- Thread-safe passenger buffer management
- Route-aware passenger generation
- Memory-bounded operations
- Graceful service lifecycle management
"""

import asyncio
import logging
import time
import math
import configparser
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import threading
import weakref
import gc


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in meters."""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


@dataclass
class ServiceStats:
    """Service performance and health statistics"""
    start_time: datetime
    active_passengers: int = 0
    total_spawned: int = 0
    total_picked_up: int = 0
    total_dropped_off: int = 0
    total_timed_out: int = 0
    memory_usage_mb: float = 0.0
    spawn_rate_per_minute: float = 0.0
    last_activity: Optional[datetime] = None


class DynamicPassengerService:
    """
    Dynamic passenger service with embedded optimization.
    
    Manages passenger lifecycle for active routes with memory-bounded operations
    and thread-safe event handling optimized for 512MB Rock S0 deployment.
    """
    
    def __init__(self, route_ids: List[str], max_memory_mb: int = 10, dispatcher=None, walking_distance_km: float = 0.5):
        """
        Initialize passenger service for specific routes with dispatcher integration.
        
        Args:
            route_ids: List of active route IDs to generate passengers for
            max_memory_mb: Maximum memory limit for service operations
            dispatcher: Dispatcher with route buffer for GPS-based route queries
            walking_distance_km: Walking distance for GPS-based route discovery
        """
        self.route_ids = set(route_ids)
        self.max_memory_mb = max_memory_mb
        self.dispatcher = dispatcher  # NEW: Dispatcher integration
        self.walking_distance_km = walking_distance_km  # NEW: GPS proximity
        self.logger = logging.getLogger(f"{__class__.__name__}")
        
        # Service state
        self.is_running = False
        self.is_initialized = False
        self._service_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        
        # Passenger management (memory-bounded)
        self.max_passengers = min(100, max_memory_mb * 10)  # ~10 passengers per MB
        self.active_passengers: Dict[str, Any] = {}  # passenger_id -> passenger_data
        self.passenger_buffer = deque(maxlen=self.max_passengers)
        
        # Background tasks
        self._spawner_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Statistics and monitoring
        self.stats = ServiceStats(start_time=datetime.now())
        self._last_memory_check = time.time()
        
        # Load configuration from config.ini
        self.config = self._load_config()
        
        self.logger.info(
            f"DynamicPassengerService initialized for {len(self.route_ids)} routes: {list(self.route_ids)[:3]}..."
            f" (memory limit: {max_memory_mb}MB, max passengers: {self.max_passengers})"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.ini file."""
        config = configparser.ConfigParser()
        config_path = 'world/arknet_transit_simulator/config/config.ini'
        
        # Default configuration
        default_config = {
            'spawn_rate_per_minute': 5.0,
            'passenger_timeout_minutes': 15.0,
            'cleanup_interval_seconds': 30.0,
            'memory_check_interval_seconds': 60.0,
            'max_spawn_per_batch': 3,
            'destination_distance_meters': 350.0
        }
        
        try:
            config.read(config_path)
            
            # Load passenger_service section
            if config.has_section('passenger_service'):
                passenger_section = config['passenger_service']
                
                return {
                    'spawn_rate_per_minute': passenger_section.getfloat('spawn_interval_seconds', 10.0) / 60.0 * 6.0,  # Convert to per minute
                    'passenger_timeout_minutes': passenger_section.getfloat('passenger_timeout_minutes', 15.0),
                    'cleanup_interval_seconds': passenger_section.getfloat('cleanup_interval_seconds', 30.0),
                    'memory_check_interval_seconds': 60.0,  # Fixed value
                    'max_spawn_per_batch': passenger_section.getint('max_concurrent_spawns', 3),
                    'destination_distance_meters': passenger_section.getfloat('destination_distance_meters', 350.0)
                }
            else:
                self.logger.warning(f"No [passenger_service] section found in {config_path}, using defaults")
                return default_config
                
        except Exception as e:
            self.logger.warning(f"Error loading config from {config_path}: {e}, using defaults")
            return default_config
    
    async def start_service(self) -> bool:
        """
        Start the dynamic passenger service.
        
        Returns:
            bool: True if service started successfully
        """
        async with self._service_lock:
            if self.is_running:
                self.logger.warning("Service is already running")
                return True
            
            try:
                self.logger.info("Starting dynamic passenger service...")
                
                # Reset shutdown event
                self._shutdown_event.clear()
                
                # Start background tasks
                self._spawner_task = asyncio.create_task(self._passenger_spawner())
                self._cleanup_task = asyncio.create_task(self._passenger_cleanup())
                self._monitor_task = asyncio.create_task(self._service_monitor())
                
                # Mark as running
                self.is_running = True
                self.is_initialized = True
                self.stats.start_time = datetime.now()
                
                self.logger.info(
                    f"Dynamic passenger service started successfully "
                    f"(routes: {len(self.route_ids)}, memory limit: {self.max_memory_mb}MB)"
                )
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start passenger service: {e}")
                await self._cleanup_tasks()
                return False
    
    async def stop_service(self) -> bool:
        """
        Stop the dynamic passenger service gracefully.
        
        Returns:
            bool: True if service stopped successfully
        """
        async with self._service_lock:
            if not self.is_running:
                self.logger.info("Service is not running")
                return True
            
            try:
                self.logger.info("Stopping dynamic passenger service...")
                
                # Signal shutdown to background tasks
                self._shutdown_event.set()
                self.is_running = False
                
                # Wait for tasks to complete gracefully
                await self._cleanup_tasks()
                
                # Clear passenger data
                self.active_passengers.clear()
                self.passenger_buffer.clear()
                
                # Force garbage collection for embedded optimization
                gc.collect()
                
                self.logger.info("Dynamic passenger service stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping passenger service: {e}")
                return False
    
    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status and statistics.
        
        Returns:
            Dict containing service status information
        """
        uptime = datetime.now() - self.stats.start_time if self.is_running else timedelta(0)
        
        return {
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'uptime_seconds': uptime.total_seconds(),
            'active_routes': list(self.route_ids),
            'route_count': len(self.route_ids),
            'active_passengers': len(self.active_passengers),
            'max_passengers': self.max_passengers,
            'memory_limit_mb': self.max_memory_mb,
            'stats': {
                'total_spawned': self.stats.total_spawned,
                'total_picked_up': self.stats.total_picked_up,
                'total_dropped_off': self.stats.total_dropped_off,
                'total_timed_out': self.stats.total_timed_out,
                'spawn_rate_per_minute': self.stats.spawn_rate_per_minute,
                'memory_usage_mb': self.stats.memory_usage_mb,
                'last_activity': self.stats.last_activity.isoformat() if self.stats.last_activity else None
            }
        }
    
    async def update_active_routes(self, new_route_ids: List[str]) -> bool:
        """
        Update the list of active routes for passenger generation.
        
        Args:
            new_route_ids: Updated list of route IDs
            
        Returns:
            bool: True if routes updated successfully
        """
        try:
            old_routes = self.route_ids.copy()
            self.route_ids = set(new_route_ids)
            
            added_routes = self.route_ids - old_routes
            removed_routes = old_routes - self.route_ids
            
            if added_routes or removed_routes:
                self.logger.info(
                    f"Routes updated - Added: {list(added_routes)}, Removed: {list(removed_routes)}"
                )
                
                # TODO: In later tasks, we'll need to handle passenger cleanup for removed routes
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating active routes: {e}")
            return False
    
    async def add_passenger_event(self, event_type: str, passenger_id: str, **kwargs) -> bool:
        """
        Add a passenger event to the processing buffer (thread-safe).
        
        Args:
            event_type: Type of event ('spawn', 'pickup', 'dropoff', 'timeout')
            passenger_id: Unique passenger identifier
            **kwargs: Additional event data
            
        Returns:
            bool: True if event added successfully
        """
        try:
            # Memory check before adding
            if len(self.passenger_buffer) >= self.passenger_buffer.maxlen:
                self.logger.warning("Passenger buffer full, dropping oldest event")
                # Buffer will automatically drop oldest due to maxlen
            
            event_data = {
                'type': event_type,
                'passenger_id': passenger_id,
                'timestamp': datetime.now(),
                **kwargs
            }
            
            self.passenger_buffer.append(event_data)
            self.stats.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding passenger event: {e}")
            return False
    
    def get_memory_usage(self) -> float:
        """
        Estimate current memory usage in MB (embedded optimization).
        
        Returns:
            float: Estimated memory usage in MB
        """
        try:
            # Rough estimation for embedded systems
            passenger_memory = len(self.active_passengers) * 0.001  # ~1KB per passenger
            buffer_memory = len(self.passenger_buffer) * 0.0005     # ~0.5KB per event
            service_memory = 0.1  # Base service overhead
            
            total_mb = passenger_memory + buffer_memory + service_memory
            self.stats.memory_usage_mb = total_mb
            
            return total_mb
            
        except Exception:
            return 0.0
    
    # Background Tasks
    
    async def _passenger_spawner(self):
        """Background task for spawning passengers based on demand."""
        self.logger.info("Passenger spawner task started")
        
        try:
            while not self._shutdown_event.is_set():
                if not self.route_ids:
                    # No active routes, wait longer
                    await asyncio.sleep(30)
                    continue
                
                # Calculate spawn rate (basic implementation, will be enhanced in later tasks)
                spawn_interval = 60.0 / self.config['spawn_rate_per_minute']
                
                # Memory check before spawning
                if len(self.active_passengers) >= self.max_passengers:
                    self.logger.debug("Max passengers reached, skipping spawn")
                    await asyncio.sleep(spawn_interval)
                    continue
                
                # Spawn passengers for active routes (placeholder implementation)
                spawned_count = await self._spawn_passengers_batch()
                
                if spawned_count > 0:
                    self.stats.total_spawned += spawned_count
                    self._update_spawn_rate()
                
                # Wait until next spawn cycle
                await asyncio.sleep(spawn_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Passenger spawner task cancelled")
        except Exception as e:
            self.logger.error(f"Passenger spawner task error: {e}")
    
    async def _passenger_cleanup(self):
        """Background task for cleaning up timed-out passengers."""
        self.logger.info("Passenger cleanup task started")
        
        try:
            while not self._shutdown_event.is_set():
                cleanup_count = await self._cleanup_timed_out_passengers()
                
                if cleanup_count > 0:
                    self.stats.total_timed_out += cleanup_count
                    self.logger.debug(f"Cleaned up {cleanup_count} timed-out passengers")
                
                # Memory optimization - force garbage collection periodically
                if time.time() - self._last_memory_check > self.config['memory_check_interval_seconds']:
                    gc.collect()
                    self._last_memory_check = time.time()
                    current_memory = self.get_memory_usage()
                    self.logger.debug(f"Memory usage: {current_memory:.2f}MB")
                
                await asyncio.sleep(self.config['cleanup_interval_seconds'])
                
        except asyncio.CancelledError:
            self.logger.info("Passenger cleanup task cancelled")
        except Exception as e:
            self.logger.error(f"Passenger cleanup task error: {e}")
    
    async def _service_monitor(self):
        """Background task for service health monitoring."""
        self.logger.info("Service monitor task started")
        
        try:
            while not self._shutdown_event.is_set():
                # Update service statistics
                self.stats.active_passengers = len(self.active_passengers)
                current_memory = self.get_memory_usage()
                
                # Log health status periodically
                if self.stats.active_passengers > 0 or current_memory > 1.0:
                    self.logger.debug(
                        f"Service health - Passengers: {self.stats.active_passengers}, "
                        f"Memory: {current_memory:.2f}MB, "
                        f"Spawn rate: {self.stats.spawn_rate_per_minute:.1f}/min"
                    )
                
                # Memory warning for embedded deployment
                if current_memory > self.max_memory_mb * 0.8:
                    self.logger.warning(
                        f"High memory usage: {current_memory:.2f}MB "
                        f"(limit: {self.max_memory_mb}MB)"
                    )
                
                await asyncio.sleep(60)  # Monitor every minute
                
        except asyncio.CancelledError:
            self.logger.info("Service monitor task cancelled")
        except Exception as e:
            self.logger.error(f"Service monitor task error: {e}")
    
    # Helper Methods
    
    async def _spawn_passengers_batch(self) -> int:
        """
        Spawn a batch of passengers using dispatcher route buffer for GPS-aware placement.
        Enhanced with route geometry queries for realistic passenger placement.
        
        Returns:
            int: Number of passengers spawned
        """
        try:
            max_spawn = min(
                self.config['max_spawn_per_batch'],
                self.max_passengers - len(self.active_passengers)
            )
            
            if max_spawn <= 0:
                return 0
            
            spawned = 0
            for _ in range(max_spawn):
                passenger_id = f"PASS_{int(time.time()*1000)}_{spawned}"
                
                # Use dispatcher route buffer for realistic passenger placement
                passenger_data = await self._create_passenger_with_route_data(passenger_id)
                
                if passenger_data:
                    self.active_passengers[passenger_id] = passenger_data
                    spawned += 1
                    
                    # Log passenger creation with GPS coordinates
                    route_id = passenger_data.get('route_id', 'unknown')
                    pickup_coords = passenger_data.get('pickup_coords', [0, 0])
                    dest_coords = passenger_data.get('destination_coords', [0, 0])
                    self.logger.debug(f"Spawned passenger {passenger_id} on route {route_id}: "
                                    f"pickup ({pickup_coords[1]:.6f}, {pickup_coords[0]:.6f}) → "
                                    f"destination ({dest_coords[1]:.6f}, {dest_coords[0]:.6f})")
            
            return spawned
            
        except Exception as e:
            self.logger.error(f"Error spawning passengers: {e}")
            return 0
    
    async def _create_passenger_with_route_data(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """Create passenger with realistic GPS coordinates from route geometry."""
        try:
            if not self.dispatcher:
                # Fallback to basic passenger data if no dispatcher
                return {
                    'id': passenger_id,
                    'spawn_time': datetime.now(),
                    'route_id': list(self.route_ids)[0] if self.route_ids else 'unknown',
                    'status': 'waiting'
                }
            
            # Get a random route from active routes
            import random
            route_id = random.choice(list(self.route_ids))
            
            # Query dispatcher for route geometry
            route_info = await self.dispatcher.query_route_by_id(route_id)
            
            if route_info and route_info.geometry and route_info.geometry.get('coordinates'):
                coords = route_info.geometry['coordinates']
                
                if len(coords) >= 2:
                    # Select pickup and destination points along route with minimum distance
                    min_distance_m = self.config['destination_distance_meters']
                    max_attempts = 20  # Limit attempts to avoid infinite loops
                    
                    for attempt in range(max_attempts):
                        pickup_idx = random.randint(0, len(coords) - 2)
                        dest_idx = random.randint(pickup_idx + 1, len(coords) - 1)
                        
                        pickup_coord = coords[pickup_idx]
                        dest_coord = coords[dest_idx]
                        
                        # Check if distance meets minimum requirement
                        pickup_lat, pickup_lon = pickup_coord[1], pickup_coord[0]  # [lon, lat] -> lat, lon
                        dest_lat, dest_lon = dest_coord[1], dest_coord[0]
                        
                        trip_distance = haversine_distance(pickup_lat, pickup_lon, dest_lat, dest_lon)
                        
                        if trip_distance >= min_distance_m:
                            break
                    else:
                        # If we couldn't find a valid pair, use the last attempt
                        self.logger.debug(f"Could not find pickup/destination pair with {min_distance_m}m minimum distance for route {route_id}")
                        pass
                    
                    return {
                        'id': passenger_id,
                        'spawn_time': datetime.now(),
                        'route_id': route_id,
                        'route_name': route_info.route_name,
                        'pickup_coords': pickup_coord,  # [lon, lat]
                        'destination_coords': dest_coord,  # [lon, lat]
                        'status': 'waiting',
                        'using_route_geometry': True
                    }
            
            # Fallback if no geometry available
            self.logger.warning(f"No route geometry available for route {route_id}")
            return {
                'id': passenger_id,
                'spawn_time': datetime.now(),
                'route_id': route_id,
                'status': 'waiting',
                'using_route_geometry': False
            }
            
        except Exception as e:
            self.logger.error(f"Error creating passenger with route data: {str(e)}")
            return None
    
    async def _cleanup_timed_out_passengers(self) -> int:
        """
        Clean up passengers that have timed out.
        
        Returns:
            int: Number of passengers cleaned up
        """
        try:
            current_time = datetime.now()
            timeout_threshold = timedelta(minutes=self.config['passenger_timeout_minutes'])
            
            timed_out_passengers = []
            
            for passenger_id, passenger_data in self.active_passengers.items():
                spawn_time = passenger_data.get('spawn_time', current_time)
                if current_time - spawn_time > timeout_threshold:
                    timed_out_passengers.append(passenger_id)
            
            # Remove timed-out passengers
            for passenger_id in timed_out_passengers:
                del self.active_passengers[passenger_id]
            
            return len(timed_out_passengers)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up passengers: {e}")
            return 0
    
    def _update_spawn_rate(self):
        """Update spawn rate statistics."""
        current_time = datetime.now()
        time_diff = (current_time - self.stats.start_time).total_seconds() / 60.0  # minutes
        
        if time_diff > 0:
            self.stats.spawn_rate_per_minute = self.stats.total_spawned / time_diff
    
    async def _cleanup_tasks(self):
        """Clean up background tasks."""
        tasks = [self._spawner_task, self._cleanup_task, self._monitor_task]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.error(f"Error during task cleanup: {e}")
        
        self._spawner_task = None
        self._cleanup_task = None
        self._monitor_task = None


# Factory function for easy service creation
async def create_passenger_service(route_ids: List[str], max_memory_mb: int = 10) -> Optional[DynamicPassengerService]:
    """
    Factory function to create and initialize a passenger service.
    
    Args:
        route_ids: List of active route IDs
        max_memory_mb: Maximum memory limit for the service
        
    Returns:
        DynamicPassengerService instance or None if creation failed
    """
    try:
        service = DynamicPassengerService(route_ids, max_memory_mb)
        
        success = await service.start_service()
        if success:
            return service
        else:
            return None
            
    except Exception as e:
        logging.error(f"Failed to create passenger service: {e}")
        return None


if __name__ == "__main__":
    """Test the passenger service with sample routes."""
    import asyncio
    
    async def test_service():
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Test with sample routes
        test_routes = ["route_1", "route_2", "route_3"]
        
        print("Testing DynamicPassengerService...")
        
        # Create service
        service = await create_passenger_service(test_routes, max_memory_mb=5)
        
        if service:
            print("✅ Service created successfully")
            
            # Run for a short time
            await asyncio.sleep(10)
            
            # Get status
            status = await service.get_service_status()
            print(f"📊 Service Status: {status}")
            
            # Stop service
            await service.stop_service()
            print("✅ Service stopped successfully")
        else:
            print("❌ Failed to create service")
    
    # Run test
    asyncio.run(test_service())