# Conductor-Reservoir Integration Refactor Plan
**Date:** November 2, 2025  
**Objective:** Refactor conductor to use RouteReservoir/DepotReservoir consistently, enabling Redis caching and Socket.IO events

---

## 🎯 Success Criteria

- ✅ Conductor queries passengers via reservoirs (not direct PassengerRepository)
- ✅ Redis caching populated and used for passenger queries
- ✅ Socket.IO events emitted when passengers spawn
- ✅ Conductor can optionally listen to Socket.IO events for real-time updates
- ✅ All existing functionality preserved (boarding, capacity management, etc.)
- ✅ Test suite passes with enhanced logging showing reservoir usage

---

## 📋 PHASE 0: Pre-Flight Validation (30 minutes)

### Step 0.1: Verify Current Baseline Functionality
**Purpose:** Ensure current system works before making changes

**Actions:**
1. Start all required services:
   ```powershell
   # Terminal 1: Start Strapi
   cd E:\projects\github\vehicle_simulator
   # Verify Strapi running at http://localhost:1337
   
   # Terminal 2: Start Redis (if not running)
   redis-server
   # OR on Windows: redis-server.exe
   
   # Terminal 3: Start Commuter Service
   cd commuter_service
   python -m uvicorn main:app --host 0.0.0.0 --port 4000 --reload
   ```

2. Seed test passengers:
   ```powershell
   cd commuter_service
   python seed.py --route 1 --day monday --start-hour 7 --end-hour 9 --type route --count 10
   ```

3. Run baseline conductor vision test:
   ```powershell
   cd E:\projects\github\vehicle_simulator
   python test_conductor_vision.py --route 1 --duration 120
   ```

**Expected Success Results:**
- ✅ All services start without errors
- ✅ 10 passengers seeded successfully in Strapi
- ✅ Conductor logs show:
  - `👁️ LOOKING FOR PASSENGERS` messages
  - `✅ Found X eligible passengers` 
  - `🚪 Boarded X passengers`
  - `🛑 Requesting driver STOP`
  - `🚀 CONTINUE signal`
- ✅ Save baseline logs to `baseline_conductor_test.log` for comparison

**Rollback Plan:** If services don't start, fix configuration before proceeding.

---

## 📋 PHASE 1: Reservoir Infrastructure Setup (1 hour)

### Step 1.1: Add Redis Client to Reservoirs
**Purpose:** Ensure RouteReservoir and DepotReservoir can use Redis caching

**File:** `commuter_service/core/domain/reservoirs/route_reservoir.py`

**Actions:**
1. Check if Redis client is already initialized in RouteReservoir
2. If not, add Redis connection in `__init__`:
   ```python
   import redis.asyncio as redis
   
   def __init__(self, passenger_repository, redis_url="redis://localhost:6379"):
       self.repository = passenger_repository
       self.redis_client = None
       self.redis_url = redis_url
   
   async def connect(self):
       """Initialize Redis connection."""
       if not self.redis_client:
           self.redis_client = await redis.from_url(self.redis_url)
   ```

3. Verify existing `push()` method populates Redis cache
4. Add `query()` method that checks Redis first, then Strapi

**Expected Success Results:**
- ✅ `RouteReservoir` class has `redis_client` attribute
- ✅ `connect()` method initializes Redis connection
- ✅ No syntax errors in modified file
- ✅ Run: `python -m pytest commuter_service/tests/ -k reservoir -v` (if tests exist)

**Verification Command:**
```powershell
cd commuter_service
python -c "from core.domain.reservoirs.route_reservoir import RouteReservoir; print('✅ RouteReservoir imports successfully')"
```

---

### Step 1.2: Implement Reservoir `query()` Method
**Purpose:** Add query interface matching conductor's current `get_eligible_passengers()` API

**File:** `commuter_service/core/domain/reservoirs/route_reservoir.py`

**Actions:**
1. Add `query()` method to RouteReservoir:
   ```python
   async def query(
       self,
       route_id: str,
       vehicle_lat: float,
       vehicle_lon: float,
       pickup_radius_km: float = 0.2,
       max_results: int = 100
   ) -> List[Dict]:
       """
       Query passengers eligible for pickup.
       
       Checks Redis cache first (TTL 5s), falls back to Strapi if cache miss.
       
       Returns:
           List of passenger dictionaries matching conductor's expected format
       """
       cache_key = f"passengers:route:{route_id}:lat:{vehicle_lat:.4f}:lon:{vehicle_lon:.4f}"
       
       # Try cache first
       if self.redis_client:
           cached = await self.redis_client.get(cache_key)
           if cached:
               logger.info(f"🔴 CACHE HIT: {cache_key}")
               return json.loads(cached)
       
       # Cache miss - query repository
       logger.info(f"🔵 CACHE MISS: Querying repository for route {route_id}")
       passengers = await self.repository.get_eligible_passengers(
           vehicle_lat=vehicle_lat,
           vehicle_lon=vehicle_lon,
           route_id=route_id,
           pickup_radius_km=pickup_radius_km,
           max_results=max_results
       )
       
       # Populate cache for next query (TTL 5 seconds)
       if self.redis_client and passengers:
           await self.redis_client.setex(
               cache_key,
               5,  # TTL in seconds
               json.dumps(passengers)
           )
       
       return passengers
   ```

2. Add similar `query()` to DepotReservoir

**Expected Success Results:**
- ✅ `RouteReservoir.query()` method exists
- ✅ Method signature matches conductor's needs
- ✅ Redis cache logic implemented with 5-second TTL
- ✅ Fallback to PassengerRepository works if Redis unavailable
- ✅ No import errors

**Verification Command:**
```powershell
python -c "from commuter_service.core.domain.reservoirs.route_reservoir import RouteReservoir; import inspect; print('✅ query() method exists') if 'query' in dir(RouteReservoir) else print('❌ Missing query()')"
```

---

