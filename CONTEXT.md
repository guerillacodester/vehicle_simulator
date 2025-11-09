# ArkNet Vehicle Simulator - Project Context

**Project**: ArkNet Fleet Manager & Vehicle Simulator
**Repository**: vehicle_simulator
**Branch**: branch-0.0.3.3
**Date**: November 8, 2025
**Status**: 🚀 Production-Grade Dashboard Implementation (Dashboard build fix pending)
**Current Phase**: Component Architecture, Service Management & Simulator Route Validation

> **📌 PRODUCTION-READY HANDOFF DOCUMENT**: This CONTEXT.md + TODO.md enable a fresh agent to rebuild and continue to production-grade MVP with zero external context. Every architectural decision, every component relationship, every critical issue, and every next step is documented here.---

## 🚀 **CURRENT STATUS: Production-Grade Next.js Dashboard**

### Overview
The project has successfully transitioned to a **production-grade Next.js dashboard** with a comprehensive component architecture. The dashboard provides real-time service management capabilities with a professional UI/UX design system.

### Key Achievements
1. **✅ Component Architecture**: Fully implemented reusable component library with theme system
2. **✅ Service Management**: Real-time service orchestration via WebSocket + REST API
3. **✅ Professional UI**: Light/dark theme system with consistent design tokens
4. **✅ Routing Structure**: Organized navigation with landing page and service management
5. **✅ User-Tiered Dashboards**: Scaffolded distinct dashboards for Customer, Operator, Agency, and Admin, each with dedicated landing pages and navigation. Main landing page now features clear cards linking to each dashboard.
6. **✅ Route Geometry Validation**: Dispatcher now fetches and concatenates ALL route shapes (Route 1 length ≈ 12.982 km)
7. **✅ Distance & Speed Analysis**: Interval A→C along-route distance 10.222 km in 424.141 s (avg ≈ 86.8 km/h) consistent with 90 km/h instantaneous reading
8. **✅ StatusBadge Enum Coverage**: Added missing `UNHEALTHY` mapping to prevent TypeScript build failure
9. **✅ Driver Code Integrity**: Reverted temporary auto-stop modification; awaiting chosen implementation strategy
10. **⏳ Build Verification Pending**: Need to re-run dashboard build to confirm StatusBadge fix

---

## 🧭 CUSTOMER PORTAL — Google Maps-style Transit Interface

We are adding a user-facing Customer Portal (mobile-first) that mirrors the intuitive search and route guidance of Google Maps for transit. The goal is a fast, responsive interface that lets riders:

- Browse all routes with concise summaries and live vehicle counts
- Select a route and see every vehicle currently on it, with the map centered on the user's location
- Plan a trip by entering origin + destination and receive the best route(s) with walking guidance
- Get an intercept guide: walking directions to the nearest stop to board the selected route and live ETA to that intercept

Key design & technical requirements:

- Map: Leaflet (PMTiles basemap via existing `osm-viewer`) with route polylines and live vehicle markers
- Real-time: WebSocket connection to `gpscentcom_server` (or Telemetry Gateway) for vehicle updates; subscribe per-route where possible
- Routing & Geospatial: Geospatial Service (port 6000) for geocoding, reverse-geocoding, stop lookup, and along-route projections
- Data Provider: a `TransitDataProvider` abstraction (TypeScript) to centralize REST + WS access, caching, and subscription management
- Trip Planner: prefer direct routes first; support 0–1 transfers; ranking by total trip time (walk + wait + ride)
- ETA: compute along-route distances using route geometry and estimate time using vehicle speed (conservative factor applied)

Acceptance criteria (MVP):

- Route Browser page: lists all routes, shows active vehicle count, route summary, and supports quick search
- Route View: selectable route with map centered on user + live vehicle markers; bottom sheet lists nearest vehicles (3 before and 3 after user)
- Trip Planner: given origin & destination, returns at least one sensible route (direct or single-transfer) with step-by-step walking+ride steps and an estimated time
- Intercept Navigation: walking route to nearest stop with live ETA for the next bus at that stop

See the `TODO.md` for prioritized implementation tasks. Implementation plan (step-by-step) below.

### Current Architecture
```
arknet_fleet_manager/dashboard/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # Landing page with feature cards
│   │   └── services/          # Service management page
│   │       └── page.tsx
│   ├── components/            # Component Library (Organized)
│   │   ├── ui/               # Base UI Components
│   │   │   ├── button/       # Button variants
│   │   │   ├── card/         # Card components
│   │   │   ├── badge/        # Badge & StatusBadge
│   │   │   └── index.ts      # UI exports
│   │   ├── layout/           # Layout Components
│   │   │   └── DashboardLayout.tsx
│   │   ├── features/         # Feature-Specific Components
│   │   │   └── ServiceCard.tsx
│   │   └── landing/          # Landing Page Components
│   │       ├── HeroSection.tsx
│   │       ├── FeatureCard.tsx
│   │       └── FeatureGrid.tsx
│   ├── contexts/             # React Contexts
│   │   └── ThemeContext.tsx # Theme provider
│   ├── lib/                  # Utilities
│   │   └── theme.ts         # Design tokens
│   └── providers/           # Data Providers
│       └── ServiceManager.ts # Service orchestration
```

### Technology Stack
- **Framework**: Next.js 16.0.1 (React 19.2.0, TypeScript)
- **Styling**: Theme-based CSS-in-JS with design tokens
- **State**: React Context + WebSocket for real-time updates
- **Backend**: FastAPI launcher service (Port 7000)
- **Communication**: WebSocket + REST API integration
- **Theme**: Light/Dark mode with localStorage persistence

---

## 🎉 **MAJOR DEVELOPMENT MILESTONE - November 7, 2025**

## 🔄 Recent Updates — November 8, 2025

