import sys
import os
import pathlib
import types
import pytest

# Ensure arknet-transit-launcher package is importable when running tests from repo root
repo_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / 'arknet-transit-launcher'))

from arknet_transit_launcher.os_adapters import windows_service


def test_detect_and_start_stop_enable_disable(monkeypatch):
    # Force tooling availability
    monkeypatch.setattr(windows_service, '_has_powershell', lambda: True)
    monkeypatch.setattr(windows_service, '_has_sc', lambda: True)

    # Fake subprocess.run for PowerShell and subprocess.call for sc
    class FakeCompleted:
        def __init__(self, rc=0, stdout='', stderr=''):
            self.returncode = rc
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, capture_output=False, text=False):
        # For detect: return service name
        return FakeCompleted(rc=0, stdout='MyService\n')

    def fake_call(cmd):
        return 0

    monkeypatch.setattr(windows_service, 'subprocess', types.SimpleNamespace(run=fake_run, call=fake_call))

    res = windows_service.detect('MyService', {})
    assert res.get('exists') is True
    assert res.get('service_name') is not None

    start_res = windows_service.start('MyService')
    assert start_res.get('ok') is True

    assert windows_service.is_active('MyService') in (True, False)  # returns boolean depending on fake

    stop_res = windows_service.stop('MyService')
    assert stop_res.get('ok') is True

    enable_res = windows_service.enable('MyService')
    assert enable_res.get('ok') is True

    disable_res = windows_service.disable('MyService')
    assert disable_res.get('ok') is True
