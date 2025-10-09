# 🐛 Bug Fix: Duplicate ID Conflict

## Issue: Route Spawns Always Showing 0

### Root Cause
**Duplicate HTML element ID:** `routeCount` was used in TWO places:
1. **Line 421:** Route dropdown button - displays number of available routes
2. **Line 450:** Stats panel - displays number of route spawn passengers

When `updateStats()` called `document.getElementById('routeCount')`, it updated the FIRST element (the dropdown), not the stats panel.

### The Fix
Changed the route dropdown to use a unique ID:

**Before:**
```html
<button class="route-dropdown-btn" id="routeDropdownBtn">
    🚌 Routes <span id="routeCount">0</span> ▼
</button>
```

**After:**
```html
<button class="route-dropdown-btn" id="routeDropdownBtn">
    🚌 Routes <span id="routeListCount">0</span> ▼
</button>
```

### Why This Happened
The route dropdown and stats panel were developed separately and both used "routeCount" as an ID. HTML IDs must be unique within a page, or `getElementById()` returns only the first match.

### Console Evidence
The logs showed everything working correctly:
```
✅ Production spawner returned 1467 spawn requests
🔍 Spawn type distribution from API: {depot: 23, route: 25, poi: 1419}
📊 Final counts after processing: {depot: 23, route: 25, poi: 1419}
📍 Layer marker counts: {depot: 23, route: 25, poi: 1419}
📊 updateStats called with: {counts: {depot: 23, route: 25, poi: 1419}, hour: 8}
   - route: 25 type: number
```

But the display showed 0 because it was updating the wrong element!

### Files Modified
- `passenger-spawning-visualization.html` - Line 421: Changed `id="routeCount"` to `id="routeListCount"`

### Testing Instructions
1. **Hard refresh** the browser page: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
2. **Verify initial load (Hour 8):**
   - Depot Spawns: 23 ✅
   - Route Spawns: 25 ✅ (was showing 0)
   - POI Spawns: 1419 ✅
   - Total: 1467 ✅

3. **Move time slider** and verify counts update:
   - Hour 9: Depot=13, Route=14, POI=0
   - Hour 10: Depot=5, Route=6, POI=0
   - Hour 17 (peak): Higher counts expected

4. **Verify route dropdown** still works:
   - Should show "🚌 Routes 6 ▼" (number of available routes)
   - Not affected by spawn counts

### Status: ✅ FIXED
The visualization should now correctly display all spawn types across all hours!
