# GeoJSON Import System - Implementation TODO

**Project**: ArkNet Vehicle Simulator  
**Branch**: branch-0.0.2.8  
**Started**: October 25, 2025  
**Updated**: October 26, 2025 (Phase 1.12 Progress - Geospatial Client migrated to commuter_simulator)  
**Status**: ✅ TIER 1 & TIER 2 Complete | 🎯 TIER 3 Phase 1.12 (2/5 steps) | ⚠️ commuter_service → commuter_simulator migration COMPLETE  
**Strategy**: Option A - Complete Imports ✅ DONE → Enable Spawning ✅ DONE → Database Integration 🎯 IN PROGRESS

> **📌 Companion Doc**: `CONTEXT.md` - Complete project context, architecture, and user preferences  
> **📚 Reference**: `GEOJSON_IMPORT_CONTEXT.md` - Detailed file analysis (historical)

**Execution Priority**:

```text
TIER 1: Phase 1.10 (Complete GeoJSON imports) ✅ COMPLETE
TIER 2: Phase 1.11 (Geospatial Services API) ✅ COMPLETE
TIER 3: Phase 1.12 (Database Integration & Validation) 🎯 CURRENT
TIER 4: Phases 4-5-6 (Passenger spawning features) 🔜 
TIER 5: Phases 2-3 (Redis optimization + Geofencing) 🔜
TRACK:  GPS CentCom Server (Production hardening) 📡 FUTURE
```

---

## 🎯 **QUICK START FOR NEW AGENTS**

### **Where Am I?**

- **Current Focus**: TIER 3 - Database Integration & Validation
- **Phase**: Phase 1.12 (Validate spatial queries and integrate with commuter_simulator)
- **Next Immediate Task**: Test spatial queries from commuter_simulator, validate performance benchmarks
- **After Phase 1.12**: Move to Phase 4 (POI-Based Spawning)
- **Blocker**: None - All 5 GeoJSON imports COMPLETE + Geospatial API operational
- **Status**: Phase 1.11 ✅ 100% COMPLETE
  - **FastAPI Geospatial Service**: Running on port 8001
  - **16/16 integration tests passing**:
    - Health checks & API info
    - Reverse geocoding with parish (e.g., "Rockley New Road, near parking, Christ Church")
    - Geofence detection (2-4ms latency)
    - Depot catchment queries (50-100ms for 1km radius)
    - Concurrent performance validated (5 req/sec)
  - **Real-time performance**:
    - Geofence: 0.23ms avg (2.31ms max)
    - Reverse geocode: 2.46ms avg (12.88ms max)
    - Depot catchment: 94.76ms avg (121ms max)
  - **All endpoints operational**:
    - `/geocode/reverse` - Lat/lon → "Road, near POI, Parish"
    - `/geofence/check` - Point-in-polygon for regions & landuse
    - `/spatial/depot-catchment` - Buildings within radius
    - `/spatial/route-buildings` - Buildings along route buffer

**Priority Path** (Option A):

```text
Phase 1.10 (Complete imports) ✅ DONE
  → Phase 1.11 (Geospatial API) ✅ DONE
  → Phase 1.12 (Validation) 🎯 NEXT
  → Phases 4/5/6 (Spawning features)
  → Phase 2 (Redis optimization)
  → Phase 3 (Geofencing)
```

### **What Do I Need to Know?**

1. **Read CONTEXT.md first** - Contains architecture, component roles, user preferences
2. **Frontend COMPLETE** - 5 working buttons with Socket.IO handlers
3. **User prefers detailed explanations** - Quality over speed
4. **Validate at each step** - Mark checkboxes, document issues
5. **Working branch**: `branch-0.0.2.6` (NOT main)

### **Critical Constraints**

- 🚨 **PostGIS MANDATORY** - All spatial tables must use geometry columns
- 🚨 **GIST indexes required** - For all PostGIS geometry columns
- 🚨 **GTFS compliance** - Follow GTFS standards for stops, shapes, routes
- 🚨 **Buildings table REQUIRED** - Foundation for realistic passenger spawning (see CONTEXT.md "Passenger Spawning Architecture")
- 🚨 **commuter_simulator is active** - `commuter_service_deprecated/` is DEPRECATED (DO NOT USE)
- ⚠️ **Streaming parser required** - building.geojson = 658MB (cannot load into memory)
- ⚠️ **All 5 datasets needed** - Buildings, Landuse, Amenities, Admin, Highways work together for spawning model
- ⚠️ **Centroid extraction required** - amenity.geojson has MultiPolygon, schema expects Point
- ⚠️ **Don't break spawn rate** - Currently calibrated to 100/hr

### **Files to Read Before Starting**

1. `CONTEXT.md` - **READ "PASSENGER SPAWNING ARCHITECTURE" AND "DATABASE ARCHITECTURE ISSUES" SECTIONS FIRST**
2. `commuter_simulator/README.md` - New architecture (Single Source of Truth pattern) ✅ **ACTIVE**
3. `arknet_fleet_manager/arknet-fleet-api/migrate_all_to_postgis.sql` - Migration script
4. `src/admin/button-handlers.ts` - Frontend handlers (387 lines)
5. `src/api/geojson-import/controllers/geojson-import.ts` - All import endpoints (uses PostGIS)

**Note**: `commuter_service_deprecated/` folder is retained for reference only - DO NOT USE in new development

---

## 📊 **OVERALL PROGRESS**

**Priority Sequence**: Option A - Complete GeoJSON Import → Enable Spawning → Optimize Performance

### **🎯 TIER 1: IMMEDIATE - GeoJSON Import System (Current Focus)**

- [x] **Phase 1.1-1.9**: Foundation & Buildings Import ✅ COMPLETE (Oct 25-26, 2025)
  - ✅ Country schema + action buttons (5 buttons in UI)
  - ✅ Backend API + PostGIS migration (11 tables, 12 GIST indexes)
  - ✅ Buildings imported (162,942 records at 1166 features/sec, 658MB file)
  - ✅ Admin levels normalized (4 levels with UI dropdown)
  - ✅ Streaming parser created and working (geojson-stream-parser.ts)

- [x] **Phase 1.10**: Optimize Remaining Import Endpoints (5/5 tasks) ✅ **COMPLETE** (Oct 26, 2025)
  - [x] Building import with streaming ✅ COMPLETE (162,942 records, 658MB, 1166 features/sec)
  - [x] **Admin import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Schema normalization: Removed redundant `code` and `region_type` fields
    - ✅ Float precision: Changed center_lat/lon from `decimal` to `float` (preserves 7+ decimals)
    - ✅ Area calculation: PostGIS ST_Area(geography) / 1000000 for accurate km²
    - ✅ All 4 levels imported: 11 Parish, 5 Town, 136 Suburb, 152 Neighbourhood = 304 regions
    - ✅ Validation: 432.98 km² vs 432 km² official (+0.2% accuracy)
    - ✅ Junction tables: 304 admin_level links, 304 country links
    - ✅ Integration tests: 17/17 passing
  - [x] **Highway import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Performance optimization: Post-batch region linking (removed per-batch spatial queries)
    - ✅ 22,719 highways imported (all LineString geometries, SRID 4326)
    - ✅ Junction tables: 22,719 country links, 23,666 region links
    - ✅ 947 highways cross parish boundaries (validated by link count > highway count)
    - ✅ Spatial queries working: 12,385 highways within 10km of Bridgetown
    - ✅ Integration tests: 16/16 passing
  - [x] **Amenity import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Column fix: Removed non-existent `poi_id` and `full_id` columns
    - ✅ Binding fix: Corrected placeholder count (11 bindings, not 12)
    - ✅ Post-batch linking: Country links + region links after streaming completes
    - ✅ 1,427 POIs imported (all Point geometries extracted from Polygon/MultiPolygon centroids)
    - ✅ Junction tables: 1,427 country links, 1,427 region links
    - ✅ Amenity types: 399 parking, 254 worship, 133 restaurant, 111 school, 99 bar, 44 fuel, etc.
    - ✅ Spatial queries working: 652 POIs within 5km of Bridgetown
    - ✅ Integration tests: 17/17 passing
  - [x] **Landuse import with streaming** ✅ COMPLETE (Oct 26, 2025)
    - ✅ Fixed column mismatch: Removed non-existent `zone_id` and `full_id` columns
    - ✅ Fixed geometry type: Changed geom column from Polygon to GEOMETRY (accepts both Polygon and MultiPolygon)
    - ✅ Post-batch linking: Country links + region links after streaming completes
    - ✅ 2,267 zones imported (Polygon and MultiPolygon geometries, SRID 4326)
    - ✅ Junction tables: 2,267 country links, 2,310 region links
    - ✅ 43 zones cross parish boundaries (validated by link count > zone count)
    - ✅ Zone types: 937 farmland, 513 grass, 160 meadow, 144 residential, 65 forest/industrial, etc.
    - ✅ Spatial queries working: 343 zones within 5km of Bridgetown
    - ✅ Integration tests: 16/16 passing
  - **Summary**: ✅ ALL 5 IMPORTS 100% COMPLETE
    - **Total features**: 189,659 (162,942 buildings + 304 regions + 22,719 highways + 1,427 POIs + 2,267 landuse)
    - **All junction tables**: Country links (189,659) + region links (27,707) operational
    - **All integration tests**: 82 Strapi tests passing (17 admin + 16 highway + 17 amenity + 16 landuse + building)
    - **All spatial indexes**: GIST indexes on all geometry columns
    - **All PostGIS geometries**: Valid with SRID 4326
    - **Boundary crossings detected**: 990 features (947 highways + 43 landuse zones)
    - **Performance**: Streaming parsers handle large files (658MB building.geojson) efficiently
    - **Cleanup**: Removed temporary check_buildings_schema.py and check_landuse_schema.py validation scripts

### **🎯 TIER 2: FOUNDATION - Enable Spawning Queries (Required for Simulator)**

- [x] **Phase 1.11**: Geospatial Services API (7/7 steps) ✅ **COMPLETE** (Oct 26, 2025)
  - [x] Created FastAPI geospatial_service with asyncpg connection pooling
  - [x] Implemented PostGIS query optimization (bbox + geography distance pattern)
  - [x] Built reverse geocoding endpoint (highway + POI + parish)
  - [x] Built geofence check endpoints (region & landuse containment)
  - [x] Built depot catchment endpoint (buildings within radius)
  - [x] Built route buildings endpoint (buildings along route buffer)
  - [x] Created integration test suite (16/16 tests passing)
  - **Performance validated for real-time async usage**:
    - Geofence: 0.23ms avg (sub-millisecond!)
    - Reverse geocode: 2.46ms avg (with parish included)
    - Depot catchment: 94.76ms avg (1km radius, 3000+ buildings)
  - **Address format**: "Road name, near POI, Parish" (e.g., "Rockley New Road, near parking, Christ Church")
  - **Endpoints operational**:
    - `GET/POST /geocode/reverse` - Reverse geocoding with parish
    - `POST /geofence/check` - Point-in-polygon checks
    - `POST /geofence/check-batch` - Batch geofence checks
    - `GET/POST /spatial/depot-catchment` - Buildings near depot
    - `POST /spatial/route-buildings` - Buildings along route
  - **Database optimizations**:
    - Bounding box prefilter using ST_MakeEnvelope (GIST index friendly)
    - Geography distance only on small result sets
    - Longitude degree conversion adjusted by cos(latitude)
    - In-memory TTL cache (5s) for repeated identical queries

- [ ] **Phase 1.12**: Database Integration & Validation (2/5 steps) 🎯 **CURRENT**
  - [x] Create API client wrapper for commuter_simulator
    - ✅ `commuter_simulator/infrastructure/geospatial/client.py` - Python client wrapper
    - ✅ Tested: reverse geocoding (105ms), geofencing (3ms), depot catchment (55ms)
    - ✅ Test: `commuter_simulator/tests/integration/test_geospatial_api.py`
  - [x] Test spatial queries from commuter_simulator spawning logic
    - ✅ Integration test: `commuter_simulator/tests/integration/test_geospatial_api.py`
    - ✅ Reverse geocoding: 4-20ms (fast enough for real-time)
    - ✅ Geofence checks: 3-5ms (sub-50ms target met)
    - ✅ Building queries: 13-59ms (good performance)
    - ✅ Depot catchment: 7-54ms (suitable for spawning)
    - ✅ Concurrent load: 0.5 queries/sec (20 concurrent)
    - ⚠️ Note: commuter_service_deprecated folder retained for reference only
  - [ ] Validate performance under realistic load (100+ vehicles)
  - [ ] Document API endpoints for other services
  - [ ] Validate all spatial indexes are used (EXPLAIN ANALYZE)

