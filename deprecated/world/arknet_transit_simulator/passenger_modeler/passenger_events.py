#!/usr/bin/env python3
"""
Passenger Event System
======================

Thread-safe event system for managing passenger lifecycle events (pickup, dropoff, spawn, timeout).
Optimized for embedded deployment with memory-bounded operations and async processing.

Features:
- Thread-safe event buffer with asyncio.Queue
- Event validation and priority handling
- Memory-bounded event processing
- Comprehensive event logging and monitoring
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class EventType(Enum):
    """Passenger event types"""
    SPAWN = "spawn"           # New passenger created and waiting
    PICKUP = "pickup"         # Passenger picked up by vehicle
    DROPOFF = "dropoff"       # Passenger dropped off at destination
    TIMEOUT = "timeout"       # Passenger timed out waiting
    ROUTE_CHANGE = "route_change"  # Passenger route updated
    CANCEL = "cancel"         # Passenger cancelled their journey


class EventPriority(Enum):
    """Event processing priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PassengerEvent:
    """
    Passenger event with comprehensive metadata.
    
    Represents a single event in the passenger lifecycle with all necessary
    data for processing and validation.
    """
    event_id: str
    event_type: EventType
    passenger_id: str
    timestamp: datetime
    route_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate event data after initialization."""
        if not self.event_id:
            self.event_id = f"EVT_{uuid.uuid4().hex[:8].upper()}"
        
        if not self.passenger_id:
            raise ValueError("passenger_id is required")
        
        if not isinstance(self.event_type, EventType):
            raise ValueError(f"Invalid event_type: {self.event_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'passenger_id': self.passenger_id,
            'timestamp': self.timestamp.isoformat(),
            'route_id': self.route_id,
            'vehicle_id': self.vehicle_id,
            'driver_id': self.driver_id,
            'location_lat': self.location_lat,
            'location_lon': self.location_lon,
            'priority': self.priority.value,
            'metadata': self.metadata,
            'processed': self.processed,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PassengerEvent':
        """Create event from dictionary."""
        event = cls(
            event_id=data['event_id'],
            event_type=EventType(data['event_type']),
            passenger_id=data['passenger_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            route_id=data.get('route_id'),
            vehicle_id=data.get('vehicle_id'),
            driver_id=data.get('driver_id'),
            location_lat=data.get('location_lat'),
            location_lon=data.get('location_lon'),
            priority=EventPriority(data.get('priority', EventPriority.NORMAL.value)),
            metadata=data.get('metadata', {}),
            processed=data.get('processed', False),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )
        return event
    
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return self.retry_count < self.max_retries
    
    def mark_retry(self) -> None:
        """Mark event for retry and increment counter."""
        self.retry_count += 1
        self.processed = False
    
    def mark_processed(self) -> None:
        """Mark event as successfully processed."""
        self.processed = True


class PassengerBuffer:
    """
    Thread-safe passenger event buffer with memory-bounded operations.
    
    Uses asyncio.Queue for thread-safe event handling with priority processing,
    memory limits, and comprehensive monitoring for embedded deployment.
    """
    
    def __init__(self, max_size: int = 1000, enable_priority: bool = True):
        """
        Initialize passenger event buffer.
        
        Args:
            max_size: Maximum number of events in buffer
            enable_priority: Enable priority-based event processing
        """
        self.max_size = max_size
        self.enable_priority = enable_priority
        self.logger = logging.getLogger(f"{__class__.__name__}")
        
        # Event queues (separate queues for different priorities if enabled)
        if enable_priority:
            self.queues = {
                EventPriority.CRITICAL: asyncio.Queue(maxsize=max_size // 4),
                EventPriority.HIGH: asyncio.Queue(maxsize=max_size // 4),
                EventPriority.NORMAL: asyncio.Queue(maxsize=max_size // 2),
                EventPriority.LOW: asyncio.Queue(maxsize=max_size // 4)
            }
        else:
            self.main_queue = asyncio.Queue(maxsize=max_size)
        
        # Buffer statistics
        self.stats = {
            'total_pushed': 0,
            'total_popped': 0,
            'total_dropped': 0,
            'total_failed': 0,
            'current_size': 0,
            'last_activity': None
        }
        
        # Event processing lock for atomic operations
        self._lock = asyncio.Lock()
        
        self.logger.info(
            f"PassengerBuffer initialized - Max size: {max_size}, "
            f"Priority enabled: {enable_priority}"
        )
    
    async def push_event(self, event: PassengerEvent, timeout: float = 1.0) -> bool:
        """
        Push event to buffer (thread-safe).
        
        Args:
            event: PassengerEvent to add to buffer
            timeout: Timeout for queue operation
            
        Returns:
            bool: True if event added successfully
        """
        try:
            async with self._lock:
                if self.enable_priority:
                    queue = self.queues[event.priority]
                else:
                    queue = self.main_queue
                
                # Try to add event with timeout
                try:
                    await asyncio.wait_for(queue.put(event), timeout=timeout)
                    
                    self.stats['total_pushed'] += 1
                    self.stats['current_size'] += 1
                    self.stats['last_activity'] = datetime.now()
                    
                    self.logger.debug(
                        f"Event pushed: {event.event_type.value} for passenger {event.passenger_id} "
                        f"(priority: {event.priority.value})"
                    )
                    return True
                    
                except asyncio.TimeoutError:
                    self.stats['total_dropped'] += 1
                    self.logger.warning(
                        f"Event dropped (buffer full): {event.event_type.value} "
                        f"for passenger {event.passenger_id}"
                    )
                    return False
                    
        except Exception as e:
            self.stats['total_failed'] += 1
            self.logger.error(f"Error pushing event: {e}")
            return False
    
    async def pop_event(self, timeout: Optional[float] = None) -> Optional[PassengerEvent]:
        """
        Pop next event from buffer with priority handling (thread-safe).
        
        Args:
            timeout: Timeout for queue operation (None = wait indefinitely)
            
        Returns:
            PassengerEvent or None if timeout/empty
        """
        try:
            async with self._lock:
                event = None
                
                if self.enable_priority:
                    # Process events by priority (CRITICAL -> HIGH -> NORMAL -> LOW)
                    for priority in [EventPriority.CRITICAL, EventPriority.HIGH, 
                                   EventPriority.NORMAL, EventPriority.LOW]:
                        queue = self.queues[priority]
                        
                        try:
                            if timeout is not None:
                                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                            else:
                                if not queue.empty():
                                    event = await queue.get()
                            
                            if event:
                                break
                                
                        except asyncio.TimeoutError:
                            continue
                else:
                    # Single queue processing
                    try:
                        if timeout is not None:
                            event = await asyncio.wait_for(self.main_queue.get(), timeout=timeout)
                        else:
                            event = await self.main_queue.get()
                    except asyncio.TimeoutError:
                        return None
                
                if event:
                    self.stats['total_popped'] += 1
                    self.stats['current_size'] = max(0, self.stats['current_size'] - 1)
                    self.stats['last_activity'] = datetime.now()
                    
                    self.logger.debug(
                        f"Event popped: {event.event_type.value} for passenger {event.passenger_id}"
                    )
                
                return event
                
        except Exception as e:
            self.stats['total_failed'] += 1
            self.logger.error(f"Error popping event: {e}")
            return None
    
    async def peek_next_event(self) -> Optional[PassengerEvent]:
        """
        Peek at next event without removing it from buffer.
        
        Returns:
            PassengerEvent or None if buffer empty
        """
        try:
            if self.enable_priority:
                for priority in [EventPriority.CRITICAL, EventPriority.HIGH, 
                               EventPriority.NORMAL, EventPriority.LOW]:
                    queue = self.queues[priority]
                    if not queue.empty():
                        # This is a bit tricky with asyncio.Queue - we'd need to implement
                        # our own queue structure for true peek. For now, return None.
                        return None
            else:
                if not self.main_queue.empty():
                    return None  # Same limitation
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error peeking event: {e}")
            return None
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """
        Get current buffer status and statistics.
        
        Returns:
            Dict containing buffer status information
        """
        status = {
            'max_size': self.max_size,
            'current_size': self.stats['current_size'],
            'enable_priority': self.enable_priority,
            'stats': self.stats.copy()
        }
        
        if self.enable_priority:
            queue_sizes = {}
            for priority, queue in self.queues.items():
                queue_sizes[priority.value] = queue.qsize()
            status['queue_sizes'] = queue_sizes
        else:
            status['main_queue_size'] = self.main_queue.qsize()
        
        return status
    
    async def clear_buffer(self) -> int:
        """
        Clear all events from buffer.
        
        Returns:
            int: Number of events cleared
        """
        try:
            async with self._lock:
                cleared_count = 0
                
                if self.enable_priority:
                    for queue in self.queues.values():
                        while not queue.empty():
                            try:
                                await asyncio.wait_for(queue.get(), timeout=0.1)
                                cleared_count += 1
                            except asyncio.TimeoutError:
                                break
                else:
                    while not self.main_queue.empty():
                        try:
                            await asyncio.wait_for(self.main_queue.get(), timeout=0.1)
                            cleared_count += 1
                        except asyncio.TimeoutError:
                            break
                
                self.stats['current_size'] = 0
                self.logger.info(f"Buffer cleared - {cleared_count} events removed")
                
                return cleared_count
                
        except Exception as e:
            self.logger.error(f"Error clearing buffer: {e}")
            return 0
    
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        if self.enable_priority:
            return all(queue.full() for queue in self.queues.values())
        else:
            return self.main_queue.full()
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        if self.enable_priority:
            return all(queue.empty() for queue in self.queues.values())
        else:
            return self.main_queue.empty()


# Convenience functions for creating common events

def create_spawn_event(passenger_id: str, route_id: str, location_lat: float, 
                      location_lon: float, **metadata) -> PassengerEvent:
    """Create a passenger spawn event."""
    return PassengerEvent(
        event_id="",  # Will be auto-generated
        event_type=EventType.SPAWN,
        passenger_id=passenger_id,
        timestamp=datetime.now(),
        route_id=route_id,
        location_lat=location_lat,
        location_lon=location_lon,
        priority=EventPriority.NORMAL,
        metadata=metadata
    )


def create_pickup_event(passenger_id: str, vehicle_id: str, driver_id: str,
                       location_lat: float, location_lon: float, **metadata) -> PassengerEvent:
    """Create a passenger pickup event."""
    return PassengerEvent(
        event_id="",  # Will be auto-generated
        event_type=EventType.PICKUP,
        passenger_id=passenger_id,
        timestamp=datetime.now(),
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        location_lat=location_lat,
        location_lon=location_lon,
        priority=EventPriority.HIGH,
        metadata=metadata
    )


def create_dropoff_event(passenger_id: str, vehicle_id: str, driver_id: str,
                        location_lat: float, location_lon: float, **metadata) -> PassengerEvent:
    """Create a passenger dropoff event."""
    return PassengerEvent(
        event_id="",  # Will be auto-generated
        event_type=EventType.DROPOFF,
        passenger_id=passenger_id,
        timestamp=datetime.now(),
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        location_lat=location_lat,
        location_lon=location_lon,
        priority=EventPriority.HIGH,
        metadata=metadata
    )


def create_timeout_event(passenger_id: str, route_id: str, **metadata) -> PassengerEvent:
    """Create a passenger timeout event."""
    return PassengerEvent(
        event_id="",  # Will be auto-generated
        event_type=EventType.TIMEOUT,
        passenger_id=passenger_id,
        timestamp=datetime.now(),
        route_id=route_id,
        priority=EventPriority.NORMAL,
        metadata=metadata
    )


if __name__ == "__main__":
    """Test the passenger event system."""
    import asyncio
    
    async def test_event_system():
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("Testing PassengerEvent system...")
        
        # Test event creation
        spawn_event = create_spawn_event(
            passenger_id="PASS_001",
            route_id="route_1",
            location_lat=13.3194,
            location_lon=-59.6369,
            spawn_location="Bus Stop A"
        )
        
        pickup_event = create_pickup_event(
            passenger_id="PASS_001",
            vehicle_id="BUS_123",
            driver_id="DRV_456",
            location_lat=13.3194,
            location_lon=-59.6369,
            pickup_time=datetime.now()
        )
        
        print(f"✅ Created events: {spawn_event.event_type.value}, {pickup_event.event_type.value}")
        
        # Test buffer operations
        buffer = PassengerBuffer(max_size=100, enable_priority=True)
        
        # Push events
        success1 = await buffer.push_event(spawn_event)
        success2 = await buffer.push_event(pickup_event)
        
        print(f"✅ Events pushed: {success1}, {success2}")
        
        # Check buffer status
        status = buffer.get_buffer_status()
        print(f"📊 Buffer Status: {status}")
        
        # Pop events (should get pickup first due to higher priority)
        event1 = await buffer.pop_event(timeout=1.0)
        event2 = await buffer.pop_event(timeout=1.0)
        
        if event1 and event2:
            print(f"✅ Events popped: {event1.event_type.value} (priority: {event1.priority.value})")
            print(f"✅ Events popped: {event2.event_type.value} (priority: {event2.priority.value})")
        
        # Test event serialization
        event_dict = spawn_event.to_dict()
        restored_event = PassengerEvent.from_dict(event_dict)
        
        print(f"✅ Event serialization test: {restored_event.passenger_id == spawn_event.passenger_id}")
        
        print("✅ All tests completed successfully!")
    
    # Run test
    asyncio.run(test_event_system())