# Commuter Service - Production-Grade Passenger Management

## 🎯 Overview

Complete passenger lifecycle management system with real-time state monitoring and WebSocket event streaming.

## ✨ Features

### 1. **Full CRUD API**
- List/search passengers with filtering
- Get single passenger details
- Create passengers manually
- Update passenger properties
- Board/alight passengers
- Cancel passengers
- Delete passengers

### 2. **State Machine**
- **WAITING**: Passenger spawned, waiting for pickup
- **BOARDED**: Passenger on vehicle
- **ALIGHTED**: Passenger completed journey (final state)
- **CANCELLED**: Passenger cancelled

State transitions are **timestamp-driven**:
- State calculated from `spawned_at`, `boarded_at`, `alighted_at` timestamps
- External processes can update timestamps
- Monitor detects changes in real-time

### 3. **Real-Time Monitoring**
- Polls Strapi every 2 seconds for changes
- Detects external updates (from vehicles, mobile apps, etc.)
- Broadcasts state changes via WebSocket
- Memory-efficient caching
- Automatic cleanup of old passengers

### 4. **WebSocket Events**
- `passenger:spawned` - New passenger created
- `passenger:boarded` - Passenger boarded vehicle
- `passenger:alighted` - Passenger completed journey
- `passenger:cancelled` - Passenger cancelled
- `passenger:state_changed` - Generic state change

## 🚀 Quick Start

### Start the Service

```powershell
python commuter_service/main.py
```

The service starts with:
- REST API on `http://localhost:4000`
- WebSocket on `ws://localhost:4000/ws/stream`
- Real-time monitor (2-second polling)

### Use the Client Console

```powershell
python clients/commuter/client_console.py
```

## 📋 API Endpoints

### Passenger CRUD

```http
GET    /api/passengers              # List passengers
GET    /api/passengers/{id}         # Get passenger
POST   /api/passengers              # Create passenger
PUT    /api/passengers/{id}          # Update passenger
PATCH  /api/passengers/{id}/board   # Board passenger
PATCH  /api/passengers/{id}/alight  # Alight passenger
PATCH  /api/passengers/{id}/cancel  # Cancel passenger
DELETE /api/passengers/{id}         # Delete passenger
```

### Monitoring

```http
GET /api/monitor/stats              # Get monitor statistics
```

### Seeding

```http
POST /api/seed                      # Seed passengers remotely
```

## 💻 Console Commands

### Connection
```
connect [url]              # Connect to service
disconnect                 # Disconnect
```

### Passenger Management
```
list [filters]             # List passengers
  list                     # All passengers
  list route 1             # Filter by route
  list status WAITING      # Filter by status
  list vehicle BUS_001     # Filter by vehicle

get <passenger_id>         # Get passenger details

board <id> <vehicle_id>    # Board passenger
  board PASS_ABC123 BUS_001

alight <id>                # Alight passenger
  alight PASS_ABC123

cancel <id>                # Cancel passenger
  cancel PASS_ABC123
```

### Seeding & Real-time
```
seed <route> <day> <hours> # Seed passengers
  seed 1 monday 7-9

subscribe <route>          # Subscribe to events
unsubscribe <route>        # Unsubscribe

monitor                    # Show monitor stats
```

## 🔄 State Transition Flow

```
     SPAWN
       ↓
   [WAITING] ──board──→ [BOARDED] ──alight──→ [ALIGHTED]
       │                     │                  (final)
       │                     │
       └─────cancel──────────┘
              ↓
         [CANCELLED]
```

### Valid Transitions
- WAITING → BOARDED
- WAITING → CANCELLED
- BOARDED → ALIGHTED
- BOARDED → CANCELLED
- CANCELLED → WAITING (resurrection)

### Invalid Transitions
- ALIGHTED → * (final state, no transitions allowed)
- Backwards transitions (except CANCELLED → WAITING)

## 📡 Real-Time Monitoring

### How it Works

1. **Client subscribes** to route via WebSocket:
   ```javascript
   {"type": "subscribe", "route": "1"}
   ```

2. **Monitor starts** tracking that route:
   - Polls Strapi every 2 seconds
   - Compares with cached state
   - Detects changes

3. **External update** (vehicle updates passenger):
   ```sql
   UPDATE active_passengers 
   SET boarded_at = '2024-11-04T08:30:00Z', 
       vehicle_id = 'BUS_001'
   WHERE passenger_id = 'PASS_ABC123'
   ```

4. **Monitor detects** change:
   - Compares timestamps
   - Calculates new state: WAITING → BOARDED
   - Emits event