### **🎯 TIER 3: ADVANCED FEATURES - Passenger Spawning System**

- [ ] **Phase 4**: POI-Based Spawning (0/18 steps)
  - Requires: Phase 1.11 (Geospatial API)
  - Activity-based passenger generation

- [ ] **Phase 5**: Depot/Route Spawners (0/11 steps)
  - Requires: Phase 1.11 (Geospatial API)
  - ST_DWithin queries for proximity spawning

- [ ] **Phase 6**: Conductor Communication (0/7 steps)
  - Requires: Phase 5 (active spawning)
  - Vehicle-passenger interaction

### **🎯 TIER 4: PRODUCTION DEPLOYMENT - Infrastructure & Scaling**

- [ ] **Phase 2**: Redis Integration (0/12 steps) - **MANDATORY for 1,200 Vehicles**
  - **When**: Required before deploying to production (100+ vehicles)
  - **Why**: Position buffering, shared state, horizontal scaling
  - **Server Requirements**: See production deployment section below
  - [ ] Install Redis on production server
  - [ ] Configure Redis for persistence (AOF + RDB)
  - [ ] Implement position buffering (reduce PostgreSQL writes 10×)
  - [ ] Add shared session state for GPS CentCom cluster
  - [ ] Implement device heartbeat tracking (TTL-based)
  - [ ] Add reverse geocoding cache (1 hour TTL)
  - [ ] Configure Redis connection pooling
  - [ ] Test failover scenarios
  - [ ] Implement batch writes from Redis to PostgreSQL
  - [ ] Add monitoring for Redis memory usage
  - [ ] Document Redis backup procedures
  - [ ] Load test with simulated 1,200 devices

- [ ] **Phase 3**: GPS CentCom Cluster Mode (0/8 steps) - **REQUIRED for 1,200 Vehicles**
  - **When**: Required before 200+ vehicles
  - **Why**: Single Node.js process can't handle 1,200 connections
  - [ ] Implement Node.js cluster mode (6-8 workers)
  - [ ] Configure worker process management (PM2 or systemd)
  - [ ] Implement Redis-based session sharing
  - [ ] Add Nginx load balancing across workers
  - [ ] Implement rolling restart mechanism (zero downtime)
  - [ ] Add worker health checks and auto-restart
  - [ ] Test with 1,200 simulated concurrent connections
  - [ ] Document cluster architecture and scaling limits

### **🎯 TIER 5: OPTIMIZATION - Performance Enhancement**

- [ ] **Phase 4**: Geofencing & Real-Time Alerts (0/8 steps)
  - **When**: After Phase 2 (Redis) complete
  - **Why**: Operator notifications for zone violations
  - [ ] Implement geofence pub/sub (Redis channels)
  - [ ] Add zone enter/exit detection logic
  - [ ] Create operator alert dashboard
  - [ ] Add SMS/email notification integration
  - [ ] Implement geofence assignment UI
  - [ ] Add historical geofence violation logs
  - [ ] Test with 100+ vehicles crossing zones
  - [ ] Document alerting workflows

### **🎯 TIER 6: SUBSCRIPTION & ANALYTICS - Historical Data API (Revenue Stream)**

- [ ] **Phase 7**: Subscription Management System (0/12 steps) - **MONETIZATION**
  - [ ] Create subscription_plans table (plan_name, price, retention_days, features)
  - [ ] Create vehicle_subscriptions table (vehicle_id, plan_id, start_date, status)
  - [ ] Implement subscription API endpoints (create, update, cancel, status)
  - [ ] Add billing integration (Stripe/PayPal API)
  - [ ] Create usage tracking (API calls, storage consumption)
  - [ ] Implement rate limiting per subscription tier
  - [ ] Add subscription dashboard (admin view: revenue, active subscribers)
  - [ ] Create customer portal (upgrade/downgrade plans, view usage)
  - [ ] Implement grace period for expired subscriptions (3 days)
  - [ ] Add automated email notifications (payment failed, expiring soon)
  - [ ] Test subscription lifecycle (trial → paid → expired → renewed)
  - [ ] Document pricing model and API quotas

- [ ] **Phase 8**: Historical Position Storage (0/10 steps) - **PAID FEATURE**
  - [ ] Create position_history table with partitioning (by month)
  - [ ] Implement conditional write logic (only for paid subscribers)
  - [ ] Add data retention policy (auto-delete based on subscription tier)
  - [ ] Create background job for Redis → PostgreSQL batch writes
  - [ ] Implement time-series indexes (BRIN for timestamp ranges)
  - [ ] Add storage monitoring (track GB per vehicle per month)
  - [ ] Test with simulated 30-day retention (600 vehicles × 17K positions/day)
  - [ ] Optimize query performance for historical range queries
  - [ ] Add data export API (CSV, JSON, GeoJSON)
  - [ ] Document storage costs per tier ($0.50-5/vehicle/month)

- [ ] **Phase 9**: Analytics API (0/15 steps) - **PAID FEATURE**
  - [ ] Route replay endpoint: GET /api/vehicles/{id}/history?start={ts}&end={ts}
  - [ ] Heat map endpoint: GET /api/analytics/heatmap?zone={id}&timerange={7d}
  - [ ] Distance traveled: GET /api/analytics/distance?vehicle={id}&period={daily/weekly}
  - [ ] Idle time analysis: GET /api/analytics/idle?threshold={5min}
  - [ ] Geofence violations: GET /api/analytics/violations?zone={id}
  - [ ] Speed analytics: GET /api/analytics/speed?vehicle={id}&threshold={80kph}
  - [ ] Aggregated fleet metrics: GET /api/analytics/fleet/summary
  - [ ] Time-of-day analysis: GET /api/analytics/tod?metric={speed/distance}
  - [ ] Implement caching layer (Redis) for expensive analytics queries
  - [ ] Add API authentication (JWT tokens per subscription)
  - [ ] Rate limiting (1000 req/day Basic, unlimited Enterprise)
  - [ ] Create visualization widgets (charts, maps, tables)
  - [ ] Test analytics with 30 days of historical data
  - [ ] Document all analytics endpoints (OpenAPI/Swagger)
  - [ ] Benchmark query performance (<2s for 30-day aggregations)

- [ ] **Phase 10**: Temporal Profile System (0/8 steps) - **ANALYTICS ENHANCEMENT**
  - Create temporal_profiles table (hour, day, rate_multiplier)
  - Define peak patterns (morning rush 7-9am, evening rush 4-7pm)
  - Create seasonal_variations table (month, holiday, multiplier)
  - Link profiles to POI types (school, office, retail, etc.)
  - Import historical patterns (if data becomes available)
  - Validation: Compare simulated vs historical demand curves

- [ ] **Phase 11**: Ridership Data Collection (0/10 steps) - **ANALYTICS ENHANCEMENT**
  - Create ridership_observations table (timestamp, location, passenger_count, route_id)
  - Create passenger_demand_history table (zone_id, hour, day, avg_count, std_dev)
  - Build import pipeline for CSV/Excel ridership data
  - Create API endpoints for manual data entry
  - Implement data validation (outlier detection, consistency checks)
  - Link observations to zones/POIs/routes
  - Generate heat maps and demand visualizations
  - Train ML models on historical data (future: replace Poisson with learned rates)
  - Export calibrated spawn_weights back to landuse/POI tables
  - Dashboard for ridership analytics

**Note**: Current GeoJSON data (189,659 features) provides 80% of spawning model needs. Phase 10-11 adds the missing 20% (temporal patterns, actual ridership) when real-world data becomes available. The existing spawn_weight, peak_hour_multiplier fields in POI/landuse schemas are placeholders ready for calibrated values.

---

## 🖥️ **PRODUCTION DEPLOYMENT REQUIREMENTS**

### **Current Development Server**

- **OVH VPS vps2023-le-2**: 2 vCores, 2 GB RAM, 40 GB Storage
- **Suitable for**: MVP development, real-time tracking demo with **30-50 vehicles**
- **NOT suitable for**: Production deployment at 1,200 vehicle scale

**MVP Capacity Analysis (Real-Time Demo, No Position Storage):**

```text
Memory allocation:
├─ PostgreSQL: ~300 MB (routes, stops, POIs - NO position history)
├─ Strapi: ~300 MB (single instance)
├─ GPS CentCom: ~100 MB + (devices × 20 KB in-memory state)
├─ Geospatial API: ~150 MB
├─ System/OS: ~200 MB
└─ Available for devices: ~950 MB

Capacity:
├─ Conservative (stable): 30-40 vehicles (80% RAM utilization)
├─ Aggressive (max): 50-60 vehicles (95% RAM utilization)
└─ Bottleneck: RAM (not CPU or storage)

Performance expectations:
├─ Position updates: <100ms latency (WebSocket in-memory)
├─ Dashboard queries: <50ms (query in-memory store, not database)
├─ Geospatial queries: <100ms (PostGIS with indexes)
└─ No disk I/O bottleneck (no position writes)

Note: Position data storage is SUBSCRIPTION-BASED (free tier = real-time only, paid tier = history + analytics)
      Free MVP demo: In-memory tracking only | Paid tiers: 7/30/90/365 day retention with analytics API
```

### **Production Scaling Requirements (1,200 Vehicles)**

**Target Fleet Size**: 1,200 GPS devices (ESP32/STM32 with Rock S0 GPS module)  
**Update Frequency**: 1 position/5 seconds  
**Base Load**: 240 position updates/second (in-memory state updates)  
**Dashboard**: 5-10 operators monitoring fleet  
**Business Model**: Free tier (real-time only) + Subscription tiers (historical data + analytics)  
**Position Storage**: Subscription-based (PostgreSQL/InfluxDB for paid tiers, ephemeral for free tier)

#### **Minimum Single Server Option**

**OVH VPS Scale-3 or Advance-2:**

- **12+ vCores** minimum
- **48-64 GB RAM** minimum
- **500 GB SSD** minimum
- **Cost**: ~$150-300/month
- **Capacity**: 800-1,200 vehicles (at limit)
- **Risk**: Single point of failure

**Software Stack:**

```text
├─ GPS CentCom (Node.js Cluster - 6-8 workers)
├─ Strapi (2 instances for HA)
├─ Geospatial API (FastAPI - 1-2 instances)
├─ PostgreSQL (with connection pooling)
├─ Redis (6-8 GB allocated)
└─ Nginx (reverse proxy + load balancer)
```

#### **Recommended Multi-Server Option (High Availability)**

**3× OVH VPS Scale-2:**

- **4 vCores each, 8 GB RAM each, 160 GB SSD each**
- **Cost**: ~$120-180/month total
- **Capacity**: 1,200+ vehicles (400 per server)
- **Benefit**: High availability, horizontal scaling, redundancy, <5 second failover

**Distribution:**

```text
Server 1 (VPS Scale-2):
├─ GPS CentCom Workers 1-2 (400 devices)
├─ Redis MASTER + Sentinel
├─ Strapi Instance 1
├─ PostgreSQL Read Replica (geospatial queries)
└─ Nginx (reverse proxy)

Server 2 (VPS Scale-2):
├─ GPS CentCom Workers 3-4 (400 devices)
├─ Redis REPLICA + Sentinel
├─ Strapi Instance 2
├─ PostgreSQL Read Replica (dashboard queries)
└─ Nginx (reverse proxy)

Server 3 (VPS Scale-2):
├─ GPS CentCom Workers 5-6 (400 devices)
├─ Redis REPLICA + Sentinel
├─ PostgreSQL PRIMARY (write master)
├─ Geospatial API (FastAPI)
└─ Nginx (reverse proxy)

External Load Balancer (CloudFlare or OVH)
```

**Database Synchronization Strategy:**

