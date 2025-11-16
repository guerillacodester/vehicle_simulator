"""
Redis Health Check
==================
Performs health checks on Redis instance using service-based management.
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

# Import RedisServiceManager for service-based health checking
try:
    from .redis_service_manager import RedisServiceManager
    SERVICE_MANAGER_AVAILABLE = True
except ImportError:
    SERVICE_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisHealthStatus(str, Enum):
    """Redis health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"
    UNREACHABLE = "unreachable"


class RedisHealthChecker:
    """Performs Redis health checks using service-based management"""

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

        # Initialize service manager for service-based health checking
        self.service_manager = RedisServiceManager() if SERVICE_MANAGER_AVAILABLE else None

    async def check_health(self) -> Dict[str, Any]:
        """
        Check Redis health using service-based management

        Returns:
            Dict with status, message, latency, etc.
        """
        # Check if Redis is configured
        if not self.redis_url or not REDIS_AVAILABLE:
            return {
                "name": "redis",
                "type": "dependency",
                "state": RedisHealthStatus.NOT_CONFIGURED.value,
                "message": "Redis not configured or library not installed",
                "latency_ms": None,
                "host": None,
                "port": None,
                "service_status": None
            }

        # FIRST: Check service status (instant, no polling)
        service_status = None
        if self.service_manager:
            try:
                service_info = self.service_manager.get_status()
                detected_info = self.service_manager.get_service_info()

                service_status = {
                    "exists": detected_info is not None and detected_info.exists,
                    "running": service_info.is_running,
                    "enabled": service_info.is_enabled,
                    "message": service_info.status_message
                }

                # If service exists but is not running, return service status immediately
                if service_status["exists"] and not service_info.is_running:
                    return {
                        "name": "redis",
                        "type": "dependency",
                        "state": RedisHealthStatus.UNHEALTHY.value,
                        "message": f"Redis service stopped: {service_info.status_message}",
                        "latency_ms": None,
                        "host": None,
                        "port": None,
                        "service_status": service_status
                    }

                # If service doesn't exist, log warning but continue with connection check
                if not service_status["exists"]:
                    logger.warning(f"Redis service not detected: {detected_info.reason if detected_info else 'No service info'}")

            except Exception as e:
                logger.warning(f"Service status check failed, falling back to connection check: {e}")

        # SECOND: Only attempt connection if service is running (or no service detected)
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
                status_message = f"Connected (latency: {latency_ms:.1f}ms)"
                if service_status and service_status.get("running"):
                    status_message += " - Service running"
                elif service_status and not service_status.get("exists"):
                    status_message += " - No service detected"

                return {
                    "name": "redis",
                    "type": "dependency",
                    "state": RedisHealthStatus.HEALTHY.value,
                    "message": status_message,
                    "latency_ms": round(latency_ms, 2),
                    "host": host,
                    "port": port,
                    "service_status": service_status
                }
            else:
                return {
                    "name": "redis",
                    "type": "dependency",
                    "state": RedisHealthStatus.UNHEALTHY.value,
                    "message": f"High latency: {latency_ms:.1f}ms",
                    "latency_ms": round(latency_ms, 2),
                    "host": host,
                    "port": port,
                    "service_status": service_status
                }

        except asyncio.TimeoutError:
            return {
                "name": "redis",
                "type": "dependency",
                "state": RedisHealthStatus.UNREACHABLE.value,
                "message": "Connection timeout",
                "latency_ms": None,
                "host": None,
                "port": None,
                "service_status": service_status
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "name": "redis",
                "type": "dependency",
                "state": RedisHealthStatus.UNHEALTHY.value,
                "message": f"Connection failed: {str(e)}",
                "latency_ms": None,
                "host": None,
                "port": None,
                "service_status": service_status
            }
    
    def _parse_redis_url(self, url: str) -> tuple:
        """Parse host and port from Redis URL"""
        try:
            # Simple parsing: redis://host:port
            if "://" in url:
                parts = url.split("://")[1].split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 6379
                return host, port
        except Exception:
            pass
        return None, None
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
