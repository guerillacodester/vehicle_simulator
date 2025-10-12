# Spawn System Debugging Session - 2025-10-12

## Problem Summary
Real-time passenger spawning system was generating 40-50 spawn requests every 30 seconds but **100% of spawns were failing** with type errors. Monitor tool was ready and waiting to display beautiful real-time spawn events with location names, but showing 0 spawns due to these errors.

## Root Causes Identified

### 1. Depot Spawning Error (100% failure rate)
**Error Message:**
```
TypeError: unsupported operand type(s) for -: 'float' and 'str'
at depot_reservoir.py:663: dlat = radians(lat2 - lat1)
```

**Root Cause:**
- Poisson spawner returns `spawn_location` as tuple with **STRING coordinates**: `('13.0982', '-59.6216')`
- Should be floats: `(13.0982, -59.6216)`
- When unpacked in `_find_nearest_depot()`, lat1/lon1 are strings
- Haversine calculation `lat2 - lat1` fails (float minus string)

**Attempted Fix (INCOMPLETE):**
- Added type conversion in `_find_nearest_depot()` for depot coordinates (lat2, lon2)
- **Missed** converting spawn_location coordinates (lat1, lon1)
- **SOLUTION NEEDED**: Convert spawn_location coords to float before Haversine calc

### 2. Route Spawning Error (100% failure rate)
**Error Message:**
```
KeyError: 0
at route_reservoir.py:456: current_location[0]
```

**Root Cause:**
- Poisson spawner returns `spawn_location` as **DICT**: `{'lat': 13.0982, 'lon': -59.6216}`
- Should be tuple: `(13.0982, -59.6216)`
- Code expects tuple indexing `location[0]` for latitude
- Dict doesn't support integer indexing → KeyError

**SOLUTION NEEDED**: Convert spawn_location dict to tuple `(lat, lon)`

## Stack Traces

### Depot Reservoir Error
```python
Traceback (most recent call last):
  File "depot_reservoir.py", line 609, in _spawning_loop
    nearest_depot = self._find_nearest_depot(spawn_location)
  File "depot_reservoir.py", line 663, in _find_nearest_depot
    dlat = radians(lat2 - lat1)
                   ~~~~~^~~~~~
TypeError: unsupported operand type(s) for -: 'float' and 'str'
```

### Route Reservoir Error
```python
Traceback (most recent call last):
  File "route_reservoir.py", line 725, in _spawning_loop
    await self.spawn_commuter(...)
  File "route_reservoir.py", line 456, in spawn_commuter
    current_location[0],
    ~~~~~~~~~~~~~~~~^^^
KeyError: 0
```

## Spawn Request Structure (ACTUAL from Poisson Spawner)

**Expected:**
```python
{
    'spawn_location': (13.0982, -59.6216),  # (lat, lon) tuple of floats
    'destination_location': (13.1234, -59.5678),
    'assigned_route': '1A',
    'priority': 3,
    ...
}
```

**ACTUAL (causing errors):**
```python
{
    'spawn_location': ('13.0982', '-59.6216'),  # Strings OR dict!
    'destination_location': ('13.1234', '-59.5678'),
    'assigned_route': '1A',
    'priority': 3,
    ...
}
```

Or possibly:
```python
{
    'spawn_location': {'lat': 13.0982, 'lon': -59.6216},  # Dict!
    'destination_location': {'lat': 13.1234, 'lon': -59.5678},
    ...
}
```

## Fixes Needed

### Priority 1: Fix Coordinate Format Conversion

**Option A: Fix at Source (Poisson Spawner)**
- Ensure Poisson spawner always returns `(float, float)` tuples
- Most robust solution

**Option B: Fix at Destination (Reservoirs)**
- Add normalization function in each reservoir:
```python
def _normalize_location(self, location):
    """Convert location to (lat, lon) tuple of floats"""
    if isinstance(location, dict):
        return (float(location['lat']), float(location['lon']))
    elif isinstance(location, (tuple, list)):
        return (float(location[0]), float(location[1]))
    else:
        raise ValueError(f"Unexpected location format: {location}")
```

### Priority 2: Complete Depot Haversine Fix

