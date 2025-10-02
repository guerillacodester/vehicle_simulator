# 🎯 NEXT SESSION: Integration Checklist

## Current Status

✅ **Phase 2.3 Complete:**

- PostGIS 3.5 installed and working
- Strapi 5.23.5 with GeoJSON import lifecycle hooks
- Content types: Country, POI, Place, Landuse, Region
- Depot Reservoir (OUTBOUND commuters)
- Route Reservoir (BIDIRECTIONAL commuters)
- Socket.IO infrastructure
- Conductor/Driver architecture

---

## 🔄 Integration Flow

### Step 1: Test GeoJSON Import (30 mins)

**Goal:** Verify geographic data flows into PostGIS correctly

**Actions:**

```bash
# 1. Start Strapi
cd arknet_fleet_manager/arknet-fleet-api
npm run develop

# 2. Build TypeScript
npm run build

# 3. Open Admin UI
# Browser: http://localhost:1337/admin
```

**Test Files Needed:**

- `barbados_pois_test.geojson` (10 POIs)
- `barbados_places_test.geojson` (10 places)
- `barbados_landuse_test.geojson` (5 zones)
- `barbados_regions_test.geojson` (3 regions)

**Expected Results:**

- ✅ `geodata_import_status`: "✅ POIs, ✅ Places, ✅ Landuse, ✅ Regions"
- ✅ Query `http://localhost:1337/api/pois` returns POIs
- ✅ Query `http://localhost:1337/api/landuse-zones` returns zones

---

### Step 2: Connect Spawner to Strapi API (45 mins)

**Goal:** Poisson spawner reads POIs and Landuse from database, not hardcoded GeoJSON files

**File to Modify:** `commuter_service/poisson_geojson_spawner.py`

**Current Implementation:**

```python
# OLD: Loads from local GeoJSON files
landuse_file = self.geojson_dir / f"{country_code}_landuse.geojson"
with open(landuse_file, 'r') as f:
    landuse_data = json.load(f)
```

**New Implementation:**

```python
# NEW: Fetch from Strapi API
from .strapi_api_client import StrapiApiClient

class PoissonGeoJSONSpawner:
    def __init__(self, strapi_url: str = "http://localhost:1337"):
        self.api_client = StrapiApiClient(base_url=strapi_url)
        self.population_zones: List[PopulationZone] = []
        self.amenity_zones: List[PopulationZone] = []
    
    async def load_geojson_data(self, country_code: str = "BB") -> bool:
        """Load geographic data from Strapi API"""
        try:
            # Fetch POIs
            pois = await self.api_client.get_pois(country_code)
            await self._process_pois(pois)
            
            # Fetch Landuse zones
            zones = await self.api_client.get_landuse_zones(country_code)
            await self._process_landuse_zones(zones)
            
            # Fetch Regions
            regions = await self.api_client.get_regions(country_code)
            await self._process_regions(regions)
            
            return True
        except Exception as e:
            logging.error(f"Failed to load data from API: {e}")
            return False
    
    async def _process_pois(self, pois: List[Dict]):
        """Convert POIs to amenity zones for spawning"""
        for poi in pois:
            zone = PopulationZone(
                zone_id=f"poi_{poi['id']}",
                center_point=(poi['latitude'], poi['longitude']),
                geometry=Point(poi['longitude'], poi['latitude']),
                base_population=0,  # POIs don't have population
                zone_type=poi['poi_type'],
                spawn_rate_per_hour=poi['spawn_weight'] * 10,
                peak_hours=[7, 8, 9, 16, 17, 18]
            )
            self.amenity_zones.append(zone)
    
    async def _process_landuse_zones(self, zones: List[Dict]):
        """Convert Landuse zones to population zones"""
        for zone in zones:
            # Parse GeoJSON geometry from string
            geometry_dict = json.loads(zone['geometry_geojson'])
            geometry = shape(geometry_dict)
            
            # Estimate population from zone type and area
            area_km2 = self._calculate_area_km2(geometry)
            population = self._estimate_population(zone['zone_type'], area_km2)
            
            pop_zone = PopulationZone(
                zone_id=f"landuse_{zone['id']}",
                center_point=(zone['center_lat'], zone['center_lon']),
                geometry=geometry,
                base_population=population,
                zone_type=zone['zone_type'],
                spawn_rate_per_hour=zone['spawn_weight'] * population * 0.01,
                peak_hours=[7, 8, 9, 16, 17, 18]
            )
            self.population_zones.append(pop_zone)
```