### Step 1.3: Add Socket.IO Event Emission to Reservoir
**Purpose:** Emit events when passengers spawn so conductor can react in real-time

**File:** `commuter_service/core/domain/reservoirs/route_reservoir.py`

**Actions:**
1. Add Socket.IO client to RouteReservoir:
   ```python
   import socketio
   
   def __init__(self, passenger_repository, redis_url="redis://localhost:6379", socketio_url="http://localhost:1337"):
       self.repository = passenger_repository
       self.redis_client = None
       self.redis_url = redis_url
       self.sio = socketio.AsyncClient()
       self.socketio_url = socketio_url
       self.sio_connected = False
   
   async def connect(self):
       """Initialize Redis and Socket.IO connections."""
       # Redis
       if not self.redis_client:
           self.redis_client = await redis.from_url(self.redis_url)
       
       # Socket.IO
       if not self.sio_connected:
           try:
               await self.sio.connect(self.socketio_url)
               self.sio_connected = True
               logger.info(f"✅ RouteReservoir connected to Socket.IO: {self.socketio_url}")
           except Exception as e:
               logger.warning(f"⚠️ Socket.IO connection failed (will continue without events): {e}")
   ```

2. Modify `push()` method to emit event after spawning:
   ```python
   async def push(self, passenger_data: Dict) -> Dict:
       """Push new passenger to repository and emit Socket.IO event."""
       # Existing push logic...
       result = await self.repository.insert_passenger(passenger_data)
       
       # Emit Socket.IO event for real-time updates
       if self.sio_connected:
           await self.sio.emit('commuter:spawned', {
               'passenger_id': result.get('passenger_id'),
               'route_id': passenger_data.get('route_id'),
               'latitude': passenger_data.get('latitude'),
               'longitude': passenger_data.get('longitude'),
               'timestamp': datetime.utcnow().isoformat()
           })
           logger.info(f"📡 Emitted commuter:spawned event for passenger {result.get('passenger_id')}")
       
       return result
   ```

**Expected Success Results:**
- ✅ Socket.IO client initialized in RouteReservoir
- ✅ `connect()` establishes Socket.IO connection
- ✅ `push()` emits `commuter:spawned` event after inserting passenger
- ✅ Graceful degradation if Socket.IO unavailable (logs warning, continues)

**Verification Test:**
```powershell
# Run a spawner and watch for Socket.IO events
cd commuter_service
python seed.py --route 1 --count 1 --type route
# Check logs for: "📡 Emitted commuter:spawned event"
```

---

### Step 1.4: Create Reservoir Factory/Manager
**Purpose:** Centralize reservoir instantiation for dependency injection

**File:** `commuter_service/core/domain/reservoirs/reservoir_manager.py` (NEW)

**Actions:**
1. Create new file:
   ```python
   """
   ReservoirManager - Singleton factory for reservoir instances.
   
   Ensures single Redis connection shared across all reservoir instances.
   """
   import logging
   from typing import Optional
   from .route_reservoir import RouteReservoir
   from .depot_reservoir import DepotReservoir
   from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
   
   logger = logging.getLogger(__name__)
   
   class ReservoirManager:
       """Singleton manager for reservoir instances."""
       
       _instance: Optional['ReservoirManager'] = None
       
       def __init__(self, redis_url="redis://localhost:6379", socketio_url="http://localhost:1337"):
           self.redis_url = redis_url
           self.socketio_url = socketio_url
           self.route_reservoir: Optional[RouteReservoir] = None
           self.depot_reservoir: Optional[DepotReservoir] = None
           self._initialized = False
       
       @classmethod
       def get_instance(cls) -> 'ReservoirManager':
           """Get singleton instance."""
           if cls._instance is None:
               cls._instance = cls()
           return cls._instance
       
       async def initialize(self):
           """Initialize all reservoirs with shared connections."""
           if self._initialized:
               return
           
           # Create shared PassengerRepository
           passenger_repo = PassengerRepository()
           
           # Create reservoirs
           self.route_reservoir = RouteReservoir(
               passenger_repository=passenger_repo,
               redis_url=self.redis_url,
               socketio_url=self.socketio_url
           )
           
           self.depot_reservoir = DepotReservoir(
               passenger_repository=passenger_repo,
               redis_url=self.redis_url,
               socketio_url=self.socketio_url
           )
           
           # Connect all
           await self.route_reservoir.connect()
           await self.depot_reservoir.connect()
           
           self._initialized = True
           logger.info("✅ ReservoirManager initialized all reservoirs")
       
       def get_route_reservoir(self) -> RouteReservoir:
           """Get RouteReservoir instance."""
           if not self._initialized:
               raise RuntimeError("ReservoirManager not initialized. Call initialize() first.")
           return self.route_reservoir
       
       def get_depot_reservoir(self) -> DepotReservoir:
           """Get DepotReservoir instance."""
           if not self._initialized:
               raise RuntimeError("ReservoirManager not initialized. Call initialize() first.")
           return self.depot_reservoir
   
   
   async def get_route_reservoir() -> RouteReservoir:
       """Convenience function for dependency injection."""
       manager = ReservoirManager.get_instance()
       if not manager._initialized:
           await manager.initialize()
       return manager.get_route_reservoir()
   
   
   async def get_depot_reservoir() -> DepotReservoir:
       """Convenience function for dependency injection."""
       manager = ReservoirManager.get_instance()
       if not manager._initialized:
           await manager.initialize()
       return manager.get_depot_reservoir()
   ```

**Expected Success Results:**
- ✅ `reservoir_manager.py` file created
- ✅ ReservoirManager implements singleton pattern
- ✅ `get_route_reservoir()` and `get_depot_reservoir()` helper functions exist
- ✅ No import errors

**Verification Command:**
```powershell
python -c "from commuter_service.core.domain.reservoirs.reservoir_manager import get_route_reservoir; print('✅ ReservoirManager imports successfully')"
```

---

## 📋 PHASE 2: Conductor Refactoring (1.5 hours)

