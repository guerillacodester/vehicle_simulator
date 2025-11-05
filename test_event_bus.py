"""Simple runtime test for the EventBus."""

import asyncio
import logging

from arknet_transit_simulator.api.events import get_event_bus, EventType


async def producer(bus):
    print("Producer: Emitting events...")
    await bus.emit(EventType.POSITION_UPDATE, {"vehicle_id": "veh1", "lat": 1.0, "lon": 2.0})
    await asyncio.sleep(0.05)
    await bus.emit(EventType.PASSENGER_BOARDED, {"vehicle_id": "veh1", "passenger_id": "p1"})
    print("Producer: Done emitting")


async def consumer(bus):
    print("Consumer: Subscribing to all events...")
    q = bus.subscribe()  # subscribe to all events
    received = []
    for i in range(2):
        ev = await asyncio.wait_for(q.get(), timeout=2.0)
        print(f"Consumer: Received event {i+1}: {ev.event_type.value}")
        received.append(ev)

    types = [r.event_type for r in received]
    assert EventType.POSITION_UPDATE in types, "Missing position update"
    assert EventType.PASSENGER_BOARDED in types, "Missing passenger boarded"
    print(" Test passed - EventBus works!")


async def main():
    logging.basicConfig(level=logging.INFO)
    bus = get_event_bus()
    # Run consumer and producer concurrently
    await asyncio.gather(consumer(bus), producer(bus))


if __name__ == "__main__":
    asyncio.run(main())
