"""
Lightweight integration layer between vehicle telemetry and depot passenger management.

Hooks into existing GPS telemetry flow to update vehicle positions for passenger matching.
Designed for minimal performance overhead with 1200+ vehicles.
"""
import asyncio
import logging
from typing import Dict, Optional, Set
from weakref import WeakSet

from .depot_passenger_manager import DepotPassengerManager
from ..vehicle.gps_device.radio_module.packet import TelemetryPacket


class PassengerIntegrationService:
    """
    Ultra-lightweight service that integrates passenger management with vehicle telemetry.
    
    Hooks into existing telemetry flow with minimal overhead:
    - Subscribes to telemetry packets for position updates
    - Manages passenger boarding at depots
    - Handles passenger lifecycle with vehicle movements
    """
    
    def __init__(self, passenger_manager: DepotPassengerManager):
        self.passenger_manager = passenger_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Track vehicles currently at depots for boarding operations
        self.vehicles_at_depots: Dict[str, str] = {}  # vehicle_id -> depot_id
        self.depot_boarding_zones: Dict[str, tuple] = {}  # depot_id -> (lat, lon, radius)
        
        # Performance optimization: batch position updates
        self.position_update_queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
        self.batch_update_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'telemetry_packets_processed': 0,
            'position_updates_processed': 0,
            'boarding_events': 0,
            'performance_warnings': 0
        }
    
    async def initialize(self, depot_zones: Dict[str, Dict]) -> None:
        """Initialize depot boarding zones and start background processing."""
        # Set up depot boarding zones with generous radius for boarding detection
        for depot_id, depot_data in depot_zones.items():
            self.depot_boarding_zones[depot_id] = (
                depot_data['lat'],
                depot_data['lon'], 
                depot_data.get('boarding_radius', 0.001)  # ~100m radius
            )
        
        # Start background batch processing
        self.batch_update_task = asyncio.create_task(self._batch_position_processor())
        
        self.logger.info(f"PassengerIntegrationService initialized with {len(depot_zones)} depot zones")
    
    def hook_telemetry_packet(self, packet: TelemetryPacket) -> None:
        """
        Hook into telemetry packet processing (called from transmitter).
        
        ULTRA-LIGHTWEIGHT: Only extracts essential data and queues for batch processing.
        """
        try:
            # Extract only essential data to minimize processing overhead
            vehicle_id = packet.deviceId
            lat, lon = packet.lat, packet.lon
            
            # Queue for batch processing (non-blocking)
            if not self.position_update_queue.full():
                self.position_update_queue.put_nowait((vehicle_id, lat, lon))
            else:
                self.stats['performance_warnings'] += 1
            
            self.stats['telemetry_packets_processed'] += 1
            
        except Exception as e:
            # Fail silently to avoid disrupting telemetry flow
            self.logger.debug(f"Error processing telemetry hook: {e}")
    
    async def _batch_position_processor(self) -> None:
        """
        Background task that processes position updates in batches for efficiency.
        
        Processes updates every 100ms or when batch reaches 50 vehicles.
        """
        batch_size = 50
        batch_timeout = 0.1  # 100ms
        position_batch = []
        
        while True:
            try:
                # Collect batch of position updates
                try:
                    # Wait for first update with timeout
                    update = await asyncio.wait_for(
                        self.position_update_queue.get(), 
                        timeout=batch_timeout
                    )
                    position_batch.append(update)
                    
                    # Quickly collect additional updates up to batch size
                    while len(position_batch) < batch_size:
                        try:
                            update = self.position_update_queue.get_nowait()
                            position_batch.append(update)
                        except asyncio.QueueEmpty:
                            break
                
                except asyncio.TimeoutError:
                    # No updates in timeout period, continue
                    continue
                
                # Process batch efficiently
                if position_batch:
                    await self._process_position_batch(position_batch)
                    position_batch.clear()
                    
            except Exception as e:
                self.logger.error(f"Error in batch position processor: {e}")
                # Clear batch and continue to prevent backlog
                position_batch.clear()
                await asyncio.sleep(0.1)
    
    async def _process_position_batch(self, position_batch: list) -> None:
        """Process a batch of position updates efficiently."""
        depot_arrivals = []  # Track vehicles arriving at depots
        depot_departures = []  # Track vehicles leaving depots
        
        for vehicle_id, lat, lon in position_batch:
            # Update vehicle position in passenger manager
            self.passenger_manager.update_vehicle_position(vehicle_id, lat, lon)
            
            # Check depot boarding zone entry/exit
            current_depot = self.vehicles_at_depots.get(vehicle_id)
            at_depot = self._check_vehicle_at_depot(vehicle_id, lat, lon)
            
            if at_depot and not current_depot:
                # Vehicle arrived at depot
                self.vehicles_at_depots[vehicle_id] = at_depot
                depot_arrivals.append((vehicle_id, at_depot))
                
            elif current_depot and not at_depot:
                # Vehicle left depot
                del self.vehicles_at_depots[vehicle_id]
                depot_departures.append((vehicle_id, current_depot))
        
        # Process boarding events in batch
        if depot_arrivals:
            await self._handle_depot_arrivals(depot_arrivals)
        
        if depot_departures:
            await self._handle_depot_departures(depot_departures)
        
        self.stats['position_updates_processed'] += len(position_batch)
    
    def _check_vehicle_at_depot(self, vehicle_id: str, lat: float, lon: float) -> Optional[str]:
        """
        Check if vehicle is within any depot boarding zone.
        
        Uses simple distance calculation for performance.
        Returns depot_id if at depot, None otherwise.
        """
        for depot_id, (depot_lat, depot_lon, radius) in self.depot_boarding_zones.items():
            # Simple squared distance check (avoids expensive sqrt)
            dist_sq = (lat - depot_lat) ** 2 + (lon - depot_lon) ** 2
            radius_sq = radius ** 2
            
            if dist_sq <= radius_sq:
                return depot_id
        
        return None
    
    async def _handle_depot_arrivals(self, arrivals: list) -> None:
        """Handle vehicles arriving at depots - initiate passenger boarding."""
        for vehicle_id, depot_id in arrivals:
            try:
                # Get passengers for this vehicle at this depot
                passengers = self.passenger_manager.get_passengers_for_vehicle(
                    vehicle_id=vehicle_id,
                    depot_id=depot_id,
                    max_passengers=20  # Reasonable boarding limit
                )
                
                if passengers:
                    # Simulate boarding process (would integrate with vehicle state)
                    await self._board_passengers(vehicle_id, passengers)
                    self.stats['boarding_events'] += len(passengers)
                    
                    self.logger.debug(
                        f"Vehicle {vehicle_id} boarded {len(passengers)} passengers at depot {depot_id}"
                    )
                
            except Exception as e:
                self.logger.error(f"Error handling depot arrival for {vehicle_id}: {e}")
    
    async def _handle_depot_departures(self, departures: list) -> None:
        """Handle vehicles leaving depots."""
        for vehicle_id, depot_id in departures:
            self.logger.debug(f"Vehicle {vehicle_id} departed depot {depot_id}")
            # Could add departure logic here if needed
    
    async def _board_passengers(self, vehicle_id: str, passengers: list) -> None:
        """
        Simulate passenger boarding process.
        
        In a full implementation, this would:
        1. Update vehicle passenger count
        2. Change passenger state to ONBOARD
        3. Set up destination monitoring
        """
        for passenger in passengers:
            # Update passenger state (simplified)
            # In real implementation, would integrate with vehicle passenger tracking
            passenger.state = "ONBOARD"
            
            # Schedule passenger removal when vehicle reaches destination
            # This would be handled by destination monitoring in a full implementation
            asyncio.create_task(
                self._monitor_passenger_destination(vehicle_id, passenger)
            )
    
    async def _monitor_passenger_destination(self, vehicle_id: str, passenger) -> None:
        """
        Monitor passenger destination and handle disembarking.
        
        Simplified implementation - in production would use more sophisticated tracking.
        """
        try:
            # Wait some time representing journey duration (simplified)
            await asyncio.sleep(30)  # Simulate 30-second journey
            
            # Remove passenger (simulate disembarking)
            self.passenger_manager.remove_passenger(passenger)
            
            self.logger.debug(f"Passenger disembarked from vehicle {vehicle_id}")
            
        except Exception as e:
            self.logger.error(f"Error monitoring passenger destination: {e}")
    
    def get_stats(self) -> Dict:
        """Get integration service statistics."""
        return {
            **self.stats,
            'vehicles_at_depots': len(self.vehicles_at_depots),
            'position_queue_size': self.position_update_queue.qsize(),
        }
    
    async def shutdown(self) -> None:
        """Graceful shutdown of integration service."""
        if self.batch_update_task:
            self.batch_update_task.cancel()
            try:
                await self.batch_update_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("PassengerIntegrationService shutdown complete")


# Global integration service instance (lightweight singleton pattern)
_integration_service: Optional[PassengerIntegrationService] = None


def get_integration_service() -> Optional[PassengerIntegrationService]:
    """Get the global integration service instance."""
    return _integration_service


def initialize_passenger_integration(passenger_manager: DepotPassengerManager, 
                                   depot_zones: Dict[str, Dict]) -> PassengerIntegrationService:
    """Initialize the global passenger integration service."""
    global _integration_service
    
    if _integration_service is not None:
        raise RuntimeError("Passenger integration service already initialized")
    
    _integration_service = PassengerIntegrationService(passenger_manager)
    asyncio.create_task(_integration_service.initialize(depot_zones))
    
    return _integration_service


def hook_telemetry_packet(packet: TelemetryPacket) -> None:
    """
    Global hook function to be called from telemetry transmitter.
    
    ULTRA-LIGHTWEIGHT: Single function call with minimal overhead.
    """
    if _integration_service:
        _integration_service.hook_telemetry_packet(packet)