**PostgreSQL (Single Write Master + Read Replicas):**

```text
All Writes → PostgreSQL Primary (Server 3)
   ↓ Streaming Replication (<100ms lag)
   ├→ Read Replica 1 (Server 1) - Geospatial queries
   └→ Read Replica 2 (Server 2) - Dashboard queries

Configuration:
- Primary: wal_level=replica, max_wal_senders=3
- Replicas: hot_standby=on
- Failover: Automatic with repmgr or Patroni
- No sync conflicts (one-way replication)
```

**Redis (Sentinel HA with Auto-Failover):**

```text
Redis Master (Server 1) - All writes
   ↓ Async replication
   ├→ Redis Replica (Server 2)
   └→ Redis Replica (Server 3)

Sentinels (all 3 servers) monitor master health:
- Quorum: 2/3 votes required for failover
- Detection: 5 seconds down-after-milliseconds
- Failover: Automatic promotion of replica to master
- Downtime: ~10 seconds for automatic failover
```

**Strapi (Active-Active with Shared PostgreSQL):**

```text
Load Balancer
   ├→ Strapi Instance 1 (Server 1) ──┐
   └→ Strapi Instance 2 (Server 2) ──┤
                                      ↓
                   PostgreSQL Primary (Server 3)

- Both instances read/write SAME database (no sync needed)
- Sessions stored in Redis Master (shared state)
- File uploads: Shared volume or S3 bucket
- No data conflicts (single source of truth)
```

**Failover Scenarios:**

| Failure | Detection | Recovery | Downtime | Impact |
|---------|-----------|----------|----------|--------|
| Redis Master dies | Sentinel quorum (5s) | Auto-promote replica | ~10 seconds | In-memory state sync delay |
| PostgreSQL Primary dies | Health check (10s) | Manual/auto promote replica | 30-60 seconds | Reads continue from replicas |
| Entire Server 1 dies | Load balancer (5s) | Route to Server 2/3 | <5 seconds | 400 devices → 600 each temp |
| Network partition | Split-brain detection | Sentinel quorum prevents | N/A | State updates paused |

**Position Storage & Monetization Strategy:**

**Free Tier (Real-Time Only):**

- In-memory state only (current position, route, driver, status)
- Real-time dashboard access
- No historical data retention
- Suitable for: Live tracking, dispatch operations, real-time monitoring

**Subscription Tier (Historical Data + Analytics):**

- Position history storage (PostgreSQL or InfluxDB/TimescaleDB)
- Configurable retention (7 days, 30 days, 90 days, 1 year)
- Analytics API endpoints (route replay, heat maps, performance metrics)
- Reports & visualizations (distance traveled, idle time, geofence violations)
- Data export (CSV, JSON, GeoJSON)
- Monthly fee covers: Storage costs + analytics processing + API access

**Technical Implementation:**

- **Option A**: PostgreSQL with Redis buffer (short-term: 7-30 days retention)
  - Use case: Recent history, basic analytics, route replay
  - Cost: ~$0.50-2/vehicle/month (storage + compute)

- **Option B**: InfluxDB/TimescaleDB (long-term: 90 days - 1 year retention)
  - Use case: Advanced analytics, trend analysis, compliance reporting
  - Cost: ~$2-5/vehicle/month (time-series optimization, higher storage)

- **Option C**: Hybrid (Redis → PostgreSQL → Cold Storage/S3)
  - Use case: Multi-tier retention (hot: 7 days, warm: 30 days, cold: 1 year)
  - Cost: ~$1-3/vehicle/month (tiered pricing based on access frequency)

**Pricing Model Examples:**

```text
Free Tier:
├─ Real-time tracking only
├─ Current position data
└─ $0/month per vehicle

Basic Plan ($5/vehicle/month):
├─ 7 days position history
├─ Basic analytics (distance, idle time)
├─ Route replay
└─ CSV export

Professional Plan ($15/vehicle/month):
├─ 30 days position history
├─ Advanced analytics (heat maps, performance)
├─ API access (1000 req/day)
├─ Automated reports
└─ GeoJSON export

Enterprise Plan ($30/vehicle/month):
├─ 1 year position history
├─ Full analytics suite
├─ Unlimited API access
├─ Custom integrations
├─ SLA guarantee (99.9% uptime)
└─ Dedicated support
```

**Revenue Projection (1,200 vehicles):**

```text
Scenario 1 (Conservative - 30% paid subscribers):
├─ 360 vehicles × $15/month (Professional) = $5,400/month
├─ Infrastructure costs: ~$200-300/month (single server)
└─ Net revenue: ~$5,100/month

Scenario 2 (Moderate - 50% paid subscribers):
├─ 600 vehicles × $15/month (Professional) = $9,000/month
├─ Infrastructure costs: ~$300-400/month (upgraded server)
└─ Net revenue: ~$8,600/month

Scenario 3 (High adoption - 70% paid subscribers):
├─ 840 vehicles × $15/month (Professional) = $12,600/month
├─ Infrastructure costs: ~$400-500/month (multi-server)
└─ Net revenue: ~$12,100/month
```

**Why Multi-Server vs Single Server:**

| Aspect | Single Server (Advance-2) | Multi-Server (3× Scale-2) |
|--------|---------------------------|---------------------------|
| **Cost** | ~$200/month | ~$150/month total |
| **Complexity** | Low (no sync needed) | Medium (sync configuration) |
| **Availability** | 99% (single point of failure) | 99.9% (survives server failure) |
| **Acceptable Downtime** | 30-60 minutes (hardware failure) | <5 seconds (automatic failover) |
| **Suitable for** | MVP, Pilot, cost-sensitive | Production SLA, mission-critical |
| **Management Effort** | Low | Medium (monitoring, failover testing) |
| **Position Storage Impact** | None (in-memory only) | None (in-memory only) |

**Recommendation**: Start with **Single Server** for MVP/Pilot (handles 50-100 vehicles with in-memory state). Migrate to **Multi-Server** when:

- You have >500 active vehicles
- SLA requires <5 minute downtime
- You decide to store position history (adds write load)
- You have operational experience to manage distributed systems
- Budget allows for monitoring/alerting infrastructure

### **Redis Requirements**

**Why Redis is MANDATORY for 1,200 vehicles:**

1. **In-memory state sharing**: GPS CentCom workers share device state across processes
2. **Dashboard performance**: Query 1,200 positions in <5ms (vs 100-200ms from PostgreSQL)
3. **Device heartbeat**: TTL-based online/offline detection
4. **Session state**: Shared sessions across Strapi instances
5. **Horizontal scaling**: Required for multi-server deployment
6. **Optional position buffering**: IF storing position history (TBD for production)

**Memory sizing (in-memory state only, no position storage):**

```text
1,200 vehicle current positions × 200 bytes = 240 KB (current state)
Device metadata (route, driver, etc.) × 1,200 = ~500 KB
Session data, heartbeats: ~200 MB
Dashboard cache: ~100 MB
Total: ~300 MB active data + 50% overhead = 450 MB minimum
Recommended allocation: 1-2 GB (comfortable headroom)

IF storing position trails (100 positions per vehicle):
Position trails: 100 × 200 bytes × 1,200 = 24 MB additional
Total with trails: ~500 MB + 50% overhead = 750 MB
Recommended allocation with trails: 2-4 GB
```

### **PostgreSQL Requirements**

**Connection pooling (PgBouncer):**

- Max connections: 100
- Pool size: 20-30
- Writes: Configuration data only (routes, stops, POIs)
- NO position writes (in-memory only for MVP)

**Storage (no position history):**

```text
Base schema + indexes: ~500 MB
GeoJSON data (189,659 features): ~4.5 GB
Routes, stops, schedules: ~500 MB
Total: ~5.5 GB (static - no growth)

IF position history added later:
1,200 vehicles × 17,280 updates/day = 20,736,000 positions/day
Daily growth: ~2 GB
Monthly growth: ~60 GB
Recommended: 500 GB minimum, with rotation/archival after 6 months
```

### **Development → Production Migration Path**

#### Phase 1: MVP Demo (Current - 2 vCore, 2 GB)

- ✅ Real-time tracking demo with **30-50 vehicles**
- ✅ In-memory state only (no position storage)
- ✅ Single GPS CentCom worker (no cluster mode)
- ✅ No Redis needed (in-memory store sufficient)
- ✅ All features work for demo/testing
- ⚠️ NOT suitable for production (no redundancy, limited capacity)

#### Phase 2: Prototype Testing (Upgrade to VPS Scale-2)

- 🎯 4 vCores, 8 GB RAM, 160 GB SSD (~$40-60/month)
- 🎯 **100-200 vehicles** capacity
- 🎯 Add Redis (1-2 GB allocation)
- 🎯 Test GPS CentCom cluster mode (2-4 workers)
- 🎯 Deploy 5-20 real prototype devices
- 🎯 Decide on position storage strategy (PostgreSQL vs InfluxDB vs ephemeral)

#### Phase 3: Pilot Deployment (Upgrade to VPS Scale-3)

- 🎯 8-12 vCores, 32 GB RAM, 400 GB SSD (~$100-150/month)
- 🎯 **500-800 vehicles** capacity
- 🎯 Redis + GPS CentCom cluster operational
- 🎯 Limited production fleet
- 🎯 Position storage implemented (if needed)
- 🎯 Monitoring and alerting configured

#### Phase 4: Full Production (VPS Advance-2 or 3× Scale-2)

- 🎯 12+ vCores, 64 GB RAM, 500 GB SSD (single server ~$200/month)
- 🎯 OR: 3× Scale-2 with load balancer (multi-server ~$150/month)
- 🎯 **1,200 vehicles** full deployment
- 🎯 Redis cluster (2-4 GB), PostgreSQL replica (if storing positions), full monitoring

### **Critical Pre-Production Checklist**

Before deploying to production with real GPS devices:

**Single Server Deployment (VPS Advance-2):**

- [ ] Server upgraded to minimum VPS Advance-2 (12 vCore, 64 GB RAM, 500 GB SSD)
- [ ] Redis installed and configured with persistence (RDB + AOF)
- [ ] GPS CentCom cluster mode implemented and tested (6-8 workers)
- [ ] PostgreSQL connection pooling configured (PgBouncer: 20-30 connections)
- [ ] Monitoring and alerting configured (CPU, RAM, disk, connection counts)
- [ ] Backup procedures documented and automated (PostgreSQL + Redis snapshots)
- [ ] Load tested with 1,200 simulated concurrent connections
- [ ] Disaster recovery plan documented (backup restoration SLA)
- [ ] Rolling deployment procedure tested

**Multi-Server Deployment (3× VPS Scale-2) - Additional Requirements:**

- [ ] PostgreSQL streaming replication configured (Primary → 2 Replicas)
- [ ] Redis Sentinel configured on all 3 servers (quorum: 2/3)
- [ ] Strapi session storage moved to Redis (shared state)
- [ ] Load balancer configured with health checks (CloudFlare or Nginx)
- [ ] Failover testing completed:
  - [ ] Redis master failure → auto-promote replica (<10s)
  - [ ] PostgreSQL primary failure → promote replica (<60s)
  - [ ] Entire server failure → load balancer routes traffic (<5s)
- [ ] Network partition handling tested (split-brain scenarios)
- [ ] Cross-server monitoring configured (centralized dashboard)
- [ ] Automated failover documented (runbooks for manual intervention)

---

## 📡 **GPS CENTCOM PRODUCTION READINESS**

- ✅ **Current Status**: MVP Demo Ready (FastAPI + WebSocket + In-Memory Store)
- [ ] **Future Tier 1**: Production-Grade Improvements
  - Persistent datastore (Redis or Postgres)
  - Per-device authentication tokens
  - Structured logging (JSON)
  - Basic metrics (Prometheus)
- [ ] **Future Tier 2**: Scale to Real Fleet
  - Horizontal scaling (Redis cluster)
  - Encrypted payloads (AESGCM server-side)
  - Advanced monitoring (Grafana/ELK)
  - CI/CD pipeline with tests

**Total Progress**: 18/92 major steps across GeoJSON + Spawning phases (Building import complete Oct 26)
**GPS CentCom**: Separate track, deferred until simulator fully functional

---

## 📡 **GPS CENTCOM SERVER STATUS**

