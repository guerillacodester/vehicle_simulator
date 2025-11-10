# Route Visualization Implementation Plan - Production Grade

## Overview
Transform the Next.js dashboard navigation control into a production-ready route visualization system with:
- Route selection dropdown
- Real-time map visualization with animated polyline rendering
- Redis caching layer for performance
- Automatic viewport adjustment
- Production-grade error handling and loading states

---

## Phase 1: Data Layer & Caching (Priority: HIGH)

### 1.1 GraphQL Client Setup
**File**: `dashboard/src/lib/graphql/client.ts`
- [ ] Configure URQL client with caching
- [ ] Add retry logic and error handling
- [ ] Configure fetch policies (cache-first for routes)

### 1.2 Route Geometry Hook
**File**: `dashboard/src/lib/graphql/route-geometry-hook.ts`
- [ ] Create `useRouteGeometry(routeName)` hook
- [ ] Integrate with existing `route-geometry.ts` module
- [ ] Add loading, error, and success states
- [ ] Implement client-side cache (React Query or SWR)

### 1.3 Redis Caching Service
**File**: `dashboard/src/lib/redis/route-cache.ts`
- [ ] Create Redis client connection (ioredis)
- [ ] Implement `getRouteGeometry(routeName)` - check cache first
- [ ] Implement `setRouteGeometry(routeName, data)` - cache for 1 hour
- [ ] Add cache invalidation strategy
- [ ] Fallback to GraphQL if Redis unavailable

**File**: `dashboard/src/app/api/routes/[routeName]/geometry/route.ts`
- [ ] Create Next.js API route handler
- [ ] Check Redis cache first
- [ ] Query Strapi GraphQL if cache miss
- [ ] Store result in Redis
- [ ] Return geometry data

---

## Phase 2: Route Selection UI (Priority: HIGH)

### 2.1 Routes List Query
**File**: `dashboard/src/lib/graphql/queries/routes.ts`
```graphql
query GetAllRoutes {
  routes {
    id
    short_name
    long_name
    color
    is_active
  }
}
```

### 2.2 Route Selector Component
**File**: `dashboard/src/components/map/RouteSelector.tsx`
- [ ] Dropdown/Combobox using shadcn/ui Select
- [ ] Load all active routes on mount
- [ ] Display: `{short_name} - {long_name}`
- [ ] Color indicator badge for each route
- [ ] Loading skeleton during fetch
- [ ] Empty state if no routes
- [ ] Search/filter functionality

### 2.3 Integration with Navigation Control
**File**: `dashboard/src/components/map/NavigationControl.tsx`
- [ ] Add RouteSelector to control panel
- [ ] Emit `onRouteSelect(routeName)` event
- [ ] Show selected route info (name, length, stops)
- [ ] Clear route button

---

## Phase 3: Map Visualization (Priority: HIGH)

### 3.1 Route Layer Component
**File**: `dashboard/src/components/map/RouteLayer.tsx`
- [ ] Accept `routeName` prop
- [ ] Fetch geometry via `useRouteGeometry(routeName)`
- [ ] Render Mapbox GL JS polyline layer
- [ ] Style with route color
- [ ] Add line width and opacity
- [ ] Show loading spinner on map during fetch

### 3.2 Animated Polyline Rendering
**File**: `dashboard/src/components/map/AnimatedRouteLine.tsx`
- [ ] Point-by-point animation (0-415 coordinates)
- [ ] Configurable animation speed (default: 50ms per point)
- [ ] Play/Pause/Stop controls
- [ ] Progress indicator (X/415 points rendered)
- [ ] Smooth transition using Mapbox `lineGradient`

### 3.3 Viewport Adjustment
**File**: `dashboard/src/lib/map/viewport-utils.ts`
- [ ] `fitBoundsToRoute(coordinates)` - calculate bounding box
- [ ] Auto-zoom to route with padding (50px)
- [ ] Smooth transition animation (1 second duration)
- [ ] Handle single-point routes gracefully

### 3.4 Route Stops Overlay
**File**: `dashboard/src/components/map/RouteStopsLayer.tsx`
- [ ] Query stops for selected route
- [ ] Render stop markers on map
- [ ] Show stop sequence numbers
- [ ] Popup with stop name on hover
- [ ] Different marker for first/last stop

---

## Phase 4: Performance Optimization (Priority: MEDIUM)

### 4.1 Route Geometry Simplification
**File**: `dashboard/src/lib/map/simplify-geometry.ts`
- [ ] Douglas-Peucker algorithm for line simplification
- [ ] Reduce 415 points to ~100 for viewport overview
- [ ] Full resolution on zoom > 14
- [ ] Cache simplified versions in Redis

### 4.2 Lazy Loading
**File**: `dashboard/src/components/map/RouteVisualization.tsx`
- [ ] Lazy load route geometry on demand
- [ ] Prefetch adjacent routes (Route 1 → prefetch Route 2)
- [ ] Unload routes not in viewport
- [ ] Memory management for multiple routes

### 4.3 Debouncing & Throttling
- [ ] Debounce route selection (300ms)
- [ ] Throttle map pan/zoom events (100ms)
- [ ] Batch Redis reads for multiple routes

