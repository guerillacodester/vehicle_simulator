# Conductor → Commuter Service Access Mechanism

## 🎯 The Question

**"How does the Conductor access passengers from the Commuter Service?"

---

## 📡 Answer: Socket.IO Event-Driven Query/Response Pattern

The Conductor **doesn't directly call** the Commuter Service. Instead, it uses **Socket.IO real-time messaging** to send queries and receive responses.

**Think of it like:** Walkie-talkie communication instead of phone calls

---

## 🔄 The Complete Flow (Step-by-Step)

### Architecture Overview

```text
┌─────────────────┐           ┌──────────────────┐           ┌─────────────────┐
│   CONDUCTOR     │           │  STRAPI HUB      │           │ DEPOT RESERVOIR │
│  (Vehicle)      │◄─────────►│  (Socket.IO)     │◄─────────►│ (Commuter Svc)  │
│                 │  Events   │                  │  Events   │                 │
│  Python/Node    │           │  Node.js         │           │  Python         │
└─────────────────┘           └──────────────────┘           └─────────────────┘
```

**Key Point:** Strapi acts as the **message broker** between Conductor and Reservoirs

---

## 📋 Mechanism Breakdown

### 1. Connection Setup (Initialization)

**Conductor Side (Vehicle):**

```python
# File: vehicle/conductor.py (hypothetical)

from commuter_service.socketio_client import create_depot_client, create_route_client

class VehicleConductor:
    def __init__(self, vehicle, socketio_url: str = "http://localhost:1337"):
        self.vehicle = vehicle
        
        # Connect to Socket.IO namespaces
        self.depot_client = create_depot_client(socketio_url)
        self.route_client = create_route_client(socketio_url)
    
    async def start(self):
        """Start conductor and connect to commuter services"""
        await self.depot_client.connect()
        await self.route_client.connect()
        
        print(f"✅ Conductor connected to commuter services")
```

**What happens:**

- Conductor creates Socket.IO clients for `/depot-reservoir` and `/route-reservoir` namespaces
- Clients connect to Strapi Socket.IO hub at port 1337
- Connection established, ready to send/receive messages

---

### 2. Querying Depot Commuters

**Conductor Sends Query:**

```python
async def query_depot_commuters(self, depot_id: str, route_id: str):
    """Query depot reservoir for available commuters"""
    
    # Build query message
    query = {
        "depot_id": depot_id,
        "route_id": route_id,
        "vehicle_location": {
            "lat": self.vehicle.latitude,
            "lon": self.vehicle.longitude
        },
        "search_radius": 500,         # 500m radius
        "available_seats": 30,        # Vehicle capacity
        "correlationId": f"query_{uuid.uuid4()}"  # For tracking response
    }
    
    # Emit query event to depot-reservoir namespace
    await self.depot_client.emit_message(
        event_type="vehicle:query_commuters",
        data=query
    )
    
    print(f"📤 Sent query to depot reservoir")
```

**Message Flow:**

```text
Conductor → Socket.IO Client → Strapi Hub → Depot Reservoir
          (Python)              (Node.js)    (Python)
```

---

### 3. Depot Reservoir Receives Query

**Depot Reservoir Event Handler:**

```python
# File: commuter_service/depot_reservoir.py

def _register_handlers(self):
    """Register Socket.IO event handlers"""
    
    async def handle_vehicle_query(message: Dict):
        """Handle vehicle query for commuters"""
        data = message.get("data", {})
        
        # Extract query parameters
        depot_id = data.get("depot_id")
        route_id = data.get("route_id")
        vehicle_location = data.get("vehicle_location", {})
        vehicle_lat = vehicle_location.get("lat")
        vehicle_lon = vehicle_location.get("lon")
        max_distance = data.get("search_radius", 1000)
        max_count = data.get("available_seats", 30)
        
        # Validate
        if not all([depot_id, route_id, vehicle_lat, vehicle_lon]):
            self.logger.warning(f"Invalid vehicle query: {data}")
            return
        
        # Query internal data structure (FIFO queue)
        commuters = self.query_commuters_sync(
            depot_id=depot_id,
            route_id=route_id,
            vehicle_location=(vehicle_lat, vehicle_lon),
            max_distance=max_distance,
            max_count=max_count
        )
        
        # Send response back
        await self._send_query_response(
            commuters,
            message.get("correlationId"),
            message.get("source")
        )
    
    # Register the handler
    self.client.on("vehicle:query_commuters", handle_vehicle_query)
```