5. **Client receives** real-time event:
   ```json
   {
     "type": "passenger:boarded",
     "data": {
       "passenger_id": "PASS_ABC123",
       "vehicle_id": "BUS_001",
       "boarded_at": "2024-11-04T08:30:00Z",
       "external_trigger": true
     }
   }
   ```

### Monitoring Statistics

```
commuter> monitor

PASSENGER MONITOR STATISTICS
================================================================================
Running:              ✅ Yes
Monitored Routes:     2
Cached Passengers:    47

State Transitions:    12
External Updates:     8
Total Changes:        20

Last Poll:            2024-11-04 15:23:45.123456
================================================================================
```

## 🧪 Testing

### 1. Test Manual Passenger Creation

```powershell
# Start service
python commuter_service/main.py

# In another terminal, use API directly
curl -X POST http://localhost:4000/api/passengers \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_id": "TEST_001",
    "route_id": "gg3pv3z19hhm117v9xth5ezq",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "destination_lat": 35.6895,
    "destination_lon": 139.6917
  }'
```

### 2. Test External State Changes

```powershell
# Start service with monitoring
python commuter_service/main.py

# Start console client and subscribe
python clients/commuter/client_console.py
> connect
> subscribe 1

# Manually update via Strapi Admin or direct DB
# Watch events stream in real-time!
```

### 3. Test Complete Lifecycle

```
commuter> connect
commuter> subscribe 1
commuter> seed 1 monday 7-7    # Seed 1 hour of passengers
commuter> list status WAITING
commuter> board PASS_ABC123 BUS_001
commuter> list status BOARDED
commuter> alight PASS_ABC123
commuter> get PASS_ABC123       # Verify state = ALIGHTED
```

## 🏗️ Architecture

```
┌─────────────────┐         HTTP/WS          ┌──────────────────┐
│  Client Console │ ◄─────────────────────► │ Commuter Service │
│                 │                          │                  │
│  - Management   │                          │  - CRUD API      │
│  - Monitoring   │                          │  - Monitor       │
│  - Real-time    │                          │  - WebSocket     │
└─────────────────┘                          └──────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │    Strapi    │
                                              │  (Database)  │
                                              └──────────────┘
                                                      ▲
                                                      │
                                              ┌──────────────┐
                                              │   Vehicles   │
                                              │  Mobile Apps │
                                              │   (External) │
                                              └──────────────┘
```

### Components

1. **Commuter Service** (Server)
   - FastAPI REST API
   - WebSocket server
   - Passenger state monitor (background task)
   - State machine validation

2. **Client Console** (Remote)
   - Connect to any service URL
   - Full passenger management
   - Real-time event streaming
   - Monitor statistics

3. **Strapi** (Database)
   - Source of truth for passenger data
   - Updated by service AND external processes
   - Polled by monitor for changes

4. **External Processes** (Vehicles, Apps)
   - Update passenger timestamps directly
   - Changes detected by monitor
   - Events broadcast to subscribers

## 📊 Production Considerations

### Performance
- **Polling interval**: 2 seconds (configurable)
- **Efficient queries**: Only fetch updated records
- **Memory usage**: Only cache active passengers
- **Auto cleanup**: Remove alighted passengers after 24 hours

### Scalability
- **Horizontal scaling**: Use Redis for shared state
- **Load balancing**: Multiple API instances
- **WebSocket clustering**: Use Redis Pub/Sub
- **Database**: Strapi handles concurrent updates

### Reliability
- **State validation**: Enforced transitions
- **Error handling**: Graceful degradation
- **Monitoring stats**: Health metrics
- **Graceful shutdown**: Clean resource cleanup

## 🔧 Configuration

Edit polling interval:

```python
# commuter_service/services/passenger_monitor.py
monitor = PassengerMonitor(
    strapi_url=config.infrastructure.strapi_url,
    poll_interval=1.0,        # 1 second polling (more responsive)
    cleanup_after_hours=12    # Clean up after 12 hours
)
```

## 🐛 Troubleshooting

### Monitor not detecting changes
- Check monitor is running: `commuter> monitor`
- Verify route is monitored (subscribe first)
- Check poll interval vs. update frequency

### WebSocket not connecting
- Verify service running on port 4000
- Check firewall settings
- Try `connect http://localhost:4000` explicitly

### State transition rejected
- Check current state: `commuter> get <id>`
- Review valid transitions (see State Machine section)
- Verify timestamps are set correctly

## 📚 Next Steps

1. **Redis Integration**: Shared cache for multi-instance deployments
2. **Push Notifications**: Real-time mobile app updates
3. **Analytics**: Passenger journey insights
4. **ML Integration**: Demand prediction, route optimization
5. **Load Testing**: Concurrent passenger management
