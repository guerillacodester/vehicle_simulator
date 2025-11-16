"""
Tests for Redis Service Manager
==============================

Tests the unified cross-platform Redis service management.
"""

import pytest
from unittest.mock import patch, MagicMock
import platform

# Mock the OS adapters based on platform
if platform.system() == "Linux":
    from arknet_transit_launcher.health.redis_service_manager import (
        RedisServiceManager, ServiceInfo, ServiceStatus, ADAPTER_TYPE
    )
else:
    # For testing on non-Linux systems, we'll mock
    pytestmark = pytest.mark.skipif(
        platform.system() != "Linux",
        reason="Service manager tests designed for Linux/systemd environment"
    )


class TestRedisServiceManager:
    """Test RedisServiceManager functionality."""

    def test_initialization(self):
        """Test basic initialization."""
        manager = RedisServiceManager()
        assert manager.service_name == "redis"
        assert manager.detected_service is None
        assert manager._adapter_available

    def test_initialization_custom_name(self):
        """Test initialization with custom service name."""
        manager = RedisServiceManager("my-redis")
        assert manager.service_name == "my-redis"

    @patch('arknet_transit_launcher.os_adapters.systemd.detect')
    def test_detect_service_found(self, mock_detect):
        """Test service detection when Redis service is found."""
        mock_detect.return_value = {
            "exists": True,
            "unit_name": "redis-server.service",
            "scope": "system"
        }

        manager = RedisServiceManager()
        result = manager.detect_service()

        assert result.exists == True
        assert result.name == "redis-server.service"
        assert result.scope == "system"
        assert manager.detected_service == result

        # Verify detect was called with expected candidates
        assert mock_detect.call_count > 0

    @patch('arknet_transit_launcher.os_adapters.systemd.detect')
    def test_detect_service_not_found(self, mock_detect):
        """Test service detection when no Redis service exists."""
        mock_detect.return_value = {"exists": False}

        manager = RedisServiceManager()
        result = manager.detect_service()

        assert result.exists == False
        assert result.name is None
        assert "No Redis service found" in result.reason

    @patch('arknet_transit_launcher.os_adapters.systemd.is_active')
    def test_get_status_running(self, mock_is_active):
        """Test getting status when service is running."""
        mock_is_active.return_value = True

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service",
            scope="system"
        )

        status = manager.get_status()

        assert status.is_running == True
        assert status.status_message == "Running"

    @patch('arknet_transit_launcher.os_adapters.systemd.is_active')
    def test_get_status_stopped(self, mock_is_active):
        """Test getting status when service is stopped."""
        mock_is_active.return_value = False

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service",
            scope="system"
        )

        status = manager.get_status()

        assert status.is_running == False
        assert status.status_message == "Stopped"

    def test_get_status_no_service(self):
        """Test getting status when no service is detected."""
        manager = RedisServiceManager()
        # detected_service is None

        status = manager.get_status()

        assert status.is_running == False
        assert status.status_message == "Service not detected"

    @patch('arknet_transit_launcher.os_adapters.systemd.start')
    @patch('arknet_transit_launcher.os_adapters.systemd.is_active')
    def test_ensure_running_already_running(self, mock_is_active, mock_start):
        """Test ensure_running when service is already running."""
        mock_is_active.return_value = True

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.ensure_running()

        assert result == True
        mock_start.assert_not_called()

    @patch('arknet_transit_launcher.os_adapters.systemd.start')
    @patch('arknet_transit_launcher.os_adapters.systemd.is_active')
    def test_ensure_running_start_success(self, mock_is_active, mock_start):
        """Test ensure_running successfully starts stopped service."""
        # First call (initial check) - stopped
        # Second call (after start) - running
        mock_is_active.side_effect = [False, True]
        mock_start.return_value = {"ok": True}

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.ensure_running()

        assert result == True
        mock_start.assert_called_once_with("redis-server.service")

    @patch('arknet_transit_launcher.os_adapters.systemd.start')
    @patch('arknet_transit_launcher.os_adapters.systemd.is_active')
    def test_ensure_running_start_failure(self, mock_is_active, mock_start):
        """Test ensure_running when start fails."""
        mock_is_active.return_value = False  # Always stopped
        mock_start.return_value = {"ok": False, "error": "Permission denied"}

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.ensure_running()

        assert result == False
        mock_start.assert_called_once()

    def test_ensure_running_no_service(self):
        """Test ensure_running when no service is detected."""
        manager = RedisServiceManager()
        # detected_service is None

        result = manager.ensure_running()

        assert result == False

    @patch('arknet_transit_launcher.os_adapters.systemd.enable')
    def test_ensure_auto_start_success(self, mock_enable):
        """Test ensure_auto_start successfully enables service."""
        mock_enable.return_value = {"ok": True}

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.ensure_auto_start()

        assert result == True
        mock_enable.assert_called_once_with("redis-server.service")

    @patch('arknet_transit_launcher.os_adapters.systemd.enable')
    def test_ensure_auto_start_failure(self, mock_enable):
        """Test ensure_auto_start when enable fails."""
        mock_enable.return_value = {"ok": False, "error": "Permission denied"}

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.ensure_auto_start()

        assert result == False

    @patch('arknet_transit_launcher.os_adapters.systemd.stop')
    def test_stop_service_success(self, mock_stop):
        """Test stop_service successfully stops service."""
        mock_stop.return_value = {"ok": True}

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.stop_service()

        assert result == True
        mock_stop.assert_called_once_with("redis-server.service")

    @patch('arknet_transit_launcher.os_adapters.systemd.stop')
    @patch('arknet_transit_launcher.os_adapters.systemd.start')
    @patch('arknet_transit_launcher.os_adapters.systemd.is_active')
    def test_restart_service_success(self, mock_is_active, mock_start, mock_stop):
        """Test restart_service successfully restarts service."""
        mock_stop.return_value = {"ok": True}
        mock_start.return_value = {"ok": True}
        mock_is_active.return_value = True  # After restart

        manager = RedisServiceManager()
        manager.detected_service = ServiceInfo(
            exists=True,
            name="redis-server.service"
        )

        result = manager.restart_service()

        assert result == True
        mock_stop.assert_called_once()
        mock_start.assert_called_once()

    def test_get_service_info(self):
        """Test get_service_info returns detected service info."""
        service_info = ServiceInfo(exists=True, name="redis-server.service")
        manager = RedisServiceManager()
        manager.detected_service = service_info

        result = manager.get_service_info()

        assert result == service_info

    def test_is_service_based_management_available(self):
        """Test service availability detection."""
        manager = RedisServiceManager()

        # No service detected
        assert not manager.is_service_based_management_available()

        # Service detected
        manager.detected_service = ServiceInfo(exists=True, name="redis-server.service")
        assert manager.is_service_based_management_available()

        # Adapter not available (would need mocking for full test)
        # This is tested implicitly through the adapter_available check


class TestServiceInfo:
    """Test ServiceInfo dataclass."""

    def test_service_info_creation(self):
        """Test ServiceInfo can be created with all fields."""
        info = ServiceInfo(
            exists=True,
            name="redis-server.service",
            scope="system",
            reason="Found via systemctl"
        )

        assert info.exists == True
        assert info.name == "redis-server.service"
        assert info.scope == "system"
        assert info.reason == "Found via systemctl"


class TestServiceStatus:
    """Test ServiceStatus dataclass."""

    def test_service_status_creation(self):
        """Test ServiceStatus can be created with all fields."""
        status = ServiceStatus(
            is_running=True,
            is_enabled=True,
            status_message="Running smoothly"
        )

        assert status.is_running == True
        assert status.is_enabled == True
        assert status.status_message == "Running smoothly"