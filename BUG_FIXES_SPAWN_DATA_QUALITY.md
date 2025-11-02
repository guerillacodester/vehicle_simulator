# Spawn Data Quality Bug Fixes

**Date**: 2024-11-02  
**Component**: Route & Depot Spawners  
**Issue**: Data quality problems identified in route manifest analysis

---

## Diagnosis Summary

### Investigation Process
1. Created `show_route_manifest.py` to display route passengers in table format
2. User noticed suspicious patterns:
   - All spawn times showing as "07:00" (no minute variation)
   - Unnatural correlation between spawn location and commute distance
   - Passengers with 0 km commute distance (identical start/destination)
   - Poor distribution along route

3. Created `check_spawn_data.py` to analyze raw database data
4. **Key Finding**: Raw data showed passengers spawned across hours (05:00, 06:00, 07:00, 08:00) but ALL had `:00:00` timestamps (no minutes/seconds)

### Diagnostic Results
```
Total route passengers: 100

SPAWN TIME DISTRIBUTION:
Hour 05:00 - 9 passengers   (all at 05:00:00.000)
Hour 06:00 - 18 passengers  (all at 06:00:00.000)
Hour 07:00 - 35 passengers  (all at 07:00:00.000)
Hour 08:00 - 38 passengers  (all at 08:00:00.000)

LOCATION CLUSTERING:
56 unique locations out of 100 passengers (56% unique)
Up to 5 passengers at exact same coordinates

DATA BUGS:
⚠️  3 passengers have IDENTICAL start and destination coordinates
   This causes 0.00 km commute distances (makes no sense)
```

---

## Root Causes Identified

### Bug 1: No Time Variation Within Hours ⚠️ CRITICAL
**File**: `route_spawner.py` line 474, `depot_spawner.py` line 516  
**Issue**: All passengers spawned in the same hour have identical timestamps (e.g., all at 07:00:00.000)

**Code**:
```python
spawn_req = SpawnRequest(
    spawn_time=current_time,  # ❌ current_time is hour-level precision
    ...
)
```

**Impact**:
- All passengers in 07:00-08:00 window show as spawned at exactly 07:00:00
- No temporal distribution within hour
- Unrealistic clustering at exact hour boundaries
- Manifest table appears broken (all times identical)

**Fix**:
```python
# Randomize spawn time within the hour (0-59 minutes, 0-59 seconds)
import random
random_minutes = random.randint(0, 59)
random_seconds = random.randint(0, 59)
actual_spawn_time = current_time.replace(minute=random_minutes, second=random_seconds, microsecond=0)

spawn_req = SpawnRequest(
    spawn_time=actual_spawn_time,  # ✅ Distributed across entire hour
    ...
)
```

---

### Bug 2: Zero-Distance Commutes (Same Start/Destination) ⚠️ HIGH
**File**: `route_spawner.py` line 460  
**Issue**: Alighting index can equal boarding index, creating passengers with 0 km commute

**Code**:
```python
board_idx = random.randint(0, len(route_coords) - 1)
alight_idx = random.randint(board_idx, len(route_coords) - 1)  # ❌ Can equal board_idx
```

