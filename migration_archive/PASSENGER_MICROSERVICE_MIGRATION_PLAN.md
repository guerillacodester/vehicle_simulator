# Passenger Microservice Migration Plan

## Granular Step-by-Step Implementation & Testing Strategy

**Project Goal:** Decouple passenger simulation from depot simulator using Strapi as central communication hub

**Architecture:** Depot Sim ↔ Strapi Hub ↔ Passenger Microservice

---

## 📋 **PHASE 1: CLEAN SLATE PREPARATION**

*Estimated Time: 1-2 hours

### **Step 1.1: Backup & Documentation** ⏱️ *15 minutes*

- [ ] **1.1.1** Create backup of current working system
- [ ] **1.1.2** Document current passenger integration points
- [ ] **1.1.3** List all files that reference passenger services
- [ ] **1.1.4** Test current depot sim to establish baseline

**Success Criteria:**

- ✅ Depot sim runs successfully with passengers
- ✅ All passenger references documented
- ✅ Backup created and verified

**Test Command:** `python -m arknet_transit_simulator --mode depot --duration 5`

---

### **Step 1.2: Remove Passenger Dependencies** ⏱️ *30 minutes*

- [ ] **1.2.1** Remove `PassengerServiceFactory` import from `depot_manager.py`
- [ ] **1.2.2** Remove passenger service initialization in `DepotManager.__init__()`
- [ ] **1.2.3** Remove passenger service startup from route distribution
- [ ] **1.2.4** Remove passenger service shutdown from depot shutdown
- [ ] **1.2.5** Comment out passenger-related logging/status calls

**Success Criteria:**

- ✅ Depot sim starts without passenger service
- ✅ No passenger-related errors in logs
- ✅ Vehicles still initialize and get routes
- ✅ Drivers still board vehicles and activate GPS

**Test Command:** `python -m arknet_transit_simulator --mode depot --duration 5`
**Expected Result:** Vehicles operational, no passengers spawned, no errors

---

### **Step 1.3: Verify Clean Depot Operation** ⏱️ *15 minutes*

- [ ] **1.3.1** Test depot initialization without passengers
- [ ] **1.3.2** Verify vehicle assignment still works
- [ ] **1.3.3** Verify driver boarding still works  
- [ ] **1.3.4** Verify route distribution still works
- [ ] **1.3.5** Check GPS device activation still works

**Success Criteria:**

- ✅ Depot opens successfully
- ✅ Vehicles get assignments
- ✅ Drivers board vehicles
- ✅ GPS coordinates loaded
- ✅ System stable without passenger service

**Test Command:** `python -m arknet_transit_simulator --mode depot --duration 10`
**Expected Log Entries:**

- "Depot initialization complete"
- "Driver [name] is ONBOARD vehicle [id]"
- "Set [X] GPS coordinates on driver"
- No passenger-related messages

---

## 📋 **PHASE 2: STANDALONE PASSENGER FOUNDATION**

*Estimated Time: 2-3 hours

### **Step 2.1: Create Plugin Architecture** ⏱️ *45 minutes*

- [ ] **2.1.1** Create `passenger_microservice/` directory structure
- [ ] **2.1.2** Create plugin base classes (`CountryPassengerPlugin`, `PluginLoader`)
- [ ] **2.1.3** Create Barbados plugin (`bb_plugin.py`) with basic data
- [ ] **2.1.4** Test plugin loading and country selection

**Success Criteria:**

- ✅ Plugin system discovers available countries
- ✅ Barbados plugin loads successfully
- ✅ Plugin provides cultural patterns and spawn weights
- ✅ No import errors or circular dependencies

**Test Command:** `cd passenger_microservice && python -c "from plugin_system import get_plugin_manager; print(get_plugin_manager().get_available_countries())"`
**Expected Result:** `{'bb': 'Barbados'}`

---

### **Step 2.2: Create Geographic Data Loader** ⏱️ *30 minutes*

- [ ] **2.2.1** Create `GeographicDataLoader` class
- [ ] **2.2.2** Add GeoJSON file discovery and loading
- [ ] **2.2.3** Add coordinate extraction and indexing
- [ ] **2.2.4** Test with sample GeoJSON data (even if limited)

**Success Criteria:**

- ✅ Loads available GeoJSON files for country
- ✅ Extracts coordinates and properties
- ✅ Creates spatial index for fast lookups
- ✅ Handles missing files gracefully

**Test Command:** `python -c "from geographic_data_loader import GeographicDataLoader; loader = GeographicDataLoader(); print(loader.get_available_datasets())"`

---

### **Step 2.3: Create Statistical Passenger Spawner** ⏱️ *45 minutes*

