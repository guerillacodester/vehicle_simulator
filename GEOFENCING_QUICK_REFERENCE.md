# 🗺️ GEOFENCING QUICK REFERENCE

**Status**: 🎨 Design Phase  
**Last Updated**: October 10, 2025

---

## ⚡ **Quick Summary**

**Goal**: Add polygon geofencing to GPS device for location awareness

**Key Decisions**:
- ✅ Irregular polygon shapes (not just circles)
- ✅ GeoJSON standard format
- ✅ Geofence logic at GPS device level
- ✅ Works with any GPS plugin (sim/hardware/replay)

---

## 📋 **7 Questions to Answer Before Coding**

1. **How many fences per depot?** (2-5? 10-20? 50+?)
2. **How many vertices per polygon?** (4-6? 10-20? 50+?)
3. **How will fences be created?** (Manual entry? GIS import? Map drawing?)
4. **Can fences change at runtime?** (Static? Dynamic? Event-driven?)
5. **How to handle invalid polygons?** (Reject? Warn? Auto-fix?)
6. **If in multiple fences, which wins?** (Priority? Smallest? All?)
7. **Fence-depot relationship?** (Tight? Loose? Independent?)

---

## 🎯 **What's Next**

1. Answer 7 questions above
2. Review architecture in `GEOFENCING_DESIGN_CONTEXT.md`
3. Approve design
4. Implement Phase 1 MVP (~3-4 hours)

---

## 📁 **Key Files**

**Design Docs**:
- `GEOFENCING_DESIGN_CONTEXT.md` ⭐ **Full architecture design**
- `GEOFENCING_QUICK_REFERENCE.md` (this file)

**Implementation Targets**:
- `arknet_transit_simulator/vehicle/gps_device/geofence_engine.py` (create new)
- `arknet_transit_simulator/vehicle/gps_device/device.py` (modify)
- Strapi: Create `geofence` content type

---

## 🏗️ **Architecture At-a-Glance**

```
GPS Device
  └─ Geofence Engine
      ├─ Load from Strapi (by route)
      ├─ Check position (point-in-polygon)
      ├─ Detect events (entered/exited)
      └─ Emit via Socket.IO

Conductor/Driver
  └─ Listen to geofence events
      └─ React to location context
```

---

## 💡 **Core Principle**

**GPS device knows where it is, not just lat/lon coordinates.**

Instead of:
```python
lat, lon = gps.get_position()  # Just numbers
```

We get:
```python
position = gps.get_position()
# position.lat, position.lon
# position.inside_fences = ["depot_north_boarding", "zone_downtown"]
# position.events = [GeofenceEvent(type="entered", fence="depot_north")]
```

---

**📖 Read Full Design**: `GEOFENCING_DESIGN_CONTEXT.md`
