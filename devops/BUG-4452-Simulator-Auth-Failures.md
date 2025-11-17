# BUG-4452: Vehicle Simulator HTTP 403 Authentication Failures

## Work Item Hierarchy
```
Epic 4386: Arknet Transit Query
└─ Feature 4387: Role-Based Access Control
   └─ User Story 4343: Enforce JWT authentication for all user-specific APIs
      └─ Bug 4452: Vehicle simulator fails with HTTP 403 errors on multiple Strapi endpoints
         ├─ Task 4453: Implement centralized Strapi authentication client for vehicle simulator
         ├─ Task 4454: Add integration tests for centralized Strapi client
         └─ Task 4455: Document centralized Strapi client architecture and usage
```

---

## Bug Description

### Summary
The vehicle simulator fails to start properly due to HTTP 403 (Forbidden) errors when multiple internal services attempt to access Strapi API endpoints. Each service independently authenticates, creating fragmented authentication logic and multiple failure points.

### Severity
**High** - Prevents simulator from operating correctly

### Components Affected
- `arknet_transit_simulator/core/dispatcher.py` - Route geometry fetching
- `arknet_transit_simulator/services/config_service.py` - Operational configuration loading
- `arknet_transit_simulator/services/commuter_http_client.py` - Commuter service connection

---

## Reproduction Steps

### Prerequisites
1. PostgreSQL database `arknettransit` running on localhost:5432
2. Strapi CMS running on http://localhost:1337
3. Redis server running on localhost:6379
4. Valid JWT credentials configured in `config.ini`:
   ```ini
   [strapi]
   username = vehicle_simulator
   password = Ga25w123
   ```

### Steps to Reproduce
```powershell
cd E:\projects\github\vehicle_simulator
python -m arknet_transit_simulator --mode depot
```

### Expected Behavior
```
2025-11-17 15:49:29,505 | INFO | [StrapiStrategy] ✅ Route 1 has 415 GPS coordinates
2025-11-17 15:49:29,592 | INFO | ═══ DEPOT INVENTORY ═══
2025-11-17 15:49:29,592 | INFO | [MainDepot] Complete Depot Inventory:
2025-11-17 15:49:29,593 | INFO |   • Total vehicles in depot: 1
2025-11-17 15:49:29,593 | INFO |   • Active vehicles: 1 (operational)
2025-11-17 15:49:31,261 | INFO | 👤 Starting driver: Jane Doe → ZR102 (active) → 1
2025-11-17 15:49:31,682 | INFO | 👤 DRIVER STATUS:
2025-11-17 15:49:31,682 | INFO |   ✅ Active: 1 drivers operating vehicles
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
```

### Actual Behavior
```
2025-11-17 15:49:29,505 | ERROR | [StrapiStrategy] Failed to fetch route 1: HTTP 403
2025-11-17 15:54:21,582 | ERROR | [ConfigService] Failed to refresh: HTTP 403
2025-11-17 15:54:24,254 | ERROR | [CommuterServiceClient] Connection failed: All connection attempts failed too
2025-11-17 15:49:29,592 | INFO | ═══ DEPOT INVENTORY ═══
2025-11-17 15:49:29,593 | INFO |   • Active vehicles: 1 (operational)
2025-11-17 15:49:31,261 | INFO | 👤 Starting driver: Jane Doe → ZR102 (active) → 1
2025-11-17 15:49:31,681 | ERROR | [StrapiStrategy] Failed to fetch route 1: HTTP 403
2025-11-17 15:49:31,681 | ERROR | No route geometry available for 1
2025-11-17 15:49:31,682 | INFO | 👤 DRIVER STATUS:
2025-11-17 15:49:31,682 | INFO |   ✅ Active: 0 drivers operating vehicles
2025-11-17 15:49:31,683 | INFO |   🔴 Idle: 0 drivers (vehicles not operational)
2025-11-17 15:49:31,683 | INFO |   📊 Total: 0 drivers in depot
2025-11-17 15:49:31,683 | WARNING | No drivers started successfully
```