**Add to `strapi_api_client.py`:**

```python
async def get_pois(self, country_code: str) -> List[Dict]:
    """Fetch POIs for country"""
    endpoint = f"/api/pois?filters[country][code][$eq]={country_code}&populate=*"
    return await self._make_request(endpoint)

async def get_landuse_zones(self, country_code: str) -> List[Dict]:
    """Fetch landuse zones for country"""
    endpoint = f"/api/landuse-zones?filters[country][code][$eq]={country_code}&populate=*"
    return await self._make_request(endpoint)

async def get_regions(self, country_code: str) -> List[Dict]:
    """Fetch regions for country"""
    endpoint = f"/api/regions?filters[country][code][$eq]={country_code}&populate=*"
    return await self._make_request(endpoint)
```

**Expected Results:**

- ✅ Spawner loads POIs from API
- ✅ Spawner loads Landuse zones from API
- ✅ Spawning locations match database POIs
- ✅ Spawn rates respect POI `spawn_weight` field

---

### Step 3: Test Depot Spawning + Boarding (30 mins)

**Goal:** Depot commuters spawn, vehicle queries, conductor picks up

**Test Script:** `test_depot_flow.py`

```python
import asyncio
from commuter_service.depot_reservoir import DepotReservoir
from commuter_service.poisson_geojson_spawner import PoissonGeoJSONSpawner

async def test_depot_flow():
    # 1. Start depot reservoir
    depot_res = DepotReservoir(socketio_url="http://localhost:1337")
    await depot_res.start()
    
    # 2. Initialize spawner with API data
    spawner = PoissonGeoJSONSpawner(strapi_url="http://localhost:1337")
    await spawner.load_geojson_data(country_code="BB")
    
    # 3. Spawn commuters at Bridgetown depot
    for _ in range(10):
        await depot_res.spawn_commuter(
            depot_id="DEPOT_BRIDGETOWN",
            route_id="ROUTE_1A",
            depot_location=(13.0969, -59.6202),
            destination=(13.1939, -59.5342),
            priority=3
        )
    
    print("✅ Spawned 10 depot commuters")
    
    # 4. Simulate vehicle query
    await asyncio.sleep(2)
    commuters = depot_res.query_commuters_sync(
        depot_id="DEPOT_BRIDGETOWN",
        route_id="ROUTE_1A",
        vehicle_location=(13.0970, -59.6203),
        max_distance=500,
        max_count=30
    )
    
    print(f"✅ Found {len(commuters)} commuters for boarding")
    
    # 5. Simulate pickup
    for commuter in commuters[:5]:
        await depot_res.mark_picked_up(commuter.commuter_id)
    
    print("✅ Picked up 5 commuters")
    
    # 6. Check reservoir stats
    stats = depot_res.get_stats()
    print(f"✅ Stats: {stats}")
    
    await depot_res.stop()

if __name__ == "__main__":
    asyncio.run(test_depot_flow())
```

**Expected Results:**

- ✅ 10 commuters spawned
- ✅ Query returns 10 commuters (all within 500m)
- ✅ 5 commuters marked as picked_up
- ✅ Remaining queue: 5 commuters

---

### Step 4: Test Route Spawning + Pickup (30 mins)

**Goal:** Route commuters spawn bidirectionally, vehicle queries by direction

**Test Script:** `test_route_flow.py`