### Step 2.1: Update Conductor to Accept Reservoir Dependencies
**Purpose:** Modify conductor initialization to receive reservoir instances

**File:** `arknet_transit_simulator/vehicle/conductor.py`

**Actions:**
1. Update `__init__()` signature:
   ```python
   def __init__(
       self, 
       conductor_id: str, 
       conductor_name: str, 
       vehicle_id: str,
       capacity: int,
       assigned_route_id: str = None,
       tick_time: float = 1.0,
       config: ConductorConfig = None,
       sio_url: Optional[str] = None,
       use_socketio: bool = True,
       passenger_db = None,  # DEPRECATED: Keep for backward compatibility
       route_reservoir = None,  # NEW: RouteReservoir instance
       depot_reservoir = None,  # NEW: DepotReservoir instance
       hardware_client = None
   ):
   ```

2. Store reservoir references:
   ```python
   # Legacy database access (DEPRECATED - use reservoirs instead)
   self.passenger_db = passenger_db
   
   # NEW: Reservoir-based access (preferred)
   self.route_reservoir = route_reservoir
   self.depot_reservoir = depot_reservoir
   
   # Flag to determine which path to use
   self.use_reservoirs = (route_reservoir is not None)
   
   if self.use_reservoirs:
       logger.info(f"✅ Conductor {vehicle_id} using RESERVOIR-based passenger queries")
   else:
       logger.warning(f"⚠️ Conductor {vehicle_id} using LEGACY PassengerRepository (deprecated)")
   ```

**Expected Success Results:**
- ✅ Conductor accepts `route_reservoir` and `depot_reservoir` parameters
- ✅ Backward compatibility maintained (still accepts `passenger_db`)
- ✅ `use_reservoirs` flag determines query path
- ✅ No syntax errors

**Verification Command:**
```powershell
python -c "from arknet_transit_simulator.vehicle.conductor import Conductor; import inspect; sig = inspect.signature(Conductor.__init__); print('✅ route_reservoir param exists') if 'route_reservoir' in sig.parameters else print('❌ Missing parameter')"
```

---

### Step 2.2: Refactor `check_for_passengers()` to Use Reservoirs
**Purpose:** Replace direct PassengerRepository calls with reservoir queries

**File:** `arknet_transit_simulator/vehicle/conductor.py`

**Actions:**
1. Locate `check_for_passengers()` method (around line 1133)
2. Add reservoir query path:
   ```python
   async def check_for_passengers(
       self,
       vehicle_lat: float,
       vehicle_lon: float,
       route: str = None
   ) -> int:
       """
       Check for passengers and board them.
       
       NOW USES RESERVOIRS with Redis caching for improved performance.
       """
       if route is None:
           route = self.assigned_route_id
       
       if self.seats_available <= 0:
           logger.info(f"🔵 Conductor {self.vehicle_id}: 🚫 Vehicle full (no seats available)")
           return 0
       
       try:
           # Enhanced logging with reservoir indicator
           cache_indicator = "🔴 [CACHE]" if self.use_reservoirs else "🔵 [DIRECT]"
           logger.info(
               f"{cache_indicator} Conductor {self.vehicle_id} 👁️  LOOKING FOR PASSENGERS:\n"
               f"   📍 Position: ({vehicle_lat:.6f}, {vehicle_lon:.6f})\n"
               f"   🚏 Route: {route}\n"
               f"   🔍 Pickup radius: {self.config.pickup_radius_km} km\n"
               f"   💺 Seats available: {self.seats_available}/{self.capacity}\n"
               f"   🔧 Query method: {'RouteReservoir (cached)' if self.use_reservoirs else 'PassengerRepository (legacy)'}"
           )
           
           # NEW: Use reservoir if available
           if self.use_reservoirs and self.route_reservoir:
               eligible = await self.route_reservoir.query(
                   route_id=route,
                   vehicle_lat=vehicle_lat,
                   vehicle_lon=vehicle_lon,
                   pickup_radius_km=self.config.pickup_radius_km,
                   max_results=self.seats_available
               )
           # LEGACY: Fall back to direct PassengerRepository
           elif self.passenger_db:
               eligible = await self.passenger_db.get_eligible_passengers(
                   vehicle_lat=vehicle_lat,
                   vehicle_lon=vehicle_lon,
                   route_id=route,
                   pickup_radius_km=self.config.pickup_radius_km,
                   max_results=self.seats_available
               )
           else:
               logger.error(f"❌ Conductor {self.vehicle_id}: No passenger query method available!")
               return 0
           
           # Rest of the method remains unchanged...
           if not eligible:
               logger.info(f"🔵 Conductor {self.vehicle_id}: ❌ No passengers found at this location")
               return 0
           
           # ... existing boarding logic ...
   ```

**Expected Success Results:**
- ✅ `check_for_passengers()` tries reservoir first, falls back to legacy
- ✅ Logs show `🔴 [CACHE]` when using reservoir, `🔵 [DIRECT]` when using legacy
- ✅ Query method logged: "RouteReservoir (cached)" vs "PassengerRepository (legacy)"
- ✅ All existing boarding logic preserved

**Verification:** Review code diff, ensure no logic removed.

---

### Step 2.3: Update Simulator to Inject Reservoirs into Conductor
**Purpose:** Wire up dependency injection in simulator startup

**File:** `arknet_transit_simulator/simulator.py`

**Actions:**
1. Locate conductor initialization (around line 470)
2. Import reservoir manager:
   ```python
   from commuter_service.core.domain.reservoirs.reservoir_manager import get_route_reservoir, get_depot_reservoir
   ```