**What happens:**

1. Depot Reservoir listens for `vehicle:query_commuters` events
2. When query arrives, it extracts parameters
3. Searches internal FIFO queue for matching commuters
4. Filters by distance (proximity check)
5. Returns up to `max_count` commuters

---

### 4. Depot Reservoir Sends Response

**Response Builder:**

```python
async def _send_query_response(
    self,
    commuters: List[LocationAwareCommuter],
    correlation_id: Optional[str],
    target: Optional[str]
):
    """Send query response via Socket.IO"""
    if not self.client:
        return
    
    # Convert commuters to JSON-serializable format
    commuter_data = [
        {
            "commuter_id": c.commuter_id,
            "current_location": {
                "lat": c.current_location[0],
                "lon": c.current_location[1]
            },
            "destination": {
                "lat": c.destination_position[0],
                "lon": c.destination_position[1]
            },
            "direction": c.direction.value,
            "priority": c.priority,
            "max_walking_distance": c.max_walking_distance_m,
            "spawn_time": c.spawn_time.isoformat(),
        }
        for c in commuters
    ]
    
    # Emit response event
    await self.client.emit_message(
        EventTypes.COMMUTERS_FOUND,  # "vehicle:commuters_found"
        {
            "commuters": commuter_data,
            "total_count": len(commuters),
            "depot_id": self.depot_id,
            "route_id": self.route_id
        },
        correlation_id=correlation_id,
        target=target
    )
    
    self.logger.info(f"📥 Sent {len(commuters)} commuters to vehicle")
```

**Message Flow:**

```text
Depot Reservoir → Strapi Hub → Socket.IO Client → Conductor
  (Python)         (Node.js)      (Python)         (Vehicle)
```

---

### 5. Conductor Receives Response

**Conductor Event Handler:**

```python
async def _setup_event_handlers(self):
    """Setup Socket.IO event handlers"""
    
    async def handle_commuters_found(message: Dict):
        """Handle commuters found response"""
        data = message.get("data", {})
        commuters = data.get("commuters", [])
        
        print(f"✅ Received {len(commuters)} commuters from depot")
        
        # Store for decision making
        self.available_commuters = commuters
        
        # Trigger boarding logic
        await self._process_boarding_candidates(commuters)
    
    # Register handler
    self.depot_client.on("vehicle:commuters_found", handle_commuters_found)
```

**What happens:**

1. Conductor listens for `vehicle:commuters_found` events
2. When response arrives, extracts commuter list
3. Stores commuters for decision making
4. Triggers boarding evaluation logic

---

## 🔄 Complete Query/Response Cycle

### Timeline View

```text
T=0s    Conductor: "I need commuters at Depot Bridgetown for Route 1A"
        ↓
T=0.01s Strapi Hub: Routes message to /depot-reservoir namespace
        ↓
T=0.02s Depot Reservoir: Receives query
        ↓
T=0.03s Depot Reservoir: Searches FIFO queue
        ↓
T=0.04s Depot Reservoir: Finds 15 commuters within 500m
        ↓
T=0.05s Depot Reservoir: Sends response with commuter data
        ↓
T=0.06s Strapi Hub: Routes response back to vehicle
        ↓
T=0.07s Conductor: Receives 15 commuters
        ↓
T=0.08s Conductor: Evaluates capacity (30 seats available)
        ↓
T=0.09s Conductor: Decides to board all 15
        ↓
T=0.10s Conductor: Tells Driver to stop
```

**Total latency:** ~100ms (real-time!)

---

## 📊 Data Structures

### Query Message Format

```json
{
  "id": "msg_1234567890",
  "type": "vehicle:query_commuters",
  "timestamp": "2025-10-03T14:30:00Z",
  "source": "vehicle-conductor",
  "data": {
    "depot_id": "DEPOT_BRIDGETOWN",
    "route_id": "ROUTE_1A",
    "vehicle_location": {
      "lat": 13.0969,
      "lon": -59.6202
    },
    "search_radius": 500,
    "available_seats": 30
  },
  "correlationId": "query_abc-123-def",
  "target": null
}
```

### Response Message Format

