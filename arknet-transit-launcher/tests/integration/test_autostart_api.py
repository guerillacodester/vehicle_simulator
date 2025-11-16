"""
Tests for autostart API endpoints.
Run with: pytest tests/integration/test_autostart_api.py
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from arknet_transit_launcher.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@patch('arknet_transit_launcher.os_adapters.systemd.enable')
def test_enable_autostart_linux(mock_enable, client):
    mock_enable.return_value = {"ok": True}
    response = client.post("/autostart/enable", json={"service": "test-service"})
    assert response.status_code == 200
    assert "Autostart enabled" in response.json()["message"]
    mock_enable.assert_called_once_with("test-service", user=True)


@patch('arknet_transit_launcher.os_adapters.systemd.disable')
def test_disable_autostart_linux(mock_disable, client):
    mock_disable.return_value = {"ok": True}
    response = client.post("/autostart/disable", json={"service": "test-service"})
    assert response.status_code == 200
    assert "Autostart disabled" in response.json()["message"]
    mock_disable.assert_called_once_with("test-service", user=True)


@patch('arknet_transit_launcher.os_adapters.systemd.is_active')
def test_get_autostart_status_linux(mock_is_active, client):
    mock_is_active.return_value = True
    response = client.get("/autostart/status?service=test-service")
    assert response.status_code == 200
    assert response.json() == {"service": "test-service", "autostart_enabled": True}
    mock_is_active.assert_called_once_with("test-service", user=True)


@patch('arknet_transit_launcher.os_adapters.systemd.enable')
def test_enable_autostart_failure(mock_enable, client):
    mock_enable.return_value = {"ok": False, "error": "systemctl not found"}
    response = client.post("/autostart/enable", json={"service": "test-service"})
    assert response.status_code == 500
    assert "Failed to enable" in response.json()["detail"]


# Windows tests would mock windows_service functions similarly
# For brevity, assuming Linux tests; add Windows mocks as needed