3. Initialize reservoirs before creating conductor:
   ```python
   # Get vehicle capacity from database
   try:
       performance = await VehiclePerformanceService.get_performance_async(vehicle_assignment.vehicle_id)
       vehicle_capacity = performance.capacity
       logger.info(f"[CONDUCTOR] Retrieved vehicle capacity from database: {vehicle_capacity} passengers")
   except Exception as perf_error:
       logger.warning(f"[CONDUCTOR] Failed to get capacity from database: {perf_error}, using default 40")
       vehicle_capacity = 40
   
   # NEW: Initialize reservoirs (replaces direct PassengerRepository)
   try:
       route_reservoir = await get_route_reservoir()
       depot_reservoir = await get_depot_reservoir()
       logger.info(f"[CONDUCTOR] ✅ Initialized RouteReservoir and DepotReservoir with Redis caching")
   except Exception as res_error:
       logger.warning(f"[CONDUCTOR] ⚠️ Failed to initialize reservoirs: {res_error}, falling back to legacy PassengerRepository")
       route_reservoir = None
       depot_reservoir = None
       
       # Fallback: Use legacy PassengerRepository
       from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
       from arknet_transit_simulator.services.strapi_passenger_service import StrapiPassengerService
       passenger_repo = PassengerRepository()
       passenger_service = StrapiPassengerService(passenger_repo)
       await passenger_service.connect()
   
   # Create conductor with reservoir dependency injection
   conductor = Conductor(
       conductor_id=f"COND-{driver_assignment.driver_id}",
       conductor_name=f"Conductor-{driver_assignment.driver_name}",
       vehicle_id=vehicle_assignment.vehicle_id,
       assigned_route_id=vehicle_assignment.route_id,
       capacity=vehicle_capacity,
       route_reservoir=route_reservoir,  # NEW
       depot_reservoir=depot_reservoir,  # NEW
       passenger_db=passenger_service if route_reservoir is None else None  # Legacy fallback
   )
   ```

**Expected Success Results:**
- ✅ Simulator imports reservoir manager
- ✅ Reservoirs initialized before conductor creation
- ✅ Conductor receives reservoir instances via dependency injection
- ✅ Graceful fallback to legacy path if reservoir initialization fails
- ✅ Logs show: "✅ Initialized RouteReservoir and DepotReservoir with Redis caching"

**Verification:** Run simulator initialization, check logs.

---

## 📋 PHASE 3: Testing & Validation (1 hour)

### Step 3.1: Unit Test Reservoir Query Method
**Purpose:** Verify reservoir query works independently

**File:** `commuter_service/tests/test_route_reservoir.py` (NEW)

**Actions:**
1. Create test file:
   ```python
   """Unit tests for RouteReservoir query method."""
   import pytest
   import asyncio
   from commuter_service.core.domain.reservoirs.route_reservoir import RouteReservoir
   from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
   
   @pytest.mark.asyncio
   async def test_reservoir_query_cache_miss():
       """Test query method on cache miss (hits repository)."""
       repo = PassengerRepository()
       reservoir = RouteReservoir(passenger_repository=repo)
       await reservoir.connect()
       
       # Query for passengers (will be cache miss first time)
       passengers = await reservoir.query(
           route_id="1",
           vehicle_lat=36.1627,
           vehicle_lon=-86.7816,
           pickup_radius_km=0.5,
           max_results=10
       )
       
       # Should return list (even if empty)
       assert isinstance(passengers, list)
       print(f"✅ Query returned {len(passengers)} passengers")
   
   @pytest.mark.asyncio
   async def test_reservoir_query_cache_hit():
       """Test query method on cache hit."""
       repo = PassengerRepository()
       reservoir = RouteReservoir(passenger_repository=repo)
       await reservoir.connect()
       
       # First query (cache miss)
       passengers1 = await reservoir.query(
           route_id="1",
           vehicle_lat=36.1627,
           vehicle_lon=-86.7816,
           pickup_radius_km=0.5,
           max_results=10
       )
       
       # Second query (should hit cache)
       passengers2 = await reservoir.query(
           route_id="1",
           vehicle_lat=36.1627,
           vehicle_lon=-86.7816,
           pickup_radius_km=0.5,
           max_results=10
       )
       
       # Results should be identical
       assert len(passengers1) == len(passengers2)
       print(f"✅ Cache hit returned same {len(passengers2)} passengers")
   ```

2. Run tests:
   ```powershell
   cd commuter_service
   python -m pytest tests/test_route_reservoir.py -v
   ```

**Expected Success Results:**
- ✅ `test_reservoir_query_cache_miss` passes
- ✅ `test_reservoir_query_cache_hit` passes
- ✅ Logs show "🔵 CACHE MISS" on first query
- ✅ Logs show "🔴 CACHE HIT" on second query

---

### Step 3.2: Integration Test - Conductor with Reservoirs
**Purpose:** Verify conductor uses reservoirs end-to-end

**Actions:**
1. Seed fresh passengers:
   ```powershell
   cd commuter_service
   python seed.py --route 1 --day monday --start-hour 7 --end-hour 9 --type route --count 15
   ```

2. Run conductor vision test with reservoir flag:
   ```powershell
   cd E:\projects\github\vehicle_simulator
   python test_conductor_vision.py --route 1 --duration 180
   ```

3. Watch for reservoir-specific logs:
   - `🔴 [CACHE]` prefix on conductor logs
   - `🔵 CACHE MISS: Querying repository` on first query
   - `🔴 CACHE HIT: passengers:route:1:...` on subsequent queries
   - `Query method: RouteReservoir (cached)`

**Expected Success Results:**
- ✅ Conductor starts successfully
- ✅ Logs show `✅ Conductor VEHICLE-001 using RESERVOIR-based passenger queries`
- ✅ First passenger query shows `🔵 CACHE MISS`
- ✅ Subsequent queries at same location show `🔴 CACHE HIT`
- ✅ Passengers board successfully (same behavior as baseline)
- ✅ Boarding count matches baseline test
- ✅ Save logs to `reservoir_conductor_test.log`

**Comparison Test:**
```powershell
# Compare boarding counts
Write-Output "Baseline test:"
Select-String "Boarded" baseline_conductor_test.log | Measure-Object
Write-Output "Reservoir test:"
Select-String "Boarded" reservoir_conductor_test.log | Measure-Object
# Counts should match
```

