"""Test the event bus in isolation."""

import asyncio
import logging
from arknet_transit_simulator.api.events import EventBus, EventType, Event

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def subscriber_task(name: str, queue: asyncio.Queue, max_events: int = 5):
    """Subscriber that receives events from the queue."""
    logger.info(f"[{name}] Subscriber started")
    count = 0
    
    while count < max_events:
        try:
            event: Event = await asyncio.wait_for(queue.get(), timeout=2.0)
            logger.info(f"[{name}] Received: {event.event_type.value} - {event.data}")
            count += 1
        except asyncio.TimeoutError:
            logger.info(f"[{name}] Timeout waiting for event")
            break
    
    logger.info(f"[{name}] Subscriber finished (received {count} events)")


async def emitter_task(event_bus: EventBus):
    """Emitter that sends events."""
    logger.info("[Emitter] Starting to emit events")
    
    # Emit different event types
    await event_bus.emit(EventType.ENGINE_STARTED, {"vehicle_id": "V001", "timestamp": "2025-11-05T10:00:00"})
    await asyncio.sleep(0.1)
    
    await event_bus.emit(EventType.POSITION_UPDATE, {"vehicle_id": "V001", "lat": 40.7128, "lon": -74.0060})
    await asyncio.sleep(0.1)
    
    await event_bus.emit(EventType.PASSENGER_BOARDED, {"vehicle_id": "V001", "passenger_id": "P123", "count": 1})
    await asyncio.sleep(0.1)
    
    await event_bus.emit(EventType.DRIVER_STATE_CHANGED, {"vehicle_id": "V001", "old_state": "IDLE", "new_state": "DRIVING"})
    await asyncio.sleep(0.1)
    
    await event_bus.emit(EventType.GPS_STARTED, {"vehicle_id": "V001"})
    await asyncio.sleep(0.1)
    
    logger.info("[Emitter] Finished emitting events")


async def main():
    """Test the event bus."""
    logger.info("=== Event Bus Test Starting ===")
    
    # Create event bus
    event_bus = EventBus(max_queue_size=100)
    
    # Create subscribers
    all_events_queue = event_bus.subscribe(event_type=None)  # Subscribe to all events
    engine_events_queue = event_bus.subscribe(event_type=EventType.ENGINE_STARTED)  # Specific event
    position_events_queue = event_bus.subscribe(event_type=EventType.POSITION_UPDATE)  # Specific event
    
    logger.info("Subscribers created")
    logger.info(f"Event bus stats: {event_bus.get_stats()}")
    
    # Start subscriber tasks
    sub1 = asyncio.create_task(subscriber_task("ALL_EVENTS", all_events_queue, max_events=5))
    sub2 = asyncio.create_task(subscriber_task("ENGINE_ONLY", engine_events_queue, max_events=1))
    sub3 = asyncio.create_task(subscriber_task("POSITION_ONLY", position_events_queue, max_events=1))
    
    # Start emitter task
    emitter = asyncio.create_task(emitter_task(event_bus))
    
    # Wait for all tasks to complete
    await asyncio.gather(sub1, sub2, sub3, emitter)
    
    logger.info("=== Event Bus Test Complete ===")
    logger.info(f"Final stats: {event_bus.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