### Simulator & Route Diagnostics
- Dispatcher now aggregates all Strapi route shapes; verified Route 1 length ≈ 12.982 km (indices 0→394).
- Start GPS fix snapped to polyline index 64 (offset 32 m); end fix at terminal index 394.
- Straight-line distance: 7.383 km; along-route subpath: 10.222 km.
- Elapsed time: 424.141 s ⇒ avg along-route speed ≈ 86.8 km/h (consistent with 90 km/h instantaneous reading).
- Conclusion: Route traversal logic correct; no premature termination.

### Engine Auto-Stop Planning (No Code Yet)
- Goal: Auto-stop engine at route completion without disrupting current continuous simulation.
- Options: (A) Driver-local terminal check; (B) Simulator orchestration watcher; (C) Conductor policy event.
- Decision Pending: Await selection—recommend (B) for clearer separation of concerns.

### Dashboard Build Fix
- Issue: Missing `UNHEALTHY` mapping in `StatusBadge` caused TypeScript Record completeness error.
- Fix: Added mapping (variant: warning, label: UNHEALTHY, emoji: 🟠). Build verification still pending.

### Next Actions
1. Re-run dashboard build to confirm fix.
2. Choose engine auto-stop approach and implement minimal event emission.
3. Add regression test ensuring consumed route distance ≤ 12.982 km + ε.
4. Extend dashboard to differentiate UNHEALTHY vs FAILED styling semantics.
5. Document chosen engine-stop approach in this file & update TODO.md accordingly.

### Risks / Watch Items
- Auto-stop must allow future multi-loop or dwell behaviors (configurable post-completion policy).
- Need to ensure dispatcher continues to handle potential shape ordering edge cases (currently assumed correct order from Strapi).

### Assumptions
- Speed telemetry instantaneous values may exceed average by a few percent—current variance acceptable.
- Route geometry stable; no dynamic mid-route shape mutations expected.

### ✅ **COMPLETED: Production-Grade Next.js Dashboard**

**Achievement**: Full production-grade dashboard with component architecture, service management, and professional UI/UX.

**What This Means**:
- ✅ Professional Next.js 16 dashboard with TypeScript
- ✅ Component-driven architecture with reusable UI library
- ✅ Light/dark theme system with design tokens
- ✅ Real-time service management via WebSocket + REST API
- ✅ FastAPI launcher service integration (port 7000)
- ✅ Organized routing structure (landing page + services)
- ✅ Production-ready component organization and folder structure

**Key Technical Achievements**:
1. **Component Architecture**: Organized into logical folders (ui/, layout/, features/, landing/)
2. **Theme System**: Complete light/dark mode with localStorage persistence
3. **Service Management**: Real-time WebSocket updates for service status
4. **UI Components**: Button, Card, Badge, StatusBadge with theme-aware styling
5. **Layout System**: DashboardLayout with header and theme toggle
6. **Landing Experience**: Professional welcome page with feature navigation

**Code Quality Improvements**:
- Component-based architecture for maintainability
- TypeScript throughout for type safety
- Theme system for consistent design
- Logical folder organization
- Reusable component library
- Clean separation of concerns

### Component Organization Structure
```
src/components/
├── ui/                    # Base UI Components (categorized)
│   ├── button/           # Button variants and styles
│   ├── card/             # Enhanced Card with 3D effects, hover states, compact sizing
│   ├── badge/            # Badge and StatusBadge components
│   └── index.ts         # Centralized UI exports
├── layout/               # Layout Components
│   └── DashboardLayout.tsx  # Main dashboard wrapper with navigation
├── features/             # Feature-Specific Components
│   └── ServiceCard.tsx  # Enhanced service management card with icons and monospace display
├── landing/              # Landing Page Components
│   ├── HeroSection.tsx  # Welcome hero section
│   ├── FeatureCard.tsx  # Feature navigation cards with consistent sizing
│   ├── FeatureGrid.tsx  # Grid layout for features with uniform card heights
│   └── index.ts         # Landing component exports
└── index.ts             # Main component exports
```

### Enhanced UI/UX Features
- **Card Consistency**: All cards use uniform 280px height with 3D shadows and hover effects
- **Compact Design**: Optimized spacing and padding for better information density
- **Global Theme**: Consistent color scheme across entire Next.js application
- **Navigation System**: Header navigation with active state highlighting and hover effects
- **Service Cards**: Enhanced with status icons, monospace port/PID display, improved badges
- **Empty States**: Professional empty state design with clear messaging and visual hierarchy
- **Controls Panel**: Styled control panel with gradient title and consistent theming

### Design System
- **Theme Tokens**: Centralized color, spacing, typography, shadows
- **Component Variants**: Consistent styling across light/dark modes
- **Responsive Design**: Mobile-first approach with breakpoints
- **Accessibility**: ARIA labels, keyboard navigation support
- **Performance**: Optimized re-renders with React best practices
- Scalability (React component architecture, API layer abstraction)
- Maintainability (TypeScript, tests, documentation)
- Team collaboration (design system, component library)

**High-Level Architecture**:
```
┌─────────────────────────────────────────┐
│     Next.js 14 Frontend (Port 3000)     │
│  (Dashboard, Fleet Mgmt, Analytics)     │
│     WebSocket + HTTP API Integration    │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
 Host Server  WebSocket    HTTP REST
 (Port 7000) Streaming    (various)
    │            │            │
    ├────────────┼────────────┤
    │
    ▼
┌─────────────────────────────────────────┐
│      5 Backend Services (Unified)       │
│  Strapi (1337), GPSCentCom (5000),      │
│  Geospatial (6001), Commuter (4000),    │
│  Simulator (5001)                       │
└─────────────────────────────────────────┘
```

**Design Specification** (In Progress):
- See **PHASE 1: NEXT.JS GUI DESIGN** section below for full spec

---

## **PHASE 1: PRODUCTION-GRADE NEXT.JS GUI SPECIFICATION**

### **1. Project Architecture & Technology Stack**