---

### Step 3.3: Verify Redis Cache Population
**Purpose:** Confirm Redis is actually being used

**Actions:**
1. Install Redis CLI if not available
2. During conductor test run, monitor Redis:
   ```powershell
   # In separate terminal
   redis-cli
   > MONITOR
   # Watch for SET commands with key pattern: passengers:route:1:lat:*:lon:*
   ```

3. Query Redis keys after test:
   ```powershell
   redis-cli
   > KEYS passengers:*
   # Should show keys like: passengers:route:1:lat:36.1627:lon:-86.7816
   
   > TTL passengers:route:1:lat:36.1627:lon:-86.7816
   # Should show remaining TTL (0-5 seconds)
   
   > GET passengers:route:1:lat:36.1627:lon:-86.7816
   # Should show JSON array of passengers
   ```

**Expected Success Results:**
- ✅ `MONITOR` shows SET commands during conductor queries
- ✅ `KEYS passengers:*` returns multiple cache keys
- ✅ Cache keys have TTL of 5 seconds or less
- ✅ GET returns valid JSON passenger data

**Failure Case:** If no keys found, check:
- Redis running? (`redis-cli PING` → `PONG`)
- Reservoir connected to Redis? (check logs for connection errors)
- Query method using Redis? (check for "🔴 CACHE HIT" logs)

---

### Step 3.4: Verify Socket.IO Event Emission
**Purpose:** Confirm spawning emits Socket.IO events

**Actions:**
1. Create Socket.IO listener script:
   ```python
   # test_socketio_listener.py
   import socketio
   import asyncio
   
   sio = socketio.AsyncClient()
   
   @sio.on('commuter:spawned')
   async def on_commuter_spawned(data):
       print(f"📡 Received commuter:spawned event:")
       print(f"   Passenger ID: {data.get('passenger_id')}")
       print(f"   Route: {data.get('route_id')}")
       print(f"   Location: ({data.get('latitude')}, {data.get('longitude')})")
       print(f"   Timestamp: {data.get('timestamp')}")
   
   async def main():
       await sio.connect('http://localhost:1337')
       print("✅ Connected to Socket.IO server, listening for commuter:spawned events...")
       await sio.wait()
   
   if __name__ == '__main__':
       asyncio.run(main())
   ```

2. Run listener in one terminal:
   ```powershell
   python test_socketio_listener.py
   ```

3. Spawn passengers in another terminal:
   ```powershell
   cd commuter_service
   python seed.py --route 1 --count 5 --type route
   ```

**Expected Success Results:**
- ✅ Listener connects successfully
- ✅ 5 `commuter:spawned` events received
- ✅ Each event contains: passenger_id, route_id, latitude, longitude, timestamp
- ✅ Spawner logs show: `📡 Emitted commuter:spawned event for passenger XXX`

**Failure Case:** If no events received:
- Check Socket.IO server running (Strapi?)
- Check reservoir's `push()` method emits events
- Check Socket.IO client connected (`self.sio_connected = True`)

---

## 📋 PHASE 4: Performance Validation (30 minutes)

### Step 4.1: Benchmark Query Performance
**Purpose:** Measure cache hit improvement over direct queries

**File:** `benchmark_reservoir_performance.py` (NEW)

**Actions:**
1. Create benchmark script:
   ```python
   """Benchmark reservoir query performance vs direct repository."""
   import asyncio
   import time
   from commuter_service.core.domain.reservoirs.reservoir_manager import get_route_reservoir
   from commuter_service.infrastructure.database.passenger_repository import PassengerRepository
   
   async def benchmark_reservoir():
       """Benchmark reservoir queries (with cache)."""
       reservoir = await get_route_reservoir()
       
       # Warm up cache
       await reservoir.query(
           route_id="1",
           vehicle_lat=36.1627,
           vehicle_lon=-86.7816,
           pickup_radius_km=0.5,
           max_results=100
       )
       
       # Benchmark 100 cache hits
       start = time.time()
       for _ in range(100):
           await reservoir.query(
               route_id="1",
               vehicle_lat=36.1627,
               vehicle_lon=-86.7816,
               pickup_radius_km=0.5,
               max_results=100
           )
       end = time.time()
       
       duration = end - start
       avg_ms = (duration / 100) * 1000
       print(f"🔴 Reservoir (cached): {duration:.3f}s for 100 queries ({avg_ms:.2f}ms avg)")
       return avg_ms
   
   async def benchmark_direct():
       """Benchmark direct repository queries (no cache)."""
       repo = PassengerRepository()
       
       # Benchmark 100 direct queries
       start = time.time()
       for _ in range(100):
           await repo.get_eligible_passengers(
               vehicle_lat=36.1627,
               vehicle_lon=-86.7816,
               route_id="1",
               pickup_radius_km=0.5,
               max_results=100
           )
       end = time.time()
       
       duration = end - start
       avg_ms = (duration / 100) * 1000
       print(f"🔵 Direct repo (no cache): {duration:.3f}s for 100 queries ({avg_ms:.2f}ms avg)")
       return avg_ms
   
   async def main():
       print("🏁 Starting performance benchmark...")
       print("=" * 60)
       
       cached_ms = await benchmark_reservoir()
       direct_ms = await benchmark_direct()
       
       speedup = direct_ms / cached_ms
       print("=" * 60)
       print(f"📊 RESULTS:")
       print(f"   Cached queries: {cached_ms:.2f}ms avg")
       print(f"   Direct queries: {direct_ms:.2f}ms avg")
       print(f"   Speedup: {speedup:.1f}x faster with cache")
       
       if speedup > 2.0:
           print("✅ EXCELLENT: Cache provides significant performance improvement")
       elif speedup > 1.2:
           print("✅ GOOD: Cache provides measurable performance improvement")
       else:
           print("⚠️ WARNING: Cache not providing expected improvement (check Redis)")
   
   if __name__ == '__main__':
       asyncio.run(main())
   ```