**Location**: `gpscentcom_server/`  
**Technology**: FastAPI + WebSocket + In-Memory Store  
**Port**: 5000  
**Status**: ✅ MVP Demo Ready (production deployment exists)

### **Current Capabilities**

✅ **Core Features**:

- Real-time WebSocket telemetry ingestion (`/device` endpoint)
- REST APIs for device queries (`/devices`, `/device/{id}`, `/route/{code}`, `/analytics`)
- Auto-cleanup of stale devices (120s timeout)
- Plugin-based GPS device (simulation, ESP32, file replay, navigator)
- PING/PONG keepalive handling
- Structured error responses (ErrorRegistry)
- CORS enabled for cross-origin requests
- Socket.IO progress events during import operations
- Production deployment (Systemd + Nginx reverse proxy)

✅ **Data Model**:

- DeviceState with Pydantic validation
- Route-based filtering and analytics
- Lat/lon, speed, heading, timestamp tracking
- Driver/conductor metadata support

### **Known Limitations** (See CONTEXT.md for details)

❌ **Critical Production Gaps**:

1. **No persistence** - In-memory only, data lost on restart
2. **Shared auth token** - All devices use same `AUTH_TOKEN`
3. **No horizontal scaling** - Single-process limitation
4. **No AESGCM server support** - Binary codec exists client-side but not server-side
5. **No monitoring/metrics** - No Prometheus, no structured logging
6. **No rate limiting** - Vulnerable to DoS attacks
7. **No unit tests** - Zero automated testing

### **Production Roadmap** (from `gpscentcom_server/TODO.md`)

**MVP Production Grade** (safe for staging/investor pilots):

