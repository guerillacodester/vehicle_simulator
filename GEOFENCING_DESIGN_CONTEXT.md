# 🗺️ GEOFENCING SYSTEM ARCHITECTURE - DESIGN CONTEXT

**Date**: October 10, 2025  
**Status**: 🎨 **DESIGN PHASE - NO CODE YET**  
**Branch**: branch-0.0.2.2

---

## 🎯 **Design Objective**

Implement a **geofencing system at the GPS device level** to enable location awareness for:
- Depot queue management (know when vehicle at depot)
- Stop detection (know when vehicle at passenger stop)
- Zone-based behavior (different rules for different areas)

**Key Principle**: Geofencing must work **regardless of GPS source** (simulated, real hardware, file replay).

---

## ✅ **Design Decisions Made**

### **1. Geofence Shapes: Irregular Polygons Required** ✅
- **Decision**: Support polygon geofences (not just circles)
- **Rationale**: Real-world depots, parking areas, and boarding zones have irregular shapes
- **Impact**: More complex math (point-in-polygon), but more accurate

### **2. GPS Device Level Integration** ✅
- **Decision**: Geofence logic lives in GPS device layer
- **Rationale**: 
  - Works with any GPS plugin (simulated, ESP32, file replay)
  - Low latency (local computation)
  - GPS device becomes self-aware of location context
- **Implementation Point**: GPS device plugin system

### **3. Location Awareness Purpose** ✅
- **Primary Use Case**: Depot queue management
  - Conductor knows "am I at depot?"
  - Conductor knows "am I in boarding zone?"
  - Conductor knows "am I at front of queue?"
- **Secondary Use Cases**:
  - Stop detection for passenger pickup
  - Route adherence monitoring
  - Zone-based speed limits, etc.

---

## 🏗️ **Architecture Design (In Progress)**

### **Proposed Polygon System**

#### **Data Format: GeoJSON Standard** (RECOMMENDED)
```json
{
  "type": "Feature",
  "properties": {
    "fence_id": "depot_north_parking",
    "name": "Depot North Parking Area",
    "tags": ["depot", "parking"],
    "priority": 2
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-59.6132, 13.0969],  // [lon, lat] - GeoJSON standard
        [-59.6130, 13.0970],
        [-59.6128, 13.0968],
        [-59.6130, 13.0967],
        [-59.6132, 13.0969]   // Close the polygon
      ]
    ]
  }
}
```

**Why GeoJSON?**
- ✅ Industry standard for geographic data
- ✅ Compatible with Google Earth, QGIS, mapping tools
- ✅ Can import/export easily
- ✅ Supports multi-polygons, holes, complex shapes
- ⚠️ Lon-first format (counter-intuitive, but standard)

---

### **Proposed Component Architecture**

```
┌─────────────────────────────────────┐
│         GPS Device                  │
│  ┌───────────────────────────────┐  │
│  │  Geofence Engine              │  │
│  │  - Load fences from Strapi    │  │
│  │  - Cache locally              │  │
│  │  - Check position on GPS upd. │  │
│  │  - Emit events (entered/exit) │  │
│  └───────────────────────────────┘  │
│            ↓                         │
│  ┌───────────────────────────────┐  │
│  │  Plugin (Sim/ESP32/Replay)    │  │
│  │  - Provides lat/lon           │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
           ↓ Geofence Events
┌─────────────────────────────────────┐
│    Conductor / Driver               │
│    - Receives geofence events       │
│    - Reacts to location context     │
└─────────────────────────────────────┘
```

---

### **Proposed Data Model**

