import sys
import os
import pathlib
import types
import asyncio

import pytest

# Ensure arknet-transit-launcher package is importable when running tests from repo root
repo_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / 'arknet-transit-launcher'))

from launcher.service_manager import ServiceManager, ManagedService, ServiceState


def test_service_manager_uses_systemd_adapter(monkeypatch):
    # Prepare ServiceManager and a managed service that requests system_service
    manager = ServiceManager()
    svc = ManagedService(name='mocksvc', port=None, health_url=None)
    svc.extra_config = {'auto_start': 'system_service'}
    manager.register_service(svc)

    # Create fake systemd adapter module
    fake_adapter = types.SimpleNamespace()

    def fake_detect(name, config):
        return {'exists': True, 'unit_name': f"{name}.service", 'scope': 'system'}

    def fake_start(unit_name, user=False):
        return {'ok': True}

    def fake_is_active(unit_name, user=False):
        return True

    fake_adapter.detect = fake_detect
    fake_adapter.start = fake_start
    fake_adapter.is_active = fake_is_active

    # Insert fake module into sys.modules where service_manager will import it
    sys.modules['arknet_transit_launcher.os_adapters.systemd'] = fake_adapter

    # Force platform to linux so service_manager picks systemd
    monkeypatch.setattr(sys, 'platform', 'linux')

    # Run the async start_service and ensure it returns RUNNING
    result = asyncio.run(manager.start_service('mocksvc'))
    assert result.state == ServiceState.RUNNING
    assert 'system service' in result.message.lower() or 'running' in result.message.lower()
