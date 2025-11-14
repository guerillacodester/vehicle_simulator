"""Simple runtime test for the EventBus."""

import asyncio
import logging

from arknet_transit_simulator.api.events.event_bus import get_event_bus
from arknet_transit_simulator.api.events.event_types import EventType


async def producer(bus):
    # Emit two events with a small pause
    await bus.emit(EventType.POSITION_UPDATE, {"vehicle_id": "veh1", "lat": 1.0, "lon": 2.0})
    await asyncio.sleep(0.05)
    await bus.emit(EventType.PASSENGER_BOARDED, {"vehicle_id": "veh1", "passenger_id": "p1"})


async def consumer(bus):
    q = bus.subscribe()  # subscribe to all events
    received = []
    for _ in range(2):
        ev = await asyncio.wait_for(q.get(), timeout=2.0)
        print("Received:", ev.to_dict())
        received.append(ev)

    types = [r.event_type for r in received]
    assert EventType.POSITION_UPDATE in types, "Missing position update"
    assert EventType.PASSENGER_BOARDED in types, "Missing passenger boarded"
    print("Test passed")


async def main():
    logging.basicConfig(level=logging.INFO)
    bus = get_event_bus()
    # Run consumer and producer concurrently
    await asyncio.gather(consumer(bus), producer(bus))


if __name__ == "__main__":
    asyncio.run(main())