- [ ] **2.3.1** Create `StatisticalPassengerSpawner` class
- [ ] **2.3.2** Implement time-based spawn rate calculation
- [ ] **2.3.3** Implement location-based spawning logic
- [ ] **2.3.4** Create passenger data structure
- [ ] **2.3.5** Test basic passenger generation (no networking yet)

**Success Criteria:**

- ✅ Generates passengers based on time of day
- ✅ Uses cultural patterns from plugin
- ✅ Places passengers at realistic coordinates
- ✅ Assigns trip purposes based on time/location

**Test Command:** `python -c "from passenger_spawner import test_passenger_generation; test_passenger_generation()"`
**Expected Result:** Sample passengers generated with coordinates and purposes

---

### **Step 2.4: Test Standalone Passenger Generation** ⏱️ *30 minutes*

- [ ] **2.4.1** Create simple test script for passenger spawning
- [ ] **2.4.2** Test rush hour vs off-peak spawning rates
- [ ] **2.4.3** Test different trip purpose distributions
- [ ] **2.4.4** Verify passenger timeout/cleanup works
- [ ] **2.4.5** Test memory usage stays bounded

**Success Criteria:**

- ✅ Higher spawn rates during rush hours (7-9 AM, 4-6 PM)
- ✅ Different trip purposes for different times
- ✅ Passengers expire after 30 minutes
- ✅ Memory usage stays under 50MB for 1000 passengers

**Test Command:** `python test_passenger_spawning.py --duration 60 --country bb`

---

## 📋 **PHASE 3: STRAPI INTEGRATION FOUNDATION**

*Estimated Time: 1-2 hours

### **Step 3.1: Strapi Depot Data Integration** ⏱️ *30 minutes*

- [ ] **3.1.1** Test current Strapi depot API endpoint
- [ ] **3.1.2** Check if depots have lat/long coordinates
- [ ] **3.1.3** Add coordinates to depot records if missing
- [ ] **3.1.4** Create depot data fetcher for passenger service

**Success Criteria:**

- ✅ `curl http://localhost:1337/api/depots` returns depot data
- ✅ Depot records contain location coordinates
- ✅ Passenger service can fetch depot locations
- ✅ Depot coordinates match expected geographic area

**Test Command:** `curl http://localhost:1337/api/depots | jq '.data[0].location'`
**Expected Result:** `{"lat": 13.281, "lon": -59.646}` (or similar)

---

### **Step 3.2: Add Passenger Tables to Strapi** ⏱️ *45 minutes*

- [ ] **3.2.1** Create `passengers` content type in Strapi
- [ ] **3.2.2** Add passenger event fields (spawn, pickup, dropoff)
- [ ] **3.2.3** Create `passenger-events` content type for real-time events
- [ ] **3.2.4** Test CRUD operations via API
- [ ] **3.2.5** Test passenger data persistence

**Success Criteria:**

- ✅ Passenger content type created with all fields
- ✅ Can POST new passenger via API
- ✅ Can GET passengers by location/status
- ✅ Event records persist correctly

**Test Commands:**

```bash
# Create passenger
curl -X POST http://localhost:1337/api/passengers -H "Content-Type: application/json" -d '{"data": {"latitude": 13.281, "longitude": -59.646, "status": "waiting"}}'

# Get passengers  
curl http://localhost:1337/api/passengers
```

---

### **Step 3.3: Socket.IO Server Setup in Strapi** ⏱️ *45 minutes*

- [ ] **3.3.1** Install socket.io dependencies in Strapi
- [ ] **3.3.2** Create socket.io server configuration
- [ ] **3.3.3** Add basic event handlers (connect/disconnect)
- [ ] **3.3.4** Test socket connections from simple client
- [ ] **3.3.5** Test event broadcasting

**Success Criteria:**

- ✅ Socket.IO server runs on Strapi (port 1337)
- ✅ Clients can connect successfully
- ✅ Events broadcast to all connected clients
- ✅ Connection/disconnection logged properly

**Test Command:**

```bash
# Test with simple node client
node -e "
const io = require('socket.io-client');
const socket = io('http://localhost:1337');
socket.on('connect', () => console.log('Connected!'));
setTimeout(() => process.exit(0), 2000);
"
```

---

## 📋 **PHASE 4: PASSENGER MICROSERVICE DEVELOPMENT**

*Estimated Time: 2-3 hours

### **Step 4.1: Basic Microservice Structure** ⏱️ *30 minutes*

- [ ] **4.1.1** Create FastAPI app structure
- [ ] **4.1.2** Add health check endpoint
- [ ] **4.1.3** Add basic logging configuration
- [ ] **4.1.4** Test HTTP server startup
- [ ] **4.1.5** Test process isolation (separate terminal)

**Success Criteria:**

- ✅ Microservice starts on different port (8001)
- ✅ Health endpoint responds correctly
- ✅ Runs independently from depot simulator
- ✅ Logs to separate log stream

**Test Commands:**

