# Vehicle Simulator - TODO & Progress Tracking

**Project**: ArkNet Fleet Manager & Vehicle Simulator
**Branch**: branch-0.0.3.3
**Date**: November 8, 2025
**Status**: 🚀 Production-Grade Dashboard Implementation (Build fix pending verification)
**Current Phase**: Component Architecture, Service Management & Route Validation

> **📌 Key Documentation**:
> - `CONTEXT.md` - Complete project context, architecture, all technical details
> - `TODO.md` - Task tracking, progress, next steps

**Execution Priority**:

## 🆕 Recent Updates (Nov 9, 2025)

**CRITICAL ROUTE GEOMETRY DOCUMENTATION ADDED**: 
- 🚨 Created `ROUTE_GEOMETRY_BIBLE.md` - THE DEFINITIVE GUIDE for route geometry
- Database route_shapes + shapes tables are FRAGMENTED (27 segments, NO ordering)
- GeoJSON files in `arknet_transit_simulator/data/` are the SINGLE SOURCE OF TRUTH
- Route 1: 418 coordinates, 27 segments, 13.347 km total distance
- **READ ROUTE_GEOMETRY_BIBLE.md BEFORE TOUCHING ANY ROUTE CODE**

Scaffolded user-tiered dashboards: Created distinct dashboards for Customer, Operator, Agency, and Admin, each with dedicated landing pages and navigation. Main landing page now features clear cards linking to each dashboard.
Migrated service management to Admin dashboard and fixed build errors.
Refactored navigation for user-tiered access and future extensibility.
Ensured all changes are non-breaking and additive, preserving existing functionality.
Established foundation for real-time telemetry, role-based navigation, and future MVP features.

### New Pending Tasks
- [x] Scaffold user-tiered dashboards (Customer, Operator, Agency, Admin)
- [x] **DOCUMENT ROUTE GEOMETRY PROPERLY** - See ROUTE_GEOMETRY_BIBLE.md
- [ ] Create API endpoint to serve GeoJSON route geometry directly (as single source of truth)
- [ ] Update dispatcher to use GeoJSON-based route endpoint
- [ ] Re-run dashboard build and confirm StatusBadge enum completeness.
- [ ] Decide engine auto-stop strategy (recommend Simulator-level watcher).
- [ ] Implement chosen auto-stop with event emission (`vehicle:arrived-at-destination`).
- [ ] Add regression test for route distance = 13.347 km ± 0.5 km (Route 1).
- [ ] Add dashboard differentiation styling for UNHEALTHY vs FAILED.

## 📡 Telemetry Integration (GPSCentCom)

Priority: High — realtime vehicle telemetry is required for live map, analytics and persistence.

Planned tasks (high level):
- [ ] Define telemetry JSON schema, TypeScript interfaces and Pydantic models
- [ ] Create Telemetry Gateway (FastAPI) with WebSocket broadcast + REST ingestion
- [ ] Implement GPSCentCom connector (subscribe to gpscentcom_server feed, normalize messages)
- [ ] Persistence: Postgres/PostGIS schema + batch writer
- [ ] Dashboard client provider/hook (WebSocket with reconnection and SSE fallback)
- [ ] Map layer + UI components for realtime vehicles
- [ ] Tests, auth, metrics and rollout

Acceptance criteria for MVP:
- Realtime feed from `gpscentcom_server` is received by the connector and forwarded to the Telemetry Gateway.
- Gateway broadcasts telemetry over WebSocket to connected dashboard clients with <200ms median latency (local test).
- Recent telemetry is persisted to Postgres/PostGIS and retrievable via REST (latest position / history).

See `CONTEXT.md` (Telemetry section) for full integration architecture and implementation notes.
 
## 🔐 Production Readiness Checklist (work with what we have)

These tasks are prioritized to make `gpscentcom_server` and the Telemetry Gateway production-ready while preserving the current in-memory default and making non-destructive, opt-in changes.