```python
import asyncio
from commuter_service.route_reservoir import RouteReservoir
from commuter_service.socketio_client import CommuterDirection

async def test_route_flow():
    # 1. Start route reservoir
    route_res = RouteReservoir(socketio_url="http://localhost:1337")
    await route_res.start()
    
    # 2. Spawn OUTBOUND commuters (suburb → city)
    for i in range(5):
        lat = 13.1500 + (i * 0.01)
        await route_res.spawn_commuter(
            route_id="ROUTE_1A",
            current_location=(lat, -59.5500),
            destination=(13.0969, -59.6202),
            direction=CommuterDirection.OUTBOUND
        )
    
    print("✅ Spawned 5 OUTBOUND commuters")
    
    # 3. Spawn INBOUND commuters (city → suburb)
    for i in range(5):
        lat = 13.0969 + (i * 0.01)
        await route_res.spawn_commuter(
            route_id="ROUTE_1A",
            current_location=(lat, -59.6202),
            destination=(13.1939, -59.5342),
            direction=CommuterDirection.INBOUND
        )
    
    print("✅ Spawned 5 INBOUND commuters")
    
    # 4. Vehicle traveling OUTBOUND queries
    await asyncio.sleep(2)
    outbound = route_res.query_commuters_sync(
        route_id="ROUTE_1A",
        vehicle_location=(13.1520, -59.5505),
        direction=CommuterDirection.OUTBOUND,
        max_distance=1000,
        max_count=5
    )
    
    print(f"✅ OUTBOUND query found {len(outbound)} commuters")
    
    # 5. Vehicle traveling INBOUND queries
    inbound = route_res.query_commuters_sync(
        route_id="ROUTE_1A",
        vehicle_location=(13.0980, -59.6200),
        direction=CommuterDirection.INBOUND,
        max_distance=1000,
        max_count=5
    )
    
    print(f"✅ INBOUND query found {len(inbound)} commuters")
    
    # 6. Verify direction filtering
    assert len(outbound) > 0, "Should find outbound commuters"
    assert len(inbound) > 0, "Should find inbound commuters"
    
    await route_res.stop()

if __name__ == "__main__":
    asyncio.run(test_route_flow())
```

**Expected Results:**

- ✅ 5 OUTBOUND commuters spawned
- ✅ 5 INBOUND commuters spawned
- ✅ OUTBOUND query returns only OUTBOUND commuters
- ✅ INBOUND query returns only INBOUND commuters
- ✅ Direction filtering works correctly

---

### Step 5: Integrate with Vehicle Simulator (60 mins)

**Goal:** Conductor queries reservoirs, Driver responds to stop commands

**File to Modify:** `arknet_transit_simulator/vehicle/conductor.py`

**Add Methods:**

```python
class VehicleConductor:
    def __init__(self, vehicle, socketio_url: str):
        self.vehicle = vehicle
        self.socketio_client = SocketIOClient(socketio_url, "/vehicle-events")
        self.depot_client = SocketIOClient(socketio_url, "/depot-reservoir")
        self.route_client = SocketIOClient(socketio_url, "/route-reservoir")
    
    async def query_depot_commuters(
        self,
        depot_id: str,
        route_id: str,
        max_count: int
    ):
        """Query depot reservoir for commuters"""
        response = await self.depot_client.emit_and_wait(
            "vehicle:query_commuters",
            {
                "depot_id": depot_id,
                "route_id": route_id,
                "vehicle_location": {
                    "lat": self.vehicle.position.latitude,
                    "lon": self.vehicle.position.longitude
                },
                "available_seats": max_count,
                "search_radius": 500
            },
            timeout=5.0
        )
        return response.get("commuters", [])
    
    async def query_route_commuters(
        self,
        route_id: str,
        direction: str,
        max_count: int
    ):
        """Query route reservoir for commuters"""
        response = await self.route_client.emit_and_wait(
            "vehicle:query_commuters",
            {
                "route_id": route_id,
                "vehicle_location": {
                    "lat": self.vehicle.position.latitude,
                    "lon": self.vehicle.position.longitude
                },
                "direction": direction,
                "available_seats": max_count,
                "search_radius": 1000
            },
            timeout=5.0
        )
        return response.get("commuters", [])
    
    async def update_loop(self):
        """Main conductor logic"""
        while self.running:
            capacity_remaining = self.vehicle.capacity - len(self.vehicle.passengers)
            
            # Check depot
            if self.is_at_depot():
                commuters = await self.query_depot_commuters(
                    depot_id=self.current_depot,
                    route_id=self.vehicle.route_id,
                    max_count=capacity_remaining
                )
                
                if commuters:
                    await self.board_commuters_at_depot(commuters)
            
            # Check route
            else:
                commuters = await self.query_route_commuters(
                    route_id=self.vehicle.route_id,
                    direction=self.vehicle.direction,
                    max_count=capacity_remaining
                )
                
                if commuters:
                    nearest = commuters[0]  # Closest commuter
                    distance = self.calculate_distance(
                        self.vehicle.position,
                        nearest["current_location"]
                    )
                    
                    if distance < 200:  # Within 200m
                        await self.pickup_route_commuter(nearest)
            
            await asyncio.sleep(1)
```