---

## Root Cause Analysis

### Problem 1: Fragmented Authentication Architecture
**Current State:**
```python
# dispatcher.py creates its own auth client
class StrapiStrategy:
    def __init__(self, api_base_url, credentials):
        self.auth_client = AuthClient(credentials)
        self.session = aiohttp.ClientSession()

# config_service.py creates its own session
class ConfigurationService:
    def __init__(self):
        self._session = aiohttp.ClientSession()
        # No authentication mechanism!

# commuter_http_client.py connects independently
class CommuterServiceClient:
    def __init__(self, base_url):
        self.client = httpx.AsyncClient()
        # Different service, but shows pattern
```

**Issues:**
1. ❌ Multiple authentication instances (dispatcher, config_service)
2. ❌ Inconsistent auth header management
3. ❌ No shared session/connection pooling
4. ❌ Duplicate error handling logic
5. ❌ No centralized credential rotation
6. ❌ ConfigService has no auth at all

### Problem 2: Strapi v5 Users-Permissions Enforcement
Strapi v5 enforces users-permissions plugin on ALL content-type routes, even with `auth: false` configured. This affects:
- `/api/routes/:routeName/geometry` - Route geometry endpoint
- `/api/operational-configurations` - Configuration data endpoint

**Workaround Applied (Temporary):**
Custom route registration in Strapi `src/index.ts` with manual JWT verification for route geometry:
```typescript
strapi.server.routes([{
  method: 'GET',
  path: '/api/routes/:routeName/geometry',
  handler: async (ctx: any, next: any) => {
    // Manually decode JWT and authenticate
    const token = authHeader.substring(7);
    const decoded = await strapi.plugin('users-permissions').service('jwt').verify(token);
    const user = await strapi.entityService.findOne('plugin::users-permissions.user', decoded.id);
    ctx.state.user = user;
    const controller = strapi.controller('api::route.route');
    return controller.getGeometry(ctx, next);
  },
  config: { auth: false }
}]);
```

This fixed route geometry but operational-configurations still fails.

---

## Proposed Solution

### Architecture: Centralized Strapi Authentication Client

Create a single source of truth for all Strapi API access:

```python
# arknet_transit_simulator/services/strapi_client.py

class StrapiClient:
    """
    Centralized authenticated HTTP client for Strapi API access.
    
    Features:
    - Single authentication point (JWT)
    - Shared aiohttp session and connection pool
    - Automatic token refresh
    - Consistent error handling
    - Request/response logging
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
    async def initialize(self):
        """Initialize session and authenticate"""
        self._session = aiohttp.ClientSession()
        await self._authenticate()
        
    async def _authenticate(self):
        """Authenticate and obtain JWT token"""
        async with self._session.post(
            f"{self.base_url}/api/auth/local",
            json={"identifier": self.username, "password": self.password}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self._token = data["jwt"]
                self._token_expiry = datetime.now() + timedelta(hours=24)
                logger.info("[StrapiClient] Authenticated successfully")
            else:
                raise AuthenticationError(f"Auth failed: HTTP {response.status}")
                
    async def _ensure_authenticated(self):
        """Check token validity and refresh if needed"""
        if not self._token or datetime.now() >= self._token_expiry:
            await self._authenticate()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {self._token}"}
        
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated GET request"""
        await self._ensure_authenticated()
        async with self._session.get(
            f"{self.base_url}{endpoint}",
            headers=self._get_headers(),
            **kwargs
        ) as response:
            if response.status == 403:
                logger.error(f"[StrapiClient] 403 Forbidden: {endpoint}")
                raise PermissionError(f"Access denied to {endpoint}")
            response.raise_for_status()
            return await response.json()
            
    async def get_route_geometry(self, route_code: str) -> Dict[str, Any]:
        """Get route geometry data"""
        return await self.get(f"/api/routes/{route_code}/geometry")
        
    async def get_configurations(self, section: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get operational configurations"""
        params = {"pagination[pageSize]": 100}
        if section:
            params["filters[section][$eq]"] = section
        data = await self.get("/api/operational-configurations", params=params)
        return data.get("data", [])
        
    async def close(self):
        """Close session"""
        if self._session:
            await self._session.close()
```