```bash
# Terminal 1: Start passenger microservice
python -m passenger_microservice --country bb --port 8001

# Terminal 2: Test health
curl http://localhost:8001/health
```

---

### **Step 4.2: Socket.IO Client Integration** ⏱️ *45 minutes*

- [ ] **4.2.1** Add socket.io client to passenger microservice
- [ ] **4.2.2** Connect to Strapi socket server
- [ ] **4.2.3** Implement event registration and identification
- [ ] **4.2.4** Test connection and basic event handling
- [ ] **4.2.5** Add connection retry logic

**Success Criteria:**

- ✅ Passenger service connects to Strapi socket server
- ✅ Registers as "passenger_service" client type
- ✅ Receives confirmation from Strapi
- ✅ Handles connection failures gracefully
- ✅ Auto-reconnects if Strapi restarts

**Test Command:** Check Strapi logs for "passenger_service connected"

---

### **Step 4.3: Passenger Spawning with Strapi Integration** ⏱️ *60 minutes*

- [ ] **4.3.1** Connect spawner to Strapi depot data
- [ ] **4.3.2** Implement passenger creation in Strapi database
- [ ] **4.3.3** Add real-time spawn event broadcasting
- [ ] **4.3.4** Test passenger persistence in database
- [ ] **4.3.5** Test event broadcasting to connected clients

**Success Criteria:**

- ✅ Passengers spawn at depot coordinates from Strapi
- ✅ Passenger records saved to Strapi database
- ✅ Spawn events broadcast via socket.io
- ✅ Can query passengers via Strapi API
- ✅ Geographic distribution looks realistic

**Test Commands:**

```bash
# Check passenger creation
curl http://localhost:1337/api/passengers

# Monitor events (with socket client)
node socket_monitor.js
```

---

### **Step 4.4: Passenger Query System** ⏱️ *45 minutes*

- [ ] **4.4.1** Implement proximity-based passenger queries
- [ ] **4.4.2** Add spatial indexing for fast lookups
- [ ] **4.4.3** Create query response system via socket.io
- [ ] **4.4.4** Test query performance with realistic data
- [ ] **4.4.5** Test concurrent queries from multiple clients

**Success Criteria:**

- ✅ Can find passengers within X km of coordinate
- ✅ Query responds in <100ms for 1000 passengers
- ✅ Results sorted by distance
- ✅ Multiple simultaneous queries work correctly
- ✅ Returns passenger status and trip details

**Test Command:** Send test query via socket.io and measure response time

---

## 📋 **PHASE 5: DEPOT-PASSENGER COMMUNICATION**

*Estimated Time: 1-2 hours

### **Step 5.1: Add Socket.IO Client to Depot Simulator** ⏱️ *30 minutes*

- [ ] **5.1.1** Add socket.io client to depot simulator
- [ ] **5.1.2** Connect depot sim to Strapi socket server
- [ ] **5.1.3** Register as "depot_service" client type
- [ ] **5.1.4** Test connection alongside passenger service
- [ ] **5.1.5** Verify both services can connect simultaneously

**Success Criteria:**

- ✅ Depot service connects to Strapi
- ✅ Both depot and passenger services connected simultaneously
- ✅ Each service has unique identification
- ✅ Strapi logs show both client types
- ✅ Services can send/receive events independently

**Test Command:** Check Strapi connection logs for both "depot_service" and "passenger_service"

---

### **Step 5.2: Vehicle-Passenger Query Integration** ⏱️ *45 minutes*

- [ ] **5.2.1** Add passenger query capability to vehicle/driver
- [ ] **5.2.2** Implement GPS-based passenger search requests
- [ ] **5.2.3** Handle passenger query responses from microservice
- [ ] **5.2.4** Test query-response cycle end-to-end
- [ ] **5.2.5** Add query result logging and validation

**Success Criteria:**

- ✅ Vehicle can request passengers near its GPS location
- ✅ Passenger service responds with nearby passengers
- ✅ Response includes passenger details and distances
- ✅ Query-response happens in real-time (<1 second)
- ✅ Multiple vehicles can query simultaneously

**Test Scenario:** Start both services, move vehicle to location with passengers, verify query works

---

### **Step 5.3: Passenger Pickup/Dropoff Events** ⏱️ *45 minutes*

- [ ] **5.3.1** Implement passenger pickup event system
- [ ] **5.3.2** Add passenger status tracking (waiting → traveling → completed)
- [ ] **5.3.3** Implement dropoff event system
- [ ] **5.3.4** Test full passenger lifecycle
- [ ] **5.3.5** Verify data consistency between services

**Success Criteria:**

- ✅ Vehicle can "pick up" passengers via event
- ✅ Passenger status updates correctly
- ✅ Vehicle can "drop off" passengers at destination
- ✅ Passenger records reflect complete journey
- ✅ Both services stay synchronized