Current code (depot_reservoir.py:640-665):
```python
for depot in self.depots:
    depot_lat = depot.latitude or (depot.location.get('lat') if depot.location else None)
    depot_lon = depot.longitude or (depot.location.get('lon') if depot.location else None)
    
    if not depot_lat or not depot_lon:
        continue
    
    # ✅ Fixed: Ensure depot coordinates are floats
    lat2 = float(depot_lat) if isinstance(depot_lat, str) else depot_lat
    lon2 = float(depot_lon) if isinstance(depot_lon, str) else depot_lon
    
    # ❌ MISSING: lat1, lon1 from location parameter still strings!
    # Haversine distance
    R = 6371000  # Earth radius in meters
    dlat = radians(lat2 - lat1)  # FAILS if lat1 is string!
```

**Fix:**
```python
def _find_nearest_depot(self, location):
    """Find nearest depot to location"""
    from math import radians, sin, cos, sqrt, atan2
    
    if not self.depots:
        return None
    
    # ✅ NORMALIZE location to (float, float)
    lat1, lon1 = self._normalize_location(location)
    
    min_distance = float('inf')
    nearest_depot = None
    
    for depot in self.depots:
        depot_lat = depot.latitude or (depot.location.get('lat') if depot.location else None)
        depot_lon = depot.longitude or (depot.location.get('lon') if depot.location else None)
        
        if not depot_lat or not depot_lon:
            continue
        
        lat2 = float(depot_lat) if isinstance(depot_lat, str) else depot_lat
        lon2 = float(depot_lon) if isinstance(depot_lon, str) else depot_lon
        
        # Haversine distance
        R = 6371000
        dlat = radians(lat2 - lat1)  # Now works! Both floats
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        if distance < min_distance:
            min_distance = distance
            nearest_depot = depot
    
    return nearest_depot
```

## Test Data

**50 depot spawn requests generated at 15:10:00**
- All failed with type error
- Error location: `depot_reservoir.py:663` (Haversine calculation)

**48 route spawn requests generated at 15:10:01**
- All failed with KeyError: 0
- Error location: `route_reservoir.py:456` (tuple indexing)

## Statistics
- **Service Status**: Running
- **Depots Loaded**: 5 (Barbados)
- **Routes Loaded**: 1 (Route 1A, 88 GPS points)
- **Amenity Zones**: 100 (schools, restaurants, clinics, etc.)
- **Spawn Interval**: 30 seconds
- **Spawn Rate**: 40-50 requests per cycle
- **Success Rate**: 0% (100% failure)
- **Monitor Tool**: Running, showing 0 spawns (waiting for fixes)

## Real-Time Monitor Ready
The `monitor_realtime_spawns.py` tool is fully operational and waiting to display:
- ✅ Socket.IO connections established
- ✅ API data loaded (5 depots, 1 route, 1 vehicle)
- ✅ Color-coded output (yellow depot, green route spawns)
- ✅ 60-second statistics display
- ❌ Showing 0 spawns (blocked by spawn errors)

## Location Name Enhancement (Implemented but Untested)
- Added `_get_location_name()` method to both reservoirs
- Uses Haversine distance to find nearest amenity within 100m
- Returns formatted names like "Restaurant (poi 45)" or "School (poi 123)"
- Enhanced spawn logging to show location names
- **Status**: Code ready, but can't test until spawning works

## Next Steps
1. **Immediate**: Add `_normalize_location()` method to both reservoirs
2. **Test**: Restart service and verify spawns succeed
3. **Verify**: Check monitor tool displays real-time spawn events
4. **Validate**: Confirm location names appear in spawn logs
5. **Celebrate**: Watch beautiful real-time spawn display with actual POI names!

## Files Modified
- ✅ `monitor_realtime_spawns.py` (created)
- ✅ `depot_reservoir.py` (partial fix, needs location normalization)
- ✅ `route_reservoir.py` (needs location normalization)
- 🔄 `poisson_geojson_spawner.py` (may need to fix at source)

## Debug Tools Used
- `exc_info=True` in error logging → Full stack traces
- Socket.IO event monitoring → Verified connections
- Terminal output analysis → Identified exact error lines
- Type inspection → Discovered string vs float issue

## Lesson Learned
**Type Safety is Critical!**
- Always validate data types at API boundaries
- GPS coordinates from APIs may be strings, not floats
- Dict vs tuple format can cause subtle KeyError bugs
- Normalization functions prevent type mismatches
- Debug logging with stack traces is essential

---
**Session End**: 2025-10-12 15:10:08
**Status**: Root causes identified, fixes designed, ready to implement
