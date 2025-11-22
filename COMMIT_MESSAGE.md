feat(telemetry): implement tiered RBAC filtering for real-time vehicle data

Implements role-based access control (RBAC) for telemetry data streaming via SSE endpoints.
Four-tier access model controls field visibility: public (10 fields), dispatcher (15 fields),
fleet_manager (16 fields), admin (17 fields). Hardcoded tier definitions eliminate database 
lookups for improved performance. All tiers validated with comprehensive test suite.

Resolves: Tiered telemetry access control requirement
Type: Feature
Scope: Authentication, Telemetry, Security
Impact: High - Enables production deployment with proper data access controls

## Changes

### Core Telemetry Filtering (gpscentcom_server/app/telemetry_filter.py)
- Added hardcoded tier-based field definitions (TIER_FIELDS) for four access levels
- Removed dependency on Strapi database lookups for tier field definitions
- Implemented efficient dictionary-based filtering that preserves field order
- Added debug logging to trace filtering operations for each tier

### Tier Definitions
**Public (unauthenticated)** - 10 fields:
- Basic tracking: lat, lon, speed, heading, timestamp, lastSeen
- Public identifiers: vehicleReg, route, driverName, conductorName
- Excludes: deviceId, driverId, internal operational data

**Dispatcher** - 15 fields:
- All public fields PLUS:
- Operational identifiers: deviceId, driverId, conductorId
- Operational data: startTime, logoutTime
- Excludes: extras (diagnostics)

**Fleet Manager** - 16 fields:
- All dispatcher fields PLUS:
- Diagnostics: extras field for troubleshooting

**Admin** - 17 fields:
- Complete access to all telemetry fields
- Full operational and diagnostic visibility

### UI Updates (arknet_fleet_manager/dashboard)
- Updated TelemetryTestComponent to display vehicleReg and driverName instead of deviceId
- Changed telemetry header format from "📍 GPS-ZR102" to "📍 ZR102 - Jane Doe"
- Improved public-facing display to hide internal device identifiers

### Authentication Flow
- Maintained JWT-based authentication through proxy server (port 7000)
- GPSCentCom server (port 5000) verifies JWT tokens via auth.py
- Principal extraction includes user tier from JWT claims
- Unauthenticated requests default to public tier filtering

### Testing
Created comprehensive test suite for tier verification:
- test_public_sse.py: Validates unauthenticated access (10 fields)
- test_dispatcher_sse.py: Validates dispatcher tier (15 fields, no extras)
- test_fleet_manager_sse.py: Validates fleet manager tier (16 fields with extras)
- test_admin_sse.py: Validates admin tier (full access)

All tests confirmed working with correct field counts and access levels.

### Database Updates
- Standardized tier names to lowercase (admin, dispatcher, fleet_manager)
- Linked user profiles to correct access tiers in Strapi
- Configured Strapi permissions for vehicle_simulator user to access vehicle data

### Bug Fixes
- Fixed PUBLIC_FIELDS to match actual DeviceState model field names
- Corrected field name mismatches (vehicle_id → deviceId, latitude → lat, etc.)
- Resolved server import issues by running as module (python -m gpscentcom_server)
- Fixed timezone import error in store.py debug logging

## Impact

### Security
- Prevents exposure of internal device identifiers to public users
- Implements proper role-based access control for sensitive operational data
- Separates diagnostic data access to fleet manager and admin tiers only

### User Experience
- Public users see clean, user-friendly vehicle tracking (vehicle reg, driver name)
- Dispatchers get operational data needed for fleet coordination
- Fleet managers access diagnostics for troubleshooting
- Admins maintain full system visibility

### Performance
- Hardcoded tier definitions eliminate database lookups for filtering
- Efficient dictionary comprehension for field filtering
- Real-time SSE streaming maintains performance across all tiers

## Testing Results

```
Public (unauthenticated):     10 fields ✓
Dispatcher:                   15 fields ✓ (no extras)
Fleet Manager:                16 fields ✓ (includes extras)
Admin (david):                17 fields ✓ (full access)
```

All tier tests passed with correct field visibility and access control.

## Related Files Modified
- gpscentcom_server/app/telemetry_filter.py
- gpscentcom_server/store.py (debug logging)
- gpscentcom_server/client_router.py (debug logging)
- arknet_fleet_manager/dashboard/src/core/telemetry/TelemetryTestComponent.tsx
- test_public_sse.py (created)
- test_dispatcher_sse.py (created)
- test_fleet_manager_sse.py (created)
- test_admin_sse.py (created)

## Breaking Changes
None - maintains backward compatibility with existing SSE clients.

## Migration Notes
No migration required. Existing public clients automatically use public tier filtering.
Authenticated clients must have valid JWT with tier claim in payload.