**Technology Choices**:
- **Framework**: Next.js 14+ (React 18+, TypeScript)
- **Package Manager**: npm (for consistency with backend package.json)
- **Styling**: Tailwind CSS + shadcn/ui (composable, accessible components)
- **State Management**: React Context + Zustand (lightweight, no Redux overhead)
- **HTTP Client**: axios with interceptors (auto-retry, auth headers)
- **WebSocket**: Socket.IO client (real-time updates)
- **Charting**: Recharts (React-based, responsive)
- **Maps**: Mapbox GL (if vehicle tracking required)
- **Testing**: Jest + React Testing Library (unit & integration)
- **Code Quality**: ESLint + Prettier (formatting)
- **Analytics**: Simple event tracking (optional, can add later)

**Folder Structure** (Production-ready):
```
nextjs-fleet-gui/
├── public/
│   ├── icons/
│   └── images/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout (header, sidebar)
│   │   ├── page.tsx            # Dashboard
│   │   ├── dashboard/
│   │   │   └── page.tsx        # Fleet overview
│   │   ├── fleet/
│   │   │   ├── page.tsx        # Vehicles list
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx    # Vehicle detail
│   │   │   └── tracking.tsx    # Map tracking
│   │   ├── passengers/
│   │   │   ├── page.tsx        # Passenger manifest
│   │   │   └── spawn.tsx       # Spawn control
│   │   ├── routes/
│   │   │   └── page.tsx        # Routes & depots
│   │   ├── analytics/
│   │   │   ├── page.tsx        # Reports dashboard
│   │   │   └── charts.tsx      # Charts & KPIs
│   │   ├── settings/
│   │   │   └── page.tsx        # System config
│   │   └── api/
│   │       ├── auth/           # JWT auth endpoints
│   │       ├── proxy/          # Backend proxy routes
│   │       └── websocket/      # WebSocket upgrade
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── dashboard/
│   │   │   ├── FleetStatus.tsx
│   │   │   ├── KPICards.tsx
│   │   │   ├── AlertBanner.tsx
│   │   │   └── QuickActions.tsx
│   │   ├── fleet/
│   │   │   ├── VehiclesTable.tsx
│   │   │   ├── VehicleRow.tsx
│   │   │   ├── VehicleControls.tsx
│   │   │   ├── VehicleMap.tsx
│   │   │   └── StatusIndicator.tsx
│   │   ├── passengers/
│   │   │   ├── ManifestTable.tsx
│   │   │   ├── SpawnForm.tsx
│   │   │   ├── DistributionChart.tsx
│   │   │   └── PassengerFilters.tsx
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Loader.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── ConfirmDialog.tsx
│   │   └── forms/
│   │       ├── FormField.tsx
│   │       └── FormSubmit.tsx
│   ├── hooks/
│   │   ├── useFleet.ts         # Fleet data + actions
│   │   ├── usePassengers.ts    # Passenger data + actions
│   │   ├── useRealtime.ts      # WebSocket subscriptions
│   │   ├── useAuth.ts          # Auth context
│   │   └── useNotification.ts  # Toast notifications
│   ├── services/
│   │   ├── api-client.ts       # Axios + interceptors
│   │   ├── websocket-client.ts # Socket.IO setup
│   │   ├── fleet-service.ts    # Fleet API calls
│   │   ├── passenger-service.ts # Passenger API calls
│   │   ├── route-service.ts    # Route API calls
│   │   └── auth-service.ts     # Authentication
│   ├── types/
│   │   ├── api.ts              # API response types
│   │   ├── domain.ts           # Business domain types
│   │   ├── ui.ts               # Component prop types
│   │   └── websocket.ts        # Real-time event types
│   ├── utils/
│   │   ├── constants.ts        # API URLs, colors, etc.
│   │   ├── format.ts           # Formatting functions
│   │   ├── validators.ts       # Input validation
│   │   ├── error-handler.ts    # Error parsing
│   │   └── logger.ts           # Client-side logging
│   ├── context/
│   │   ├── AuthContext.tsx     # JWT + user info
│   │   ├── NotificationContext.tsx # Toast notifications
│   │   └── AppContext.tsx      # Global app state
│   ├── styles/
│   │   ├── globals.css         # Global Tailwind
│   │   └── theme.css           # Theme variables
│   └── lib/
│       └── env.ts              # Environment validation
├── public/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example                # Environment template
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── eslint.config.mjs
├── jest.config.js
├── next.config.js
└── README.md
```

### **2. API Integration Layer Design**

**Backend API Contracts** (to implement):

**Fleet Management API** (`http://localhost:7000/api`):
```typescript
// Vehicles
GET /api/vehicles                    // List all vehicles
GET /api/vehicles/{id}               // Vehicle detail
POST /api/vehicles/{id}/engine/start
POST /api/vehicles/{id}/engine/stop
POST /api/vehicles/{id}/boarding/enable
POST /api/vehicles/{id}/boarding/disable
GET /api/vehicles/{id}/position      // Real-time position

// Passengers (Commuter Service)
GET /api/passengers                  // List passengers
GET /api/passengers/manifest/{route_id} // Route manifest
POST /api/passengers/spawn           // Spawn passengers
DELETE /api/passengers               // Delete passengers
GET /api/passengers/distribution     // Hour distribution

// Routes
GET /api/routes                      // List routes
GET /api/routes/{id}                 // Route detail

// Depots
GET /api/depots                      // List depots
GET /api/depots/{id}                 // Depot detail

// System
GET /api/health                      // System health
GET /api/services/status             // All services status
POST /api/services/{service}/start
POST /api/services/{service}/stop
GET /api/config                      // System configuration
POST /api/config                     // Update configuration
```

**WebSocket Events** (Real-time streaming):
```typescript
// Vehicle tracking
vehicle:position-update
vehicle:engine-status-changed
vehicle:boarding-status-changed
vehicle:arrived-at-destination

// Passenger events
passenger:boarded
passenger:alighted
passenger:spawned
passenger:deleted

// Service events
service:started
service:stopped
service:health-changed
system:alert

// Connection events
connected
disconnected
reconnected
error
```

### **3. Component Hierarchy & Page Flows**

**Main Pages** (7 primary views):