### Refactor Existing Services

**dispatcher.py:**
```python
class StrapiStrategy:
    def __init__(self, strapi_client: StrapiClient):
        self.client = strapi_client  # Use shared client
        
    async def get_route_info(self, route_code: str) -> Optional[RouteInfo]:
        try:
            data = await self.client.get_route_geometry(route_code)
            return RouteInfo(
                route_id=route_code,
                route_name=data["routeName"],
                geometry={"type": "LineString", "coordinates": data["coordinates"]},
                distance_km=data["distanceKm"],
                coordinate_count=len(data["coordinates"])
            )
        except Exception as e:
            logger.error(f"[StrapiStrategy] Error: {e}")
            return None
```

**config_service.py:**
```python
class ConfigurationService:
    def __init__(self, strapi_client: StrapiClient):
        self.client = strapi_client  # Use shared client
        
    async def refresh(self):
        try:
            configs = await self.client.get_configurations()
            # Process configs...
        except Exception as e:
            logger.error(f"[ConfigService] Error: {e}")
```

**simulator.py initialization:**
```python
async def initialize(self):
    # Create single Strapi client
    self.strapi_client = StrapiClient(
        base_url=self.config.infrastructure.strapi_url,
        username=self.config.infrastructure.strapi_username,
        password=self.config.infrastructure.strapi_password
    )
    await self.strapi_client.initialize()
    
    # Pass to all services
    self.dispatcher = Dispatcher(strapi_client=self.strapi_client)
    self.config_service = ConfigurationService(strapi_client=self.strapi_client)
```

---

## Implementation Plan

### Task 4453: Implement Centralized Strapi Client

**Acceptance Criteria:**
- ✅ Create `arknet_transit_simulator/services/strapi_client.py`
- ✅ Implement authentication with JWT
- ✅ Implement token refresh logic
- ✅ Implement typed methods for route geometry, configurations
- ✅ Add comprehensive error handling
- ✅ Add request/response logging
- ✅ Refactor `dispatcher.py` to use centralized client
- ✅ Refactor `config_service.py` to use centralized client
- ✅ Update `simulator.py` initialization

**Files to Modify:**
1. `arknet_transit_simulator/services/strapi_client.py` (NEW)
2. `arknet_transit_simulator/core/dispatcher.py` (REFACTOR)
3. `arknet_transit_simulator/services/config_service.py` (REFACTOR)
4. `arknet_transit_simulator/simulator.py` (UPDATE)

### Task 4454: Add Integration Tests

**Test Cases:**
```python
# tests/integration/test_strapi_client.py

async def test_authentication():
    """Test JWT authentication"""
    client = StrapiClient(STRAPI_URL, USERNAME, PASSWORD)
    await client.initialize()
    assert client._token is not None
    await client.close()

async def test_get_route_geometry():
    """Test route geometry endpoint"""
    client = StrapiClient(STRAPI_URL, USERNAME, PASSWORD)
    await client.initialize()
    data = await client.get_route_geometry("1")
    assert data["routeName"] == "1"
    assert len(data["coordinates"]) == 415
    assert data["distanceKm"] > 13.0
    await client.close()

async def test_get_configurations():
    """Test operational configurations endpoint"""
    client = StrapiClient(STRAPI_URL, USERNAME, PASSWORD)
    await client.initialize()
    configs = await client.get_configurations()
    assert len(configs) > 0
    assert all("section" in c and "parameter" in c for c in configs)
    await client.close()

async def test_token_refresh():
    """Test automatic token refresh"""
    client = StrapiClient(STRAPI_URL, USERNAME, PASSWORD)
    await client.initialize()
    old_token = client._token
    client._token_expiry = datetime.now() - timedelta(seconds=1)
    await client.get_route_geometry("1")
    assert client._token != old_token
    await client.close()

async def test_403_error_handling():
    """Test proper handling of 403 errors"""
    client = StrapiClient(STRAPI_URL, "invalid", "invalid")
    with pytest.raises(AuthenticationError):
        await client.initialize()
```