---

## Phase 5: Error Handling & Loading States (Priority: HIGH)

### 5.1 Error Boundaries
**File**: `dashboard/src/components/map/RouteErrorBoundary.tsx`
- [ ] Catch rendering errors
- [ ] Display user-friendly error message
- [ ] Retry button
- [ ] Log errors to monitoring service

### 5.2 Loading States
- [ ] Skeleton loader for route list
- [ ] Map overlay spinner during geometry fetch
- [ ] Progress bar for animation
- [ ] Shimmer effect for route info panel

### 5.3 Fallback Strategies
- [ ] Redis unavailable → direct GraphQL query
- [ ] GraphQL error → show cached data with warning
- [ ] Invalid route → show "Route not found"
- [ ] Network error → retry 3x with exponential backoff

---

## Phase 6: Production Features (Priority: MEDIUM)

### 6.1 Multi-Route Display
**File**: `dashboard/src/components/map/MultiRouteLayer.tsx`
- [ ] Select multiple routes (checkbox list)
- [ ] Display all selected routes simultaneously
- [ ] Color-coded overlays
- [ ] Legend showing active routes
- [ ] Toggle individual route visibility

### 6.2 Route Metrics Panel
**File**: `dashboard/src/components/map/RouteMetricsPanel.tsx`
- [ ] Total distance
- [ ] Number of stops
- [ ] Estimated travel time
- [ ] Service frequency
- [ ] Active vehicles on route (real-time)

### 6.3 Export Functionality
- [ ] Export route as GeoJSON
- [ ] Export as KML for Google Earth
- [ ] Copy coordinates to clipboard
- [ ] Download route image (map screenshot)

---

## Phase 7: Redis Infrastructure (Priority: HIGH)

### 7.1 Redis Setup
**File**: `docker-compose.yml` (add Redis service)
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  command: redis-server --appendonly yes
```

### 7.2 Redis Configuration
**File**: `dashboard/.env.local`
```
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600
REDIS_ROUTE_PREFIX=route:geometry:
```

### 7.3 Redis Client
**File**: `dashboard/src/lib/redis/client.ts`
- [ ] Initialize Redis client with error handling
- [ ] Graceful degradation if Redis unavailable
- [ ] Connection pooling
- [ ] Health check endpoint

---

## Phase 8: Testing & Validation (Priority: MEDIUM)

### 8.1 Unit Tests
- [ ] Test `useRouteGeometry` hook
- [ ] Test Redis cache hit/miss
- [ ] Test geometry simplification
- [ ] Test viewport calculations

### 8.2 Integration Tests
- [ ] Test route selection → map update flow
- [ ] Test animation controls
- [ ] Test cache invalidation
- [ ] Test error recovery

### 8.3 Performance Tests
- [ ] Benchmark Redis vs direct GraphQL
- [ ] Test with 10+ routes loaded
- [ ] Memory profiling
- [ ] Network waterfall analysis

---

## Implementation Order (Sprint Plan)

### Sprint 1 (Days 1-2): Foundation
1. Redis setup (Docker)
2. Redis client & caching service
3. Next.js API route with Redis
4. GraphQL route list query

### Sprint 2 (Days 3-4): UI Components
5. Route selector dropdown
6. Integration with navigation control
7. Basic route layer (static polyline)
8. Viewport adjustment

### Sprint 3 (Days 5-6): Animation & Polish
9. Animated polyline rendering
10. Play/pause controls
11. Route stops overlay
12. Loading states & error handling

### Sprint 4 (Days 7-8): Performance & Production
13. Geometry simplification
14. Multi-route display
15. Route metrics panel
16. Testing & validation

---

## Dependencies to Install

```json
{
  "dependencies": {
    "ioredis": "^5.3.2",
    "@tanstack/react-query": "^5.0.0",
    "@turf/bbox": "^6.5.0",
    "@turf/simplify": "^6.5.0",
    "mapbox-gl": "^2.15.0",
    "framer-motion": "^10.16.0"
  },
  "devDependencies": {
    "@types/mapbox-gl": "^2.7.0"
  }
}
```

---

## Success Metrics

- [ ] Route selection to map render < 500ms (with cache)
- [ ] Redis cache hit rate > 80%
- [ ] Animation smooth at 60fps
- [ ] No memory leaks after 100 route switches
- [ ] Zero crashes on network errors
- [ ] Works offline (cached routes only)

---

## Production Checklist

- [ ] Redis monitoring (uptime, memory)
- [ ] Error logging (Sentry)
- [ ] Performance monitoring (Web Vitals)
- [ ] Cache invalidation strategy documented
- [ ] Backup plan if Redis unavailable
- [ ] User documentation with screenshots
- [ ] Mobile responsive (touch controls)

---

## Next Steps

1. **Start Here**: Phase 7 (Redis Infrastructure) + Phase 1.3 (Redis Caching Service)
2. **Then**: Phase 2 (Route Selection UI)
3. **Finally**: Phase 3 (Map Visualization)

This plan ensures production-grade quality with proper caching, error handling, and performance optimization.