1. **Dashboard** (`/`)
   - Fleet status cards (total vehicles, active, idle, etc.)
   - KPI indicators (avg passengers, utilization %, etc.)

---

## 📡 Telemetry Gateway & gpscentcom_server Integration

This section explains how the Telemetry Gateway will integrate with the existing `gpscentcom_server` to provide realtime telemetry to the Next.js dashboard and other clients.

High-level responsibilities:
- gpscentcom_server: existing telemetry server (source of raw telemetry). It publishes vehicle packets via WebSocket/TCP (configurable) to subscribers.
- Connector (gpscentcom adapter): lightweight consumer that subscribes to `gpscentcom_server`, validates and normalizes raw messages into the canonical TelemetryPoint schema, and forwards them to the Telemetry Gateway ingestion endpoint or Redis stream.
- Telemetry Gateway (FastAPI): central broker and ingestion service that:
  - Exposes a secure WebSocket endpoint for dashboard and external clients: `/ws/telemetry`
  - Exposes internal REST ingestion endpoint (protected) for connectors: `POST /internal/telemetry`
  - Persists telemetry to Postgres/PostGIS via an async worker pipeline
  - Provides REST endpoints for historical queries and latest position lookups
  - Broadcasts validated telemetry to connected clients in near-real-time

Data flow (sequence):
1. `gpscentcom_server` emits raw telemetry packets (binary or JSON) on its feed.
2. Connector subscribes, decodes packets, maps fields to TelemetryPoint, and forwards to the Telemetry Gateway (`POST /internal/telemetry` or publishes to Redis).
3. Gateway validates payload with Pydantic, enqueues the record to an internal async queue or Redis stream, broadcasts the point to connected WebSocket clients, and returns 202 Accepted to the connector.
4. Background ingestion worker flushes queued points in batches to Postgres/PostGIS and marks them complete. Errors are retried with backoff and poisoned messages are logged.

TelemetryPoint canonical schema (summary):
```json
{
   "vehicle_id": "string",
   "timestamp": "2025-11-08T12:34:56.789Z",
   "lat": 12.345678,
   "lon": -98.765432,
   "speed_m_s": 5.5,
   "heading": 123.4,
   "route_id": "optional",
   "seq": 12345,
   "meta": { }
}
```

Gateway endpoints (MVP):
- `POST /internal/telemetry` (connector → gateway) — accepts TelemetryPoint, returns 202
- `GET /telemetry/latest/{vehicle_id}` — returns latest persisted position
- `GET /telemetry/history?vehicle_id=&start=&end=&limit=` — historical points
- `GET /health`, `GET /metrics` — health & Prometheus metrics
- `WebSocket /ws/telemetry` — real-time broadcast; subscribe to channel or filter by vehicle(s)

WebSocket contract (simple):
- Client opens WS connection with auth token: `wss://gateway/ws/telemetry?token=...`
- Server accepts and may send initial snapshot: `{ "type": "snapshot", "vehicles": { vehicle_id: TelemetryPoint } }`
- Server sends incremental messages: `{ "type":"telemetry", "payload": TelemetryPoint }`
- Clients can send control messages (subscribe/unsubscribe): `{ "type":"subscribe", "vehicle_ids": ["v1","v2"] }`

Security and auth:
- Connectors and internal ingestion endpoints must authenticate via API key or mTLS (avoid public ingestion endpoints without auth).
- Client WebSocket connections use bearer tokens (JWT) issued per client with scopes (read-only or admin).
- Gateway enforces CORS, rate-limits ingestion, and audits high-error rates.

Persistence and schema notes:
- Use Postgres + PostGIS. Table schema: `telemetry_points(id, vehicle_id, ts timestamptz, geom geography(Point,4326), speed numeric, heading numeric, raw jsonb)` with indexes on `(vehicle_id, ts DESC)` and spatial GIST on `geom`.
- Store raw payload for forensics and replay.
- Use batch inserts (e.g., 100–1000 rows) for throughput.

Scaling & resilience:
- For single-instance/dev: connector → gateway (in-process) → DB writer (async background) is fine.
- For scale: use Redis/Kafka as ingestion buffer; connectors write to stream, multiple gateway or worker instances consume and write to DB; gateway instances subscribe to Redis pub/sub for broadcasting to sockets.

How this integrates with existing `gpscentcom_server`:
- `gpscentcom_server` remains the telemetry source and any device/driver will continue to send to it.
- The Connector subscribes as a client of `gpscentcom_server` (using its documented protocol) — this is non-intrusive: it only reads messages and does not modify upstream server behavior.
- The Dashboard then consumes telemetry exclusively from the Telemetry Gateway (not directly from gpscentcom_server). This decouples UI clients from the raw telemetry protocol and centralizes security, persistence, and scaling.

Operational notes & runbook (quick):
1. Start Postgres/PostGIS and apply migration for `telemetry_points`.
2. Start Telemetry Gateway (FastAPI) with configured DB and Redis (optional).
3. Start Connector configured to connect to `ws://localhost:5000` (gpscentcom_server).
4. Start dashboard and point TelemetryProvider to `wss://gateway/ws/telemetry`.
5. Verify live positions appear; check `GET /telemetry/latest/{vehicle_id}` for persisted points.

Immediate next steps (in repo):
- Add telemetry schema files: `gateway/schemas.py` and `arknet_fleet_manager/dashboard/src/features/telemetry/types.ts`.
- Scaffold `gateway/main.py` with WS endpoints (MVP) and an internal ingestion route.
- Add a small mock connector `gateway/connectors/mock_gpscentcom.py` for local dev testing.

See the TODO list for tracked tasks and acceptance criteria.

1. **Fleet Management** (`/fleet`)
   - Sortable/filterable vehicles table
   - Real-time status indicators
   - Inline controls (start, stop, enable boarding)
   - Vehicle detail modal (position, route, driver, passengers)
   - Map view with vehicle markers (bonus feature)

2. **Vehicle Tracking** (`/fleet/tracking`)
   - Mapbox GL map
   - Vehicle markers with real-time updates
   - Route polylines
   - Passenger pickup/dropoff points
   - Filter by route/status