- [ ] Persistent datastore (Redis or Postgres) - **HIGH PRIORITY**
- [ ] Structured logging (JSON logs for cloud platforms)
- [ ] Basic metrics (Prometheus)
- [ ] TLS/HTTPS termination (wss://)
- [ ] Per-device identifiers + token pairs
- [ ] Unit tests for core modules
- [ ] Graceful shutdown improvements

**MVP Complete** (foundation for real deployment):

- [ ] Horizontally scalable store (Redis cluster/Postgres HA)
- [ ] Per-device authentication & key management
- [ ] Encrypted payloads (AES/TLS end-to-end)
- [ ] Replay protection / integrity checks
- [ ] Advanced monitoring & alerts (Grafana/ELK)
- [ ] CI/CD pipeline with tests
- [ ] Extensible codec framework (CBOR, protobuf)

### **Integration with Vehicle Simulator**

**Current Flow**:

```text
arknet_transit_simulator
  └─ vehicle/gps_device/
       ├─ Plugin Manager (simulation/ESP32/file/navigator)
       ├─ RxTx Buffer (FIFO queue, max 1000 items)
       ├─ WebSocketTransmitter
       └─ PacketCodec (JSON/AESGCM)
            ↓
            ws://server:5000/device?token=xxx&deviceId=yyy
            ↓
gpscentcom_server
  ├─ rx_handler.py (WebSocket endpoint)
  ├─ connection_manager.py (lifecycle management)
  ├─ store.py (in-memory DeviceState)
  └─ api_router.py (REST endpoints)
       ↓
       GET /devices → Dashboard
```

**Recommendation**:

- ✅ Use now for development, testing, and demos (10-50 vehicles)
- ❌ Don't deploy to real vehicles without Redis + per-device auth
- 🎯 Priority if moving to production: Redis storage, per-device tokens, Prometheus metrics

---

## 🎨 **PHASE 1: COUNTRY SCHEMA + ACTION BUTTONS**

**Goal**: Update country schema, add action buttons, migrate successfully, verify UI

### **STEP 1.1: Analyze Current State** ⏱️ 30 min

- [x] **1.1.1** Read current country schema
  - File: `arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/schema.json`
  - Document existing fields
  - ✅ COMPLETED: Schema analyzed (113→145 lines)
  - ✅ COMPLETED: Database verified (16 columns in `countries` table)
  - ✅ COMPLETED: Migrated `geodata_import_status` from text→json with structured default
  - ✅ COMPLETED: Cleared old data, ready for fresh import tracking
  
- [x] **1.1.2** Verify action-buttons plugin exists
  - Path: `src/plugins/strapi-plugin-action-buttons/`
  - Plugin name: `strapi-plugin-action-buttons` ✅ (custom ArkNet plugin, no marketplace equivalent)
  - Check if enabled in `config/plugins.js`
  - ✅ COMPLETED: Plugin directory structure verified
  - ✅ COMPLETED: Documentation exists (ARCHITECTURE.md, EXAMPLES.ts, README.md)
  - ✅ COMPLETED: Plugin enabled in config/plugins.ts
  - ✅ COMPLETED: Built files exist in dist/ folder
  - ✅ COMPLETED: Strapi restart validated schema migration (text→jsonb)
  
- [x] **1.1.3** List current country fields in database
  - Query: `SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'countries'`
  - ✅ COMPLETED: 16 columns verified
  - ✅ COMPLETED: geodata_import_status confirmed as jsonb (migration successful)
  - ✅ COMPLETED: No unexpected schema changes after restart
  - ✅ COMPLETED: Database ready for button field addition

**✅ Validation**: Schema read, plugin confirmed, database columns listed

---

### **STEP 1.2: Review Plugin Documentation** ⏱️ 30 min

- [x] **1.2.1** Read plugin architecture ✅
  - File: `src/plugins/strapi-plugin-action-buttons/ARCHITECTURE.md`
  - ✅ COMPLETED: 290 lines read
  - ✅ COMPLETED: Component hierarchy understood (Schema → Registration → Component → Handler)
  - ✅ COMPLETED: Data flow understood (Button → window[onClick] → handler → DB)
  - ✅ COMPLETED: Security model understood (browser execution with admin privileges)
  
- [x] **1.2.2** Review examples ✅
  - File: `src/plugins/strapi-plugin-action-buttons/EXAMPLES.ts`
  - ✅ COMPLETED: 257 lines read
  - ✅ COMPLETED: 5 example handlers reviewed (send email, upload CSV, generate report, sync CRM, default action)
  - ✅ COMPLETED: Handler pattern understood: window[functionName] = async (fieldName, fieldValue, onChange) => {...}
  - ✅ COMPLETED: Metadata tracking pattern: onChange({ status, timestamp, ...data })
  - ✅ COMPLETED: Error handling pattern: try/catch with success/failed status
  
- [x] **1.2.3** Understand field configuration ✅
  - Focus: `plugin::action-buttons.button-field` field type
  - ✅ COMPLETED: Read README.md documentation (lines 1-250)
  - ✅ COMPLETED: Field configuration structure:

    ```json
    {
      "type": "customField",
      "customField": "plugin::action-buttons.button-field",
      "options": {
        "buttonLabel": "Click Me",
        "onClick": "handleMyAction"
      }
    }
    ```

  - ✅ COMPLETED: Handler signature: `function(fieldName: string, fieldValue: any, onChange?: (value: any) => void)`
  - ✅ COMPLETED: Ready to design GeoJSON import button configuration

**✅ Validation**: Plugin architecture understood, field configuration mastered

---

### **STEP 1.3: Backup Current Schema** ⏱️ 15 min

- [x] **1.3.1** Backup database ✅
  - Command: `pg_dump -U david -h 127.0.0.1 -d arknettransit -F p -f backup_TIMESTAMP.sql`
  - ✅ COMPLETED: Created backup_20251025_145744.sql (6.4 MB)
  - ✅ COMPLETED: All tables, data, schemas, constraints, indexes backed up
  
- [x] **1.3.2** Backup schema.json ✅
  - Command: `Copy-Item schema.json schema.json.backup_TIMESTAMP`
  - ✅ COMPLETED: Created schema.json.backup_20251025_152235 (3,357 bytes)
  - ✅ COMPLETED: Current schema with 145 lines and json field backed up
  
- [x] **1.3.3** Document rollback procedure ✅
  - Database: `psql -U david -h 127.0.0.1 -d arknettransit -f backup_20251025_145744.sql`
  - Schema: `Copy-Item schema.json.backup_20251025_152235 schema.json -Force; npm run develop`
  - ✅ COMPLETED: Rollback procedures documented

**✅ Validation**: Backups created (6.4 MB database + 3.4 KB schema), rollback documented

---

### **STEP 1.4: Install Socket.IO & Setup Infrastructure** ⏱️ 15 min

- [x] **1.4.1** Install Socket.IO client dependency ✅
  - Command: `npm install socket.io-client --save`
  - ✅ COMPLETED: Installed socket.io-client@4.8.1
  - ✅ COMPLETED: Verified in package.json (3 packages added)
  
- [x] **1.4.2** Create button-handlers.ts file structure ✅
  - File: `src/admin/button-handlers.ts`
  - ✅ COMPLETED: Created file with 387 lines
  - ✅ COMPLETED: Added TypeScript declarations for 5 handlers
  - ✅ COMPLETED: Added Socket.IO import and connection logic
  - ✅ COMPLETED: Added utility functions (getCountryId, getAuthToken, getApiBaseUrl)
  - ✅ COMPLETED: Created generic handleGeoJSONImport function
  - ✅ COMPLETED: Created 5 specific handlers (highway, amenity, landuse, building, admin)
  - ✅ COMPLETED: Added real-time Socket.IO progress tracking
  - ✅ COMPLETED: Added error handling and user feedback
  
- [x] **1.4.3** Add first button field to schema (Highway) ✅
  - File: `src/api/country/content-types/country/schema.json`
  - ✅ COMPLETED: Added `import_highway` field (lines 143-150)
  - ✅ COMPLETED: Configured as customField type
  - ✅ COMPLETED: Set customField to "plugin::action-buttons.button-field"
  - ✅ COMPLETED: Added options { buttonLabel: "🛣️ Import Highways", onClick: "handleImportHighway" }
  - ✅ COMPLETED: Validated JSON syntax (no errors)
  - ✅ COMPLETED: Schema now 153 lines (was 145)
  
- [x] **1.4.4** Create first handler (handleImportHighway) ✅
  - ✅ COMPLETED: Handler already created in step 1.4.2
  - ✅ COMPLETED: Full Socket.IO implementation
  - ✅ COMPLETED: Progress tracking with real-time updates
  - ✅ COMPLETED: Error handling and user feedback
  - ✅ COMPLETED: Metadata updates (status, progress, features)
  
- [x] **1.4.5** Wire up handler in app.tsx ✅
  - File: `src/admin/app.ts`
  - ✅ COMPLETED: Added import './button-handlers' at line 2
  - ✅ COMPLETED: Handlers will load when admin panel initializes
  - ✅ COMPLETED: All 5 handlers available on window object

**✅ Validation**: Socket.IO installed, handler structure created, Highway button ready

---

### **STEP 1.5: Test First Button (Highway)** ✅ COMPLETE

- [x] **1.5.1** Restart Strapi ✅
  - ✅ COMPLETED: Strapi restarted successfully
  - ✅ COMPLETED: No schema errors
  - ✅ COMPLETED: Custom field registered correctly
  
- [x] **1.5.2** Test Highway button in admin UI ✅
  - ✅ COMPLETED: Highway button appears in country edit page
  - ✅ COMPLETED: Confirmation dialog shows "Import highway.geojson for this country?"
  - ✅ COMPLETED: Handler functional
  
- [x] **1.5.3** Validate Highway button complete ✅
  - ✅ Button renders correctly
  - ✅ Handler function loaded (window.handleImportHighway)
  - ✅ Socket.IO client ready
  - ✅ Error handling graceful

**✅ Validation**: First button working, pattern validated

---

### **STEP 1.6: Add Remaining 4 Buttons** ✅ COMPLETE

- [x] **1.6.1** Add Amenity button field + handler ✅
  - ✅ COMPLETED: Added `import_amenity` field to schema
  - ✅ COMPLETED: Handler `handleImportAmenity` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import amenity.geojson for this country?"
  
- [x] **1.6.2** Add Landuse button field + handler ✅
  - ✅ COMPLETED: Added `import_landuse` field to schema
  - ✅ COMPLETED: Handler `handleImportLanduse` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import landuse.geojson for this country?"
  
- [x] **1.6.3** Add Building button field + handler ✅
  - ✅ COMPLETED: Added `import_building` field to schema
  - ✅ COMPLETED: Handler `handleImportBuilding` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import building.geojson for this country?"
  
- [x] **1.6.4** Add Admin button field + handler ✅
  - ✅ COMPLETED: Added `import_admin` field to schema
  - ✅ COMPLETED: Handler `handleImportAdmin` already exists in button-handlers.ts
  - ✅ COMPLETED: Tested - button shows "Import admin.geojson for this country?"
  
- [x] **1.6.5** Final validation - All 5 buttons ✅
  - ✅ VERIFIED: All 5 buttons render in UI
  - ✅ VERIFIED: Each button tested individually
  - ✅ VERIFIED: All handlers loaded (window.handleImport*)
  - ✅ VERIFIED: Confirmation dialogs display correct filenames

**✅ Validation**: All 5 buttons working, UI complete - PHASE 1 COMPLETE!

---

### **STEP 1.7: Highway Import with PostGIS** ⏱️ 90 min  

- [x] **1.7.1-1.7.3b** Backend API + Highway record insertion ✅ COMPLETE
  - Created `/api/import-geojson/highway` endpoint
  - Highway properties mapped and inserted
  - Tested with first feature from highway.geojson

- [x] **1.7.3c** PostGIS geometry insertion ✅ COMPLETE (Oct 25, 2025 17:57)
  - **CRITICAL FIX**: Rewrote from individual points to PostGIS LineString
  - Uses `ST_GeomFromText()` with WKT format
  - Single UPDATE query per highway
  - GIST spatial index on highways.geom column
  - Tested: 5-point LineString created successfully

**✅ Validation**: Highway import working with proper PostGIS geometry

---

### **STEP 1.8: 🚨 CRITICAL - Complete PostGIS Migration** ⏱️ 2-3 hours

**STATUS**: BLOCKING - Must complete before any other imports

**Problem**: Database uses individual lat/lon columns instead of PostGIS geometry  
**Impact**: $50K+ cost, 90% more records, 10-100x slower queries  
**Solution**: Execute comprehensive PostGIS migration for ALL spatial tables

#### **1.8.1** Execute PostGIS Migration Script ✅ COMPLETE (Oct 25, 2025 18:15)

- [x] **1.8.1a** Review migration script ✅
  - File: `arknet_fleet_manager/arknet-fleet-api/migrate_all_to_postgis.sql`
  - Migrates: stops, shapes, depots, geofences, vehicle_events, active_passengers
  
- [x] **1.8.1b** Execute migration ✅
  - Command executed successfully
  - No errors during execution
  - All success messages confirmed
  
- [x] **1.8.1c** Verify PostGIS columns created ✅
  - Verified 11 tables with geometry columns
  - Tables: highways, stops, depots, landuse_zones, pois, regions, geofences, shape_geometries, vehicle_events, active_passengers, geofence_all

#### **1.8.2** Verify GIST Spatial Indexes ✅ COMPLETE (Oct 25, 2025 18:16)

- [x] **1.8.2a** Check spatial indexes exist ✅
  - Verified 12 GIST spatial indexes created
  - Tables: highways, stops, depots, landuse_zones, pois, regions, geofences, shape_geometries, vehicle_events, active_passengers, geofence_circles, geofence_polygons
  - All using GIST index method

- [ ] **1.8.2b** Verify index types are GIST
  - All spatial indexes must use GIST (not BTREE)

#### **1.8.3** Test Spatial Queries

- [ ] **1.8.3a** Test point distance query (stops)
  - Find stops within 1km of a point
  - Verify uses spatial index (check EXPLAIN ANALYZE)
  
#### **1.8.3** Test Spatial Queries ✅ COMPLETE (Oct 25, 2025 18:17)

- [x] **1.8.3a** Test distance calculation (depots) ✅
  - Tested ST_DWithin() for finding depots within 5km
  - Query execution: 21.382ms
  - Found 4 depots within range
  
- [x] **1.8.3b** Test line length calculation (highways) ✅
  - Tested ST_Length() on highways and shape_geometries
  - Highway: 0.055 km (55 meters)
  - Shape geometries: Ranges from 0.24 km to 1.41 km
  
- [x] **1.8.3c** Verified PostGIS geometry types ✅
  - Highways: LineString with ST_NumPoints() working
  - Depots: Point geometry with ST_AsText() working
  - Shape geometries: Aggregated LineStrings (7-45 points each)

#### **1.8.4** Update Import Code for PostGIS ✅ COMPLETE (Oct 25, 2025 18:25)

- [x] **1.8.4a** Update amenity/POI import ✅
  - Extracts centroid from Point/Polygon/MultiPolygon geometries
  - Inserts as PostGIS Point: `ST_GeomFromText('POINT(lon lat)', 4326)`
  - Handles all geometry types with centroid calculation
  
- [x] **1.8.4b** Update landuse import ✅
  - Converts Polygon/MultiPolygon to PostGIS Polygon
  - Uses `ST_GeomFromText('POLYGON(...)', 4326)`
  - Handles MultiPolygon by using first polygon
  
- [x] **1.8.4c** Update building import ✅
  - Placeholder implementation (table doesn't exist yet)
  - PostGIS pattern documented for future implementation
  - Notes: Requires streaming parser for 658MB file
  
- [x] **1.8.4d** Update admin boundaries import ✅
  - Converts Polygon/MultiPolygon to PostGIS MultiPolygon
  - Uses `ST_GeomFromText('MULTIPOLYGON(...)', 4326)`
  - Handles single Polygon by converting to MultiPolygon for consistency

**✅ Validation**: All import endpoints updated with PostGIS geometry insertion pattern

---

### **STEP 1.9: Create Buildings Content Type** ⏱️ 30 min ✅ COMPLETE

**CRITICAL**: Buildings table required for realistic passenger spawning model (see CONTEXT.md "Passenger Spawning Architecture")

- [x] **1.9.1** Create building content type schema ✅
  - File: `src/api/building/content-types/building/schema.json`
  - ✅ Created schema with collectionName: "buildings"
  - ✅ Created controllers, routes, and services
  
- [x] **1.9.2** Define building schema fields ✅
  - ✅ `building_id` (UID, required, unique)
  - ✅ `osm_id` (biginteger, required)
  - ✅ `full_id` (string, maxLength: 50)
  - ✅ `building_type` (string, default: "yes")
  - ✅ `name` (string, nullable, maxLength: 255)
  - ✅ `addr_street` (string, nullable)
  - ✅ `addr_city` (string, nullable)
  - ✅ `addr_housenumber` (string, nullable)
  - ✅ `levels` (integer, nullable) - number of floors
  - ✅ `height` (decimal, nullable)
  - ✅ `amenity` (string, nullable)
  - ✅ `country` (relation to country, manyToOne)
  
- [x] **1.9.3** Add PostGIS geometry column ✅
  - ✅ Ran SQL: `ALTER TABLE buildings ADD COLUMN geom geometry(Polygon, 4326);`
  - ✅ Created GIST index: `CREATE INDEX idx_buildings_geom ON buildings USING GIST(geom);`
  - ✅ Verified: `\d buildings` shows geom geometry(Polygon,4326) column
  - ✅ GIST index confirmed: idx_buildings_geom gist (geom)
  
- [x] **1.9.4** Strapi restart and table creation ✅
  - ✅ Strapi restarted successfully
  - ✅ Buildings table created automatically by Strapi ORM
  - ✅ Buildings relation added to country schema
  - ✅ Ready for import endpoint testing (requires streaming parser for 658MB file)

**✅ Validation**: Buildings table exists with PostGIS geometry column and GIST index

---

### **STEP 1.10: Streaming GeoJSON Parser** ⏱️ 90 min

**CRITICAL**: Required for all GeoJSON imports - ensures consistency, memory efficiency, and production scalability

**Strategy Decision**: Implement streaming for **ALL 5 content types** (highway, amenity, landuse, building, admin)

**Rationale**:

- **Consistency**: Single code path reduces bugs and maintenance
- **Memory Efficiency**: 628MB building.geojson requires streaming; applying to all ensures <500MB memory usage
- **Progress Feedback**: Real-time progress bars for all imports (not just large files)
- **Future-Proofing**: Data grows (Barbados → multi-country), small files today = large files tomorrow
- **Batch Processing**: Consistent 500-1000 feature batches for optimal database performance

**File Size Analysis**:

- building.geojson: **628.45 MB** ⚠️ CRITICAL - streaming required
- highway.geojson: **41.22 MB** - streaming beneficial
- landuse.geojson: **4.12 MB** - streaming for consistency
- amenity.geojson: **3.65 MB** - streaming for consistency
- admin boundaries: **0.02-0.28 MB** - streaming for consistency

- [x] **1.10.1** Install streaming parser dependencies ✅
  - ✅ Ran: `cd arknet_fleet_manager/arknet-fleet-api && npm install stream-json`
  - ✅ Verified in package.json: "stream-json": "^1.9.1"
  
- [x] **1.10.2** Create reusable GeoJSON streaming parser utility ✅
  - ✅ Created: `src/utils/geojson-stream-parser.ts` (243 lines)
  - ✅ Implemented `streamGeoJSON()` function with batch processing
  - ✅ Implemented `estimateFeatureCount()` for progress estimation
  - ✅ Features:
    - Memory-efficient streaming (uses stream-json pipeline)
    - Configurable batch size (default: 500 features)
    - Progress callbacks per batch (for Socket.IO)
    - Error handling (file not found, malformed JSON, batch processing errors)
    - Pause/resume stream during batch processing
    - TypeScript interfaces: StreamingOptions, StreamProgress, StreamResult
  
- [ ] **1.10.3** Update ALL 5 import endpoints to use streaming
  - ⏳ **Admin import** - UPDATE endpoint (exists, imports 1 feature, needs full streaming import)
  - ⏳ **Highway import** - UPDATE endpoint (exists, uses readFileSync, needs streaming)
  - ⏳ **Amenity import** - UPDATE endpoint (exists, uses readFileSync, needs streaming)
  - ⏳ **Landuse import** - UPDATE endpoint (exists, uses readFileSync, needs streaming)
  - ✅ **Building import** - COMPLETED with streaming (628MB file, 500 feature batches, 162,942 records)
  - Replace all `fs.readFileSync` with streaming parser
  - Process features in batches (500-1000 at a time)
  - Emit Socket.IO progress updates per batch
  - **NOTE**: Strapi v5 EntityService doesn't have `createMany()` - use bulk SQL inserts
  - **STATUS**: 1/5 complete (Building only), 4 endpoints need conversion to streaming
  
- [ ] **1.10.4** Test streaming with building.geojson (stress test)
  - Click Building button in UI
  - Monitor memory usage (should stay <500MB throughout)
  - Verify progress updates in real-time (batch-by-batch)
  - Test with 628MB file (may take 10-30 minutes)
  - Confirm no memory leaks during long import
  
- [ ] **1.10.5** Validate streaming performance for all imports
  - Test all 5 import buttons sequentially
  - Check memory usage during each import (<500MB)
  - Verify no memory leaks between imports
  - Confirm batch progress updates working for all types
  - Measure and document import times per file
  
- [ ] **1.10.6** Production optimization
  - Fine-tune batch size for optimal performance (test 500, 1000, 2000)
  - Add error recovery (resume from last successful batch)
  - Add import cancellation support
  - Document memory usage benchmarks in CONTEXT.md

**✅ Validation**: Streaming parser working for all 5 content types, memory <500MB, no leaks, 628MB file imports successfully

---

### **STEP 1.11: Geospatial Services API (Phase 1)** ⏱️ 90 min

**CRITICAL**: Provides optimized spatial queries for simulators (see CONTEXT.md "Geospatial Services Architecture")

#### **Phase 1: Strapi Custom Controllers** (Current)

- [ ] **1.11.1** Create geospatial content type structure
  - Generate: `cd arknet_fleet_manager/arknet-fleet-api && npm run strapi generate`
  - Select: "api" → "geospatial"
  - Creates: `src/api/geospatial/` folder structure
  
- [ ] **1.11.2** Implement geofencing endpoints
  - File: `src/api/geospatial/controllers/geospatial.ts`
  - Endpoint: `POST /api/geospatial/check-geofence`
    - Input: `{ lat, lon }`
    - Query: `SELECT * FROM geofences WHERE ST_Contains(geom, ST_MakePoint(?, ?))`
    - Output: Array of zones containing point
  - Endpoint: `POST /api/geospatial/batch-geofence`
    - Input: `[{ lat, lon }, ...]`
    - Batch query for multiple points
  
- [ ] **1.11.3** Implement reverse geocoding endpoints
  - Endpoint: `POST /api/geospatial/reverse-geocode`
    - Input: `{ lat, lon }`
    - Query: Find nearest address/building with name
    - Output: `{ address, building_name, distance }`
  
- [ ] **1.11.4** Implement spawning spatial queries
  - Endpoint: `GET /api/geospatial/route-buildings?route_id=X&buffer=500`
    - Query: `ST_DWithin(building.geom, route_shape.geom, buffer)`
    - Output: Buildings within route buffer
  - Endpoint: `GET /api/geospatial/depot-buildings?depot_id=X&radius=1000`
    - Query: `ST_DWithin(building.geom, depot.geom, radius)`
    - Output: Buildings in depot catchment
  - Endpoint: `GET /api/geospatial/zone-containing?lat=X&lon=Y`
    - Query: `ST_Contains(landuse_zone.geom, ST_MakePoint(?, ?))`
    - Output: Landuse zone containing point
  - Endpoint: `GET /api/geospatial/nearby-pois?lat=X&lon=Y&radius=500`
    - Query: `ST_DWithin(poi.geom, ST_MakePoint(?, ?), radius)`
    - Output: POIs within radius
  
- [ ] **1.11.5** Add route definitions
  - File: `src/api/geospatial/routes/geospatial.ts`
  - Configure all endpoints with proper HTTP methods
  - Add authentication/authorization if needed
  
- [ ] **1.11.6** Test geospatial endpoints
  - Test geofence check with known coordinates
  - Test route-buildings query with existing route
  - Test depot-buildings query with existing depot
  - Verify PostGIS functions working (ST_DWithin, ST_Contains)
  - Check query performance (<100ms for simple queries)
  
- [ ] **1.11.7** Document API endpoints
  - Add OpenAPI/Swagger documentation
  - Document expected inputs/outputs
  - Provide example curl commands

**✅ Validation**: All geospatial endpoints working, simulators can query spatial data

**⏳ Phase 2 (Future)**: Extract to separate `geospatial_service/` FastAPI service when scaling needed (>1000 req/s)

---

### **STEP 1.12: Database Integration** ⏱️ 32 min

- [ ] **1.12.1** Update geodata_import_status after import
  - After successful import, update JSON field
  - Set status, featureCount, lastImportDate, jobId
  - Verify field updates in database
  
- [ ] **1.9.2** Store features in database (temporary solution)
  - Create temporary table for imported features
  - Store GeoJSON features during import
  - Verify data persists
  
- [ ] **1.9.3** Test end-to-end import (Highway)
  - Import highway.geojson fully
  - Verify database updated
  - Verify button metadata updated
  - Verify geodata_import_status field updated
  
- [ ] **1.9.4** Validate all 5 file types import to DB
  - Import all 5 file types sequentially
  - Verify data in database for each
  - Check geodata_import_status field shows all 5
  - Verify total feature counts accurate

**✅ Validation**: Full import pipeline working, data persisting, UI showing accurate status

---

### **STEP 1.10: Final Testing & Documentation** ⏱️ 20 min

- [ ] **1.10.1** Complete end-to-end test
  - Import all 5 GeoJSON files
  - Verify all progress updates work
  - Verify all database updates complete
  - Screenshot working UI
  
- [ ] **1.10.2** Document implementation
  - Update CONTEXT.md with GeoJSON import architecture
  - Document Socket.IO integration
  - Document streaming parser approach
  
- [ ] **1.10.3** Update TODO.md completion
  - Mark all Phase 1 steps complete
  - Update progress counters
  - Add session log entries
  - Mark Phase 1 as ✅ COMPLETE

**✅ Validation**: Phase 1 fully complete, documented, tested

---

## � **PHASE EXECUTION ORDER (Option A)**

Following the priority sequence, phases should be executed in this order:

1. ✅ **Phase 1.1-1.9**: Foundation (COMPLETE)
2. ⏳ **Phase 1.10**: Complete Import Endpoints (CURRENT - 1/5 tasks)
   - Only Building uses streaming (162,942 records imported)
   - Admin/Highway/Amenity/Landuse endpoints exist but incomplete
   - Need to update 4 endpoints: streaming parser + full imports
3. 🔜 **Phase 1.11**: Geospatial Services API (NEXT - enables spawning)
4. 🔜 **Phase 1.12**: Database Integration & Validation
5. 🔜 **Phase 4**: POI-Based Spawning (requires 1.11)
6. 🔜 **Phase 5**: Depot/Route Spawners (requires 1.11)
7. 🔜 **Phase 6**: Conductor Communication (requires 5)
8. 🔜 **Phase 2**: Redis + Reverse Geocoding (optimization)
9. 🔜 **Phase 3**: Geofencing (requires 2)

**Note**: Phase 2 (Redis) is moved after spawning phases since it's an optimization, not a blocker. PostgreSQL queries (~2s) work fine for initial development. Optimize with Redis (<200ms) after spawning is functional.

---

## �🔴 **PHASE 2: REDIS + REVERSE GEOCODING**

**EXECUTION ORDER**: After Phase 6 (Conductor Communication)  
**STATUS**: Deferred - Optimization phase, not a blocker for spawning functionality

---

### **STEP 1.5: Update Country Schema** ⏱️ 30 min

- [ ] **1.5.1** Edit schema.json
  - Add `geodata_import_buttons` field
  - Add `geodata_import_status` field
  
- [ ] **1.5.2** Verify JSON syntax
  - Check for trailing commas
  - Validate with JSON linter

**✅ Validation**: Schema updated, JSON valid

---

### **STEP 1.6: Run Migration** ⏱️ 1 hour

- [ ] **1.6.1** Stop Strapi server
  
- [ ] **1.6.2** Start Strapi in development mode
  - Command: `cd arknet_fleet_manager/arknet-fleet-api && npm run develop`
  
- [ ] **1.6.3** Watch console for migration logs
  - Look for: "Schema updated for content-type: country"
  - Check for errors
  
- [ ] **1.6.4** Verify in database
  - Query: `SELECT column_name FROM information_schema.columns WHERE table_name = 'countries' AND column_name IN ('geodata_import_buttons', 'geodata_import_status')`
  - Expected: Both columns exist

**✅ Validation**: Migration successful, columns exist in database

---

### **STEP 1.7: Verify in Strapi Admin UI** ⏱️ 30 min

- [ ] **1.7.1** Login to Strapi admin
  - URL: `http://localhost:1337/admin`
  
- [ ] **1.7.2** Navigate to Content Manager → Country
  
- [ ] **1.7.3** Open Barbados record (or create test country)
  
- [ ] **1.7.4** Verify action buttons render
  - Should see 7 buttons
  - Buttons should be clickable
  
- [ ] **1.7.5** Verify geodata_import_status field
  - Should show JSON editor
  - Should have default values

**✅ Validation**: UI renders correctly, fields visible

---

### **STEP 1.8: Create Window Handlers** ⏱️ 3 hours

- [ ] **1.8.1** Create admin extensions directory
  - Path: `arknet_fleet_manager/arknet-fleet-api/admin-extensions/`
  
- [ ] **1.8.2** Create handlers file
  - File: `admin-extensions/geojson-handlers.js`
  
- [ ] **1.8.3** Implement window.importGeoJSON handler

  ```javascript
  window.importGeoJSON = async (entityId, metadata) => {
    const { fileType } = metadata;
    console.log(`🚀 Importing ${fileType} for country ${entityId}`);
    
    try {
      const response = await fetch('/api/geojson-import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('jwtToken')}`
        },
        body: JSON.stringify({ countryId: entityId, fileType })
      });
      
      const result = await response.json();
      
      if (response.ok) {
        console.log('✅ Import started:', result);
        alert(`Import started! Job ID: ${result.jobId}`);
      } else {
        console.error('❌ Import failed:', result);
        alert(`Import failed: ${result.error}`);
      }
    } catch (error) {
      console.error('❌ Import error:', error);
      alert(`Import error: ${error.message}`);
    }
  };
  ```
  
- [ ] **1.8.4** Implement window.viewImportStats handler

  ```javascript
  window.viewImportStats = async (entityId, metadata) => {
    console.log(`📊 Viewing import stats for country ${entityId}`);
    alert('Stats view not yet implemented');
  };
  ```
  
- [ ] **1.8.5** Implement window.clearRedisCache handler

  ```javascript
  window.clearRedisCache = async (entityId, metadata) => {
    console.log(`🗑️ Clearing Redis cache for country ${entityId}`);
    const confirmed = confirm('Clear all Redis cache for this country?');
    if (!confirmed) return;
    alert('Cache clear not yet implemented');
  };
  ```
  
- [ ] **1.8.6** Inject script into Strapi admin
  - Check if custom admin build needed
  - Add script tag to `admin/src/index.html` OR
  - Use webpack config OR
  - Use Strapi plugin hooks

**✅ Validation**: Handlers created and registered globally

---

### **STEP 1.9: Test Handlers** ⏱️ 1 hour

- [ ] **1.9.1** Open Strapi admin in browser
  
- [ ] **1.9.2** Open DevTools Console (F12)
  
- [ ] **1.9.3** Test window.importGeoJSON manually
  - Command: `window.importGeoJSON(1, { fileType: 'highway' })`
  - Expected: Console log + fetch request (404 OK - API not built yet)
  
- [ ] **1.9.4** Click "Import Highways" button
  - Expected: Handler triggered, console logs appear
  
- [ ] **1.9.5** Click all other buttons
  - Verify each triggers correct handler

**✅ Validation**: All handlers trigger correctly, buttons functional

---

### **STEP 1.10: Phase 1 Checkpoint** ⏱️ 30 min

**✅ Phase 1 Complete When:**

- [x] Country schema migration successful
- [x] Action buttons render in Strapi admin
- [x] Window handlers trigger (even if API returns 404)
- [x] geodata_import_status field visible
- [x] All 7 buttons functional

**💾 Git Commit:**

```bash
git add arknet_fleet_manager/arknet-fleet-api/src/api/country/content-types/country/schema.json
git add arknet_fleet_manager/arknet-fleet-api/admin-extensions/geojson-handlers.js
git commit -m "feat: Add GeoJSON import action buttons to country schema