2. Run benchmark:
   ```powershell
   python benchmark_reservoir_performance.py
   ```

**Expected Success Results:**
- ✅ Cached queries: < 5ms average
- ✅ Direct queries: 50-200ms average (depends on Strapi latency)
- ✅ Speedup: > 10x faster with cache
- ✅ Output shows "✅ EXCELLENT: Cache provides significant performance improvement"

**Acceptable Range:**
- Cached: 1-10ms
- Direct: 50-500ms
- Speedup: > 5x

**Failure Case:** If speedup < 2x:
- Check Redis running and accessible
- Check cache TTL not expired during benchmark
- Check network latency to Strapi

---

### Step 4.2: Load Test - Multiple Conductors
**Purpose:** Verify system handles multiple concurrent conductors

**File:** `test_multi_conductor_load.py` (NEW)

**Actions:**
1. Create load test script:
   ```python
   """Load test with multiple concurrent conductors."""
   import asyncio
   from arknet_transit_simulator.vehicle.conductor import Conductor, ConductorConfig
   from commuter_service.core.domain.reservoirs.reservoir_manager import get_route_reservoir, get_depot_reservoir
   
   async def run_conductor(conductor_id: str, route_id: str, duration: int = 60):
       """Run a single conductor for duration seconds."""
       route_res = await get_route_reservoir()
       depot_res = await get_depot_reservoir()
       
       config = await ConductorConfig.from_config_service()
       conductor = Conductor(
           conductor_id=conductor_id,
           conductor_name=f"Conductor-{conductor_id}",
           vehicle_id=f"VEHICLE-{conductor_id}",
           capacity=40,
           assigned_route_id=route_id,
           config=config,
           route_reservoir=route_res,
           depot_reservoir=depot_res
       )
       
       # Simulate conductor checking for passengers every 2 seconds
       queries = 0
       start = asyncio.get_event_loop().time()
       while asyncio.get_event_loop().time() - start < duration:
           await conductor.check_for_passengers(
               vehicle_lat=36.1627 + (queries * 0.001),  # Slight position changes
               vehicle_lon=-86.7816 + (queries * 0.001),
               route=route_id
           )
           queries += 1
           await asyncio.sleep(2)
       
       print(f"✅ {conductor_id} completed {queries} queries in {duration}s")
       return queries
   
   async def main():
       print("🏁 Starting multi-conductor load test...")
       print("   Creating 5 concurrent conductors")
       print("   Each will query every 2 seconds for 60 seconds")
       print("=" * 60)
       
       # Seed passengers first
       print("📍 Ensure passengers seeded: python commuter_service/seed.py --route 1 --count 20")
       await asyncio.sleep(2)
       
       # Run 5 conductors concurrently
       tasks = [
           run_conductor(f"COND-{i}", "1", duration=60)
           for i in range(1, 6)
       ]
       
       results = await asyncio.gather(*tasks)
       total_queries = sum(results)
       
       print("=" * 60)
       print(f"📊 RESULTS:")
       print(f"   Total queries: {total_queries}")
       print(f"   Expected cache hits: ~{total_queries * 0.8:.0f} (80%)")
       print(f"   Check logs for cache hit ratio")
       print("✅ Load test completed successfully")
   
   if __name__ == '__main__':
       asyncio.run(main())
   ```

2. Seed passengers:
   ```powershell
   cd commuter_service
   python seed.py --route 1 --count 20 --type route
   ```

3. Run load test:
   ```powershell
   cd E:\projects\github\vehicle_simulator
   python test_multi_conductor_load.py
   ```

**Expected Success Results:**
- ✅ All 5 conductors start successfully
- ✅ Total ~150 queries executed (5 conductors × 30 queries each)
- ✅ Logs show mix of cache hits and misses
- ✅ No errors or timeouts
- ✅ Redis handles concurrent connections
- ✅ No memory leaks (check Redis memory: `redis-cli INFO memory`)

---

## 📋 PHASE 5: Cleanup & Documentation (30 minutes)

### Step 5.1: Update Architecture Documentation
**Purpose:** Document the new reservoir-based architecture

**File:** `CONTEXT.md`

**Actions:**
1. Update "Conductor-Reservoir Integration Status" section:
   ```markdown
   ## Conductor-Reservoir Integration Status
   
   **Status:** ✅ COMPLETED (November 2, 2025)
   
   ### Current Architecture (After Refactor)
   
   **Write Path (Spawning):**
   ```
   PoissonGeoJSONSpawner
       ↓
   RouteReservoir.push()
       ↓ (emits Socket.IO event)
   PassengerRepository
       ↓
   Strapi API
       ↓ (also writes to Redis cache)
   Redis Cache (TTL: 5s)
   ```
   
   **Read Path (Conductor Queries):**
   ```
   Conductor.check_for_passengers()
       ↓
   RouteReservoir.query()
       ↓ (checks cache first)
   Redis Cache (TTL: 5s)
       ↓ (cache miss)
   PassengerRepository.get_eligible_passengers()
       ↓
   Strapi API
   ```
   
   ### Benefits Achieved
   
   - ✅ **Consistent Architecture**: Both writes and reads use reservoirs
   - ✅ **Redis Caching**: 10-50x faster queries via cache hits
   - ✅ **Socket.IO Events**: Real-time passenger spawn notifications
   - ✅ **Backward Compatibility**: Falls back to legacy path if reservoirs unavailable
   - ✅ **Performance**: Benchmarked 5-10ms cached queries vs 50-200ms direct queries
   
   ### Configuration
   
   ```python
   # Redis connection
   REDIS_URL = "redis://localhost:6379"
   
   # Cache TTL
   CACHE_TTL_SECONDS = 5
   
   # Socket.IO server
   SOCKETIO_URL = "http://localhost:1337"
   ```
   ```

2. Add performance metrics section
3. Update dependency injection diagram