**Test Scenario:** Full journey - spawn passenger, vehicle queries, pickup, travel, dropoff

---

## 📋 **PHASE 6: INTEGRATION TESTING & VALIDATION**

*Estimated Time: 1-2 hours

### **Step 6.1: End-to-End Integration Test** ⏱️ *30 minutes*

- [ ] **6.1.1** Start Strapi server
- [ ] **6.1.2** Start passenger microservice
- [ ] **6.1.3** Start depot simulator
- [ ] **6.1.4** Verify all connections established
- [ ] **6.1.5** Run complete simulation cycle

**Success Criteria:**

- ✅ All three services start successfully
- ✅ Socket connections established
- ✅ Passengers spawn at realistic locations
- ✅ Vehicles can find and interact with passengers
- ✅ No errors or connection issues

**Test Command:** Three-terminal test with all services running simultaneously

---

### **Step 6.2: Performance & Stress Testing** ⏱️ *30 minutes*

- [ ] **6.2.1** Test with high passenger volume (500+ passengers)
- [ ] **6.2.2** Test with multiple vehicles querying simultaneously
- [ ] **6.2.3** Test service restart scenarios
- [ ] **6.2.4** Test network disconnection/reconnection
- [ ] **6.2.5** Monitor memory usage over time

**Success Criteria:**

- ✅ System handles 500+ passengers without performance degradation
- ✅ Multiple vehicle queries don't cause bottlenecks
- ✅ Services reconnect automatically after failures
- ✅ Memory usage stays stable over long runs
- ✅ Response times stay under 200ms

---

### **Step 6.3: Feature Validation** ⏱️ *30 minutes*

- [ ] **6.3.1** Verify rush hour passenger patterns
- [ ] **6.3.2** Verify geographic distribution (depot vs other locations)
- [ ] **6.3.3** Verify trip purpose distributions
- [ ] **6.3.4** Verify passenger timeout and cleanup
- [ ] **6.3.5** Verify data persistence across restarts

**Success Criteria:**

- ✅ More passengers during 7-9 AM and 4-6 PM
- ✅ Higher passenger density at depot locations
- ✅ Work trips dominant during rush hours
- ✅ Passengers disappear after 30 minutes if not picked up
- ✅ Passenger data survives service restarts

---

## 📋 **PHASE 7: DOCUMENTATION & DEPLOYMENT**

*Estimated Time: 30-60 minutes

### **Step 7.1: Update Documentation** ⏱️ *30 minutes*

- [ ] **7.1.1** Update README with new architecture
- [ ] **7.1.2** Document service startup sequence
- [ ] **7.1.3** Document API endpoints and events
- [ ] **7.1.4** Update TODO.md to reflect completion
- [ ] **7.1.5** Create troubleshooting guide

### **Step 7.2: Create Deployment Scripts** ⏱️ *30 minutes*

- [ ] **7.2.1** Create startup script for all services
- [ ] **7.2.2** Create Docker configuration (optional)
- [ ] **7.2.3** Create monitoring/health check scripts
- [ ] **7.2.4** Test deployment on clean environment

---

## 🎯 **SUCCESS CRITERIA FOR COMPLETE PROJECT**

### **Functional Requirements:**

- ✅ Passenger and depot simulators run as independent processes
- ✅ Communication happens via Strapi Socket.IO hub
- ✅ Passengers spawn based on country-specific plugins
- ✅ Depot coordinates come from Strapi database
- ✅ Vehicles can query and interact with passengers
- ✅ Full passenger lifecycle (spawn → pickup → dropoff)

### **Performance Requirements:**

- ✅ System handles 500+ concurrent passengers
- ✅ Passenger queries respond in <200ms
- ✅ Memory usage stays under 100MB per service
- ✅ Services auto-reconnect after failures

### **Architecture Requirements:**

- ✅ True process isolation (can restart independently)
- ✅ Plugin-based country configuration
- ✅ Strapi as single source of truth
- ✅ Real-time event broadcasting
- ✅ Data persistence across restarts

---

## 🚀 **EXECUTION STRATEGY**

### **Daily Planning:**

- **Day 1:** Phases 1-2 (Clean slate + standalone passenger foundation)
- **Day 2:** Phases 3-4 (Strapi integration + microservice)  
- **Day 3:** Phases 5-7 (Communication + testing + deployment)

### **Testing Protocol:**

1. **After each step:** Run specified test command
2. **Before next phase:** Verify all success criteria met
3. **After each phase:** Full regression test
4. **End of day:** Commit working state to git

### **Rollback Strategy:**

- Maintain git branch for each phase
- Keep backup of working depot simulator
- Document all changes for easy reversal

---

**Are you ready to begin with Phase 1, Step 1.1? We'll go step by step and test each micro-change before proceeding.**