- Add geodata_import_buttons field with 7 buttons
- Add geodata_import_status field for tracking imports
- Implement window handlers: importGeoJSON, viewImportStats, clearRedisCache
- Buttons render in Strapi admin UI
- Handlers trigger on click (API endpoints to be implemented)"

git push origin branch-0.0.2.6
```

**📝 Notes/Issues:**

- (Document any issues encountered)

---

🔴 **PHASE 2: REDIS + REVERSE GEOCODING**

**Goal**: Install Redis, implement geospatial service, benchmark <200ms

### **STEP 2.1: Install Redis Server** ⏱️ 1 hour

- [ ] **2.1.1** Download Redis
  - Windows: Redis for Windows OR WSL2 + Redis
  - Download from: <https://redis.io/download> or <https://github.com/microsoftarchive/redis/releases>
  
- [ ] **2.1.2** Install/Extract Redis
  - Extract to: `C:\Redis` (Windows) or `/usr/local/bin` (WSL)
  
- [ ] **2.1.3** Start Redis server
  - Command: `redis-server` (or `redis-server.exe`)
  
- [ ] **2.1.4** Test connection
  - Command: `redis-cli ping`
  - Expected: `PONG`

**✅ Validation**: Redis responds with PONG

---

### **STEP 2.2: Configure Redis** ⏱️ 1 hour

- [ ] **2.2.1** Create redis.conf (if not exists)
  
- [ ] **2.2.2** Set password
  - Add: `requirepass your_secure_password_here`
  
- [ ] **2.2.3** Enable persistence
  - Add: `appendonly yes`
  - Add: `appendfilename "appendonly.aof"`
  
- [ ] **2.2.4** Set memory limits
  - Add: `maxmemory 512mb`
  - Add: `maxmemory-policy allkeys-lru`
  
- [ ] **2.2.5** Restart Redis with config
  - Command: `redis-server redis.conf`
  
- [ ] **2.2.6** Test authenticated connection
  - Command: `redis-cli -a your_password ping`
  - Expected: `PONG`

**✅ Validation**: Redis configured with password and persistence

---

### **STEP 2.3: Install Node.js Redis Client** ⏱️ 30 min

- [ ] **2.3.1** Navigate to API directory
  - Command: `cd arknet_fleet_manager/arknet-fleet-api`
  
- [ ] **2.3.2** Install ioredis
  - Command: `npm install ioredis --save`
  
- [ ] **2.3.3** Verify installation
  - Check: `package.json` contains `"ioredis": "^..."`

**✅ Validation**: ioredis installed in package.json

---

### **STEP 2.4: Create Redis Client Utility** ⏱️ 1 hour

- [ ] **2.4.1** Create utils directory (if not exists)
  - Path: `src/utils/`
  
- [ ] **2.4.2** Create redis-client.js
  - File: `src/utils/redis-client.js`
  
- [ ] **2.4.3** Implement client

  ```javascript
  const Redis = require('ioredis');
  
  const redis = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || null,
    retryStrategy: (times) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    maxRetriesPerRequest: 3
  });
  
  redis.on('connect', () => {
    console.log('✅ Redis connected:', redis.options.host);
  });
  
  redis.on('error', (err) => {
    console.error('❌ Redis error:', err.message);
  });
  
  redis.on('close', () => {
    console.warn('⚠️ Redis connection closed');
  });
  
  module.exports = redis;
  ```

**✅ Validation**: Redis client created

---

### **STEP 2.5: Configure Environment** ⏱️ 15 min

- [ ] **2.5.1** Edit .env file
  - File: `arknet_fleet_manager/arknet-fleet-api/.env`
  
- [ ] **2.5.2** Add Redis config

  ```env
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_PASSWORD=your_secure_password_here
  ```

**✅ Validation**: Environment variables set

---

### **STEP 2.6: Test Redis Connection** ⏱️ 30 min

- [ ] **2.6.1** Create test script
  - File: `scripts/test-redis.js`
  
- [ ] **2.6.2** Implement test

  ```javascript
  const redis = require('../src/utils/redis-client');
  
  async function test() {
    console.log('Testing Redis connection...');
    
    await redis.set('test_key', 'Hello ArkNet Redis!');
    const value = await redis.get('test_key');
    console.log('✅ Retrieved:', value);
    
    await redis.del('test_key');
    console.log('✅ Test complete');
    
    process.exit(0);
  }
  
  test().catch(err => {
    console.error('❌ Test failed:', err);
    process.exit(1);
  });
  ```
  
- [ ] **2.6.3** Run test
  - Command: `node scripts/test-redis.js`
  - Expected: "Retrieved: Hello ArkNet Redis!"

**✅ Validation**: Redis connection test passes

---

### **STEP 2.7: Create Redis Geospatial Service** ⏱️ 4 hours

- [ ] **2.7.1** Create services directory (if not exists)
  - Path: `src/services/`
  
- [ ] **2.7.2** Create service file
  - File: `src/services/redis-geo.service.js`
  
- [ ] **2.7.3** Implement service class

  ```javascript
  const redis = require('../utils/redis-client');
  
  class RedisGeoService {
    // Add highway to geospatial index
    async addHighway(countryCode, lon, lat, highwayId, metadata) {
      const key = `highways:${countryCode}`;
      await redis.geoadd(key, lon, lat, `highway:${highwayId}`);
      await redis.hset(`highway:${highwayId}`, metadata);
    }
    
    // Add POI to geospatial index
    async addPOI(countryCode, lon, lat, poiId, metadata) {
      const key = `pois:${countryCode}`;
      await redis.geoadd(key, lon, lat, `poi:${poiId}`);
      await redis.hset(`poi:${poiId}`, metadata);
    }
    
    // Find nearby highways
    async findNearbyHighways(countryCode, lon, lat, radiusMeters = 50) {
      const key = `highways:${countryCode}`;
      const results = await redis.georadius(
        key, lon, lat, radiusMeters, 'm', 'WITHDIST', 'ASC'
      );
      
      const enriched = await Promise.all(
        results.map(async ([id, distance]) => {
          const metadata = await redis.hgetall(id);
          return { id, distance: parseFloat(distance), ...metadata };
        })
      );
      
      return enriched;
    }
    
    // Find nearby POIs
    async findNearbyPOIs(countryCode, lon, lat, radiusMeters = 100) {
      const key = `pois:${countryCode}`;
      const results = await redis.georadius(
        key, lon, lat, radiusMeters, 'm', 'WITHDIST', 'ASC'
      );
      
      const enriched = await Promise.all(
        results.map(async ([id, distance]) => {
          const metadata = await redis.hgetall(id);
          return { id, distance: parseFloat(distance), ...metadata };
        })
      );
      
      return enriched;
    }
    
    // Reverse geocoding cache
    async getReverseGeocode(lat, lon) {
      const key = `geo:${lat.toFixed(4)}:${lon.toFixed(4)}`;
      return await redis.get(key);
    }
    
    async setReverseGeocode(lat, lon, address, ttl = 3600) {
      const key = `geo:${lat.toFixed(4)}:${lon.toFixed(4)}`;
      await redis.setex(key, ttl, address);
    }
    
    // Clear country cache
    async clearCountryCache(countryCode) {
      const patterns = [
        `highways:${countryCode}`,
        `pois:${countryCode}`,
        `highway:*`,
        `poi:*`,
        `geo:*`
      ];
      
      for (const pattern of patterns) {
        const keys = await redis.keys(pattern);
        if (keys.length > 0) {
          await redis.del(...keys);
        }
      }
    }
  }
  
  module.exports = new RedisGeoService();
  ```

**✅ Validation**: Service created with all methods

---

### **STEP 2.8: Test Geospatial Service** ⏱️ 2 hours

- [ ] **2.8.1** Create test script
  - File: `scripts/test-redis-geo.js`
  
- [ ] **2.8.2** Add test data

  ```javascript
  const redisGeo = require('../src/services/redis-geo.service');
  
  async function test() {
    console.log('Testing Redis Geospatial Service...\n');
    
    // Test 1: Add highways
    console.log('1️⃣ Adding highways...');
    await redisGeo.addHighway('barbados', -59.5905, 13.0806, 5172465, {
      name: 'Tom Adams Highway',
      type: 'trunk',
      ref: 'ABC'
    });
    console.log('✅ Highway added');
    
    // Test 2: Add POIs
    console.log('\n2️⃣ Adding POIs...');
    await redisGeo.addPOI('barbados', -59.6016, 13.0947, 123, {
      name: 'Bridgetown Mall',
      type: 'mall'
    });
    console.log('✅ POI added');
    
    // Test 3: Find nearby highways
    console.log('\n3️⃣ Finding nearby highways...');
    const highways = await redisGeo.findNearbyHighways('barbados', -59.5905, 13.0806, 50);
    console.log('✅ Found:', highways);
    
    // Test 4: Find nearby POIs
    console.log('\n4️⃣ Finding nearby POIs...');
    const pois = await redisGeo.findNearbyPOIs('barbados', -59.6016, 13.0947, 100);
    console.log('✅ Found:', pois);
    
    // Test 5: Cache reverse geocode
    console.log('\n5️⃣ Testing cache...');
    await redisGeo.setReverseGeocode(13.0806, -59.5905, 'Tom Adams Highway, Barbados');
    const cached = await redisGeo.getReverseGeocode(13.0806, -59.5905);
    console.log('✅ Cached address:', cached);
    
    console.log('\n✅ All tests passed!');
    process.exit(0);
  }
  
  test().catch(err => {
    console.error('❌ Test failed:', err);
    process.exit(1);
  });
  ```
  
- [ ] **2.8.3** Run test
  - Command: `node scripts/test-redis-geo.js`
  - Verify all assertions pass

**✅ Validation**: Geospatial service tests pass

---

### **STEP 2.9: Create Reverse Geocode API** ⏱️ 3 hours

- [ ] **2.9.1** Create API structure
  - Directory: `src/api/reverse-geocode/`
  - Subdirs: `controllers/`, `routes/`
  
- [ ] **2.9.2** Create controller
  - File: `src/api/reverse-geocode/controllers/reverse-geocode.js`
  
- [ ] **2.9.3** Implement controller

  ```javascript
  const redisGeoService = require('../../../services/redis-geo.service');
  
  module.exports = {
    async reverseGeocode(ctx) {
      const { lat, lon, countryCode = 'barbados' } = ctx.query;
      
      if (!lat || !lon) {
        return ctx.badRequest('Missing lat or lon parameter');
      }
      
      const latitude = parseFloat(lat);
      const longitude = parseFloat(lon);
      
      // Check cache first
      let address = await redisGeoService.getReverseGeocode(latitude, longitude);
      
      if (address) {
        return ctx.send({
          address,
          source: 'cache',
          timestamp: Date.now()
        });
      }
      
      // Cache miss - query Redis geospatial
      const [nearbyHighways, nearbyPOIs] = await Promise.all([
        redisGeoService.findNearbyHighways(countryCode, longitude, latitude, 50),
        redisGeoService.findNearbyPOIs(countryCode, longitude, latitude, 100)
      ]);
      
      // Format address
      const highway = nearbyHighways[0];
      const poi = nearbyPOIs[0];
      
      if (!highway && !poi) {
        address = 'Unknown location';
      } else if (highway && !poi) {
        address = highway.name || `${highway.type} road`;
      } else if (!highway && poi) {
        address = `Near ${poi.name}`;
      } else {
        address = `${highway.name}, near ${poi.name}`;
      }
      
      // Cache result
      await redisGeoService.setReverseGeocode(latitude, longitude, address);
      
      return ctx.send({
        address,
        source: 'computed',
        highway: highway || null,
        poi: poi || null,
        timestamp: Date.now()
      });
    }
  };
  ```
  
- [ ] **2.9.4** Create routes
  - File: `src/api/reverse-geocode/routes/reverse-geocode.js`
  
- [ ] **2.9.5** Implement routes

  ```javascript
  module.exports = {
    routes: [
      {
        method: 'GET',
        path: '/reverse-geocode',
        handler: 'reverse-geocode.reverseGeocode',
        config: {
          auth: false // Public for testing
        }
      }
    ]
  };
  ```

**✅ Validation**: API endpoint created

---

### **STEP 2.10: Test Reverse Geocode API** ⏱️ 1 hour

- [ ] **2.10.1** Start Strapi server
  - Command: `npm run develop`
  
- [ ] **2.10.2** Test first request (cache miss)
  - URL: `http://localhost:1337/api/reverse-geocode?lat=13.0806&lon=-59.5905`
  - Expected: `{ "address": "Tom Adams Highway", "source": "computed", ... }`
  
