"""
Redis Service Manager - Unified Cross-Platform Redis Service Management
========================================================================

Provides a unified interface for managing Redis as an OS service on Linux (systemd)
and Windows (Windows Services), eliminating the need for polling and providing
automatic startup, health monitoring, and lifecycle management.
"""

import os
import platform
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

# Import OS adapters
try:
    if platform.system() == "Linux":
        from ..os_adapters import systemd as os_adapter
        ADAPTER_TYPE = "systemd"
    elif platform.system() == "Windows":
        from ..os_adapters import windows_service as os_adapter
        ADAPTER_TYPE = "windows"
    else:
        # Fallback for other systems
        ADAPTER_TYPE = "unknown"
        os_adapter = None
except ImportError:
    ADAPTER_TYPE = "none"
    os_adapter = None

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a detected service."""
    exists: bool
    name: Optional[str] = None
    scope: Optional[str] = None  # 'system', 'user' for Linux; None for Windows
    reason: Optional[str] = None


@dataclass
class ServiceStatus:
    """Current status of a service."""
    is_running: bool
    is_enabled: bool = False
    status_message: Optional[str] = None


class RedisServiceManager:
    """
    Unified Redis service manager for Linux and Windows.

    Provides a consistent API for:
    - Detecting Redis service installation
    - Checking service status
    - Starting/stopping services
    - Enabling auto-startup
    - Graceful error handling
    """

    def __init__(self, service_name: str = "redis"):
        """
        Initialize Redis service manager.

        Args:
            service_name: Base name to search for Redis service
        """
        self.service_name = service_name
        self.detected_service: Optional[ServiceInfo] = None
        self._adapter_available = os_adapter is not None

        if not self._adapter_available:
            logger.warning(f"OS adapter not available for {platform.system()}")

    def detect_service(self) -> ServiceInfo:
        """
        Detect if Redis is installed as a service on this system.

        Returns:
            ServiceInfo with detection results
        """
        if not self._adapter_available:
            return ServiceInfo(
                exists=False,
                reason=f"OS adapter not available for {platform.system()}"
            )

        # Try common Redis service names
        candidates = [
            "redis",           # Generic
            "redis-server",    # Linux common
            "Redis",           # Windows common
            "redis-service",   # Alternative
        ]

        for candidate in candidates:
            try:
                result = os_adapter.detect(candidate, {})
                if result.get("exists"):
                    service_info = ServiceInfo(
                        exists=True,
                        name=result.get("service_name") or result.get("unit_name"),
                        scope=result.get("scope"),
                        reason=None
                    )
                    self.detected_service = service_info
                    logger.info(f"Detected Redis service: {service_info.name} (scope: {service_info.scope})")
                    return service_info
            except Exception as e:
                logger.debug(f"Error detecting service {candidate}: {e}")
                continue

        # No service found
        self.detected_service = ServiceInfo(
            exists=False,
            reason="No Redis service found with common names"
        )
        logger.info("No Redis service detected on system")
        return self.detected_service

    def get_status(self) -> ServiceStatus:
        """
        Get current status of Redis service.

        Returns:
            ServiceStatus with current state
        """
        if not self.detected_service or not self.detected_service.exists:
            return ServiceStatus(
                is_running=False,
                status_message="Service not detected"
            )

        if not self._adapter_available:
            return ServiceStatus(
                is_running=False,
                status_message="OS adapter not available"
            )

        try:
            service_name = self.detected_service.name
            is_running = os_adapter.is_active(service_name)

            # For systemd, we can check if enabled
            is_enabled = False
            if ADAPTER_TYPE == "systemd":
                # Check if service is enabled (would start on boot)
                # This is a simplified check - in practice we'd need to check systemctl is-enabled
                pass  # TODO: Implement enablement check

            return ServiceStatus(
                is_running=is_running,
                is_enabled=is_enabled,
                status_message="Running" if is_running else "Stopped"
            )

        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return ServiceStatus(
                is_running=False,
                status_message=f"Error: {str(e)}"
            )

    def ensure_running(self) -> bool:
        """
        Ensure Redis service is running. Start if stopped.

        Returns:
            True if service is now running, False otherwise
        """
        if not self.detected_service or not self.detected_service.exists:
            logger.warning("Cannot ensure running: Redis service not detected")
            return False

        status = self.get_status()
        if status.is_running:
            logger.debug("Redis service already running")
            return True

        # Try to start the service
        try:
            service_name = self.detected_service.name
            result = os_adapter.start(service_name)

            if result.get("ok"):
                logger.info(f"Successfully started Redis service: {service_name}")
                # Wait a moment for startup
                import time
                time.sleep(2)
                # Verify it's now running
                new_status = self.get_status()
                return new_status.is_running
            else:
                logger.error(f"Failed to start Redis service: {result}")
                return False

        except Exception as e:
            logger.error(f"Error starting Redis service: {e}")
            return False

    def ensure_auto_start(self) -> bool:
        """
        Ensure Redis service is configured to start automatically on boot.

        Returns:
            True if auto-start is enabled, False otherwise
        """
        if not self.detected_service or not self.detected_service.exists:
            logger.warning("Cannot ensure auto-start: Redis service not detected")
            return False

        if not self._adapter_available:
            logger.warning("Cannot ensure auto-start: OS adapter not available")
            return False

        try:
            service_name = self.detected_service.name
            result = os_adapter.enable(service_name)

            if result.get("ok"):
                logger.info(f"Successfully enabled auto-start for Redis service: {service_name}")
                return True
            else:
                logger.error(f"Failed to enable auto-start for Redis service: {result}")
                return False

        except Exception as e:
            logger.error(f"Error enabling auto-start for Redis service: {e}")
            return False

    def stop_service(self) -> bool:
        """
        Stop the Redis service.

        Returns:
            True if successfully stopped, False otherwise
        """
        if not self.detected_service or not self.detected_service.exists:
            logger.warning("Cannot stop: Redis service not detected")
            return False

        try:
            service_name = self.detected_service.name
            result = os_adapter.stop(service_name)

            if result.get("ok"):
                logger.info(f"Successfully stopped Redis service: {service_name}")
                return True
            else:
                logger.error(f"Failed to stop Redis service: {result}")
                return False

        except Exception as e:
            logger.error(f"Error stopping Redis service: {e}")
            return False

    def restart_service(self) -> bool:
        """
        Restart the Redis service.

        Returns:
            True if successfully restarted, False otherwise
        """
        if not self.detected_service or not self.detected_service.exists:
            logger.warning("Cannot restart: Redis service not detected")
            return False

        logger.info(f"Restarting Redis service: {self.detected_service.name}")

        # Stop first
        if not self.stop_service():
            logger.warning("Failed to stop service during restart")
            return False

        # Wait a moment
        import time
        time.sleep(1)

        # Start again
        return self.ensure_running()

    def get_service_info(self) -> Optional[ServiceInfo]:
        """
        Get information about the detected Redis service.

        Returns:
            ServiceInfo if detected, None otherwise
        """
        return self.detected_service

    def is_service_based_management_available(self) -> bool:
        """
        Check if service-based Redis management is available on this system.

        Returns:
            True if OS service management is supported, False otherwise
        """
        return self._adapter_available and self.detected_service is not None and self.detected_service.exists