3. **Passenger Management** (`/passengers`)
   - Manifest table (passenger list for route)
   - Filters (status, time, route)
   - Distribution chart (passengers by hour)
   - Spawn control form
   - Bulk delete with confirmation

4. **Routes & Depots** (`/routes`)
   - Routes list with stats
   - Depot list with catchment areas
   - Building/POI associations
   - Route editing (future: API support)

5. **Analytics** (`/analytics`)
   - Daily summaries
   - Charts (passenger trends, vehicle utilization, etc.)
   - Report export (CSV, JSON)
   - KPI dashboards

6. **Settings** (`/settings`)
   - System configuration (pickup radius, etc.)
   - Service restart controls
   - User preferences (dark mode, etc.)
   - Audit log viewer

### **4. Real-Time Integration Strategy**

**WebSocket Architecture**:
- Socket.IO client auto-connects on app load
- Subscribes to relevant event channels
- Auto-reconnect with exponential backoff
- Updates React state on events
- Notifies user of critical events

**Event Subscription Pattern**:
```typescript
// Example: useRealtime hook
useRealtime('vehicle:position-update', (event) => {
  setVehicles(prev => 
    prev.map(v => v.id === event.vehicle_id 
      ? { ...v, position: event.position }
      : v
    )
  )
})
```

**Performance Optimization**:
- Batch updates (debounce rapid changes)
- Virtual scrolling for large tables
- Lazy load map when tracking page visible
- Cache vehicle/route data with TTL
- Selective re-renders (useCallback, useMemo)

### **5. Authentication & Authorization**

**User Roles** (3 levels):
- **Admin**: Full system access (all endpoints, config changes)
- **Operator**: Fleet control (start/stop, passenger control)
- **Viewer**: Read-only access (dashboards, reports)

**Implementation**:
- JWT token stored in httpOnly cookie
- Automatic refresh on 401 response
- Role check at page level (redirect to login if unauthorized)
- Protected API routes in Next.js `/api/`

### **6. Error Handling & User Feedback**

**Error Scenarios**:
- Network timeout → Auto-retry with exponential backoff
- Service unavailable → Show maintenance banner
- Authentication expired → Redirect to login
- Permission denied → Show error toast
- API validation error → Show field-level errors in forms

**User Notifications**:
- Toast notifications (success, error, warning, info)
- In-page error banners (for persistent issues)
- Loading skeletons (during data fetch)
- Confirmation dialogs (before destructive actions)
- Real-time alerts (WebSocket-driven)

### **7. Testing Strategy**

**Test Coverage** (Target: 80%):
- **Unit Tests**: Components, hooks, utilities (Jest + RTL)
- **Integration Tests**: API calls, WebSocket events
- **E2E Tests**: Critical workflows (Playwright)
- **Visual Regression**: Component snapshots

### **8. Performance & Scalability**

**Targets**:
- Time to Interactive (TTI): <3s
- First Contentful Paint (FCP): <2s
- Lighthouse score: >90
- WebSocket latency: <100ms for updates

**Optimizations**:
- Code splitting per route
- Image optimization (Next.js Image component)
- Static generation for routes/depots lists
- Incremental Static Regeneration (ISR) for config
- Service Worker for offline support (future)

### **9. Development Phases** (Execution Order)

**Phase 1A** (Week 1): Project setup + Dashboard skeleton
- Initialize Next.js project
- Setup Tailwind + shadcn/ui
- Build layout components
- Create basic dashboard with mock data

**Phase 1B** (Week 2): Fleet Management + API integration
- Build vehicles table + filters
- Implement HTTP client + fleet-service
- Add vehicle control commands
- Real-time status indicators

**Phase 1C** (Week 3): Real-time features + Passenger Management
- WebSocket integration
- Passenger manifest
- Spawn control form
- Distribution chart

**Phase 1D** (Week 4): Advanced features + Polish
- Map integration
- Analytics/reporting
- Settings page
- Error handling + notifications
- Tests + documentation

---

## 🚨 **MANDATORY AGENT DIRECTIVES - READ FIRST**

**⚠️ STOP: Before doing ANYTHING else, internalize these directives:**

### **Your Role & Authority**

You are a **50+ year full-stack developer veteran** with deep expertise across all technologies in this stack. You have the authority and responsibility to:

### **⚠️ CRITICAL: NO NEW MARKDOWN FILES**
- **NEVER create new .md files** for documentation, summaries, or analysis
- All information goes into **CONTEXT.md** or **TODO.md** ONLY
- Exception: Module-specific READMEs inside their own directories (e.g., `gps_telemetry_client/README.md`)
- If you need to document something, add a section to CONTEXT.md or TODO.md

1. **✅ PUSH BACK HARD** on poor suggestions, anti-patterns, or violations of best practices
   - Question unclear requirements before implementing
2. **✅ ENFORCE BEST PRACTICES**
   - Follow SOLID principles religiously
   - Write clean, maintainable, testable code
   - Use proper error handling and validation
   - Implement proper TypeScript typing (no `any` without justification)
   - Follow established patterns in the codebase

3. **✅ WORK INCREMENTALLY & TEST CONSTANTLY**
   - Break work into granular, testable steps
   - Test each change before moving forward
   - Verify success response before proceeding to next step
   - Never skip validation or testing phases
   - If a test fails, STOP and fix it before continuing
   - Perform a deep analysis of the codebase before proceeding
   - analyze the TODO.md and determine steps to MVP and our next immediate steps

4. **✅ MAINTAIN DOCUMENTATION DISCIPLINE**
   - Update CONTEXT.md immediately after every successful change
   - Update TODO.md checkboxes and progress counters as work completes
   - Lint both .md files for errors (proper markdown syntax)
   - Keep session notes and discoveries documented
   - Track progress counters (X/Y steps complete)

5. **✅ PROVIDE COMMIT MESSAGES**
   - After every successful change, provide a clear, descriptive commit message
   - Follow conventional commits format: `type(scope): description`
   - Include what changed, why it changed, and impact
   - Ready for immediate `git commit`

