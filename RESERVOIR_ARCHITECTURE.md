# Commuter Service - Reservoir Architecture

## 🎯 The Problem You Identified

**Question**: "Do these APIs go through the reservoirs or straight to Strapi? Have we made the reservoirs redundant?"

**Answer**: You caught a critical architectural issue! The initial CRUD API bypassed reservoirs entirely. This is now **FIXED**.

## 🏗️ Correct Architecture: Repository-Reservoir Pattern

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT / CONDUCTOR                        │
│              (HTTP API, Console, Vehicle Apps)               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      CRUD API LAYER                          │
│            (passenger_crud.py, commuter_manifest.py)         │
│                                                              │
│  • Validation                                                │
│  • State machine enforcement                                 │
│  • HTTP ↔ Domain translation                                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESERVOIR LAYER ⭐                        │
│         (RouteReservoir, DepotReservoir)                     │
│                                                              │
│  • Cache invalidation                                        │
│  • Event emission (WebSocket)                                │
│  • Business logic coordination                               │
│  • Spawning orchestration                                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 REPOSITORY LAYER                             │
│              (PassengerRepository)                           │
│                                                              │
│  • Direct Strapi API access                                  │
│  • CRUD operations                                           │
│  • Query building                                            │
│  • No business logic                                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    STRAPI DATABASE                           │
│                  (Source of Truth)                           │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Why Reservoirs Are NOT Redundant

### 1. **Cache Management**
```python
# WRONG: Direct Strapi access
await strapi_client.put(f"/api/active-passengers/{id}", ...)
# ❌ Cache not invalidated!
# ❌ Redis still has old data!

# RIGHT: Through reservoir
await reservoir.mark_picked_up(passenger_id, vehicle_id)
# ✅ Updates Strapi
# ✅ Invalidates Redis cache
# ✅ Other services see fresh data
```

### 2. **Event Emission**
```python
# WRONG: Direct update
await passenger_repo.mark_boarded(passenger_id)
# ❌ No WebSocket event!
# ❌ Subscribed clients don't get notified!

# RIGHT: Through reservoir
await reservoir.mark_picked_up(passenger_id, vehicle_id)
# ✅ Updates database
# ✅ Emits passenger:boarded event
# ✅ All subscribers notified instantly
```

### 3. **Batch Operations**
```python
# WRONG: Loop through passengers
for passenger in passengers:
    await passenger_repo.insert_passenger(...)
# ❌ N database calls
# ❌ N cache invalidations
# ❌ N events (overwhelming clients)

# RIGHT: Batch through reservoir
await reservoir.push_batch(spawn_requests)
# ✅ Single bulk insert
# ✅ Single cache invalidation
# ✅ Batched event emission
```

### 4. **Consistency Guarantees**
```python
# Reservoir ensures:
✅ Atomicity: All-or-nothing operations
✅ Consistency: Cache and DB always in sync
✅ Event ordering: State changes broadcast in correct order
✅ Error handling: Rollback on failures
```

## 📊 Data Flow Examples

### Example 1: Spawning Passengers (Seeding)

```
seed.py
  │
  ├─→ RouteSpawner.spawn()
  │     │
  │     └─→ Generates SpawnRequest[]
  │
  └─→ RouteReservoir.push_batch(spawn_requests)
        │
        ├─→ PassengerRepository.bulk_insert_passengers()
        │     │
        │     └─→ Strapi API (batch insert)
        │
        ├─→ Invalidate Redis cache
        │
        └─→ Emit passenger:spawned events
              │
              └─→ WebSocket clients receive events
```

### Example 2: Boarding Passenger (CRUD API)

```
Client: PATCH /api/passengers/{id}/board

API Layer (passenger_crud.py)
  │
  ├─→ Validate state transition (WAITING → BOARDED)
  │
  └─→ RouteReservoir.mark_picked_up(passenger_id, vehicle_id)
        │
        ├─→ PassengerRepository.mark_boarded(passenger_id, vehicle_id)
        │     │
        │     └─→ Strapi API (update)
        │
        ├─→ Invalidate cache for this route
        │
        └─→ Emit passenger:boarded event
              │
              └─→ Subscribed clients get real-time update
```

### Example 3: Conductor Picks Up Passenger

```
Conductor Service
  │
  └─→ POST /api/passengers/{id}/board
        │
        └─→ [Same flow as Example 2]
              │
              ├─→ Updates through reservoir
              ├─→ Cache invalidated
              └─→ Events emitted
```

## 🔧 Repository vs Reservoir

### PassengerRepository (Data Access)
**Responsibility**: Talk to Strapi  
**Operations**:
- `insert_passenger()` - Single insert
- `bulk_insert_passengers()` - Batch insert
- `mark_boarded()` - Update to BOARDED
- `mark_alighted()` - Update to ALIGHTED
- `get_waiting_passengers_by_route()` - Query

