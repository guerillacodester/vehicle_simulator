# 🗺️ LocationService Architecture — Complete Design

**Status**: Architecture Design Complete  
**Date**: October 10, 2025  
**Module**: `arknet_transit_simulator/geospatial/`

---

## Executive Summary

The **LocationService** is the single source of truth for all position-awareness capabilities in the system. It provides:

1. **Geofence containment** (circle + polygon support)
2. **Nearest entity queries** (stops, POIs, places)
3. **Event-driven triggers** (location-based automation)
4. **Real-time updates** (Strapi-backed, dynamic add/remove)
5. **Multi-actor coordination** (passengers, conductors, drivers)

**MVP Strategy**: Start with **circles** (simple 3-field UI), architect for **polygons** (zero refactoring needed later).

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Phased Geometry Support](#phased-geometry-support)
3. [Data Models](#data-models)
4. [LocationService API](#locationservice-api)
5. [Strapi Schema](#strapi-schema)
6. [UI Strategy (MVP → Advanced)](#ui-strategy)
7. [Event Flow](#event-flow)
8. [Performance](#performance)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Examples](#examples)

---

## Design Principles

1. **Single Source of Truth**: All position-awareness queries go through LocationService
2. **Geometry Agnostic**: Support circles AND polygons with unified API
3. **Progressive Enhancement**: Start simple (circles), refine later (polygons)
4. **Zero Refactoring**: MVP → Advanced requires no code changes, only data additions
5. **Strapi-Backed**: All geofences/triggers stored in Strapi, runtime cache in LocationService
6. **Real-time Updates**: Dynamic add/remove/update without restarts
7. **Thread-Safe**: Concurrent reads/writes from GPS devices, passengers, conductors

---

## Phased Geometry Support

### Phase 1: MVP — Circles Only (Weeks 1-2)

**Capabilities:**
- ✅ Circle geofences (lat, lon, radius)
- ✅ Geofence enter/exit events
- ✅ Nearest stop/POI queries
- ✅ Basic triggers (depot entry, proximity alerts)
- ✅ Simple Strapi UI (3 fields: lat, lon, radius)

**UI Simplicity:**
```
Create Geofence (Circle)
┌─────────────────────────────────┐
│ Name: Depot North               │
│ Type: [depot ▼]                 │
│                                 │
│ Center Latitude:  -37.8136      │
│ Center Longitude: 145.0123      │
│ Radius (meters):  80            │
│                                 │
│ [Create Geofence]               │
└─────────────────────────────────┘
```

**Why circles for MVP:**
- Simple UI (3 input fields, no drawing tools)
- Fast to prototype and test
- Good enough for basic depot/proximity triggers
- Users can define geofences immediately without learning GIS tools

**Limitations accepted:**
- Not precise for irregular shapes
- May include unwanted adjacent areas
- Cannot define complex zones with holes

### Phase 2: Advanced — Polygons Added (Weeks 3-4)

**Capabilities:**
- ✅ All Phase 1 features
- ✅ Polygon geofences (GeoJSON)
- ✅ Precise depot boundaries
- ✅ Complex service areas
- ✅ Import from GeoJSON files
- ✅ Visual map-based drawing tool (Strapi plugin or external)

**UI Enhancement:**
```
Create Geofence (Polygon)
┌─────────────────────────────────┐
│ Name: Depot North - Precise     │
│ Type: [depot ▼]                 │
│ Geometry: [● Circle  ○ Polygon] │
│                                 │
│ [Draw on Map] or [Import GeoJSON]│
│                                 │
│ ┌─────────────────────────────┐ │
│ │      [Interactive Map]      │ │
│ │   Click to add vertices     │ │
│ │   Double-click to finish    │ │
│ └─────────────────────────────┘ │
│                                 │
│ Coordinates (GeoJSON):          │
│ [[145.0123, -37.8136],          │
│  [145.0128, -37.8136],          │
│  [145.0128, -37.8132],          │
│  [145.0123, -37.8132],          │
│  [145.0123, -37.8136]]          │
│                                 │
│ [Create Geofence]               │
└─────────────────────────────────┘
```

**Upgrade path:**
- Existing circle geofences continue to work
- Users can convert circle → polygon (approximate as square)
- New geofences can be either type
- No code changes in LocationService (already supports both)

---

## Data Models

### Geofence (Unified Model)

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

class GeometryType(Enum):
    CIRCLE = "circle"
    POLYGON = "polygon"

@dataclass
class Point:
    """Geographic point"""
    lat: float
    lon: float
    
    def to_tuple(self) -> tuple:
        return (self.lat, self.lon)

@dataclass
class BoundingBox:
    """Rectangular bounding box for optimization"""
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    
    def contains(self, point: Point) -> bool:
        """Quick containment check"""
        return (self.min_lon <= point.lon <= self.max_lon and
                self.min_lat <= point.lat <= self.max_lat)

@dataclass
class Geofence:
    """
    Unified geofence model supporting both circles and polygons.
    
    MVP: Use geometry_type="circle" with center + radius
    Phase 2: Add geometry_type="polygon" with polygon coordinates
    """
    id: str
    name: str
    type: str  # "depot", "boarding_zone", "service_area", "restricted"
    
    # Geometry (one must be specified)
    geometry_type: GeometryType
    
    # Circle geometry (required if geometry_type == CIRCLE)
    center: Optional[Point] = None
    radius_meters: Optional[float] = None
    
    # Polygon geometry (required if geometry_type == POLYGON)
    polygon: Optional[List[List[float]]] = None  # GeoJSON: [[lon, lat], ...]
    
    # Computed (auto-generated)
    bbox: Optional[BoundingBox] = None
    
    # Metadata
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and compute bbox"""
        if self.geometry_type == GeometryType.CIRCLE:
            if not self.center or not self.radius_meters:
                raise ValueError("Circle geofence requires center and radius_meters")
            self.bbox = self._compute_circle_bbox()
        
        elif self.geometry_type == GeometryType.POLYGON:
            if not self.polygon or len(self.polygon) < 3:
                raise ValueError("Polygon geofence requires at least 3 coordinates")
            self.bbox = self._compute_polygon_bbox()
            self._validate_polygon()
    
    def contains(self, point: Point) -> bool:
        """Check if point is inside geofence (unified interface)"""
        # Quick reject via bbox
        if not self.bbox.contains(point):
            return False
        
        # Type-specific containment check
        if self.geometry_type == GeometryType.CIRCLE:
            return self._contains_circle(point)
        else:
            return self._contains_polygon(point)
    
    def _contains_circle(self, point: Point) -> bool:
        """Circle containment using haversine distance"""
        from geospatial.utils import haversine_distance
        distance = haversine_distance(self.center, point)
        return distance <= self.radius_meters
    
    def _contains_polygon(self, point: Point) -> bool:
        """Polygon containment using ray casting algorithm"""
        from geospatial.utils import point_in_polygon
        return point_in_polygon(point, self.polygon)
    
    def _compute_circle_bbox(self) -> BoundingBox:
        """Compute bounding box for circle"""
        # Approximate: 1 degree lat/lon ≈ 111 km at equator
        # More precise: use haversine_inverse
        lat_delta = (self.radius_meters / 111000.0)
        lon_delta = (self.radius_meters / (111000.0 * abs(math.cos(math.radians(self.center.lat)))))
        
        return BoundingBox(
            min_lon=self.center.lon - lon_delta,
            min_lat=self.center.lat - lat_delta,
            max_lon=self.center.lon + lon_delta,
            max_lat=self.center.lat + lat_delta
        )
    
    def _compute_polygon_bbox(self) -> BoundingBox:
        """Compute bounding box for polygon"""
        lons = [coord[0] for coord in self.polygon]
        lats = [coord[1] for coord in self.polygon]
        
        return BoundingBox(
            min_lon=min(lons),
            min_lat=min(lats),
            max_lon=max(lons),
            max_lat=max(lats)
        )
    
    def _validate_polygon(self):
        """Validate polygon (closed ring, no self-intersection)"""
        # Check closed ring
        if self.polygon[0] != self.polygon[-1]:
            raise ValueError("Polygon must be a closed ring (first == last coordinate)")
        
        # TODO: Add self-intersection check if needed (complex)
    
    @classmethod
    def from_strapi(cls, data: dict) -> 'Geofence':
        """Create Geofence from Strapi API response"""
        geometry_type = GeometryType(data['geometry_type'])
        
        if geometry_type == GeometryType.CIRCLE:
            return cls(
                id=str(data['id']),
                name=data['name'],
                type=data['type'],
                geometry_type=geometry_type,
                center=Point(lat=data['center_lat'], lon=data['center_lon']),
                radius_meters=data['radius_meters'],
                enabled=data.get('enabled', True),
                metadata=data.get('metadata', {})
            )
        else:  # POLYGON
            return cls(
                id=str(data['id']),
                name=data['name'],
                type=data['type'],
                geometry_type=geometry_type,
                polygon=data['polygon'],
                enabled=data.get('enabled', True),
                metadata=data.get('metadata', {})
            )
```

### LocationContext (Output)

```python
@dataclass
class NearestResult:
    """Result for nearest-X queries"""
    id: str
    name: str
    category: Optional[str] = None
    distance_meters: float = 0.0
    bearing_degrees: Optional[float] = None
    position: Optional[Point] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class GeofenceEvent:
    """Event fired when geofence transition occurs"""
    type: str  # "entered" or "exited"
    fence_id: str
    fence_name: str
    timestamp: datetime
    position: Point

@dataclass
class LocationContext:
    """
    Complete location intelligence for a single GPS position.
    Returned by LocationService.get_location_context()
    """
    position: Point
    timestamp: datetime
    
    # Geofence containment
    geofences: Set[str] = field(default_factory=set)  # IDs of containing geofences
    geofence_events: List[GeofenceEvent] = field(default_factory=list)
    
    # Nearest entities
    nearest_stop: Optional[NearestResult] = None
    nearest_poi: Optional[NearestResult] = None
    nearest_place: Optional[NearestResult] = None
    
    # Optional: multiple nearby entities
    nearby_stops: List[NearestResult] = field(default_factory=list)
    nearby_pois: List[NearestResult] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return {
            "position": {"lat": self.position.lat, "lon": self.position.lon},
            "timestamp": self.timestamp.isoformat(),
            "geofences": list(self.geofences),
            "geofence_events": [
                {
                    "type": e.type,
                    "fence_id": e.fence_id,
                    "fence_name": e.fence_name,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.geofence_events
            ],
            "nearest_stop": {
                "id": self.nearest_stop.id,
                "name": self.nearest_stop.name,
                "distance_meters": self.nearest_stop.distance_meters
            } if self.nearest_stop else None,
            "nearest_poi": {
                "id": self.nearest_poi.id,
                "name": self.nearest_poi.name,
                "distance_meters": self.nearest_poi.distance_meters
            } if self.nearest_poi else None
        }
```

---

## LocationService API

```python
from threading import RLock
from typing import Dict, List, Set, Optional
from datetime import datetime

class LocationService:
    """
    Single source of truth for position-awareness.
    
    Provides:
    - Geofence containment (circles + polygons)
    - Nearest entity queries (stops, POIs, places)
    - Event-driven triggers
    - Real-time updates from Strapi
    """
    
    def __init__(self, strapi_client=None):
        # Data stores
        self._geofences: Dict[str, Geofence] = {}
        self._stops: Dict[str, Stop] = {}
        self._pois: Dict[str, POI] = {}
        self._places: Dict[str, Place] = {}
        self._triggers: Dict[str, LocationTrigger] = {}
        
        # Spatial indexes (for performance)
        self._stops_kdtree = None
        self._pois_kdtree = None
        self._places_kdtree = None
        
        # State tracking (for transition detection)
        self._position_state: Dict[str, Set[str]] = {}  # vehicle_id -> geofence_ids
        
        # Thread safety
        self._geofences_lock = RLock()
        self._spatial_lock = RLock()
        self._triggers_lock = RLock()
        
        # Strapi sync
        self.strapi = strapi_client
    
    # ═══════════════════════════════════════════════════════════════
    # PRIMARY API: Location Context
    # ═══════════════════════════════════════════════════════════════
    
    def get_location_context(
        self,
        position: Point,
        entity_id: str = None,  # vehicle_id, passenger_id, etc.
        route_filter: str = None,
        detect_transitions: bool = True,
        include_nearby: bool = False,
        nearby_radius_meters: float = 500.0
    ) -> LocationContext:
        """
        Get complete location intelligence for a position.
        
        This is the primary API used by GPS devices, passengers, conductors.
        
        Args:
            position: GPS position to query
            entity_id: Optional ID for state tracking (e.g., vehicle_id)
            route_filter: Optional route ID to filter stops/POIs
            detect_transitions: If True, detect geofence enter/exit events
            include_nearby: If True, populate nearby_stops/pois lists
            nearby_radius_meters: Radius for nearby queries
        
        Returns:
            LocationContext with geofences, nearest entities, events
        """
        context = LocationContext(
            position=position,
            timestamp=datetime.now()
        )
        
        # 1. Check geofence containment
        context.geofences = self._get_containing_geofences(position)
        
        # 2. Detect transitions (enter/exit events)
        if detect_transitions and entity_id:
            context.geofence_events = self._detect_transitions(
                entity_id,
                context.geofences
            )
        
        # 3. Find nearest stop
        context.nearest_stop = self.get_nearest_stop(position, route_filter)
        
        # 4. Find nearest POI
        context.nearest_poi = self.get_nearest_poi(position)
        
        # 5. Find nearest place
        context.nearest_place = self.get_nearest_place(position)
        
        # 6. Optional: nearby entities
        if include_nearby:
            context.nearby_stops = self.get_nearby_stops(position, nearby_radius_meters)
            context.nearby_pois = self.get_nearby_pois(position, nearby_radius_meters)
        
        return context
    
    # ═══════════════════════════════════════════════════════════════
    # GEOFENCE QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    def _get_containing_geofences(self, position: Point) -> Set[str]:
        """Get IDs of all geofences containing position"""
        containing = set()
        
        with self._geofences_lock:
            for fence_id, fence in self._geofences.items():
                if not fence.enabled:
                    continue
                
                if fence.contains(position):
                    containing.add(fence_id)
        
        return containing
    
    def _detect_transitions(self, entity_id: str, current_fences: Set[str]) -> List[GeofenceEvent]:
        """Detect geofence enter/exit events"""
        events = []
        
        # Get previous state
        previous_fences = self._position_state.get(entity_id, set())
        
        # Detect entered fences
        entered = current_fences - previous_fences
        for fence_id in entered:
            fence = self._geofences.get(fence_id)
            if fence:
                events.append(GeofenceEvent(
                    type="entered",
                    fence_id=fence_id,
                    fence_name=fence.name,
                    timestamp=datetime.now(),
                    position=None  # Can add position if needed
                ))
        
        # Detect exited fences
        exited = previous_fences - current_fences
        for fence_id in exited:
            fence = self._geofences.get(fence_id)
            if fence:
                events.append(GeofenceEvent(
                    type="exited",
                    fence_id=fence_id,
                    fence_name=fence.name,
                    timestamp=datetime.now(),
                    position=None
                ))
        
        # Update state
        self._position_state[entity_id] = current_fences
        
        return events
    
    # ═══════════════════════════════════════════════════════════════
    # NEAREST ENTITY QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    def get_nearest_stop(self, position: Point, route_filter: str = None) -> Optional[NearestResult]:
        """Find nearest stop to position"""
        if not self._stops_kdtree:
            return None
        
        # Query KDTree (fast)
        with self._spatial_lock:
            dist, idx = self._stops_kdtree.query([position.lat, position.lon])
            stop = list(self._stops.values())[idx]
        
        # Optional: filter by route
        if route_filter and route_filter not in stop.route_ids:
            # TODO: Query k-nearest and filter
            pass
        
        return NearestResult(
            id=stop.id,
            name=stop.name,
            category="stop",
            distance_meters=dist * 111000,  # rough conversion
            position=stop.position,
            metadata={"route_ids": stop.route_ids}
        )
    
    def get_nearest_poi(self, position: Point, category: str = None) -> Optional[NearestResult]:
        """Find nearest POI to position"""
        # Similar to get_nearest_stop
        pass
    
    def get_nearest_place(self, position: Point) -> Optional[NearestResult]:
        """Find nearest place to position"""
        # Similar to get_nearest_stop
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # GEOFENCE MANAGEMENT (Real-time CRUD)
    # ═══════════════════════════════════════════════════════════════
    
    def add_geofence(self, geofence: Geofence) -> None:
        """Add geofence at runtime"""
        with self._geofences_lock:
            self._geofences[geofence.id] = geofence
        logger.info(f"Added geofence: {geofence.name} ({geofence.geometry_type.value})")
    
    def remove_geofence(self, geofence_id: str) -> None:
        """Remove geofence at runtime"""
        with self._geofences_lock:
            if geofence_id in self._geofences:
                del self._geofences[geofence_id]
                logger.info(f"Removed geofence: {geofence_id}")
    
    def update_geofence(self, geofence_id: str, geofence: Geofence) -> None:
        """Update existing geofence"""
        with self._geofences_lock:
            self._geofences[geofence_id] = geofence
        logger.info(f"Updated geofence: {geofence.name}")
    
    def get_geofence(self, geofence_id: str) -> Optional[Geofence]:
        """Get geofence by ID"""
        return self._geofences.get(geofence_id)
    
    def list_geofences(self, fence_type: str = None, enabled_only: bool = True) -> List[Geofence]:
        """List all geofences with optional filters"""
        with self._geofences_lock:
            fences = list(self._geofences.values())
        
        if enabled_only:
            fences = [f for f in fences if f.enabled]
        
        if fence_type:
            fences = [f for f in fences if f.type == fence_type]
        
        return fences
    
    # ═══════════════════════════════════════════════════════════════
    # STRAPI SYNC
    # ═══════════════════════════════════════════════════════════════
    
    def refresh_from_strapi(self, entity_type: str = "all") -> None:
        """Load/refresh data from Strapi"""
        if not self.strapi:
            logger.warning("No Strapi client configured")
            return
        
        if entity_type in ["all", "geofences"]:
            geofences_data = self.strapi.get_collection("geofences", filters={"enabled": True})
            self._sync_geofences(geofences_data)
        
        if entity_type in ["all", "stops"]:
            stops_data = self.strapi.get_collection("route-stops")
            self._sync_stops(stops_data)
        
        # TODO: POIs, places, triggers
    
    def _sync_geofences(self, geofences_data: List[dict]) -> None:
        """Sync geofences from Strapi data"""
        with self._geofences_lock:
            self._geofences.clear()
            for data in geofences_data:
                geofence = Geofence.from_strapi(data)
                self._geofences[geofence.id] = geofence
        
        logger.info(f"Synced {len(self._geofences)} geofences from Strapi")
    
    # ═══════════════════════════════════════════════════════════════
    # TRIGGER SYSTEM (Future)
    # ═══════════════════════════════════════════════════════════════
    
    def register_trigger(self, trigger: LocationTrigger) -> None:
        """Register location-based trigger"""
        with self._triggers_lock:
            self._triggers[trigger.id] = trigger
    
    def evaluate_triggers(self, context: LocationContext) -> List[TriggerEvent]:
        """Evaluate all triggers for given location context"""
        # TODO: Implement trigger evaluation
        pass
```

---

## Strapi Schema

### Geofences Content Type (MVP + Phase 2)

**File**: `strapi/src/api/geofence/content-types/geofence/schema.json`

```json
{
  "kind": "collectionType",
  "collectionName": "geofences",
  "info": {
    "singularName": "geofence",
    "pluralName": "geofences",
    "displayName": "Geofence",
    "description": "Location-based geofences (circles and polygons)"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "name": {
      "type": "string",
      "required": true,
      "unique": false
    },
    "type": {
      "type": "enumeration",
      "enum": ["depot", "boarding_zone", "service_area", "restricted", "proximity", "custom"],
      "required": true,
      "default": "custom"
    },
    "geometry_type": {
      "type": "enumeration",
      "enum": ["circle", "polygon"],
      "required": true,
      "default": "circle"
    },
    "center_lat": {
      "type": "decimal",
      "required": false,
      "description": "Circle center latitude (required if geometry_type=circle)"
    },
    "center_lon": {
      "type": "decimal",
      "required": false,
      "description": "Circle center longitude (required if geometry_type=circle)"
    },
    "radius_meters": {
      "type": "decimal",
      "required": false,
      "min": 1,
      "description": "Circle radius in meters (required if geometry_type=circle)"
    },
    "polygon": {
      "type": "json",
      "required": false,
      "description": "GeoJSON polygon coordinates [[lon,lat],...] (required if geometry_type=polygon)"
    },
    "bbox": {
      "type": "json",
      "required": false,
      "description": "Bounding box [min_lon, min_lat, max_lon, max_lat] (auto-computed)"
    },
    "enabled": {
      "type": "boolean",
      "default": true,
      "required": true
    },
    "metadata": {
      "type": "json",
      "description": "Custom metadata (tags, priority, color, etc.)"
    },
    "routes": {
      "type": "relation",
      "relation": "manyToMany",
      "target": "api::route.route",
      "inversedBy": "geofences"
    },
    "depots": {
      "type": "relation",
      "relation": "manyToMany",
      "target": "api::depot.depot",
      "inversedBy": "geofences"
    }
  }
}
```

**Lifecycle Hooks** (auto-compute bbox):

**File**: `strapi/src/api/geofence/content-types/geofence/lifecycles.js`

```javascript
module.exports = {
  async beforeCreate(event) {
    const { data } = event.params;
    
    // Auto-compute bbox based on geometry type
    if (data.geometry_type === 'circle' && data.center_lat && data.center_lon && data.radius_meters) {
      data.bbox = computeCircleBbox(data.center_lat, data.center_lon, data.radius_meters);
    } else if (data.geometry_type === 'polygon' && data.polygon) {
      data.bbox = computePolygonBbox(data.polygon);
    }
  },
  
  async beforeUpdate(event) {
    const { data } = event.params;
    
    // Recompute bbox if geometry changed
    if (data.geometry_type === 'circle' && data.center_lat && data.center_lon && data.radius_meters) {
      data.bbox = computeCircleBbox(data.center_lat, data.center_lon, data.radius_meters);
    } else if (data.geometry_type === 'polygon' && data.polygon) {
      data.bbox = computePolygonBbox(data.polygon);
    }
  }
};

function computeCircleBbox(lat, lon, radiusMeters) {
  const latDelta = radiusMeters / 111000;
  const lonDelta = radiusMeters / (111000 * Math.abs(Math.cos(lat * Math.PI / 180)));
  
  return [
    lon - lonDelta,  // min_lon
    lat - latDelta,  // min_lat
    lon + lonDelta,  // max_lon
    lat + latDelta   // max_lat
  ];
}

function computePolygonBbox(polygon) {
  const lons = polygon.map(coord => coord[0]);
  const lats = polygon.map(coord => coord[1]);
  
  return [
    Math.min(...lons),
    Math.min(...lats),
    Math.max(...lons),
    Math.max(...lats)
  ];
}
```

---

## UI Strategy

### MVP: Simple Circle Form (Strapi Admin)

**Phase 1 UI**: Built-in Strapi admin panel, 3 input fields

```
Geofences → Create New Entry
┌───────────────────────────────────────┐
│ Name*: Depot North                    │
│                                       │
│ Type*: [depot ▼]                      │
│                                       │
│ Geometry Type*: [● circle  ○ polygon] │
│                                       │
│ ╔════ Circle Geometry ════╗          │
│ ║ Center Latitude*:        ║          │
│ ║ -37.8136                 ║          │
│ ║                          ║          │
│ ║ Center Longitude*:       ║          │
│ ║ 145.0123                 ║          │
│ ║                          ║          │
│ ║ Radius (meters)*:        ║          │
│ ║ 80                       ║          │
│ ╚══════════════════════════╝          │
│                                       │
│ Enabled: [✓]                          │
│                                       │
│ Metadata (JSON):                      │
│ {"capacity": 5, "priority": 10}       │
│                                       │
│ Routes: [Select routes...]            │
│ Depots: [Select depots...]            │
│                                       │
│ [Save] [Cancel]                       │
└───────────────────────────────────────┘
```

**How users define circle geofences:**

1. Find lat/lon from Google Maps:
   - Right-click location → "What's here?"
   - Copy coordinates (-37.8136, 145.0123)

2. Estimate radius:
   - Use Google Maps measure tool
   - Or rough guess (small depot = 50m, large depot = 100m)

3. Paste into Strapi form → Save

**Time to create**: 30 seconds per geofence

---

### Phase 2: Map-Based Drawing Tool

**Option A: Strapi Plugin** (strapi-plugin-mapbox or custom)

```
Geofences → Create New Entry
┌───────────────────────────────────────┐
│ Name*: Depot North - Precise          │
│                                       │
│ Type*: [depot ▼]                      │
│                                       │
│ Geometry Type*: [○ circle  ● polygon] │
│                                       │
│ ╔════ Polygon Geometry (Map) ════╗   │
│ ║                                 ║   │
│ ║ ┌─────────────────────────────┐ ║   │
│ ║ │ 🗺️ Interactive Map          │ ║   │
│ ║ │                             │ ║   │
│ ║ │  [Draw Polygon] [Import]    │ ║   │
│ ║ │                             │ ║   │
│ ║ │        ╔═══╗                │ ║   │
│ ║ │        ║   ║ ← Depot        │ ║   │
│ ║ │        ╚═══╝                │ ║   │
│ ║ │                             │ ║   │
│ ║ │  Click to add vertices      │ ║   │
│ ║ │  Double-click to finish     │ ║   │
│ ║ └─────────────────────────────┘ ║   │
│ ║                                 ║   │
│ ║ Coordinates (auto-generated):   ║   │
│ ║ [[145.0123, -37.8136],          ║   │
│ ║  [145.0128, -37.8136],          ║   │
│ ║  [145.0128, -37.8132],          ║   │
│ ║  [145.0123, -37.8132],          ║   │
│ ║  [145.0123, -37.8136]]          ║   │
│ ╚═════════════════════════════════╝   │
│                                       │
│ [Save] [Cancel]                       │
└───────────────────────────────────────┘
```

**Option B: External Tool + Import**

1. Draw polygon in Google Earth / QGIS / Mapbox Studio
2. Export as GeoJSON
3. Paste into Strapi "polygon" field (JSON)

**Option C: Custom Frontend Dashboard**

Build separate admin UI with:
- Map view (Leaflet / Mapbox)
- Drawing tools
- Geofence list
- Real-time preview

---

## Event Flow (Complete Example)

### Scenario: Vehicle enters depot → Conductor triggers driver stop

```
┌──────────┐    ┌────────────┐    ┌───────────┐    ┌──────────┐
│ GPSDevice│    │ LocationSvc│    │ Conductor │    │  Driver  │
└──────────┘    └────────────┘    └───────────┘    └──────────┘
      │                │                 │                │
      │ GPS: (-37.813, │                 │                │
      │  145.012)      │                 │                │
      ├───────────────>│                 │                │
      │                │                 │                │
      │                │ check geofences │                │
      │                │ → depot_north   │                │
      │                │   (circle, r=80)│                │
      │                │ distance = 15m  │                │
      │                │ INSIDE!         │                │
      │                │                 │                │
      │ context:       │                 │                │
      │ {geofences:    │                 │                │
      │  ["depot_north"]│                │                │
      │  events: [      │                │                │
      │   {type:entered}│                │                │
      │  ]}            │                 │                │
      │<───────────────┤                 │                │
      │                │                 │                │
      │ emit: geofence:│                 │                │
      │  event         │                 │                │
      ├────────────────┼────────────────>│                │
      │                │                 │                │
      │                │                 │ check: 10m from│
      │                │                 │  depot center? │
      │                │                 │                │
      │                │                 │ emit: driver:  │
      │                │                 │  stop_command  │
      │                │                 ├───────────────>│
      │                │                 │                │
      │                │                 │                │ STOP
```

**Code:**

```python
# GPSDevice
sample = gps_plugin.get_position()  # (-37.813, 145.012)

context = location_service.get_location_context(
    sample,
    entity_id=vehicle_id,
    detect_transitions=True
)

# context.geofences = {"depot_north"}
# context.geofence_events = [GeofenceEvent(type="entered", fence_id="depot_north", ...)]

for event in context.geofence_events:
    sio.emit("geofence:event", {
        "vehicle_id": vehicle_id,
        "type": event.type,
        "fence_id": event.fence_id,
        "fence_name": event.fence_name
    })
```

```python
# Conductor
@sio.on("geofence:event")
def on_geofence_event(data):
    if data["type"] == "entered" and data["fence_id"] == "depot_north":
        # Monitor for precise stop position
        conductor.in_depot = True

@sio.on("vehicle:location")
def on_vehicle_location(data):
    if conductor.in_depot:
        # Check distance to depot center
        depot_center = get_depot_center("depot_north")
        distance = haversine_distance(data["position"], depot_center)
        
        if distance <= 10.0:  # 10m from center
            sio.emit("driver:stop_command", {
                "reason": "depot_parking_position"
            })
            conductor.in_depot = False
```

---

## Performance

### Circle Geofence Check

```python
# 1. Bbox check (fast)
if not bbox.contains(point):  # ~5 CPU ops
    return False

# 2. Haversine distance
distance = haversine(center, point)  # ~20 CPU ops
return distance <= radius
```

**Time**: ~0.5 microseconds

### Polygon Geofence Check

```python
# 1. Bbox check (fast)
if not bbox.contains(point):  # ~5 CPU ops
    return False

# 2. Ray casting point-in-polygon
return point_in_polygon(point, polygon)  # ~10-50 CPU ops
```

**Time**: ~1-5 microseconds (depends on vertex count)

### Scale Test (1,200 vehicles × 100 geofences)

**Naive approach** (no optimization):
- 120,000 containment checks per position update
- Circle: 60 ms
- Polygon: 600 ms

**With bbox optimization**:
- Bbox rejects 90% of checks
- Circle: 6 ms
- Polygon: 60 ms

**With spatial index (R-tree)**:
- Only check nearby geofences
- 12 ms (both circle and polygon)

**Conclusion**: Performance is acceptable with bbox optimization; spatial index optional.

---

## Implementation Roadmap

### Week 1: MVP — Circle Geofences

**Day 1-2: Core LocationService**
- [x] Design complete ✅ (this document)
- [ ] Implement `Geofence` class (circle support only)
- [ ] Implement `LocationContext` model
- [ ] Implement `LocationService.get_location_context()`
- [ ] Implement `LocationService._get_containing_geofences()`
- [ ] Implement `LocationService._detect_transitions()`
- [ ] Unit tests (geofence containment, transitions)

**Day 3: Strapi Integration**
- [ ] Create Strapi `geofence` content type
- [ ] Add lifecycle hooks (auto-compute bbox)
- [ ] Test CRUD via Strapi admin panel
- [ ] Create sample circle geofences (3-5 depots)

**Day 4: GPS Device Integration**
- [ ] Modify `GPSDevice._data_worker()` to call LocationService
- [ ] Emit `geofence:event` via Socket.IO
- [ ] Test with simulated GPS movement
- [ ] Verify enter/exit events fire correctly

**Day 5: Example & Documentation**
- [ ] Create `examples/location_service_demo.py`
- [ ] Document API usage
- [ ] Create quick start guide
- [ ] Update `TODO.md` with Phase 2 plan

### Week 2: Nearest Entity Queries

**Day 1-2: Spatial Indexing**
- [ ] Implement KDTree wrapper (scipy.spatial)
- [ ] Implement `LocationService._sync_stops()` with index build
- [ ] Implement `LocationService.get_nearest_stop()`
- [ ] Unit tests (nearest queries, accuracy)

**Day 3: Complete LocationContext**
- [ ] Add `nearest_poi`, `nearest_place` queries
- [ ] Add `nearby_*` queries (within radius)
- [ ] Integrate with existing stop/POI data from Strapi
- [ ] Test with realistic data (1000+ stops)

**Day 4-5: Conductor/Passenger Integration**
- [ ] Update `Conductor` to use LocationService
- [ ] Update `Passenger` to query LocationService
- [ ] Test complete flow: passenger → conductor → driver
- [ ] Performance testing (1,200 vehicles)

### Week 3-4: Phase 2 — Polygon Support

**Day 1-2: Polygon Geometry**
- [ ] Add polygon support to `Geofence` class
- [ ] Implement point-in-polygon (ray casting)
- [ ] Add polygon validation (closed ring, self-intersection check)
- [ ] Unit tests (complex polygons, holes, edge cases)

**Day 3: Strapi UI Enhancement**
- [ ] Research Strapi map plugins (strapi-plugin-mapbox)
- [ ] Install/configure map plugin
- [ ] Test polygon drawing in admin panel
- [ ] Create sample polygon geofences

**Day 4: Migration & Testing**
- [ ] Convert existing circle geofences to polygons (where appropriate)
- [ ] Test hybrid (some circles, some polygons)
- [ ] Performance comparison (circle vs polygon)
- [ ] Update documentation

**Day 5: Triggers (Phase 2.5)**
- [ ] Implement trigger evaluation system
- [ ] Add GPIO/callback action executors
- [ ] Create example triggers (depot entry, stop proximity)
- [ ] Test end-to-end trigger flows

---

## Examples

### Example 1: Create Circle Geofence (MVP)

**Via Strapi REST API:**

```bash
curl -X POST http://localhost:1337/api/geofences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "data": {
      "name": "Depot North - Boarding",
      "type": "boarding_zone",
      "geometry_type": "circle",
      "center_lat": -37.8136,
      "center_lon": 145.0123,
      "radius_meters": 80,
      "enabled": true,
      "metadata": {
        "capacity": 5,
        "priority": 10
      }
    }
  }'
```

**Response:**

```json
{
  "data": {
    "id": 1,
    "attributes": {
      "name": "Depot North - Boarding",
      "type": "boarding_zone",
      "geometry_type": "circle",
      "center_lat": -37.8136,
      "center_lon": 145.0123,
      "radius_meters": 80,
      "bbox": [145.01158, -37.81432, 145.01302, -37.81288],
      "enabled": true,
      "metadata": {
        "capacity": 5,
        "priority": 10
      },
      "createdAt": "2025-10-10T12:00:00.000Z",
      "updatedAt": "2025-10-10T12:00:00.000Z"
    }
  }
}
```

### Example 2: Query Location Context

```python
from arknet_transit_simulator.geospatial import LocationService, Point

# Initialize
location_service = LocationService(strapi_client=strapi)
location_service.refresh_from_strapi()

# Query position
position = Point(lat=-37.8136, lon=145.0123)
context = location_service.get_location_context(
    position,
    entity_id="vehicle_001",
    detect_transitions=True
)

# Result
print(f"Geofences: {context.geofences}")
# Geofences: {'depot_north'}

print(f"Events: {context.geofence_events}")
# Events: [GeofenceEvent(type='entered', fence_id='depot_north', ...)]

print(f"Nearest stop: {context.nearest_stop.name} ({context.nearest_stop.distance_meters}m)")
# Nearest stop: Main St (45m)
```

### Example 3: Create Polygon Geofence (Phase 2)

**Via Strapi REST API:**

```bash
curl -X POST http://localhost:1337/api/geofences \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "Depot North - Precise Boundary",
      "type": "depot",
      "geometry_type": "polygon",
      "polygon": [
        [145.01230, -37.81360],
        [145.01280, -37.81360],
        [145.01280, -37.81320],
        [145.01230, -37.81320],
        [145.01230, -37.81360]
      ],
      "enabled": true
    }
  }'
```

### Example 4: Real-time Geofence Update

```python
# Admin adds emergency restricted zone
emergency_fence = Geofence(
    id="emergency_001",
    name="Emergency - Road Closure",
    type="restricted",
    geometry_type=GeometryType.CIRCLE,
    center=Point(lat=-37.8200, lon=145.0200),
    radius_meters=200,
    enabled=True,
    metadata={"reason": "accident", "expires": "2025-10-10T18:00:00Z"}
)

# Add to LocationService (immediate effect)
location_service.add_geofence(emergency_fence)

# All vehicles now detect this geofence
# Triggers can fire alerts, re-routing, etc.
```

---

## Summary

### Architecture Decisions ✅

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Geometry support** | Both circles AND polygons | MVP simplicity + future precision |
| **MVP geometry** | Circles (lat/lon/radius) | 3-field UI, fast prototyping |
| **Phase 2 geometry** | Polygons (GeoJSON) | Precise boundaries, industry standard |
| **Data model** | Unified `Geofence` class | Single API, zero refactoring |
| **Storage** | Strapi (persistent) + LocationService (cache) | Real-time updates, single source of truth |
| **Performance** | Bbox pre-filter + optional spatial index | Fast enough for 1,200 vehicles |
| **UI MVP** | Simple Strapi form (3 fields) | No custom tools needed |
| **UI Phase 2** | Map-based drawing tool (plugin or external) | Visual polygon creation |

### Key Benefits

1. **Progressive enhancement**: Start simple (circles), refine later (polygons), no rework
2. **Single API**: `location_service.get_location_context()` works for both geometries
3. **Real-time**: Add/remove/update geofences without restart
4. **Strapi-backed**: Admin UI, versioning, relations, webhooks
5. **Thread-safe**: Concurrent queries from multiple GPS devices
6. **Event-driven**: Geofence transitions trigger actions automatically

### Next Action

Choose implementation start:

1. **Start MVP now** → Create `arknet_transit_simulator/geospatial/` skeleton + circle support
2. **Strapi first** → Create content type, test CRUD, then build LocationService
3. **Review & refine** → Discuss any architecture concerns before coding

Your call — ready to implement?