6. **✅ AVOID FILE POLLUTION**
   - Do NOT create junk scripts or temporary files
   - Do NOT create unnecessary wrapper files
   - Do NOT create summary markdown files unless explicitly requested
   - Use existing tools and patterns
   - Clean up after yourself

7. **✅ DEBUGGING MINDSET**
   - When errors occur, diagnose root cause before suggesting fixes
   - Provide detailed analysis of what went wrong and why
   - Explain trade-offs of different solutions
   - Test fixes thoroughly before declaring success

### **Workflow Enforcement**

**For EVERY task, follow this sequence:**

```text
1. READ & ANALYZE
   ├─ Understand the requirement deeply
   ├─ Check existing code patterns
   ├─ Identify potential issues or improvements
   └─ Question unclear aspects

2. PROPOSE & DISCUSS
   ├─ Suggest best approach (may differ from user's request)
   ├─ Explain WHY this approach is better
   ├─ Provide alternatives with trade-offs
   └─ Get confirmation before proceeding

3. IMPLEMENT INCREMENTALLY
   ├─ Break into small, testable steps
   ├─ Implement one step at a time
   ├─ Test each step thoroughly
   └─ Verify success before next step

4. VALIDATE & TEST
   ├─ Run all relevant tests
   ├─ Verify database changes (if applicable)
   ├─ Check for regressions
   └─ Confirm success response

5. DOCUMENT & COMMIT
   ├─ Update CONTEXT.md with changes
   ├─ Update TODO.md checkboxes/progress
   ├─ Lint markdown files
   ├─ Provide commit message
   └─ Verify documentation is accurate

6. NEVER SKIP STEPS
   └─ If ANY step fails, STOP and fix it
```

### **Critical Reminders**

- **Branch**: `branch-0.0.2.8` (NOT main)
- **Single Source of Truth**: Strapi (all writes via Entity Service API)
- **Spatial Data**: PostGIS geometry columns (NOT lat/lon pairs)
- **Import Pattern**: Streaming parser + bulk SQL (500-1000 feature batches)
- **No Shortcuts**: Quality over speed, always
- **User Preference**: Detailed explanations, analysis-first approach

**If you read this section, you are now operating under these directives. Proceed accordingly.**

---

## 🚀 **IMMEDIATE CONTEXT FOR NEW AGENTS**

### **Where We Are RIGHT NOW (October 28, 2025)**

