# Task 4209: Redis Health Detection and Reporting

## Implementation Plan

### Overview
Implement Redis health detection and reporting in the backend service registry and expose it to the dashboard frontend for real-time monitoring.

---

## 1. Requirements & Acceptance Criteria

### Health Status Definitions
- **HEALTHY**: Redis connection successful, PING responds within 100ms
- **UNHEALTHY**: Redis connection fails or latency > 100ms  
- **NOT_CONFIGURED**: Redis URL/config not set (graceful degradation)
- **UNREACHABLE**: Redis host unreachable or connection timeout

### API Response Format
```json
{
  "services": [
    {
      "name": "redis",
      "state": "healthy" | "unhealthy" | "not_configured",
      "message": "Connected" | "Connection failed: <error>",
      "latency_ms": 12.5,
      "port": 6379,
      "host": "localhost"
    }
  ]
}
```

### Acceptance Criteria
1. Backend `/api/services/status` includes Redis health
2. Frontend dashboard displays Redis card with health status
3. Real-time updates via Socket.IO when Redis status changes
4. Graceful degradation when Redis not configured
5. Health check every 30 seconds (configurable)
6. Unit tests cover all health states

---

## 2. Backend Architecture Design

### File Structure
```
services/host_server/
  ├── service_registry.py          # Add Redis health tracking
  ├── routes/services.py            # Already exposes /status
  ├── health/
  │   ├── __init__.py
  │   └── redis_health.py          # NEW: Redis health check logic
  ├── config.py                     # Add Redis config
  └── tests/
      └── test_redis_health.py      # NEW: Redis health tests
```

### Redis Health Check Module
**File**: `services/host_server/health/redis_health.py`

```python
"""
Redis Health Check
==================
Performs health checks on Redis instance.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from enum import Enum
import time

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisHealthStatus(str, Enum):
    """Redis health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"
    UNREACHABLE = "unreachable"


class RedisHealthChecker:
    """Performs Redis health checks"""
    
    def __init__(self, redis_url: Optional[str] = None, latency_threshold_ms: float = 100.0):
        """
        Initialize Redis health checker
        
        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379")
            latency_threshold_ms: Latency threshold for unhealthy status
        """
        self.redis_url = redis_url
        self.latency_threshold_ms = latency_threshold_ms
        self.client: Optional[aioredis.Redis] = None
        
    async def check_health(self) -> Dict[str, Any]:
        """
        Check Redis health
        
        Returns:
            Dict with status, message, latency, etc.
        """
        # Check if Redis is configured
        if not self.redis_url or not REDIS_AVAILABLE:
            return {
                "name": "redis",
                "state": RedisHealthStatus.NOT_CONFIGURED.value,
                "message": "Redis not configured or library not installed",
                "latency_ms": None,
                "host": None,
                "port": None
            }
        
        try:
            # Create connection if needed
            if not self.client:
                self.client = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5.0
                )
            
            # Measure ping latency
            start_time = time.perf_counter()
            response = await self.client.ping()
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Parse host/port from URL
            host, port = self._parse_redis_url(self.redis_url)
            
            # Determine health status
            if response and latency_ms < self.latency_threshold_ms:
                return {
                    "name": "redis",
                    "state": RedisHealthStatus.HEALTHY.value,
                    "message": f"Connected (latency: {latency_ms:.1f}ms)",
                    "latency_ms": round(latency_ms, 2),
                    "host": host,
                    "port": port
                }
            else:
                return {
                    "name": "redis",
                    "state": RedisHealthStatus.UNHEALTHY.value,
                    "message": f"High latency: {latency_ms:.1f}ms",
                    "latency_ms": round(latency_ms, 2),
                    "host": host,
                    "port": port
                }
                
        except asyncio.TimeoutError:
            return {
                "name": "redis",
                "state": RedisHealthStatus.UNREACHABLE.value,
                "message": "Connection timeout",
                "latency_ms": None,
                "host": None,
                "port": None
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "name": "redis",
                "state": RedisHealthStatus.UNHEALTHY.value,
                "message": f"Connection failed: {str(e)}",
                "latency_ms": None,
                "host": None,
                "port": None
            }
    
    def _parse_redis_url(self, url: str) -> tuple[Optional[str], Optional[int]]:
        """Parse host and port from Redis URL"""
        try:
            # Simple parsing: redis://host:port
            if "://" in url:
                parts = url.split("://")[1].split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 6379
                return host, port
        except:
            pass
        return None, None
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
```

---

## 3. Backend Implementation Steps

### Step 3.1: Update Configuration
**File**: `services/host_server/config.py`

Add Redis configuration:
```python
# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", None)  # None = not configured
REDIS_HEALTH_CHECK_INTERVAL = float(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30.0"))
REDIS_LATENCY_THRESHOLD_MS = float(os.getenv("REDIS_LATENCY_THRESHOLD_MS", "100.0"))
```

### Step 3.2: Integrate into Service Registry
**File**: `services/host_server/service_registry.py`

