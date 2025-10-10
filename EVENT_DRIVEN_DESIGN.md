# 🎯 Event-Driven Conductor Design

**Date:** October 10, 2025  
**Topic:** Event Triggering Mechanism for Conductor Actions

---

## Design Question

**How should we trigger the conductor to perform their job?**

Options:
1. **Event Subscription (Pub/Sub)**
2. **Polling**
3. **Direct Method Calls**
4. **State Machine with Callbacks**

---

## ✅ RECOMMENDED: Event-Driven Pub/Sub Architecture

### Why This Is Best:

1. **Decoupling** - Conductor doesn't need to know about vehicle, depot, or queue internals
2. **Scalability** - Multiple conductors can subscribe to same events
3. **Testability** - Easy to mock events and test conductor reactions
4. **Auditability** - All events can be logged for debugging
5. **Real-time** - Socket.IO already in place for real-time updates
6. **Flexibility** - Easy to add new event handlers without changing existing code

### Architecture Pattern: Event Bus + Socket.IO

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Vehicle   │────────▶│  Event Bus   │────────▶│  Conductor  │
│   Service   │ publish │              │subscribe│   Service   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ├──────────▶ Socket.IO (real-time)
                              ├──────────▶ Event Log (audit)
                              └──────────▶ Analytics (metrics)
```

---

## Implementation Design

### 1. Event Bus (Central Event Manager)

```python
# event_bus.py

from typing import Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio


class EventType(Enum):
    """All possible events in the system"""
    # Vehicle events
    VEHICLE_ENTERED_DEPOT = "vehicle.entered_depot"
    VEHICLE_FIRST_IN_QUEUE = "vehicle.first_in_queue"
    VEHICLE_BOARDING_ELIGIBLE = "vehicle.boarding_eligible"
    VEHICLE_BOARDING_STARTED = "vehicle.boarding_started"
    VEHICLE_BOARDING_COMPLETE = "vehicle.boarding_complete"
    VEHICLE_DEPARTED = "vehicle.departed"
    VEHICLE_ARRIVED_AT_STOP = "vehicle.arrived_at_stop"
    
    # Conductor events
    CONDUCTOR_ASSIGNED = "conductor.assigned"
    CONDUCTOR_STARTED_BOARDING = "conductor.started_boarding"
    CONDUCTOR_PASSENGER_BOARDED = "conductor.passenger_boarded"
    CONDUCTOR_DOORS_CLOSED = "conductor.doors_closed"
    
    # Passenger events
    PASSENGER_SPAWNED = "passenger.spawned"
    PASSENGER_WAITING = "passenger.waiting"
    PASSENGER_BOARDED = "passenger.boarded"
    PASSENGER_ALIGHTED = "passenger.alighted"


@dataclass
class Event:
    """Base event structure"""
    event_type: EventType
    timestamp: datetime
    data: Dict
    source: str
    
    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'source': self.source
        }


class EventBus:
    """
    Central event bus for pub/sub pattern
    
    Usage:
        # Initialize
        bus = EventBus()
        
        # Subscribe
        bus.subscribe(EventType.VEHICLE_BOARDING_ELIGIBLE, conductor.on_boarding_eligible)
        
        # Publish
        bus.publish(Event(
            event_type=EventType.VEHICLE_BOARDING_ELIGIBLE,
            timestamp=datetime.now(),
            data={'vehicle_id': 'vehicle_123', 'depot_id': 'BGI_CHEAPSIDE_03'},
            source='VehicleService'
        ))
    """
    
    def __init__(self):
        # Subscribers: EventType -> List[Callable]
        self._subscribers: Dict[EventType, List[Callable]] = {}
        
        # Event history (for debugging/audit)
        self._event_history: List[Event] = []
        self._max_history = 1000
        
        # Statistics
        self._event_counts: Dict[EventType, int] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to listen for
            handler: Async or sync function to call when event occurs
                     Signature: handler(event: Event) -> None
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        print(f"📡 Subscribed {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Remove a subscription"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish event asynchronously
        
        Args:
            event: Event to publish
        """
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Update statistics
        if event.event_type not in self._event_counts:
            self._event_counts[event.event_type] = 0
        self._event_counts[event.event_type] += 1
        
        # Call all subscribers
        if event.event_type in self._subscribers:
            tasks = []
            for handler in self._subscribers[event.event_type]:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    # Wrap sync function in async
                    tasks.append(asyncio.to_thread(handler, event))
            
            # Execute all handlers concurrently
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def publish(self, event: Event) -> None:
        """
        Publish event synchronously (creates task if in async context)
        
        Args:
            event: Event to publish
        """
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.publish_async(event))
        except RuntimeError:
            # No event loop, run synchronously
            asyncio.run(self.publish_async(event))
    
    def get_event_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get recent event history"""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type][-limit:]
        return self._event_history[-limit:]
    
    def get_statistics(self) -> Dict[str, int]:
        """Get event counts"""
        return {k.value: v for k, v in self._event_counts.items()}


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    return _event_bus
```

---

### 2. Conductor Event Handlers

```python
# conductor_service.py

