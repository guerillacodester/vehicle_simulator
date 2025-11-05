"""Non-blocking event bus using asyncio.Queue for pub/sub pattern."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from dataclasses import dataclass, field

from .event_types import EventType


logger = logging.getLogger(__name__)


@dataclass
class Event:
    """An event with type, data, and metadata."""
    
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class EventBus:
    """
    Non-blocking event bus using asyncio.Queue.
    
    Subscribers receive events asynchronously without blocking the emitter.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize event bus.
        
        Args:
            max_queue_size: Maximum events to queue per subscriber
        """
        self._subscribers: Dict[EventType, List[asyncio.Queue]] = {}
        self._all_subscribers: List[asyncio.Queue] = []
        self._max_queue_size = max_queue_size
        logger.info("EventBus initialized with max_queue_size=%d", max_queue_size)
    
    def subscribe(self, event_type: EventType | None = None) -> asyncio.Queue:
        """
        Subscribe to events.
        
        Args:
            event_type: Specific event type to subscribe to, or None for all events
            
        Returns:
            Queue that will receive Event objects
        """
        queue = asyncio.Queue(maxsize=self._max_queue_size)
        
        if event_type is None:
            # Subscribe to all events
            self._all_subscribers.append(queue)
            logger.info("New subscriber for ALL events (total all-subscribers: %d)", 
                       len(self._all_subscribers))
        else:
            # Subscribe to specific event type
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(queue)
            logger.info("New subscriber for %s (total subscribers: %d)", 
                       event_type.value, len(self._subscribers[event_type]))
        
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """
        Unsubscribe a queue from all events.
        
        Args:
            queue: The queue to unsubscribe
        """
        # Remove from all-subscribers
        if queue in self._all_subscribers:
            self._all_subscribers.remove(queue)
            logger.info("Unsubscribed from ALL events")
        
        # Remove from specific event subscribers
        for event_type, queues in self._subscribers.items():
            if queue in queues:
                queues.remove(queue)
                logger.info("Unsubscribed from %s", event_type.value)
    
    async def emit(self, event_type: EventType, data: Dict[str, Any]):
        """
        Emit an event to all subscribers (non-blocking).
        
        Args:
            event_type: Type of event
            data: Event data payload
        """
        event = Event(event_type=event_type, data=data)
        
        # Collect all queues that should receive this event
        target_queues = []
        
        # Add specific subscribers
        if event_type in self._subscribers:
            target_queues.extend(self._subscribers[event_type])
        
        # Add all-event subscribers
        target_queues.extend(self._all_subscribers)
        
        if not target_queues:
            # No subscribers, nothing to do
            return
        
        logger.debug("Emitting %s to %d subscribers", event_type.value, len(target_queues))
        
        # Put event in all queues (non-blocking)
        for queue in target_queues:
            try:
                # Use put_nowait to avoid blocking
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Queue full for %s, dropping event", event_type.value)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the event bus."""
        return {
            "all_subscribers": len(self._all_subscribers),
            "type_subscribers": {
                event_type.value: len(queues) 
                for event_type, queues in self._subscribers.items()
            },
            "max_queue_size": self._max_queue_size
        }


# Global event bus instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