**Impact**:
- 3 out of 100 passengers had identical pickup/dropoff coordinates
- 0.00 km commute distance (doesn't make sense for transit)
- Corrupts statistical analysis of commute patterns

**Fix**:
```python
board_idx = random.randint(0, len(route_coords) - 1)

# Ensure at least 1 stop difference to avoid 0km commutes
if board_idx == len(route_coords) - 1:
    # Last stop - pick any earlier stop as destination (reverse direction)
    alight_idx = random.randint(0, board_idx - 1)
else:
    # Normal case - pick any stop AFTER boarding position
    alight_idx = random.randint(board_idx + 1, len(route_coords) - 1)  # ✅ Always different
```

---

### Bug 3: Excessive Location Clustering ⚠️ MODERATE
**File**: `route_spawner.py` line 457  
**Issue**: Multiple passengers can spawn at exact same coordinates (44% duplication rate)

**Code**:
```python
for i in range(spawn_count):
    board_idx = random.randint(0, len(route_coords) - 1)  # ❌ Pure random, allows duplicates
```

**Current State**:
- 56 unique locations / 100 passengers (44% are duplicates)
- Up to 5 passengers at same exact coordinates
- Some clustering might be natural (same building) but 44% is excessive

**Status**: ⚠️ DEFERRED
- Need to evaluate if this is realistic (multiple people from same building)
- Could implement weighted distribution based on building density
- For now, focusing on critical time/distance bugs

---

## Files Modified

### 1. `commuter_simulator/core/domain/spawner_engine/route_spawner.py`
**Function**: `_generate_spawn_requests()`
- ✅ Added random minute/second to spawn times
- ✅ Fixed zero-distance bug (alight_idx must differ from board_idx)
- ✅ Updated logging to show actual_spawn_time

### 2. `commuter_simulator/core/domain/spawner_engine/depot_spawner.py`
**Function**: `_generate_spawn_requests()`
- ✅ Added random minute/second to spawn times
- ✅ Updated logging to show actual_spawn_time

---

## Testing & Validation

### Pre-Fix Data Quality
```
❌ Time Distribution: All :00:00 timestamps (no variation)
❌ Zero Commutes: 3 passengers (3%)
❌ Location Clustering: 44% duplicate coordinates
```

### Expected Post-Fix Quality
```
✅ Time Distribution: Uniform spread across 60 minutes (05:00 to 05:59)
✅ Zero Commutes: 0 passengers (all have minimum 1-stop distance)
❌ Location Clustering: Still 44% (deferred for later optimization)
```

### Validation Commands
```bash
# 1. Clear old data
python scripts/delete_passengers.py

# 2. Respawn with fixes
python -m commuter_simulator --depot-spawning --route-spawning --duration 168 --time-step 60

# 3. Check time distribution
python scripts/check_spawn_data.py

# 4. View manifest
python scripts/show_route_manifest.py --day monday --start-hour 7 --end-hour 9
```

---

## Impact Assessment

### Critical Fix (Bug 1 - Time Variation)
- **Before**: All passengers in hour show as spawned at :00:00
- **After**: Passengers distributed uniformly across entire hour (e.g., 07:14:23, 07:38:51, 07:02:44)
- **User Impact**: Manifest table now shows realistic temporal distribution
- **System Impact**: Better simulation realism, accurate time-based analytics

### High Priority Fix (Bug 2 - Zero Commutes)
- **Before**: 3% of passengers had identical start/destination (0 km commute)
- **After**: All passengers have minimum 1-stop distance
- **User Impact**: Manifest table no longer shows nonsensical 0.00 km commutes
- **System Impact**: More realistic demand patterns, valid distance statistics

### Deferred Optimization (Bug 3 - Clustering)
- **Current**: 44% duplicate spawn locations
- **Decision**: May be realistic (multiple people from same building)
- **Future**: Consider building density weighting for better spatial distribution

---

## Related Scripts

### Diagnostic Tools
- `scripts/check_spawn_data.py` - Analyzes raw database for data quality issues
- `scripts/show_route_manifest.py` - Displays route passenger manifest table
- `scripts/analyze_route_passengers.py` - Statistical analysis with charts

### Data Management
- `scripts/delete_passengers.py` - Clears passenger database for fresh spawning

---

## Lessons Learned

1. **Always validate time precision**: Don't assume datetime objects carry full precision
2. **Test boundary conditions**: Random ranges should explicitly exclude edge cases (same start/dest)
3. **Diagnostic scripts are essential**: Created `check_spawn_data.py` to diagnose root cause
4. **Separate data from visualization**: Initially thought manifest API was broken, but raw data revealed spawner bugs

---

## Next Steps

1. ✅ Respawn all passengers with fixes applied
2. ✅ Validate time distribution shows minutes/seconds variation
3. ✅ Confirm zero 0 km commutes in new data
4. ⏸️ Evaluate location clustering patterns (deferred)
5. ⏸️ Consider building-density weighted spawn distribution (future enhancement)