```text
CURRENT STATE (October 31, 2025 - Geospatial API Production-Ready):
✅ ConfigProvider Pattern: Single source of truth for infrastructure config
✅ Eliminated 90+ hardcoded URLs: 17+ files across all subsystems updated
✅ Configuration Architecture: Root config.ini (infrastructure) + .env (secrets) + DB (operational)
✅ GPS Client Port Fixed: 8000 → 5000 (correct GPSCentCom port)
✅ UTF-8 Encoding Fixed: 7 files updated to handle emoji/special chars in config.ini
✅ Launcher Consolidated: Deleted 3 redundant scripts, launch.py is single launcher
✅ Integration Test Passing: launch.py successfully starts all subsystems
✅ Route-Depot Junction Table: Populated with 1 association (Route 1 ↔ Speightstown, 223m)
✅ Precompute Script: commuter_service/scripts/precompute_route_depot_associations.py
✅ Zero Configuration Redundancies: Between files and database confirmed
✅ GEOSPATIAL API PRODUCTION-READY: 52+ endpoints, 13/13 critical tests passing (100%)
✅ API Coverage Analysis: Fully supports depot-based, route-based, hybrid terminal spawning
✅ GeospatialClient Integration Ready: commuter_service/infrastructure/geospatial/client.py
✅ Performance Validated: <100ms queries, <500ms analytics - all targets met
✅ Error Handling: Production-grade 503/504 responses with graceful degradation
✅ Documentation: API_REFERENCE.md, GEOSPATIAL_API_COMPLETENESS_ASSESSMENT.md complete
❌ RouteSpawner Failing: No spawn-config for route documentId 14
❌ DepotSpawner Limited: 4 of 5 depots have no routes (only Speightstown has Route 1)
❌ 0% Spawn Success: EXPECTED - can't spawn without routes/configs

GEOSPATIAL API IMPLEMENTATION (October 31, 2025):
✅ 9 Router Categories - 52+ Endpoints:
   - /routes: 7 endpoints (all, detail, geometry, buildings, metrics, coverage, nearest)
   - /depots: 7 endpoints (all, detail, catchment, routes, coverage, nearest)
   - /buildings: 7 endpoints (at-point, along-route, in-polygon, density, count, stats, batch)
   - /analytics: 5 endpoints (heatmap, route-coverage, depot-service-areas, population, demand)
   - /meta: 6 endpoints (health, version, stats, bounds, regions, tags)
   - /spawn: 10 endpoints (depot-analysis, all-depots, route-analysis, config GET/POST, multipliers)
   - /geocode: 2 endpoints (reverse, batch)
   - /geofence: 2 endpoints (check, batch)
   - /spatial: 6 endpoints (legacy compatibility, buildings/pois nearest)
✅ SOLID Architecture: Single Responsibility, Separation of Concerns
✅ Hybrid Spawn Model: terminal_population × route_attractiveness fully supported
✅ Configuration Management: Runtime-adjustable spawn parameters via /spawn/config
✅ Test Results: 13/13 critical endpoints passing (100% success rate)
✅ Fixes Applied:
   - POST body parameter handling (3 endpoints fixed)
   - SQL type casting (numeric vs float)
   - Geometry column handling (ST_Centroid for polygons)
   - KeyError protection (safe dictionary access depot.get('attributes', {}))
   - Missing endpoints added (batch geocoding/geofencing, legacy spatial)
✅ Files: geospatial_service/api/{routes,depots,buildings,analytics,metadata,spawn,geocoding,geofencing,spatial}.py

CONFIGURATION REFACTORING (October 31, 2025):
✅ Created common/config_provider.py: ConfigProvider singleton with InfrastructureConfig dataclass
✅ Updated config.ini: Comprehensive infrastructure settings with documentation
✅ Fixed Files (17+):
   - GPS Telemetry Client: client.py, __init__.py, test_client.py, README.md
   - Geospatial Service: main.py
   - Commuter Simulator: geospatial/client.py, database/strapi_client.py, 
     database/passenger_repository.py, interfaces/http/commuter_manifest.py, main.py
   - Transit Simulator: config/config_loader.py, simulator.py, vehicle/conductor.py,
     core/dispatcher.py, vehicle/driver/navigation/vehicle_driver.py, 
     services/config_service.py, __main__.py
   - Root Scripts: launcher/config.py
✅ Deprecated arknet_transit_simulator/config/config.ini (all operational settings moved to DB)
✅ Added 8 vehicle_simulator entries to operational_config_seed_data.json (23 total)
✅ Files Deleted: start_services.py, start_fleet_services.py, start_all_systems.py (redundant)
✅ Documentation Cleanup: Pending deletion of HARDCODED_VALUES_ASSESSMENT.md, 
   GPS_RECONNECTION_IMPLEMENTATION.md, FLEET_SERVICES.md

IMMEDIATE NEXT TASK (October 31, 2025):
🎯 Use New Geospatial API to List Routes & Create Spawn Configs
   - Step 1: Run list_routes.py using /routes/all API endpoint
   - Step 2: Verify route IDs (documentId vs id confusion)
   - Step 3: Create spawn-config entries for all routes in database
   - Step 4: Test RouteSpawner with proper configs
   - Goal: Get RouteSpawner generating passengers
   - After: Test full spawn cycle (depot + route spawners together)

CLEAN ARCHITECTURE (October 29 - REFACTORED):
commuter_service/ (Passenger Generation - CLEAN ARCHITECTURE)
  ├─ main.py: Single entrypoint with SpawnerCoordinator
  ├─ domain/: Pure business logic (no external dependencies)
  │   └─ services/
  │       ├─ spawning/: DepotSpawner, RouteSpawner, base interfaces
  │       └─ reservoirs/: RouteReservoir, DepotReservoir
  ├─ application/: Use cases and orchestration
  │   ├─ coordinators/: SpawnerCoordinator
  │   └─ queries/: manifest_query (enrichment logic)
  ├─ infrastructure/: External systems
  │   ├─ persistence/strapi/: PassengerRepository
  │   ├─ geospatial/: GeospatialClient
  │   ├─ config/: SpawnConfigLoader
  │   └─ events/: PostgreSQL LISTEN/NOTIFY
  └─ interfaces/: Entry points
      ├─ http/: FastAPI commuter_manifest API (port 4000)
      └─ cli/: manifest_cli visualization tool

arknet_transit_simulator/ (Vehicle Movement - COMPLETE)
  ├─ Vehicles drive routes
  ├─ Conductor listens for passengers
  └─ Conductor picks up passengers from reservoirs

clients/ (GUI-Agnostic Service Clients - Nov 2, 2025)
  ├─ gpscentcom/: GPS telemetry client (HTTP + WebSocket streaming)
  │   ├─ models.py: Vehicle, AnalyticsResponse, HealthResponse
  │   ├─ client.py: GPSTelemetryClient with observer pattern
  │   └─ observers.py: TelemetryObserver, CallbackObserver
  ├─ geospatial/: Geospatial service client
  │   ├─ models.py: Address, RouteGeometry, Building, DepotInfo, SpawnPoint
  │   ├─ client.py: GeospatialClient (reverse_geocode, get_route_geometry, etc.)
  │   └─ __init__.py
  ├─ commuter/: Commuter service client
  │   ├─ models.py: Passenger, ManifestResponse, BarchartResponse, TableResponse, RouteMetrics, SeedRequest, SeedResponse
  │   ├─ client.py: CommuterClient (get_manifest, get_barchart, seed_passengers, etc.)
  │   └─ __init__.py
  └─ simulator/: Simulator control client (TODO - requires HTTP control API)
      ├─ models.py: SimulatorStatus, VehicleInfo, ControlResponse (TODO)
      ├─ client.py: SimulatorClient (start, stop, pause, resume, get_status) (TODO)
      └─ __init__.py (TODO)

Purpose: Enable Next.js, console, .NET, mobile apps to consume services
Pattern: Observable, config auto-loading, type-safe Pydantic models
Missing: Simulator needs HTTP control API (POST /simulator/start, stop, pause, resume, GET /simulator/status)

DEPENDENCIES & BLOCKERS:
✅ None - All spawner implementation complete
✅ Clean architecture refactoring complete (Oct 29)
✅ Geospatial API production-ready (Oct 31)
✅ Ready for route listing and spawn config creation
✅ GeospatialService operational (localhost:6000)
✅ Strapi operational (localhost:1337)
✅ Client libraries created (Nov 2) - GPS, Geospatial, Commuter

PATH TO MVP (TIER 5-6 - REVISED Oct 28):
TIER 5 → Route-Depot Association & RouteSpawner Integration ✅ STEP 1/7 COMPLETE (Oct 28)
   - ✅ Create route-depots junction table (schema, cached labels, lifecycle hooks, bidirectional UI)
  - Precompute geospatial associations
  - Update DepotSpawner logic for associated routes
  - Wire existing RouteSpawner to coordinator (implementation already complete)
  - Add PubSub for reservoir visualization
  - Execute comprehensive flag tests
TIER 6 → Conductor Integration & Reservoir Wiring
  - Connect Conductor to reservoirs
  - Implement pickup logic integration
  - End-to-end vehicle-passenger flow
TIER 7 → Redis, Geofencing, Production Optimization
```

---

## 📝 **REFERENCE: Backend Service Details**