**Expected Success Results:**
- ✅ CONTEXT.md reflects new architecture
- ✅ Diagrams show reservoir-based flow
- ✅ Performance metrics documented
- ✅ Configuration parameters listed

---

### Step 5.2: Update TODO.md
**Purpose:** Mark refactoring tasks complete

**File:** `TODO.md`

**Actions:**
1. Mark completed tasks:
   ```markdown
   - [x] Refactor conductor to use reservoirs
     - Updated conductor to query via RouteReservoir/DepotReservoir instead of PassengerRepository directly.
     - Enabled Redis caching with 5-second TTL
     - Added Socket.IO event emission on passenger spawn
     - Achieved 10-50x performance improvement on cached queries
     - Maintained backward compatibility with legacy PassengerRepository path
   ```

**Expected Success Results:**
- ✅ TODO.md updated
- ✅ Completed items checked off
- ✅ Performance improvements noted

---

### Step 5.3: Create Migration Guide
**Purpose:** Help others understand the refactoring

**File:** `docs/RESERVOIR_MIGRATION_GUIDE.md` (NEW)

**Actions:**
1. Create guide:
   ```markdown
   # Reservoir Migration Guide
   
   ## Overview
   This guide explains the conductor refactoring from direct PassengerRepository access to reservoir-based queries with Redis caching.
   
   ## What Changed
   
   ### Before (Legacy)
   ```python
   # Direct PassengerRepository access
   passengers = await passenger_db.get_eligible_passengers(...)
   ```
   
   ### After (Reservoir-based)
   ```python
   # Cached reservoir queries
   passengers = await route_reservoir.query(...)
   ```
   
   ## Performance Improvements
   
   - Cache hits: ~5ms average
   - Cache misses: ~100ms average (hits Strapi)
   - Speedup: 10-50x on cache hits
   - TTL: 5 seconds
   
   ## Migration Checklist
   
   - [ ] Redis running on localhost:6379
   - [ ] ReservoirManager initialized before conductor creation
   - [ ] Conductor receives `route_reservoir` parameter
   - [ ] Logs show "using RESERVOIR-based passenger queries"
   - [ ] Cache hit logs appear: "🔴 CACHE HIT"
   - [ ] Socket.IO events emitted on spawning
   
   ## Troubleshooting
   
   ### No cache hits
   - Check Redis: `redis-cli PING`
   - Check keys: `redis-cli KEYS passengers:*`
   - Check TTL: `redis-cli TTL passengers:route:1:...`
   
   ### Slow queries
   - Check Strapi latency
   - Check Redis latency: `redis-cli --latency`
   - Check network connectivity
   
   ### Socket.IO events not received
   - Check Strapi Socket.IO server running
   - Check reservoir's `sio_connected` flag
   - Check event name: `commuter:spawned`
   ```

**Expected Success Results:**
- ✅ Migration guide created
- ✅ Before/after examples clear
- ✅ Troubleshooting section helpful
- ✅ Performance metrics documented

---

## 📋 PHASE 6: Final Validation & Rollout (30 minutes)

### Step 6.1: Run Full Integration Test Suite
**Purpose:** Verify entire system works end-to-end

**Actions:**
1. Clean slate:
   ```powershell
   # Clear Redis cache
   redis-cli FLUSHALL
   
   # Delete all passengers from Strapi
   cd commuter_service
   python -c "from infrastructure.database.passenger_repository import PassengerRepository; import asyncio; asyncio.run(PassengerRepository().delete_all_passengers())"
   ```

2. Run full test sequence:
   ```powershell
   # 1. Seed passengers
   python seed.py --route 1 --day monday --start-hour 7 --end-hour 9 --count 20 --type route
   
   # 2. Run conductor vision test
   cd ..
   python test_conductor_vision.py --route 1 --duration 300
   
   # 3. Verify in parallel: Socket.IO listener
   # (In separate terminal)
   python test_socketio_listener.py
   
   # 4. Monitor Redis
   # (In separate terminal)
   redis-cli MONITOR
   ```

3. Checklist during test:
   - [ ] 20 passengers seeded successfully
   - [ ] Conductor starts with reservoir-based queries
   - [ ] First query shows cache miss
   - [ ] Subsequent queries show cache hits
   - [ ] Passengers board successfully
   - [ ] Driver receives stop/continue signals
   - [ ] Socket.IO listener receives spawn events
   - [ ] Redis MONITOR shows SET/GET commands

**Expected Success Results:**
- ✅ All checklist items pass
- ✅ Conductor completes journey successfully
- ✅ Boarding behavior matches baseline
- ✅ Performance improved (cache hits faster)
- ✅ No errors in logs

---

### Step 6.2: Performance Comparison Report
**Purpose:** Document improvement metrics

**Actions:**
1. Generate comparison report:
   ```powershell
   # Run benchmark
   python benchmark_reservoir_performance.py > reservoir_performance_report.txt
   
   # Extract metrics
   Select-String "Cached queries:" reservoir_performance_report.txt
   Select-String "Direct queries:" reservoir_performance_report.txt
   Select-String "Speedup:" reservoir_performance_report.txt
   ```

2. Compare baseline vs reservoir test logs:
   ```powershell
   # Count passenger queries
   Write-Output "Baseline queries:"
   Select-String "LOOKING FOR PASSENGERS" baseline_conductor_test.log | Measure-Object
   
   Write-Output "Reservoir queries:"
   Select-String "LOOKING FOR PASSENGERS" reservoir_conductor_test.log | Measure-Object
   
   # Count cache hits
   Write-Output "Cache hits:"
   Select-String "CACHE HIT" reservoir_conductor_test.log | Measure-Object
   ```

**Expected Success Results:**
- ✅ Cached queries: < 10ms
- ✅ Direct queries: > 50ms
- ✅ Speedup: > 5x
- ✅ Cache hit rate: > 50% (for repeated location queries)

---

### Step 6.3: Update GitHub Branch & Commit
**Purpose:** Save refactoring work

**Actions:**
1. Review all changes:
   ```powershell
   git status
   git diff
   ```

