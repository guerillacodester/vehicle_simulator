# DEFINITIVE ARCHITECTURE - Passenger Spawning System

## Overview

Database-centric architecture with Socket.IO for real-time notifications only.

## Components

### 1. Database (Strapi PostgreSQL)

- **Single source of truth** for all passenger data
- Stores: passenger_id, route_id, location, destination, status, timestamps
- Accessed via Strapi REST API

### 2. Commuter Service (Python)

- **Depot Reservoir**: Spawns outbound passengers at depots
- **Route Reservoir**: Spawns bidirectional passengers along routes
- **Automatic spawning**: Poisson-based probability, no external triggers
- **Writes to DB**: Every spawn creates database record
- **Emits events**: Socket.IO notifications (IDs only, no data payload)

### 3. Socket.IO Server (Strapi)

- **Notification-only pub/sub**
- Events emitted:
  - `COMMUTER_SPAWNED` → `{passenger_id, route_id}`
  - `COMMUTER_PICKED_UP` → `{passenger_id}`
- Events received:
  - `QUERY_COMMUTERS` → Deprecated (use REST API instead)

### 4. Actors (Vehicles, Visualization)

- **Read from database**: Query `/api/active-passengers`
- **Listen to Socket.IO**: Get notified of changes, then query DB
- **Never write directly**: Updates go through Strapi API

## Data Flow

### Spawning Flow

```text
1. Reservoir (background task)
   ↓
2. Generate passenger (PoissonGeoJSONSpawner)
   ↓
3. Write to database (POST /api/active-passengers)
   ↓
4. Emit Socket.IO event ({passenger_id})
   ↓
5. Subscribers receive notification
   ↓
6. Subscribers query DB for details (GET /api/active-passengers/:id)
```

### Pickup Flow

```text
1. Vehicle detects nearby passenger (GET /api/active-passengers/near-location)
   ↓
2. Vehicle picks up passenger
   ↓
3. Vehicle updates status (POST /api/active-passengers/mark-boarded/:id)
   ↓
4. Strapi updates database
   ↓
5. Socket.IO emits COMMUTER_PICKED_UP event
   ↓
6. Subscribers receive notification
   ↓
7. Visualization refreshes display
```

## API Endpoints

### Read Operations

- `GET /api/active-passengers` - List all active passengers
- `GET /api/active-passengers/:id` - Get passenger details
- `GET /api/active-passengers/near-location?lat=X&lon=Y&radius=Z` - Spatial query
- `GET /api/active-passengers/by-route/:routeId` - Filter by route
- `GET /api/active-passengers/by-status/:status` - Filter by status

### Write Operations

- `POST /api/active-passengers` - Create passenger (Reservoirs only)
- `POST /api/active-passengers/mark-boarded/:id` - Update to ONBOARD
- `POST /api/active-passengers/mark-alighted/:id` - Update to COMPLETED
- `DELETE /api/active-passengers/cleanup/expired` - Remove expired

## Socket.IO Namespaces

### `/depot-reservoir`

- Emits: `COMMUTER_SPAWNED`, `COMMUTER_PICKED_UP`
- For: Depot-spawned passengers

### `/route-reservoir`

- Emits: `COMMUTER_SPAWNED`, `COMMUTER_PICKED_UP`
- For: Route-spawned passengers

### `/vehicle-events`

- Receives: Vehicle location updates
- Emits: Vehicle state changes

## Why This Architecture?

✅ **Single Source of Truth**: Database always has current state
✅ **Real-time Updates**: Socket.IO notifies without polling
✅ **Scalable**: Multiple actors can read concurrently
✅ **Testable**: Can query database directly
✅ **Decoupled**: Actors don't need to know about each other
✅ **Persistent**: Database survives service restarts

## What NOT to Do

❌ **Don't** send full passenger data in Socket.IO events (send IDs only)
❌ **Don't** query passengers via Socket.IO (use REST API)
❌ **Don't** write to database directly (use Strapi API)
❌ **Don't** store passenger data in memory only (always persist to DB)
❌ **Don't** make reservoirs listen for spawn triggers (automatic spawning)

## Service Startup

1. **Strapi**: `cd arknet-fleet-api && npm run develop`
2. **Commuter Service**: `python -m commuter_service`
3. **Visualization**: Open `http://localhost:1337/passenger-spawning-visualization.html`

Passengers spawn automatically. No manual triggers needed.
