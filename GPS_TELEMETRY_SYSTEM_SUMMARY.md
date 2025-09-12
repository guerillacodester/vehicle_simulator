# 🚐 Vehicle GPS Telemetry System - Easy Summary

## **The Big Picture: From Engine to GPS Server**

Think of this like a **digital vehicle** that drives along real routes and sends GPS data to a server, just like a real bus or van with a GPS tracker.

## **🔄 The Complete Flow**

```text
Real Route → Engine Physics → Distance Calculation → GPS Coordinates → Transmission
    ↓             ↓                    ↓                    ↓               ↓
 GeoJSON      Speed×Time         Route Interpolation    Plugin System   GPS Server
```

---

## **📍 Step 1: Route Building (route_topology.py)**

**What it does:** Takes messy route data and creates a clean, ordered path

**Input:** Fragmented GeoJSON route files (like puzzle pieces)
**Output:** One continuous route from start to finish

**How it works:**

1. **Load segments** - Read all the route pieces from GeoJSON
2. **Build graph** - Connect pieces that touch each other
3. **Find longest path** - Use smart search to find the complete route from terminus to terminus
4. **Order coordinates** - Create a clean list of GPS points in driving order

**Think of it like:** Taking a torn-up road map and reassembling it into one continuous driving route.

---

## **⚙️ Step 2: Engine Physics Simulation**

**What it does:** Simulates realistic vehicle movement based on speed and time

**Key Components:**

- **Speed Model** - How fast the vehicle goes (considers traffic, stops, etc.)
- **Engine Block** - Calculates `distance = speed × time` for each tick
- **Engine Buffer** - Stores the calculated distances

**Example:** If a vehicle goes 30 km/h for 1 minute, it travels 0.5 km total distance.

---

## **🗺️ Step 3: Distance → GPS Coordinates (vehicle_driver.py)**

**The Magic Conversion:** Turns abstract distance into real GPS coordinates

**Process:**

```python
# Get distance from engine
distance_km = engine_buffer.read().get("distance", 0.0)  # e.g., 2.5 km

# Convert to GPS coordinates on the route
lat, lon, bearing = interpolate_along_route_geodesic(route, distance_km)
# Result: lat=13.1234, lon=-59.5678, bearing=45°
```

**How interpolation works:**

1. **Walk the route** - Go through each segment of the route
2. **Find the right segment** - Where does the 2.5km distance fall?
3. **Project position** - Use geodesic math to find exact GPS coordinates
4. **Calculate heading** - Which direction is the vehicle facing?

**Think of it like:** You've driven 2.5km along a specific road - where exactly are you on that road?

---

## **🔌 Step 4: Plugin System - Getting Data to GPS Buffer**

**The Plugin Architecture:** Clean way to feed GPS data from different sources

### **Plugin Interface (ITelemetryPlugin)**

```python
class ITelemetryPlugin:
    def get_data(self) -> Dict[str, Any]:
        """Return GPS telemetry data as dictionary"""
```

### **Available Plugins:**

- **🧭 Navigator Plugin** - Gets data from route simulation (used in depot)
- **📡 Simulation Plugin** - Generates test data
- **🔧 ESP32 Plugin** - Reads from real hardware
- **📁 File Replay Plugin** - Replays recorded data

### **How Navigator Plugin Works (Main System):**

```python
class NavigatorTelemetryPlugin:
    def get_data(self):
        # Get position from vehicle driver
        telemetry_entry = self.navigator.telemetry_buffer.read()
        
        # Convert to standard GPS format
        return {
            "lat": telemetry_entry.get("lat"),      # GPS latitude
            "lon": telemetry_entry.get("lon"),      # GPS longitude  
            "speed": telemetry_entry.get("speed"),  # Current speed
            "heading": telemetry_entry.get("bearing"), # Direction
            "device_id": self.device_id,            # Vehicle ID
            "timestamp": datetime.now().isoformat() # When
        }
```

---

## **📡 Step 5: GPS Device & Transmission**

### **The GPS Device Pipeline:**

```text
Plugin → GPS Device → RxTx Buffer → WebSocket Transmitter → GPS Server
```

### **How Data Flows Through GPS Device:**

1. **Data Worker Thread:**

   ```python
   def _data_worker(self):
       # Get data from active plugin every tick
       telemetry_data = self.plugin_manager.get_data()  # 🔌 Plugin provides data
       
       if telemetry_data:
           self.rxtx_buffer.write(telemetry_data)       # 📦 Store in buffer
   ```

2. **Transmitter Worker Thread:**

   ```python
   def _transmitter_worker(self):
       # Read from buffer and send to server
       data = self.rxtx_buffer.read()                   # 📤 Get from buffer
       
       if data:
           packet = make_packet(data)                   # 📋 Format as packet
           await self.transmitter.send(packet)         # 🌐 Send to GPS server
   ```

### **Plugin System Benefits:**

- **🔄 Flexible** - Can switch between simulation, real hardware, or file replay
- **🧪 Testable** - Easy to inject test data
- **🔌 Extensible** - Add new data sources without changing GPS device code
- **🎯 Clean** - GPS device doesn't care where data comes from

---

## **🎯 Complete Example: One Tick of the System**

1. **Engine:** "Vehicle moved 0.1km in this tick"
2. **VehicleDriver:** "0.1km puts us at GPS coordinates 13.1234, -59.5678"
3. **Navigator Plugin:** "Here's the GPS data: lat=13.1234, lon=-59.5678, speed=30"
4. **GPS Device:** "Got data from plugin, storing in buffer"
5. **Transmitter:** "Sending GPS packet to server: {deviceId: 'BUS001', lat: 13.1234...}"
6. **GPS Server:** "Received location update for BUS001"

**The beauty:** Each component only knows about its immediate neighbors, making the system modular and testable!

---

## **🔧 Key Files and Locations**

| Component | File Location | Purpose |
|-----------|---------------|---------|
| Route Building | `route_topology.py` | Converts GeoJSON to ordered route |
| Engine Physics | `engine_block.py` | Calculates distance from speed×time |
| Distance→GPS | `vehicle_driver.py` | Interpolates distance to GPS coordinates |
| Plugin Interface | `plugins/interface.py` | Defines ITelemetryPlugin contract |
| GPS Device | `device.py` | Manages plugin data flow to transmission |
| Math Functions | `math.py` | Geodesic calculations for GPS positioning |

---

## **🚀 Testing and Examples**

- **`test_gps_device_consumer.py`** - Clean example of how to use GPS device API
- **`direct_gps_test.py`** - Simple standalone GPS device test
- **`send_test_packet.py`** - Inject test packets to running vehicles

---

*This system enables realistic vehicle simulation with accurate GPS telemetry transmission to remote servers, supporting both testing and production deployment scenarios.*