```python
@dataclass
class Geofence:
    """Represents a geographic fence (polygon or circle)"""
    fence_id: str
    name: str
    fence_type: Literal["circular", "polygon"]
    tags: List[str]  # e.g., ["depot", "boarding"]
    priority: int = 0  # Higher = more important
    
    # Geometry (GeoJSON compatible)
    geometry: Dict[str, Any]  # GeoJSON geometry object
    
    # Bounding box for optimization
    bbox: Tuple[float, float, float, float]  # (min_lon, min_lat, max_lon, max_lat)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Relations
    depot_id: Optional[str] = None
    stop_id: Optional[str] = None
    route_id: Optional[str] = None
    
    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if point is inside fence"""
        # 1. Quick bounding box check
        if not self._in_bbox(lat, lon):
            return False
        
        # 2. Precise check based on type
        if self.fence_type == "circular":
            return self._check_circular(lat, lon)
        elif self.fence_type == "polygon":
            return self._check_polygon(lat, lon)
    
    def _in_bbox(self, lat: float, lon: float) -> bool:
        """Quick bounding box check (optimization)"""
        min_lon, min_lat, max_lon, max_lat = self.bbox
        return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
    
    def _check_polygon(self, lat: float, lon: float) -> bool:
        """Point-in-polygon using ray casting algorithm"""
        # Implementation needed
        pass


class GeofenceEngine:
    """Manages geofence checking for GPS device"""
    
    def __init__(self):
        self.fences: Dict[str, Geofence] = {}
        self.current_fences: Set[str] = set()  # Fences we're currently inside
    
    async def load_fences_from_api(self, route_id: Optional[str] = None):
        """Load geofences from Strapi API"""
        # Fetch from Strapi, cache locally
        pass
    
    def check_position(self, lat: float, lon: float) -> List[Geofence]:
        """Check which fences contain this position"""
        results = []
        for fence in self.fences.values():
            if fence.contains_point(lat, lon):
                results.append(fence)
        return results
    
    def detect_events(self, lat: float, lon: float) -> List[GeofenceEvent]:
        """Detect ENTERED/EXITED events"""
        active_fences = {f.fence_id for f in self.check_position(lat, lon)}
        events = []
        
        # ENTERED events
        for fence_id in active_fences - self.current_fences:
            events.append(GeofenceEvent(
                event_type="entered",
                fence_id=fence_id,
                fence=self.fences[fence_id]
            ))
        
        # EXITED events
        for fence_id in self.current_fences - active_fences:
            events.append(GeofenceEvent(
                event_type="exited",
                fence_id=fence_id,
                fence=self.fences[fence_id]
            ))
        
        self.current_fences = active_fences
        return events


@dataclass
class GeofenceEvent:
    """Represents a geofence event (entered/exited)"""
    event_type: Literal["entered", "exited", "dwelling"]
    fence_id: str
    fence: Geofence
    timestamp: datetime = field(default_factory=datetime.now)
```

---

### **Proposed GPS Device Integration**

```python
# In GPSDevice class
class GPSDevice(BaseComponent):
    def __init__(self, device_id, ws_transmitter, plugin_config=None):
        # ... existing code ...
        
        # Add geofence engine
        self.geofence_engine = GeofenceEngine()
        self.geofence_callback = None  # For local event handling
    
    async def load_geofences(self, route_id: Optional[str] = None):
        """Load geofences for this device"""
        await self.geofence_engine.load_fences_from_api(route_id)
    
    def set_geofence_callback(self, callback):
        """Set callback for geofence events"""
        self.geofence_callback = callback
    
    def _data_worker(self):
        """Worker thread that collects data from plugin and writes to buffer"""
        while not self._stop.is_set():
            # Get telemetry data from plugin
            telemetry_data = self.plugin_manager.get_data()
            
            if telemetry_data:
                # Write to buffer for transmission
                self.rxtx_buffer.write(telemetry_data)
                
                # Check geofences (NEW)
                self._check_geofences(
                    telemetry_data['lat'],
                    telemetry_data['lon']
                )
    
    def _check_geofences(self, lat: float, lon: float):
        """Check current position against geofences"""
        events = self.geofence_engine.detect_events(lat, lon)
        
        for event in events:
            # Emit via Socket.IO (if connected)
            if self.use_socketio and self.sio_connected:
                asyncio.create_task(self._emit_geofence_event(event))
            
            # Trigger local callback
            if self.geofence_callback:
                self.geofence_callback(event)
    
    async def _emit_geofence_event(self, event: GeofenceEvent):
        """Emit geofence event via Socket.IO"""
        event_data = {
            "device_id": self.component_id,
            "event": event.event_type,
            "fence_id": event.fence_id,
            "fence_name": event.fence.name,
            "tags": event.fence.tags,
            "timestamp": event.timestamp.isoformat()
        }
        await self.sio.emit('geofence:event', event_data)
```