- [ ] **2.10.3** Test second request (cache hit)
  - Same URL
  - Expected: `{ "address": "Tom Adams Highway", "source": "cache", ... }`
  
- [ ] **2.10.4** Test without data
  - URL: `http://localhost:1337/api/reverse-geocode?lat=0&lon=0`
  - Expected: `{ "address": "Unknown location", ... }`

**✅ Validation**: API returns addresses, cache working

---

### **STEP 2.11: Benchmark Performance** ⏱️ 3 hours

- [ ] **2.11.1** Create benchmark script
  - File: `scripts/benchmark-reverse-geocode.js`
  
- [ ] **2.11.2** Implement benchmark

  ```javascript
  const axios = require('axios');
  
  // Generate 100 random coordinates in Barbados
  // (Barbados bounds: lat 13.04-13.33, lon -59.65--59.42)
  function generateCoordinates(count) {
    const coords = [];
    for (let i = 0; i < count; i++) {
      coords.push({
        lat: 13.04 + Math.random() * 0.29,
        lon: -59.65 + Math.random() * 0.23,
        name: `Point ${i + 1}`
      });
    }
    return coords;
  }
  
  async function benchmark() {
    const coords = generateCoordinates(100);
    const results = { cache: [], computed: [] };
    
    console.log('Running benchmark (100 requests)...\n');
    
    // Pass 1: All cache misses
    for (const coord of coords) {
      const start = Date.now();
      const response = await axios.get(
        `http://localhost:1337/api/reverse-geocode?lat=${coord.lat}&lon=${coord.lon}`
      );
      const latency = Date.now() - start;
      results.computed.push(latency);
    }
    
    // Pass 2: All cache hits
    for (const coord of coords) {
      const start = Date.now();
      const response = await axios.get(
        `http://localhost:1337/api/reverse-geocode?lat=${coord.lat}&lon=${coord.lon}`
      );
      const latency = Date.now() - start;
      results.cache.push(latency);
    }
    
    console.log('=== BENCHMARK RESULTS ===');
    console.log('\nCache Misses (computed):');
    console.log('  Count:', results.computed.length);
    console.log('  Avg:', avg(results.computed), 'ms');
    console.log('  P95:', percentile(results.computed, 95), 'ms');
    console.log('  P99:', percentile(results.computed, 99), 'ms');
    
    console.log('\nCache Hits:');
    console.log('  Count:', results.cache.length);
    console.log('  Avg:', avg(results.cache), 'ms');
    console.log('  P95:', percentile(results.cache, 95), 'ms');
    console.log('  P99:', percentile(results.cache, 99), 'ms');
    
    console.log('\n✅ Target: Cache hit <10ms, Cache miss <200ms');
  }
  
  function avg(arr) {
    return (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
  }
  
  function percentile(arr, p) {
    const sorted = arr.sort((a, b) => a - b);
    const index = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[index];
  }
  
  benchmark();
  ```
  
- [ ] **2.11.3** Run benchmark
  - Command: `node scripts/benchmark-reverse-geocode.js`
  - Record results
  
- [ ] **2.11.4** Document results
  - Create: `docs/redis-performance-benchmark.md`
  - Include: Avg, p95, p99 for cache hit/miss

**✅ Validation**: Benchmark shows <10ms cache hit, <200ms cache miss

---

### **STEP 2.12: Phase 2 Checkpoint** ⏱️ 30 min

**✅ Phase 2 Complete When:**

- [x] Redis server running
- [x] Reverse geocode API responding
- [x] Cache hit <10ms
- [x] Cache miss <200ms
- [x] 10x+ faster than PostgreSQL (optional comparison)

**💾 Git Commit:**

```bash
git add src/utils/redis-client.js
git add src/services/redis-geo.service.js
git add src/api/reverse-geocode/
git add scripts/test-redis*.js scripts/benchmark-reverse-geocode.js
git add docs/redis-performance-benchmark.md
git commit -m "feat: Implement Redis geospatial service for reverse geocoding

- Add Redis client with connection pooling
- Implement geospatial service (GEOADD, GEORADIUS)
- Add reverse geocoding API endpoint
- Cache results for <10ms cache hits
- Benchmark shows <200ms cache miss performance
- 10x+ faster than PostgreSQL queries"

git push origin branch-0.0.2.6
```

**📝 Notes/Issues:**

- (Document any issues)

---

## 🔔 **PHASE 3: GEOFENCING**

**EXECUTION ORDER**: After Phase 2 (Redis + Reverse Geocoding)  
**STATUS**: Deferred - Requires Redis infrastructure from Phase 2

## 🎯 **PHASE 4: POI-BASED SPAWNING**

**EXECUTION ORDER**: After Phase 1.12 (Database Integration)  
**STATUS**: Ready after Geospatial API is complete  
**BLOCKER**: Requires Phase 1.11 Geospatial Services API

## 🚌 **PHASE 5: DEPOT/ROUTE SPAWNERS**

**EXECUTION ORDER**: After Phase 4 or in parallel with Phase 4  
**STATUS**: Ready after Geospatial API is complete  
**BLOCKER**: Requires Phase 1.11 Geospatial Services API

## 🔗 **PHASE 6: CONDUCTOR COMMUNICATION**

**EXECUTION ORDER**: After Phase 5 (Depot/Route Spawners)  
**STATUS**: Requires active passenger spawning to be functional  
**BLOCKER**: Requires Phase 5 (passenger spawning operational)

## Phases 3-6 to be detailed after Phase 2 completion

---

## 📝 **SESSION NOTES**

### **Session 1: October 25, 2025 - Documentation & Planning**

**Context**: User lost chat history, requested full context rebuild

**Activities**:

1. ✅ Read PROJECT_STATUS.md and ARCHITECTURE_DEFINITIVE.md
2. ✅ Created initial TODO list (8 items)
3. ✅ User clarified: This is a feasibility study for Redis + geofencing + spawning
4. ✅ Deep codebase analysis (action-buttons plugin, spawning systems, geofence API)
5. ✅ Analyzed 11 GeoJSON files (user confirmed scope, excluded barbados_geocoded_stops)
6. ✅ Created GEOJSON_IMPORT_CONTEXT.md (600+ lines architecture study)
7. ✅ User requested phased approach reorganization
8. ✅ Confirmed custom action-buttons plugin (no marketplace equivalent)
9. ✅ Built TODO.md with 65+ granular steps across 6 phases
10. ✅ Created CONTEXT.md as single source of truth
11. ✅ Added 10 detailed system integration workflows to CONTEXT.md
12. ✅ User asked to confirm conductor/driver/commuter roles
13. ✅ Discovered architectural error: "Conductor Service" doesn't exist
14. ✅ Fixed CONTEXT.md: Assignment happens in spawn strategies, not centralized service
15. ✅ Added component roles section to CONTEXT.md
16. ✅ User asked: "Can agent pick up where we left off with minimal prompting?"
17. ✅ Enhanced CONTEXT.md with session history, user preferences, critical decisions
18. ✅ Enhanced TODO.md with quick start guide for new agents

**Key Decisions**:

- Redis chosen for 10-100x performance improvement (PostgreSQL ~2000ms → Redis <200ms)
- 11 GeoJSON files in scope (excluding barbados_geocoded_stops)
- Custom action-buttons plugin confirmed (built in-house, no marketplace equivalent)
- Streaming parser required for building.geojson (658MB)
- Centroid extraction required for amenity.geojson (MultiPolygon → Point)
- 6-phase implementation approach
- Event-based passenger assignment (no centralized conductor service)

**Blockers**: None

**Next Steps**:

- ⏸️ Waiting for user approval to begin Step 1.1.1
- Ready to read country schema and start Phase 1

**Issues Discovered**:

- ✅ FIXED: Documentation incorrectly described "Conductor Service" for centralized assignment
  - Reality: Route assignment happens in `spawn_interface.py` spawn strategies
  - Conductor is vehicle component, not centralized service
- ✅ CLARIFIED: Plugin is custom-built `strapi-plugin-action-buttons` (no marketplace equivalent)
  - Initial research error suggested external package
  - Confirmed as in-house custom plugin on October 25

**Agent Handoff Notes**:

- All documentation complete and validated
- User prefers detailed analysis before implementation
- User values clarity and validation at each step
- Working on branch `branch-0.0.2.6` (NOT main)
- CONTEXT.md is primary reference (1,700+ lines)
- TODO.md is active task tracker (65+ steps)
- GEOJSON_IMPORT_CONTEXT.md is historical reference

---

### **Template for Future Sessions**

```markdown
### **Session X: [Date] - [Title]**

**Activities**:
- [ ] Task 1
- [ ] Task 2

**Key Decisions**:
- Decision 1: Rationale

**Blockers**: 
- Issue 1: Description

**Next Steps**:
- Next action

**Issues Discovered**:
- Issue 1: Description and resolution status
```

---

### **Session 2: October 25, 2025 - Implementation Started**

**Context**: Phase 1 implementation began

**Activities**:

1. ✅ **Step 1.1.1 COMPLETE** - Read current country schema
   - Read schema.json (113→145 lines after update)
   - Verified database: 16 columns in `countries` table
   - Found existing deletion history data
   - Cleared old data (fresh start approach)
   - Migrated `geodata_import_status`: text→json with structured default
   - Updated TODO.md progress tracking

2. ✅ **Step 1.1.2 COMPLETE** - Verify action-buttons plugin exists
   - Verified plugin directory structure
   - Confirmed documentation exists (ARCHITECTURE.md, EXAMPLES.ts, README.md)
   - Verified plugin enabled in config/plugins.ts
   - Checked dist/ folder contains built files
   - Validated schema migration after Strapi restart (text→jsonb)
   - Updated TODO.md progress tracking

3. ✅ **Step 1.1.3 COMPLETE** - List current country fields in database
   - Queried database: 16 columns verified
   - Confirmed geodata_import_status type is jsonb (migration successful)
   - No unexpected schema changes after Strapi restart
   - Database ready for button field addition
   - Updated TODO.md progress tracking

4. ✅ **Step 1.2.1 COMPLETE** - Read plugin architecture
   - Read ARCHITECTURE.md (290 lines)
   - Understood component hierarchy: Schema → Plugin Registration (server/admin) → CustomFieldButton → Handler
   - Understood data flow: Button click → window[onClick] → handler(fieldName, fieldValue, onChange) → DB
   - Learned security model: Handlers run in browser with admin privileges
   - Identified extension points: Button labels, handler functions, metadata structure, UI feedback
   - Updated TODO.md progress tracking

5. ✅ **Step 1.2.2 COMPLETE** - Review plugin examples
   - Read EXAMPLES.ts (257 lines)
   - Reviewed 5 example handlers: send email, upload CSV, generate report, sync CRM, default action
   - Understood handler pattern: window[functionName] = async (fieldName, fieldValue, onChange) => {...}
   - Learned metadata tracking: onChange({ status, timestamp, ...data })
   - Learned error handling: try/catch with success/failed status tracking
   - Updated TODO.md progress tracking

6. ✅ **Step 1.2.3 COMPLETE** - Understand field configuration
   - Read README.md documentation (lines 1-250)
   - Learned field configuration structure:
     - type: "customField"
     - customField: "plugin::action-buttons.button-field"
     - options: { buttonLabel, onClick }
   - Understood handler signature: (fieldName, fieldValue, onChange)
   - Ready to design GeoJSON import button configuration
   - Updated TODO.md progress tracking

7. ✅ **Step 1.3.1 COMPLETE** - Backup database
   - Created backup_20251025_145744.sql (6.4 MB)
   - Backed up all tables, data, schemas, constraints, indexes
   - Updated TODO.md progress tracking

8. ✅ **Step 1.3.2 COMPLETE** - Backup schema.json
   - Created schema.json.backup_20251025_152235 (3,357 bytes)
   - Backed up current schema with 145 lines and json field
   - Updated TODO.md progress tracking

9. ✅ **Step 1.3.3 COMPLETE** - Document rollback procedure
   - Database rollback: `psql -U david -h 127.0.0.1 -d arknettransit -f backup_20251025_145744.sql`
   - Schema rollback: `Copy-Item schema.json.backup_20251025_152235 schema.json -Force; npm run develop`
   - Updated TODO.md progress tracking

**Schema Changes**:

- File: `src/api/country/content-types/country/schema.json`
- Field: `geodata_import_status` changed from `text` to `json`
- Added structured default with 5 file types (highway, amenity, landuse, building, admin)
- Each tracks: status, lastImportDate, featureCount, lastJobId

**Database Actions**:

- Connected to `arknettransit` database
- Cleared `geodata_import_status` and `geodata_last_import` fields
- Ready for fresh import tracking

**Backup Files Created**:

- Database: `backup_20251025_145744.sql` (6.4 MB)
- Schema: `schema.json.backup_20251025_152235` (3,357 bytes)
- Rollback procedures documented

**Key Decisions**:

- Chose Option B (Fresh Start) over preserving deletion history
- Documented old status for reference only
- Created database backup before schema modifications (6.4 MB)
- Created schema.json backup for safe rollback (3.4 KB)

**Next Steps**:

- ⏸️ Step 1.4 - Design Button Configuration

---

**Last Updated**: October 25, 2025  
**Next Session**: Step 1.4 - Design Button Configuration