2. Stage changes:
   ```powershell
   git add commuter_service/core/domain/reservoirs/
   git add arknet_transit_simulator/vehicle/conductor.py
   git add arknet_transit_simulator/simulator.py
   git add test_conductor_vision.py
   git add benchmark_reservoir_performance.py
   git add test_multi_conductor_load.py
   git add docs/RESERVOIR_MIGRATION_GUIDE.md
   git add CONTEXT.md
   git add TODO.md
   ```

3. Commit with detailed message:
   ```powershell
   git commit -m "Refactor conductor to use RouteReservoir with Redis caching

   BREAKING CHANGE: Conductor now requires reservoir dependency injection

   Changes:
   - Added RouteReservoir.query() method with Redis caching (5s TTL)
   - Added Socket.IO event emission on passenger spawn
   - Created ReservoirManager for singleton reservoir instances
   - Updated Conductor to accept route_reservoir/depot_reservoir params
   - Modified simulator to inject reservoirs into conductor
   - Maintained backward compatibility with legacy PassengerRepository path

   Performance improvements:
   - Cached queries: ~5ms (vs 100ms direct)
   - 10-50x speedup on cache hits
   - Socket.IO events enable real-time passenger tracking

   Testing:
   - Added unit tests for reservoir query method
   - Added integration test with conductor vision
   - Added performance benchmark script
   - Added multi-conductor load test

   Documentation:
   - Updated CONTEXT.md with new architecture diagrams
   - Created RESERVOIR_MIGRATION_GUIDE.md
   - Updated TODO.md

   Closes #XXX"
   ```

4. Push to branch:
   ```powershell
   git push origin branch-0.0.3.0
   ```

**Expected Success Results:**
- ✅ All changes committed
- ✅ Detailed commit message
- ✅ Pushed to branch successfully
- ✅ No merge conflicts

---

## 🎯 Final Success Criteria Checklist

After completing all phases, verify:

### Functional Requirements
- [ ] ✅ Conductor queries passengers via RouteReservoir.query()
- [ ] ✅ Redis cache populated on first query
- [ ] ✅ Subsequent queries hit cache (< 10ms)
- [ ] ✅ Cache misses fall back to Strapi (50-200ms)
- [ ] ✅ Socket.IO events emitted on passenger spawn
- [ ] ✅ Passengers board successfully (same as baseline)
- [ ] ✅ Driver receives stop/continue signals
- [ ] ✅ Capacity management works correctly

### Performance Requirements
- [ ] ✅ Cached queries: < 10ms average
- [ ] ✅ Speedup: > 5x vs direct queries
- [ ] ✅ Cache hit rate: > 50% on repeated queries
- [ ] ✅ No memory leaks in Redis
- [ ] ✅ Handles 5+ concurrent conductors

### Architectural Requirements
- [ ] ✅ Consistent reservoir usage (writes and reads)
- [ ] ✅ Redis caching enabled and functional
- [ ] ✅ Socket.IO events implemented
- [ ] ✅ Dependency injection pattern used
- [ ] ✅ Backward compatibility maintained
- [ ] ✅ Graceful degradation if Redis unavailable

### Testing Requirements
- [ ] ✅ Unit tests pass
- [ ] ✅ Integration tests pass
- [ ] ✅ Performance benchmarks meet targets
- [ ] ✅ Load tests handle concurrent conductors
- [ ] ✅ Baseline behavior preserved

### Documentation Requirements
- [ ] ✅ CONTEXT.md updated
- [ ] ✅ TODO.md updated
- [ ] ✅ Migration guide created
- [ ] ✅ Code comments added
- [ ] ✅ Commit messages detailed

---

## 🔄 Rollback Plan

If any phase fails catastrophically:

### Phase 1-2 Rollback (Before conductor changes)
```powershell
# Revert reservoir changes only
git checkout HEAD -- commuter_service/core/domain/reservoirs/
```

### Phase 3-4 Rollback (After conductor changes)
```powershell
# Revert all changes
git checkout HEAD -- .
git clean -fd
```

### Partial Rollback (Keep reservoir, remove conductor integration)
```powershell
# Revert conductor changes only
git checkout HEAD -- arknet_transit_simulator/vehicle/conductor.py
git checkout HEAD -- arknet_transit_simulator/simulator.py
```

---

## 📊 Estimated Timeline

- **Phase 0** (Pre-Flight): 30 minutes
- **Phase 1** (Reservoir Setup): 1 hour
- **Phase 2** (Conductor Refactor): 1.5 hours
- **Phase 3** (Testing): 1 hour
- **Phase 4** (Performance): 30 minutes
- **Phase 5** (Documentation): 30 minutes
- **Phase 6** (Final Validation): 30 minutes

**Total: 5.5 hours**

---

## 🎓 Key Learning Outcomes

After completing this refactor, you will have:

1. **Consistent Architecture**: All passenger queries go through reservoirs
2. **Performance Improvement**: 10-50x faster with Redis caching
3. **Real-time Events**: Socket.IO notifications for passenger spawning
4. **Scalability**: Multiple conductors share Redis cache
5. **Observability**: Enhanced logging shows cache hits/misses
6. **Best Practices**: Dependency injection, graceful degradation, comprehensive testing

---

## 📞 Support & Troubleshooting

If you encounter issues during execution:

1. **Check logs first**: All components log detailed messages
2. **Verify services running**: Strapi, Redis, Commuter Service
3. **Test incrementally**: Don't skip phases
4. **Compare with baseline**: Use baseline_conductor_test.log as reference
5. **Review expected results**: Each step has clear success criteria

**Common Issues:**
- Redis not running → `redis-server` or `redis-server.exe`
- Strapi not accessible → Check port 1337, admin panel
- Import errors → Check Python path, virtual environment
- Cache not populating → Check Redis connection, logs
- Socket.IO events not received → Check Strapi Socket.IO server

---

**Ready to begin? Start with Phase 0! 🚀**