**Does NOT**:
- ❌ Manage cache
- ❌ Emit events
- ❌ Batch optimization
- ❌ Business logic

### RouteReservoir (Business Logic)
**Responsibility**: Coordinate passenger operations  
**Operations**:
- `push()` - Add single passenger (+ cache + events)
- `push_batch()` - Add multiple (optimized + events)
- `mark_picked_up()` - Board passenger (+ cache + events)
- `mark_dropped_off()` - Alight passenger (+ cache + events)
- `available()` - Query with caching

**Always**:
- ✅ Uses PassengerRepository for data access
- ✅ Invalidates cache
- ✅ Emits WebSocket events
- ✅ Handles errors gracefully

## 🚨 Anti-Patterns (What NOT To Do)

### ❌ WRONG: Bypass Reservoir
```python
# In conductor or API
async def board_passenger(passenger_id, vehicle_id):
    repo = PassengerRepository()
    await repo.mark_boarded(passenger_id)  # ❌ BAD!
```

**Problems**:
- Cache not invalidated
- No events emitted
- No business logic enforcement

### ✅ RIGHT: Use Reservoir
```python
# In conductor or API
async def board_passenger(passenger_id, vehicle_id):
    reservoir = RouteReservoir(passenger_repository=repo)
    await reservoir.mark_picked_up(passenger_id, vehicle_id)  # ✅ GOOD!
```

**Benefits**:
- Cache invalidated automatically
- Events emitted to subscribers
- Consistent with rest of system

## 🔄 When To Use Each

### Use PassengerRepository directly:
- ❌ **NEVER** from external code
- ✅ Only from within Reservoir implementations
- ✅ Only for low-level data access

### Use RouteReservoir:
- ✅ All spawning operations
- ✅ All state changes (board/alight)
- ✅ All passenger queries
- ✅ From CRUD API
- ✅ From Conductor
- ✅ From any service

## 📈 Performance Benefits

### Without Reservoir (Direct Access)
```
Request 1: Get waiting passengers
  └─→ Strapi query (300ms)

Request 2: Get waiting passengers (same route)
  └─→ Strapi query (300ms)  ❌ Wasteful!

Request 3: Get waiting passengers (same route)
  └─→ Strapi query (300ms)  ❌ Wasteful!

Total: 900ms
```

### With Reservoir (Cached)
```
Request 1: Get waiting passengers
  ├─→ Check Redis cache (miss)
  ├─→ Strapi query (300ms)
  └─→ Cache result in Redis

Request 2: Get waiting passengers (same route)
  └─→ Redis cache hit (5ms)  ✅ Fast!

Request 3: Get waiting passengers (same route)
  └─→ Redis cache hit (5ms)  ✅ Fast!

Total: 310ms (3x faster!)
```

## 🎯 The Fix Applied

### Before (WRONG)
```python
# passenger_crud.py
@router.patch("/{passenger_id}/board")
async def board_passenger(...):
    # Direct Strapi access ❌
    async with httpx.AsyncClient() as client:
        await client.put(f"{strapi_url}/api/active-passengers/{id}", ...)
    
    # Manual event emission ❌
    await emit_passenger_event(...)
```

### After (CORRECT)
```python
# passenger_crud.py
@router.patch("/{passenger_id}/board")
async def board_passenger(...):
    # Through reservoir ✅
    reservoir = RouteReservoir(passenger_repository=repo)
    await reservoir.mark_picked_up(passenger_id, vehicle_id)
    
    # Cache invalidated ✅
    # Events emitted automatically ✅
```

## 🚀 For Conductor Integration

When conductor picks up passengers:

```python
# conductor_service/vehicle_operations.py

async def pick_up_passenger(vehicle_id: str, passenger_id: str):
    """Vehicle picks up waiting passenger"""
    
    # Get commuter service client
    commuter_client = get_commuter_service_client()
    
    # Use CRUD API (which uses reservoir internally)
    response = await commuter_client.patch(
        f"/api/passengers/{passenger_id}/board",
        json={"vehicle_id": vehicle_id}
    )
    
    # ✅ Reservoir handles:
    # - Database update
    # - Cache invalidation
    # - Event emission
    # - State validation
```

## 📝 Summary

**Reservoirs are essential** because they:

1. **Manage cache** - Invalidate Redis when data changes
2. **Emit events** - Notify WebSocket clients of state changes
3. **Optimize batch operations** - Bulk inserts, batched events
4. **Enforce consistency** - Cache and DB always in sync
5. **Centralize business logic** - Single place for passenger operations

**Repository is just data access** - No logic, no cache, no events.

**All passenger operations MUST go through reservoirs** for consistency! ✅