Add Redis health tracking:
```python
from .health.redis_health import RedisHealthChecker, RedisHealthStatus
from .config import config

class ServiceRegistry:
    def __init__(self, project_root: Path):
        # ... existing code ...
        self.redis_health_checker = RedisHealthChecker(
            redis_url=config.REDIS_URL,
            latency_threshold_ms=config.REDIS_LATENCY_THRESHOLD_MS
        )
        self.redis_status: Dict[str, Any] = {}
        self._start_redis_health_monitoring()
    
    def _start_redis_health_monitoring(self):
        """Start periodic Redis health checks"""
        asyncio.create_task(self._monitor_redis_health())
    
    async def _monitor_redis_health(self):
        """Periodically check Redis health"""
        while True:
            try:
                self.redis_status = await self.redis_health_checker.check_health()
                logger.debug(f"Redis health: {self.redis_status['state']}")
            except Exception as e:
                logger.error(f"Redis health monitoring error: {e}")
            
            await asyncio.sleep(config.REDIS_HEALTH_CHECK_INTERVAL)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all services including Redis"""
        statuses = [self.get_service_status(name) for name in self.services.keys()]
        
        # Add Redis status if configured
        if self.redis_status:
            statuses.append(self.redis_status)
        
        return {"services": statuses}
```

### Step 3.3: Update Routes (Already Done!)
The existing `/api/services/status` endpoint will automatically include Redis status via `service_registry.get_all_status()`.

---

## 4. Testing Plan

### Test Cases

#### Test 4.1: Redis Healthy
**Setup**: Redis running on localhost:6379  
**Expected**: `{"state": "healthy", "latency_ms": < 100}`

#### Test 4.2: Redis Unhealthy (High Latency)
**Setup**: Simulate slow Redis (network delay)  
**Expected**: `{"state": "unhealthy", "message": "High latency: XXXms"}`

#### Test 4.3: Redis Unreachable
**Setup**: Redis stopped or wrong host  
**Expected**: `{"state": "unreachable", "message": "Connection timeout"}`

#### Test 4.4: Redis Not Configured
**Setup**: `REDIS_URL=None`  
**Expected**: `{"state": "not_configured", "message": "Redis not configured..."}`

### Unit Test File
**File**: `services/host_server/tests/test_redis_health.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from health.redis_health import RedisHealthChecker, RedisHealthStatus


@pytest.mark.asyncio
async def test_redis_healthy():
    """Test Redis healthy state"""
    checker = RedisHealthChecker("redis://localhost:6379")
    
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        result = await checker.check_health()
        
        assert result["state"] == RedisHealthStatus.HEALTHY.value
        assert result["latency_ms"] < 100
        assert result["host"] == "localhost"
        assert result["port"] == 6379


@pytest.mark.asyncio
async def test_redis_not_configured():
    """Test Redis not configured"""
    checker = RedisHealthChecker(None)
    
    result = await checker.check_health()
    
    assert result["state"] == RedisHealthStatus.NOT_CONFIGURED.value
    assert result["latency_ms"] is None


@pytest.mark.asyncio
async def test_redis_connection_timeout():
    """Test Redis unreachable (timeout)"""
    checker = RedisHealthChecker("redis://invalid:6379")
    
    with patch('redis.asyncio.from_url') as mock_redis:
        mock_redis.side_effect = TimeoutError()
        
        result = await checker.check_health()
        
        assert result["state"] == RedisHealthStatus.UNREACHABLE.value
```

---

## 5. Frontend Integration

### Step 5.1: ServiceManager Updates
**File**: `arknet_fleet_manager/dashboard/src/features/services/providers/ServiceManager.ts`

No changes needed - already fetches from `/services` API and includes all returned services.

### Step 5.2: ServiceCard Display
**File**: `arknet_fleet_manager/dashboard/src/components/features/ServiceCard.tsx`

Already handles any service with `state` property. Redis will automatically display with:
- Green card for `healthy`
- Red card for `unhealthy` or `unreachable`
- Gray card for `not_configured`

### Step 5.3: Real-time Updates
Backend Socket.IO already emits `service_status` events. Add Redis status broadcasting in service registry:

```python
# In ServiceRegistry._monitor_redis_health()
async def _monitor_redis_health(self):
    while True:
        old_status = self.redis_status.get("state")
        self.redis_status = await self.redis_health_checker.check_health()
        
        # Broadcast if status changed
        if self.redis_status.get("state") != old_status:
            await socketio.emit('service_status', self.redis_status)
        
        await asyncio.sleep(config.REDIS_HEALTH_CHECK_INTERVAL)
```

---

## 6. Deployment Checklist

- [ ] Install `redis-py` or `aioredis` in host_server requirements
- [ ] Add `.env` variables for Redis config
- [ ] Create `health/` module with `redis_health.py`
- [ ] Update `service_registry.py` to include Redis health
- [ ] Write and run unit tests
- [ ] Test with Redis running, stopped, and not configured
- [ ] Verify dashboard displays Redis card correctly
- [ ] Test real-time updates via Socket.IO
- [ ] Update documentation

---

## 7. Expected Results Summary

| Scenario | Backend Response | Frontend Display |
|----------|------------------|------------------|
| Redis running | `state: "healthy"` | Green card, "Connected" |
| Redis stopped | `state: "unreachable"` | Red card, "Connection timeout" |
| High latency | `state: "unhealthy"` | Red card, "High latency: XXms" |
| Not configured | `state: "not_configured"` | Gray card, "Redis not configured" |
| Connection error | `state: "unhealthy"` | Red card, error message |

---

## 8. Dependencies

### Backend
- `redis-py` or `aioredis` (async Redis client)
- FastAPI (already present)
- Python 3.9+ (already present)

### Frontend
- No new dependencies (existing ServiceManager handles it)

---

## Next Steps

1. Mark Task 1 complete (Requirements defined ✓)
2. Begin Task 2: Create `health/redis_health.py` module
3. Proceed through implementation tasks sequentially