```json
{
  "id": "msg_0987654321",
  "type": "vehicle:commuters_found",
  "timestamp": "2025-10-03T14:30:00.050Z",
  "source": "depot-reservoir",
  "data": {
    "commuters": [
      {
        "commuter_id": "COM_12345",
        "current_location": {
          "lat": 13.0970,
          "lon": -59.6203
        },
        "destination": {
          "lat": 13.1939,
          "lon": -59.5342
        },
        "direction": "outbound",
        "priority": 3,
        "max_walking_distance": 100,
        "spawn_time": "2025-10-03T14:25:00Z"
      },
      {
        "commuter_id": "COM_12346",
        "current_location": {
          "lat": 13.0971,
          "lon": -59.6204
        },
        "destination": {
          "lat": 13.1500,
          "lon": -59.5500
        },
        "direction": "outbound",
        "priority": 2,
        "max_walking_distance": 150,
        "spawn_time": "2025-10-03T14:26:00Z"
      }
    ],
    "total_count": 2,
    "depot_id": "DEPOT_BRIDGETOWN",
    "route_id": "ROUTE_1A"
  },
  "correlationId": "query_abc-123-def",
  "target": "vehicle-conductor"
}
```

---

## 🎯 Route Reservoir (Same Pattern)

### Query Route Commuters

```python
async def query_route_commuters(self):
    """Query route reservoir for commuters along route"""
    
    query = {
        "route_id": "ROUTE_1A",
        "vehicle_location": {
            "lat": self.vehicle.latitude,
            "lon": self.vehicle.longitude
        },
        "direction": "outbound",      # Match vehicle direction
        "search_radius": 1000,        # 1km lookahead
        "available_seats": 5,         # Remaining capacity
        "correlationId": f"query_{uuid.uuid4()}"
    }
    
    # Send to route-reservoir namespace
    await self.route_client.emit_message(
        event_type="vehicle:query_commuters",
        data=query
    )
```

**Same mechanism, different namespace!**

---

## 🔐 Why This Architecture?

### Benefits

**1. Decoupling

- Conductor and Reservoir don't need to know each other's implementation
- Can be written in different languages (Python, Node.js, etc.)
- Easy to swap implementations

**2. Scalability

- Multiple conductors can query simultaneously
- Strapi hub handles routing and load balancing
- Easy to add more reservoir instances

**3. Real-time

- Sub-100ms latency
- Event-driven (no polling)
- Bidirectional communication

**4. Reliability

- Message persistence (optional)
- Automatic reconnection
- Error handling built-in

**5. Observability

- All messages logged
- Easy to debug
- Can monitor event flow

---

## 🛠️ Implementation Details

### Socket.IO Client (Python Side)

```python
# File: commuter_service/socketio_client.py

class SocketIOClient:
    """Socket.IO client for Python services"""
    
    def __init__(self, url: str, namespace: str, service_type: ServiceType):
        self.url = url
        self.namespace = namespace
        self.service_type = service_type
        self.sio = socketio.AsyncClient(logger=True, engineio_logger=False)
        self.event_handlers: Dict[str, Callable] = {}
        self.connected = False
    
    async def connect(self):
        """Connect to Socket.IO server"""
        await self.sio.connect(
            self.url,
            namespaces=[self.namespace],
            transports=['websocket', 'polling']
        )
        self.connected = True
        print(f"✅ Connected to {self.url}{self.namespace}")
    
    async def emit_message(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        target: Optional[str] = None
    ):
        """Emit a message to the server"""
        message = SocketIOMessage(
            id=f"msg_{uuid.uuid4()}",
            type=event_type,
            timestamp=datetime.now().isoformat(),
            source=self.service_type.value,
            data=data,
            correlationId=correlation_id,
            target=target
        )
        
        await self.sio.emit('message', message.to_dict(), namespace=self.namespace)
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        async def wrapper(message: Dict):
            if message.get('type') == event_type:
                await handler(message)
        
        self.sio.on('message', wrapper, namespace=self.namespace)
```

### Convenience Functions

```python
def create_depot_client(url: str = "http://localhost:1337") -> SocketIOClient:
    """Create client for depot reservoir"""
    return SocketIOClient(url, "/depot-reservoir", ServiceType.VEHICLE_CONDUCTOR)

def create_route_client(url: str = "http://localhost:1337") -> SocketIOClient:
    """Create client for route reservoir"""
    return SocketIOClient(url, "/route-reservoir", ServiceType.VEHICLE_CONDUCTOR)
```