- [ ] Enforce auth on REST and WebSocket endpoints (Authorization: Bearer <token>) — reject unauthorized requests early.
- [ ] Add broadcast subscription endpoint (`/ws/telemetry` or SSE `/sse/telemetry`) to stream device updates to dashboard clients.
- [ ] Implement sink/plugin API (register/deregister webhooks) and a webhook sink prototype with retry and DLQ — opt-in only, no default Postgres persistence.
- [ ] Improve logging & metrics: structured JSON logs, add `/metrics` Prometheus endpoint, and extend `/health` with component-level checks.
- [ ] Persistence plugin (optional): scaffold Postgres/PostGIS plugin and migrations; keep in-memory store as the default unless a sink/plugin is enabled.
- [ ] Security hardening: TLS guidance, CORS tightening, rate-limiting middleware, input size limits, and dependency pinning.
- [ ] Secrets & config: promote secure secret management (env + Vault) and validation for required settings.
- [ ] Operationalization: container image, readiness/liveness probes, deployment manifests (k8s/docker-compose), and runbook.
- [ ] Tests & CI: unit tests for parser/connector, integration tests with a mock gpscentcom server, and CI that runs lint/build/tests.
- [ ] Docs & onboarding: update `CONTEXT.md`, README, and create a short runbook explaining how to enable sinks and configure auth.

Notes:
- All additions should be non-destructive and opt-in. The in-memory `Store` remains the default unless a customer enables a sink/plugin.
- Start with auth enforcement + broadcast endpoint + basic metrics (high impact, low effort). The webhook sink prototype is the next priority.
## ✅ **COMPLETED: Production Dashboard Foundation**

### Component Architecture
- [x] **Theme System**: Complete light/dark theme with design tokens
- [x] **UI Component Library**: Button, Card, Badge, StatusBadge components
- [x] **Layout Components**: DashboardLayout with header and theme toggle
- [x] **Feature Components**: ServiceCard for service management
- [x] **Landing Components**: HeroSection, FeatureCard, FeatureGrid
- [x] **Component Organization**: Logical folder structure (ui/, layout/, features/, landing/)
- [x] **Import Path Fixes**: Corrected relative imports after reorganization

### Service Management
- [x] **ServiceManager Provider**: WebSocket + REST API integration
- [x] **Real-time Updates**: Live service status via WebSocket
- [x] **Launcher Integration**: FastAPI backend on port 7000
- [x] **Service Controls**: Start/stop services with dependency checking
- [x] **Dispatcher Full Route Shapes**: Fetch & concatenate ALL shapes (Route 1 length confirmed)

### Routing & Navigation
- [x] **Landing Page**: Professional welcome page with feature cards
- [x] **Services Page**: Service management dashboard at `/services`
- [x] **Navigation Structure**: Clear routing hierarchy

## 🚧 **IN PROGRESS: Dashboard Enhancement**

### UI/UX Improvements
- [x] **Card Consistency**: Uniform sizing (280px height), 3D effects, hover animations
- [x] **Compact Design**: Reduced padding, optimized spacing, better information density
- [x] **Global Theme**: Consistent color scheme across entire Next.js app
- [x] **Navigation System**: Header navigation with active state highlighting
- [x] **Service Cards**: Enhanced with icons, monospace port/PID display, improved status badges
- [x] **Empty States**: Professional empty state design with clear messaging
- [x] **Controls Panel**: Styled control panel with gradient title and consistent theming
- [x] **StatusBadge UNHEALTHY Fix**: Added missing enum mapping; build verification pending
- [x] **Route Distance Validation**: Confirmed traversal metrics vs speed readings
- [x] **Driver Auto-Stop Revert**: Restored original driver without auto-stop logic
- [ ] **Responsive Design**: Mobile-friendly layouts and breakpoints
- [ ] **Loading States**: Skeleton loaders and progress indicators
- [ ] **Error Handling**: User-friendly error messages and recovery
- [ ] **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### Feature Expansion
- [ ] **Fleet Monitor**: Real-time vehicle tracking dashboard
- [ ] **Route Management**: Route configuration and depot management
- [ ] **Analytics Dashboard**: Performance metrics and reporting
- [ ] **System Health**: Platform monitoring and diagnostics

## 📋 **BACKLOG: Future Enhancements**

### Advanced Components
- [ ] **Data Tables**: Sortable, filterable tables for large datasets
- [ ] **Charts & Graphs**: Performance visualization components
- [ ] **Maps Integration**: Geospatial visualization for routes
- [ ] **Modal System**: Reusable modal dialogs and forms

### Backend Integration
- [ ] **GraphQL Provider**: Strapi integration for data management
- [ ] **Telemetry Provider**: GPSCentCom data streaming
- [ ] **Authentication**: User management and security
- [ ] **API Caching**: Performance optimization for data fetching
