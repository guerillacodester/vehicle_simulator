import sys
import os
import pathlib
import types
import asyncio

import pytest

# Ensure arknet-transit-launcher package is importable when running tests from repo root
repo_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / 'arknet-transit-launcher'))

from arknet_transit_launcher.os_adapters import systemd


def test_detect_and_start_stop_enable_disable(monkeypatch):
    # Force systemctl presence
    monkeypatch.setattr(systemd, '_has_systemctl', lambda: True)

    # Stub _run_systemctl to simulate systemctl responses
    def fake_run(args, capture_output=False, check=False, user=False):
        cmd = args[0] if args else ''
        # status should return rc 0 for existing unit
        if args[0] == 'status':
            return {'rc': 0, 'stdout': 'active', 'stderr': ''}
        # is-active uses is-active --quiet -> rc 0
        if args[0] == 'is-active':
            return {'rc': 0, 'stdout': '', 'stderr': ''}
        # start/stop/enable/disable return rc 0
        return {'rc': 0, 'stdout': '', 'stderr': ''}

    monkeypatch.setattr(systemd, '_run_systemctl', fake_run)

    res = systemd.detect('myservice', {})
    assert res.get('exists') is True
    assert res.get('unit_name') is not None

    start_res = systemd.start('myservice', user=False)
    assert start_res.get('ok') is True

    assert systemd.is_active('myservice', user=False) is True

    stop_res = systemd.stop('myservice', user=False)
    assert stop_res.get('ok') is True

    enable_res = systemd.enable('myservice', user=False)
    assert enable_res.get('ok') is True

    disable_res = systemd.disable('myservice', user=False)
    assert disable_res.get('ok') is True