---

## 📝 Conductor Complete Example

```python
class VehicleConductor:
    def __init__(self, vehicle, socketio_url: str = "http://localhost:1337"):
        self.vehicle = vehicle
        self.depot_client = create_depot_client(socketio_url)
        self.route_client = create_route_client(socketio_url)
        self.available_commuters = []
    
    async def start(self):
        """Start conductor"""
        # Connect to services
        await self.depot_client.connect()
        await self.route_client.connect()
        
        # Setup event handlers
        self.depot_client.on("vehicle:commuters_found", self._handle_depot_response)
        self.route_client.on("vehicle:commuters_found", self._handle_route_response)
        
        # Start main loop
        await self._conductor_loop()
    
    async def _conductor_loop(self):
        """Main conductor logic"""
        while self.running:
            # Check if at depot
            if self.is_at_depot():
                await self._query_depot()
            else:
                await self._query_route()
            
            await asyncio.sleep(1)
    
    async def _query_depot(self):
        """Query depot for commuters"""
        await self.depot_client.emit_message(
            "vehicle:query_commuters",
            {
                "depot_id": self.current_depot,
                "route_id": self.vehicle.route_id,
                "vehicle_location": {
                    "lat": self.vehicle.latitude,
                    "lon": self.vehicle.longitude
                },
                "search_radius": 500,
                "available_seats": self.vehicle.capacity - len(self.vehicle.passengers)
            }
        )
    
    async def _query_route(self):
        """Query route for commuters"""
        await self.route_client.emit_message(
            "vehicle:query_commuters",
            {
                "route_id": self.vehicle.route_id,
                "vehicle_location": {
                    "lat": self.vehicle.latitude,
                    "lon": self.vehicle.longitude
                },
                "direction": self.vehicle.direction,
                "search_radius": 1000,
                "available_seats": self.vehicle.capacity - len(self.vehicle.passengers)
            }
        )
    
    async def _handle_depot_response(self, message: Dict):
        """Handle depot commuters response"""
        commuters = message.get("data", {}).get("commuters", [])
        
        if commuters:
            # Tell driver to stop
            await self.driver.stop_vehicle()
            
            # Board commuters
            for commuter in commuters:
                await self.board_commuter(commuter)
                await self.notify_picked_up(commuter["commuter_id"])
            
            # Resume
            await self.driver.resume_vehicle()
    
    async def _handle_route_response(self, message: Dict):
        """Handle route commuters response"""
        commuters = message.get("data", {}).get("commuters", [])
        
        if commuters:
            # Evaluate closest commuter
            nearest = commuters[0]
            distance = self.calculate_distance(nearest["current_location"])
            
            if distance < 200:  # Within 200m
                await self.pickup_route_commuter(nearest)
    
    async def notify_picked_up(self, commuter_id: str):
        """Notify reservoir of pickup"""
        await self.depot_client.emit_message(
            "commuter:picked_up",
            {
                "commuter_id": commuter_id,
                "vehicle_id": self.vehicle.id
            }
        )
```

---

## 🎯 Summary

### The Mechanism is

**Event-Driven Query/Response via Socket.IO

1. **Conductor** emits `vehicle:query_commuters` event
2. **Strapi Hub** routes to appropriate namespace
3. **Reservoir** receives event, queries internal data
4. **Reservoir** emits `vehicle:commuters_found` response
5. **Strapi Hub** routes back to conductor
6. **Conductor** receives commuters, makes decisions

**No direct function calls, no REST API polling—pure real-time events!**

---

## 🔑 Key Takeaways

- ✅ **Socket.IO** = Real-time bidirectional communication
- ✅ **Namespaces** = Separate channels (depot, route, vehicle)
- ✅ **Events** = `vehicle:query_commuters`, `vehicle:commuters_found`, `commuter:picked_up`
- ✅ **Strapi Hub** = Central message broker
- ✅ **Decoupled** = Conductor and Reservoir don't directly call each other
- ✅ **Fast** = Sub-100ms latency
- ✅ **Scalable** = Multiple vehicles can query simultaneously

**It's like a smart postal service for real-time vehicle-passenger coordination!** 📬🚌