---

## 📊 **Strapi Data Model Design**

### **Content Type: `geofence`**

```javascript
{
  "collectionName": "geofences",
  "info": {
    "singularName": "geofence",
    "pluralName": "geofences",
    "displayName": "Geofence"
  },
  "attributes": {
    "fence_id": {
      "type": "string",
      "required": true,
      "unique": true
    },
    "name": {
      "type": "string",
      "required": true
    },
    "fence_type": {
      "type": "enumeration",
      "enum": ["circular", "polygon"],
      "default": "circular"
    },
    "geometry": {
      "type": "json",
      "required": true,
      "description": "GeoJSON geometry object"
    },
    "tags": {
      "type": "json",
      "description": "Array of tags like ['depot', 'boarding']"
    },
    "priority": {
      "type": "integer",
      "default": 0,
      "description": "Higher priority wins if in multiple fences"
    },
    "metadata": {
      "type": "json",
      "description": "Additional properties"
    },
    "depot": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::depot.depot"
    },
    "stop": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::stop.stop"
    },
    "route": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::route.route"
    }
  }
}
```

---

## 🚀 **Implementation Strategy**

### **Phase 1: MVP Polygon Geofencing** (3-4 hours)
**Goal**: Basic polygon support at GPS device level

**Tasks**:
1. ✅ Create `GeofenceEngine` class (~30 min)
   - Point-in-polygon algorithm (ray casting)
   - Bounding box optimization
   - Event detection (entered/exited)

2. ✅ Integrate with GPS Device (~45 min)
   - Add geofence checking to data worker
   - Emit events via Socket.IO
   - Add geofence callback support

3. ✅ Create Strapi content type (~20 min)
   - `geofence` collection
   - Relations to depots/stops/routes

4. ✅ API Client for fence loading (~30 min)
   - Fetch geofences from Strapi
   - Cache locally in GPS device
   - Filter by route/depot

5. ✅ Testing infrastructure (~45 min)
   - Unit tests for point-in-polygon
   - Integration tests with simulated GPS
   - Test depot arrival/departure detection

6. ✅ Documentation (~30 min)
   - How to create geofences in Strapi
   - GeoJSON format guide
   - Event handling examples

**Total**: ~3.5 hours

---

### **Phase 2: Advanced Features** (Future)
- GeoJSON file import/export
- Self-intersection validation
- R-tree spatial indexing (for 100+ fences)
- Progressive fence loading (load as vehicle moves)
- Dwelling events (been inside fence for X seconds)
- Approaching events (within 2x radius, moving toward)
- Map-based fence drawing in Strapi

---

## 🔧 **Performance Considerations**

### **Optimization Strategy**

**Problem**: 1,200 vehicles × 100 fences × 1Hz = 120,000 checks/second

**Solution 1: Bounding Box Pre-filter**
```python
# Quick reject ~90% of fences
if not fence.bbox_contains(lat, lon):
    continue  # Skip expensive polygon check
```
- **Saves**: 90% of polygon computations
- **Complexity**: O(1) for bbox check vs. O(n) for polygon

**Solution 2: Load Relevant Fences Only**
```python
# Only load fences for vehicle's route
gps_device.load_geofences(route_id="1A")  # Loads ~10 fences instead of 100
```
- **Saves**: 90% memory and computation
- **Risk**: What if vehicle goes off-route?

**Solution 3: R-tree Spatial Index** (Phase 2)
```python
# Query is O(log n) instead of O(n)
from rtree import index
idx = index.Index()
potential_fences = idx.intersection((lat, lon, lat, lon))
```
- **Saves**: 95%+ computation for large fence counts
- **Cost**: External dependency, more complex