For reference when building the Next.js frontend:

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| Strapi | 1337 | CMS + entity management | Running |
| GPSCentCom | 5000 | Telemetry collection | Running |
| Geospatial | 6001 | PostGIS spatial queries | Running |
| Commuter Service | 4000 | Passenger spawning + manifest | Running |
| Vehicle Simulator | 5001 | Fleet simulation + control API | Running |
| Host Server | 7000 | Service orchestration + proxy | Running |

**Key Backend URLs** (for frontend config):
```
BACKEND_URL=http://localhost:7000
STRAPI_URL=http://localhost:1337
SIMULATOR_URL=http://localhost:5001
COMMUTER_URL=http://localhost:4000
GEOSPATIAL_URL=http://localhost:6001
GPSCENTCOM_URL=http://localhost:5000
WEBSOCKET_URL=ws://localhost:7000
```

All services are **production-ready** and stable for frontend development.

---

## CONTEXT

## Data Access Design

### Separation of Data Providers
To ensure Separation of Duties (SoD) and adhere to best engineering practices, the project uses two distinct DataProviders:

1. **TelemetryDataProvider**:
   - **Purpose**: Handles real-time telemetry data from gpscentcom_server.
   - **Responsibilities**:
     - Connect to gpscentcom_server as a subscribed client.
     - Manage real-time updates for vehicle positions, statuses, and other telemetry data.
     - Provide methods for subscribing to updates, accessing cached data, and disconnecting when not needed.
   - **Methods**:
     - `subscribeToTelemetry`: Establishes a connection and listens for updates.
     - `getTelemetryData`: Returns cached telemetry data.
     - `disconnectTelemetry`: Closes the connection when no longer needed.

2. **GraphQLDataProvider**:
   - **Purpose**: Interacts with Strapi via GraphQL for hierarchical data (e.g., vehicles, routes, depots, drivers).
   - **Responsibilities**:
     - Fetch hierarchical data securely and efficiently.
     - Perform CRUD operations for vehicles, routes, depots, and drivers.
   - **Methods**:
     - `getVehicles`, `getRoutes`, `getDepots`, `getDrivers`: Fetch data from Strapi.
     - `createVehicle`, `updateVehicle`, `deleteVehicle`: CRUD operations for vehicles.
     - `createRoute`, `updateRoute`, `deleteRoute`: CRUD operations for routes.
     - `createDepot`, `updateDepot`, `deleteDepot`: CRUD operations for depots.
     - `createDriver`, `updateDriver`, `deleteDriver`: CRUD operations for drivers.

### Service Management

#### ServiceManager
To centralize the management of all services, the project includes a `ServiceManager` module.

- **Purpose**: Provides a unified interface for starting, stopping, and checking the status of all services (e.g., gpscentcom_server, simulator).
- **Responsibilities**:
  - Start and stop services remotely.
  - Check the real-time status of services.
  - Ensure secure and reliable communication with services.
- **Methods**:
  - `startService(serviceName)`: Starts the specified service.
  - `stopService(serviceName)`: Stops the specified service.
  - `getServiceStatus(serviceName)`: Returns the real-time status of the specified service.
  - `getAllServiceStatuses()`: Returns the status of all services in a single call.

#### Integration with TelemetryDataProvider
- The `TelemetryDataProvider` uses the `ServiceManager` to manage telemetry-related services (e.g., gpscentcom_server).
- This ensures a clear separation of concerns and simplifies service management.

### Benefits of Centralized Service Management
- **Scalability**: Easily add or remove services without affecting other parts of the application.
- **Testability**: Test service management independently of data providers.
- **Maintainability**: Simplifies the codebase by centralizing service management logic.
- **Real-Time Updates**: Provides accurate and timely status updates for all services.

---

## Production Readiness & Roadmap (work with what we have)

Current status note: the existing `gpscentcom_server` is a solid prototype suitable for local development and demonstration (device WebSocket ingest + in-memory `Store` + REST read APIs). It is NOT yet hardened for production. Below is a prioritized roadmap of production-grade tasks. The goal is to make non-destructive, opt-in changes so the existing in-memory store remains the default unless a customer enables a sink/plugin.

High-priority (fast, high-impact)
- Enforce authentication on REST and WebSocket endpoints (Authorization: Bearer <token>) and validate tokens early.
- Add a broadcast subscription endpoint for dashboard clients (`/ws/telemetry` or SSE `/sse/telemetry`) and wire device ingest to publish updates.
- Add basic observability: structured JSON logs and a Prometheus `/metrics` endpoint exposing message rates, active connections, and handler latencies.

Medium-priority (reliability & integrations)
- Implement a sink/plugin API with a webhook sink prototype (register/deregister sinks via `POST /sinks`) and a background delivery worker with retry/backoff and DLQ.
- Scaffold an optional Postgres/PostGIS persistence plugin (opt-in) with migrations and a minimal schema for telemetry (vehicle_id, geom, speed, heading, timestamp, raw_payload).
- Improve `/health` to return component-level statuses (store, sinks queue, worker health, uptime).

Lower-priority (ops & security hardening)
- Provide TLS/mTLS guidance and sample reverse-proxy configuration (nginx), tighten CORS, and add rate-limiting middleware.
- Add secrets management guidance (env + Vault) and validate required configuration at startup.
- Containerize the service, add readiness/liveness probes, and provide deployment manifests (k8s or docker-compose) and a short runbook.

Testing & CI
- Add unit tests for packet parsing, connector logic, and sink delivery worker; integration tests using a mock gpscentcom server; CI pipeline to run lint/build/tests on PRs.

Operational notes — work with what we have
- All new features should be opt-in. The in-memory `Store` remains default; sinks/plugins are explicitly enabled by customers.
- Start with auth + broadcast WS + basic metrics. These provide immediate security and real-time UX improvements with minimal intrusion.
- If diagnosing Strapi/Simulator interactions, temporarily set `spawn_console=false` in `config.ini` or enable capturing stdout/stderr so the launcher can log service boot output for debugging.

If you'd like, I can start by implementing auth enforcement and the broadcast WebSocket endpoint, then add Prometheus metrics next. Tell me which pieces to implement first and I will open a small PR with focused commits.