**Acceptance Criteria:**
- ✅ 100% code coverage for `strapi_client.py`
- ✅ Tests pass for authentication, route geometry, configurations
- ✅ Tests verify token refresh logic
- ✅ Tests verify error handling

### Task 4455: Documentation

**Deliverables:**
1. Update `arknet_transit_simulator/README.md` with architecture diagram
2. Add docstrings to all `strapi_client.py` methods
3. Create `docs/STRAPI_CLIENT_GUIDE.md` with usage examples
4. Update `CONTEXT.md` with authentication architecture

---

## Verification

### Before Fix (Current Behavior)
```powershell
PS E:\projects\github\vehicle_simulator> python -m arknet_transit_simulator --mode depot
2025-11-17 15:49:29,505 | ERROR | [StrapiStrategy] Failed to fetch route 1: HTTP 403
2025-11-17 15:54:21,582 | ERROR | [ConfigService] Failed to refresh: HTTP 403
2025-11-17 15:49:31,681 | ERROR | No route geometry available for 1
2025-11-17 15:49:31,683 | WARNING | No drivers started successfully
```

### After Fix (Expected Behavior)
```powershell
PS E:\projects\github\vehicle_simulator> python -m arknet_transit_simulator --mode depot
2025-11-17 16:00:00,000 | INFO | [StrapiClient] Authenticated successfully
2025-11-17 16:00:00,100 | INFO | [StrapiStrategy] ✅ Route 1 has 415 GPS coordinates
2025-11-17 16:00:00,200 | INFO | [StrapiStrategy] Distance: 13.39 km
2025-11-17 16:00:00,300 | INFO | [ConfigService] Refreshed 42 configurations
2025-11-17 16:00:00,400 | INFO | ═══ DEPOT INVENTORY ═══
2025-11-17 16:00:00,500 | INFO |   • Active vehicles: 1 (operational)
2025-11-17 16:00:02,000 | INFO | 👤 Starting driver: Jane Doe → ZR102 (active) → 1
2025-11-17 16:00:02,100 | INFO | 👤 DRIVER STATUS:
2025-11-17 16:00:02,100 | INFO |   ✅ Active: 1 drivers operating vehicles
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
```

---

## Success Metrics

1. **Authentication Success Rate**: 100% (no 403 errors on startup)
2. **Code Duplication**: Reduced from 3 auth implementations to 1
3. **Maintainability**: Single point for credential changes
4. **Error Recovery**: Automatic token refresh
5. **Performance**: Shared connection pool reduces overhead

---

## Related Work Items

- **4344**: Update Strapi permissions for all relevant endpoints
- **4345**: Validate user context in backend services
- **4346**: Audit and restrict public endpoints
- **4243**: Create API endpoint to serve GeoJSON route geometry directly ✅ (Completed)
- **4244**: Update dispatcher to use GeoJSON-based route endpoint ✅ (Completed)

---

## Notes

### Strapi v5 Workaround Status
- ✅ Route geometry endpoint: Custom route with manual JWT auth
- ❌ Operational configurations endpoint: Still needs custom route or centralized client

### Commuter Service Error
The `CommuterServiceClient` connection failure is unrelated to Strapi auth - it's attempting to connect to a separate microservice (commuter_service) at http://localhost:8002 which may not be running. This is outside the scope of this bug fix.

---

**Created**: 2025-11-17  
**Last Updated**: 2025-11-17  
**Status**: Active  
**Assignee**: Guerilla Codester  
**Priority**: High