from event_bus import get_event_bus, Event, EventType
from location_service import LocationService
from datetime import datetime


class ConductorService:
    """
    Conductor service that reacts to events
    
    The conductor is EVENT-DRIVEN:
    - Listens for VEHICLE_BOARDING_ELIGIBLE event
    - Automatically starts boarding process
    - Emits events when passengers board
    """
    
    def __init__(self, conductor_id: str, vehicle_id: str):
        self.conductor_id = conductor_id
        self.vehicle_id = vehicle_id
        self.is_boarding = False
        self.passengers = []
        
        # Subscribe to events
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Register event handlers"""
        bus = get_event_bus()
        
        # Listen for boarding eligibility
        bus.subscribe(
            EventType.VEHICLE_BOARDING_ELIGIBLE,
            self.on_boarding_eligible
        )
        
        # Listen for passenger arrivals
        bus.subscribe(
            EventType.PASSENGER_WAITING,
            self.on_passenger_waiting
        )
        
        print(f"🎫 Conductor {self.conductor_id} subscribed to events")
    
    async def on_boarding_eligible(self, event: Event):
        """
        Handler for VEHICLE_BOARDING_ELIGIBLE event
        
        Triggered when:
        - Vehicle is in assigned depot geofence
        - Vehicle is first in queue
        
        Action:
        - Start accepting passengers
        - Open doors
        - Emit CONDUCTOR_STARTED_BOARDING event
        """
        # Check if this event is for our vehicle
        if event.data.get('vehicle_id') != self.vehicle_id:
            return
        
        print(f"🚌 Conductor {self.conductor_id} received boarding eligible event")
        print(f"   Vehicle: {event.data['vehicle_id']}")
        print(f"   Depot: {event.data['depot_id']}")
        
        # Start boarding
        await self._start_boarding(event.data['depot_id'])
    
    async def _start_boarding(self, depot_id: str):
        """Start the boarding process"""
        if self.is_boarding:
            print(f"⚠️  Already boarding!")
            return
        
        self.is_boarding = True
        
        print(f"🚪 Opening doors at {depot_id}")
        print(f"👋 Conductor {self.conductor_id} ready to accept passengers")
        
        # Emit event
        bus = get_event_bus()
        bus.publish(Event(
            event_type=EventType.CONDUCTOR_STARTED_BOARDING,
            timestamp=datetime.now(),
            data={
                'conductor_id': self.conductor_id,
                'vehicle_id': self.vehicle_id,
                'depot_id': depot_id,
                'max_capacity': 14,
                'current_passengers': len(self.passengers)
            },
            source='ConductorService'
        ))
    
    async def on_passenger_waiting(self, event: Event):
        """
        Handler for PASSENGER_WAITING event
        
        Check if passenger wants to board this vehicle
        """
        if not self.is_boarding:
            return
        
        # Check if passenger is at our location
        passenger_id = event.data.get('passenger_id')
        passenger_destination = event.data.get('destination')
        
        # Check capacity
        if len(self.passengers) >= 14:
            print(f"🚫 Vehicle full, cannot board passenger {passenger_id}")
            return
        
        # Board the passenger
        await self._board_passenger(passenger_id, passenger_destination)
    
    async def _board_passenger(self, passenger_id: str, destination: str):
        """Board a passenger"""
        self.passengers.append({
            'id': passenger_id,
            'destination': destination,
            'boarded_at': datetime.now()
        })
        
        print(f"✅ Passenger {passenger_id} boarded ({len(self.passengers)}/14)")
        
        # Emit event
        bus = get_event_bus()
        bus.publish(Event(
            event_type=EventType.CONDUCTOR_PASSENGER_BOARDED,
            timestamp=datetime.now(),
            data={
                'conductor_id': self.conductor_id,
                'vehicle_id': self.vehicle_id,
                'passenger_id': passenger_id,
                'current_passengers': len(self.passengers),
                'max_capacity': 14
            },
            source='ConductorService'
        ))
        
        # Check if full
        if len(self.passengers) >= 14:
            await self._close_doors()
    
    async def _close_doors(self):
        """Close doors and signal ready to depart"""
        self.is_boarding = False
        
        print(f"🚪 Closing doors - {len(self.passengers)} passengers onboard")
        
        # Emit event
        bus = get_event_bus()
        bus.publish(Event(
            event_type=EventType.VEHICLE_BOARDING_COMPLETE,
            timestamp=datetime.now(),
            data={
                'vehicle_id': self.vehicle_id,
                'passenger_count': len(self.passengers)
            },
            source='ConductorService'
        ))
```

---

### 3. Vehicle Service (Event Publisher)

```python
# vehicle_service.py

from event_bus import get_event_bus, Event, EventType
from location_service import LocationService
from datetime import datetime


class VehicleService:
    """
    Vehicle service that publishes events
    
    Responsibilities:
    - Monitor vehicle location
    - Check queue position
    - Publish events when conditions change
    """
    
    def __init__(self, vehicle_id: str, assigned_depot_id: str):
        self.vehicle_id = vehicle_id
        self.assigned_depot_id = assigned_depot_id
        self.current_lat = None
        self.current_lon = None
        self.queue_position = None
        
        self.location_service = LocationService()
    
    async def update_location(self, lat: float, lon: float):
        """
        Update vehicle location and check for events
        
        This is called whenever GPS position changes
        """
        old_lat, old_lon = self.current_lat, self.current_lon
        self.current_lat = lat
        self.current_lon = lon
        
        # Check if entered depot
        was_in_depot = False
        if old_lat and old_lon:
            was_in_depot = self.location_service.is_vehicle_in_assigned_depot(
                self.vehicle_id, old_lat, old_lon
            )
        
        is_in_depot = self.location_service.is_vehicle_in_assigned_depot(
            self.vehicle_id, lat, lon
        )
        
        # Entered depot?
        if is_in_depot and not was_in_depot:
            await self._emit_entered_depot()
    
    async def _emit_entered_depot(self):
        """Emit event when vehicle enters depot"""
        bus = get_event_bus()
        bus.publish(Event(
            event_type=EventType.VEHICLE_ENTERED_DEPOT,
            timestamp=datetime.now(),
            data={
                'vehicle_id': self.vehicle_id,
                'depot_id': self.assigned_depot_id,
                'latitude': self.current_lat,
                'longitude': self.current_lon
            },
            source='VehicleService'
        ))
    
    async def update_queue_position(self, position: int):
        """
        Update queue position and check for boarding eligibility
        
        Called by QueueService when position changes
        """
        old_position = self.queue_position
        self.queue_position = position
        
        # Became first in queue?
        if position == 1 and old_position != 1:
            await self._check_boarding_eligibility()
    
    async def _check_boarding_eligibility(self):
        """Check if vehicle can start boarding"""
        # Must be in depot AND first in queue
        is_in_depot = self.location_service.is_vehicle_in_assigned_depot(
            self.vehicle_id,
            self.current_lat,
            self.current_lon
        )
        
        is_first = self.queue_position == 1
        
        if is_in_depot and is_first:
            await self._emit_boarding_eligible()
    
    async def _emit_boarding_eligible(self):
        """Emit event when vehicle becomes eligible to board"""
        bus = get_event_bus()
        bus.publish(Event(
            event_type=EventType.VEHICLE_BOARDING_ELIGIBLE,
            timestamp=datetime.now(),
            data={
                'vehicle_id': self.vehicle_id,
                'depot_id': self.assigned_depot_id,
                'queue_position': self.queue_position,
                'latitude': self.current_lat,
                'longitude': self.current_lon
            },
            source='VehicleService'
        ))
        
        print(f"✅ Vehicle {self.vehicle_id} is BOARDING ELIGIBLE")
```

---

## Event Flow Example

```
1. Vehicle arrives at depot
   └─▶ VehicleService.update_location(13.098, -59.621)
       └─▶ Detects: entered depot geofence
           └─▶ Publishes: VEHICLE_ENTERED_DEPOT event

2. Queue manager updates position
   └─▶ QueueService.vehicle_moved_to_first()
       └─▶ VehicleService.update_queue_position(1)
           └─▶ Checks: in depot? YES, first in queue? YES
               └─▶ Publishes: VEHICLE_BOARDING_ELIGIBLE event

3. Conductor receives event
   └─▶ ConductorService.on_boarding_eligible(event)
       └─▶ Opens doors, starts accepting passengers
           └─▶ Publishes: CONDUCTOR_STARTED_BOARDING event

4. Passenger arrives
   └─▶ PassengerService.spawn_at_depot()
       └─▶ Publishes: PASSENGER_WAITING event

5. Conductor receives passenger event
   └─▶ ConductorService.on_passenger_waiting(event)
       └─▶ Checks capacity, boards passenger
           └─▶ Publishes: CONDUCTOR_PASSENGER_BOARDED event

6. Vehicle becomes full
   └─▶ ConductorService._board_passenger()
       └─▶ Detects: 14/14 passengers
           └─▶ Closes doors
               └─▶ Publishes: VEHICLE_BOARDING_COMPLETE event
```

---

## Benefits Over Alternatives

### vs Polling
| Feature | Event-Driven | Polling |
|---------|-------------|---------|
| CPU Usage | Low (idle until event) | High (constant checks) |
| Latency | Instant | Depends on poll interval |
| Scalability | Excellent | Poor (N vehicles × M checks/sec) |
| Code Clarity | Clear event handlers | Messy if/else chains |

### vs Direct Method Calls
| Feature | Event-Driven | Direct Calls |
|---------|-------------|--------------|
| Coupling | Loose (pub/sub) | Tight (imports) |
| Testing | Easy (mock events) | Hard (mock objects) |
| Extensibility | Easy (add subscribers) | Hard (modify callers) |
| Auditability | Built-in (event log) | Manual logging |

### vs State Machine
| Feature | Event-Driven | State Machine |
|---------|-------------|---------------|
| Flexibility | Very flexible | Rigid states |
| Multi-actor | Easy (many subscribers) | Complex (nested states) |
| Debugging | Event history | State transitions |
| Learning Curve | Moderate | Steep |

---

## Socket.IO Integration

```python
# socketio_event_bridge.py

from event_bus import get_event_bus, Event, EventType
from socketio_service import get_socketio_instance


class SocketIOEventBridge:
    """
    Bridge between EventBus and Socket.IO
    
    Forwards events to connected clients
    """
    
    def __init__(self):
        self.sio = get_socketio_instance()
        self.bus = get_event_bus()
        
        # Subscribe to ALL events
        for event_type in EventType:
            self.bus.subscribe(event_type, self.forward_to_socketio)
    
    async def forward_to_socketio(self, event: Event):
        """Forward event to Socket.IO clients"""
        await self.sio.emit(
            event.event_type.value,
            event.to_dict()
        )
```

---

## Testing

```python
# test_event_driven_conductor.py

import pytest
from event_bus import EventBus, Event, EventType
from conductor_service import ConductorService
from datetime import datetime


@pytest.mark.asyncio
async def test_conductor_reacts_to_boarding_eligible():
    """Test that conductor starts boarding when eligible"""
    
    # Setup
    bus = EventBus()
    conductor = ConductorService('conductor_1', 'vehicle_123')
    
    # Emit boarding eligible event
    event = Event(
        event_type=EventType.VEHICLE_BOARDING_ELIGIBLE,
        timestamp=datetime.now(),
        data={
            'vehicle_id': 'vehicle_123',
            'depot_id': 'BGI_CHEAPSIDE_03',
            'queue_position': 1
        },
        source='Test'
    )
    
    await bus.publish_async(event)
    
    # Assert
    assert conductor.is_boarding == True
```

---

## Summary

✅ **RECOMMENDED: Event-Driven Pub/Sub Architecture**

**Advantages:**
- ✅ Decoupled components
- ✅ Scalable (multiple subscribers)
- ✅ Testable (mock events)
- ✅ Auditable (event history)
- ✅ Real-time (Socket.IO integration)
- ✅ Extensible (add handlers easily)

**Implementation:**
1. Central `EventBus` for pub/sub
2. `ConductorService` subscribes to events
3. `VehicleService` publishes events
4. Socket.IO bridge for real-time updates
5. Event history for debugging

This is the industry-standard pattern for event-driven systems! 🎯