**Expected Results:**

- ✅ Conductor queries depot when at depot
- ✅ Conductor queries route when traveling
- ✅ Driver stops when commanded
- ✅ Passengers board correctly
- ✅ Socket.IO events flow properly

---

### Step 6: Statistical Validation (45 mins)

**Goal:** Verify spawning rates match real-world patterns

**Validation Script:** `validate_spawning_statistics.py`

```python
import asyncio
from datetime import datetime, timedelta
from commuter_service.poisson_geojson_spawner import PoissonGeoJSONSpawner

async def validate_statistics():
    spawner = PoissonGeoJSONSpawner()
    await spawner.load_geojson_data("BB")
    
    # Test 1: Peak vs. Off-peak ratio
    morning_peak = spawner.calculate_spawn_count(
        hour=8, zone_type="residential"
    )
    midday = spawner.calculate_spawn_count(
        hour=13, zone_type="residential"
    )
    
    ratio = morning_peak / midday
    print(f"Peak/Off-peak ratio: {ratio:.2f}")
    assert 2.0 < ratio < 3.0, "Should be ~2.5x"
    
    # Test 2: Residential outbound morning bias
    outbound, inbound = spawner.calculate_directional_split(
        hour=8, zone_type="residential"
    )
    print(f"Morning residential: {outbound}% outbound, {inbound}% inbound")
    assert outbound > 65, "Should be >65% outbound"
    
    # Test 3: Commercial inbound evening bias
    outbound, inbound = spawner.calculate_directional_split(
        hour=17, zone_type="commercial"
    )
    print(f"Evening commercial: {outbound}% outbound, {inbound}% inbound")
    assert inbound > 65, "Should be >65% inbound"
    
    print("✅ All statistical validations passed")

if __name__ == "__main__":
    asyncio.run(validate_statistics())
```

**Expected Results:**

- ✅ Peak/off-peak ratio: 2.0-3.0
- ✅ Morning residential: >65% outbound
- ✅ Evening commercial: >65% inbound
- ✅ Statistical patterns match real-world behavior

---

## 📋 Success Criteria

### Integration Complete When

- ✅ GeoJSON imports working (POIs, Landuse, Regions)
- ✅ Spawner reads from Strapi API (not local files)
- ✅ Depot commuters spawn and board correctly
- ✅ Route commuters spawn bidirectionally
- ✅ Conductor queries both reservoirs
- ✅ Driver responds to stop commands
- ✅ Statistical validation passes
- ✅ Socket.IO events flow end-to-end

---

## 🎯 MVP Milestone: READY FOR DEMO

Once integration complete:

- System spawns realistic commuter patterns
- Vehicles pick up passengers intelligently
- Geographic data drives everything
- No hardcoded locations
- Fully event-driven architecture
- Production-ready foundation

**Estimated Time: 3-4 hours of focused work

Next session: Let's do this! 🚀
