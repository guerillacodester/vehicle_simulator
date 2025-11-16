"""
Integration Test for Unified Redis Service Management
======================================================

Demonstrates the unified RedisServiceManager working across platforms.
"""

import pytest
from unittest.mock import patch, MagicMock
from arknet_transit_launcher.health.redis_service_manager import (
    RedisServiceManager, ServiceInfo, ServiceStatus
)


def test_unified_api_linux():
    """Test that the API works the same regardless of platform."""
    with patch('arknet_transit_launcher.health.redis_service_manager.platform.system', return_value='Linux'), \
         patch('arknet_transit_launcher.health.redis_service_manager.os_adapter') as mock_adapter:

        # Mock systemd adapter
        mock_adapter.detect.return_value = {"exists": True, "unit_name": "redis-server.service", "scope": "system"}
        mock_adapter.is_active.return_value = True
        mock_adapter.start.return_value = {"ok": True}
        mock_adapter.enable.return_value = {"ok": True}

        manager = RedisServiceManager()

        # Test unified API
        service_info = manager.detect_service()
        assert service_info.exists == True
        assert service_info.name == "redis-server.service"

        status = manager.get_status()
        assert status.is_running == True

        # Test service management
        assert manager.ensure_running() == True  # Already running
        assert manager.ensure_auto_start() == True


def test_unified_api_windows():
    """Test that the API works the same on Windows."""
    with patch('arknet_transit_launcher.health.redis_service_manager.platform.system', return_value='Windows'), \
         patch('arknet_transit_launcher.health.redis_service_manager.os_adapter') as mock_adapter:

        # Mock Windows service adapter
        mock_adapter.detect.return_value = {"exists": True, "service_name": "Redis", "reason": None}
        mock_adapter.is_active.return_value = True
        mock_adapter.start.return_value = {"ok": True}
        mock_adapter.enable.return_value = {"ok": True}

        manager = RedisServiceManager()

        # Test unified API
        service_info = manager.detect_service()
        assert service_info.exists == True
        assert service_info.name == "Redis"

        status = manager.get_status()
        assert status.is_running == True

        # Test service management
        assert manager.ensure_running() == True
        assert manager.ensure_auto_start() == True


def test_service_not_found():
    """Test behavior when Redis service is not found."""
    with patch('arknet_transit_launcher.health.redis_service_manager.os_adapter') as mock_adapter:
        mock_adapter.detect.return_value = {"exists": False}

        manager = RedisServiceManager()

        service_info = manager.detect_service()
        assert service_info.exists == False

        status = manager.get_status()
        assert status.is_running == False
        assert status.status_message == "Service not detected"

        # Service operations should fail gracefully
        assert manager.ensure_running() == False
        assert manager.ensure_auto_start() == False


def test_service_operations():
    """Test complete service lifecycle operations."""
    with patch('arknet_transit_launcher.health.redis_service_manager.os_adapter') as mock_adapter:
        # Setup mock service
        mock_adapter.detect.return_value = {"exists": True, "unit_name": "redis-server.service"}
        mock_adapter.is_active.side_effect = [False, True, True, False, True]  # stopped -> running -> running -> stopped -> running
        mock_adapter.start.return_value = {"ok": True}
        mock_adapter.stop.return_value = {"ok": True}
        mock_adapter.enable.return_value = {"ok": True}

        manager = RedisServiceManager()
        manager.detect_service()

        # Test ensure_running starts stopped service
        assert manager.ensure_running() == True

        # Test status updates
        status = manager.get_status()
        assert status.is_running == True

        # Test restart
        assert manager.restart_service() == True

        # Test auto-start
        assert manager.ensure_auto_start() == True


def test_error_handling():
    """Test graceful error handling."""
    with patch('arknet_transit_launcher.health.redis_service_manager.os_adapter') as mock_adapter:
        # Setup service
        mock_adapter.detect.return_value = {"exists": True, "unit_name": "redis-server.service"}
        mock_adapter.is_active.return_value = False  # Service is stopped
        mock_adapter.start.side_effect = Exception("Permission denied")
        mock_adapter.enable.side_effect = Exception("Access denied")

        manager = RedisServiceManager()
        manager.detect_service()

        # Operations should fail gracefully without exceptions
        result_running = manager.ensure_running()
        result_auto_start = manager.ensure_auto_start()

        assert result_running == False, f"Expected False, got {result_running}"
        assert result_auto_start == False, f"Expected False, got {result_auto_start}"

        # Status should still work
        status = manager.get_status()
        assert isinstance(status, ServiceStatus)


if __name__ == "__main__":
    # Run basic smoke test
    print("Running unified Redis service manager integration tests...")

    test_unified_api_linux()
    print("✓ Linux API test passed")

    test_unified_api_windows()
    print("✓ Windows API test passed")

    test_service_not_found()
    print("✓ Service not found test passed")

    test_service_operations()
    print("✓ Service operations test passed")

    test_error_handling()
    print("✓ Error handling test passed")

    print("\n🎉 All integration tests passed!")
    print("The unified RedisServiceManager provides consistent API across Linux and Windows.")