**Recommendation**: Start with Solutions 1 & 2, add Solution 3 if needed.

---

## 📋 **Open Questions to Resolve**

### **1. Fence Count & Complexity**
- **Q**: How many polygon fences per depot?
- **Options**: 2-5 (simple), 10-20 (moderate), 50+ (complex)
- **Impact**: Affects performance optimization strategy

### **2. Fence Complexity**
- **Q**: How many vertices per polygon typically?
- **Options**: 4-6 (rectangles), 10-20 (detailed), 50+ (highly detailed)
- **Impact**: Affects computation time

### **3. Fence Source**
- **Q**: How will fences be created?
- **Options**:
  - Manual coordinate entry in Strapi
  - Import from GIS tools (Google Earth, QGIS)
  - Draw on map interface
  - Generate programmatically from depot boundaries
- **Decision Needed**: Determines UI/UX requirements

### **4. Update Frequency**
- **Q**: Can fences change during simulation runtime?
- **Options**:
  - Static (load once at startup)
  - Dynamic (reload periodically)
  - Event-driven (Strapi webhook triggers reload)
- **Decision Needed**: Affects caching strategy

### **5. Validation Strictness**
- **Q**: How to handle invalid polygons?
- **Options**:
  - Reject (strict validation)
  - Accept with warnings
  - Auto-fix (e.g., auto-close polygon)
- **Decision Needed**: Affects user experience

### **6. Priority Resolution**
- **Q**: If vehicle in multiple overlapping fences, which wins?
- **Options**:
  - Highest priority number
  - Smallest area
  - Most specific tag
  - All (return list)
- **Decision Needed**: Affects event handling logic

### **7. Fence Association**
- **Q**: Should geofences be related to depots/stops?
- **Options**:
  - Tightly coupled (each depot has defined fences)
  - Loosely coupled (fences tagged with depot ID)
  - Independent (fences standalone, matched by location)
- **Decision Needed**: Affects data model

---

## 🎯 **Next Steps When Resuming**

1. **Answer Open Questions** (above)
2. **Review and approve architecture design**
3. **Create implementation plan** (break down Phase 1 into tasks)
4. **Start coding** GeofenceEngine class
5. **Integrate** with GPS Device
6. **Test** with simulated GPS data
7. **Create** Strapi content type
8. **Document** usage and examples

---

## 🔗 **Related Context Documents**

- **`SESSION_RESUME_CONTEXT.md`** - Priority 2 Phase 1 (Socket.IO) completion status
- **`QUICK_RESUME.md`** - Quick start guide for Priority 2
- **`TODO.md`** - Overall project roadmap (Priority 2 Phase 2 is next)

---

## 💡 **Key Architectural Principles**

1. **GPS Device Abstraction**: Geofencing works regardless of GPS source (sim, hardware, replay)
2. **Performance First**: Optimize for 1,200 concurrent vehicles
3. **Standards Compliance**: Use GeoJSON (industry standard)
4. **Graceful Degradation**: System works without geofences (optional feature)
5. **Event-Driven**: Use events (entered/exited) rather than polling
6. **Cache Local, Fetch Remote**: Strapi as source of truth, local cache for speed

---

## 🚨 **Critical Dependencies**

**Before implementing geofencing**:
1. ✅ GPS Device plugin system (DONE)
2. ✅ Socket.IO integration (DONE - Priority 2 Phase 1)
3. ⏸️ Conductor location awareness (NEEDED - currently conductor doesn't know position)
4. ⏸️ Strapi geofence content type (NEEDED - need to create)

**Blocker**: Conductor currently doesn't receive driver location updates.
**Solution**: Make conductor listen to `driver:location:update` Socket.IO events (Phase 1.5)

---

**Design Session Saved**: October 10, 2025  
**Ready to Resume**: ✅ YES (answer open questions, then implement)  
**Estimated Implementation Time**: 3-4 hours for Phase 1 MVP

---

**🎯 NEXT ACTION**: Answer the 7 open questions above, then approve architecture and proceed to implementation.
