"""Systemd adapter (best-effort).

This module provides convenience functions used by the launcher. It is intentionally
defensive: `systemctl` may be absent (Windows) or may require elevated permissions.
Functions return structured dicts so callers can surface friendly messages to users.
"""
from typing import Dict, Any, Optional
import shutil
import subprocess


def _has_systemctl() -> bool:
    return shutil.which("systemctl") is not None


def _run_systemctl(args, capture_output: bool = False, check: bool = False, user: bool = False):
    base = ["systemctl"]
    if user:
        base = ["systemctl", "--user"]
    cmd = base + args
    try:
        completed = subprocess.run(cmd, capture_output=capture_output, text=True)
        return {"rc": completed.returncode, "stdout": completed.stdout if capture_output else None, "stderr": completed.stderr if capture_output else None}
    except FileNotFoundError as e:
        return {"rc": 127, "error": str(e)}


def detect(service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if a systemd unit exists for the service.

    Returns: {exists: bool, unit_name: Optional[str], scope: 'system'|'user'|None, reason: Optional[str]}
    """
    if not _has_systemctl():
        return {"exists": False, "unit_name": None, "scope": None, "reason": "systemctl not found"}

    # Common unit name candidates
    candidates = [f"{service_name}.service", f"{service_name}-service.service", service_name]
    # Try system scope first, then user
    for scope_user in (False, True):
        for unit in candidates:
            res = _run_systemctl(["status", unit], capture_output=True, user=scope_user)
            if res.get("rc") == 0:
                return {"exists": True, "unit_name": unit, "scope": "user" if scope_user else "system", "reason": None}
    return {"exists": False, "unit_name": None, "scope": None, "reason": "no matching unit"}


def is_active(unit_name: str, user: bool = False) -> bool:
    if not _has_systemctl():
        return False
    res = _run_systemctl(["is-active", "--quiet", unit_name], capture_output=False, user=user)
    return res.get("rc") == 0


def start(unit_name: str, user: bool = False) -> Dict[str, Any]:
    if not _has_systemctl():
        return {"ok": False, "error": "systemctl not found"}
    res = _run_systemctl(["start", unit_name], capture_output=True, user=user)
    ok = res.get("rc") == 0
    return {"ok": ok, "rc": res.get("rc"), "stderr": res.get("stderr"), "stdout": res.get("stdout")}


def stop(unit_name: str, user: bool = False) -> Dict[str, Any]:
    if not _has_systemctl():
        return {"ok": False, "error": "systemctl not found"}
    res = _run_systemctl(["stop", unit_name], capture_output=True, user=user)
    ok = res.get("rc") == 0
    return {"ok": ok, "rc": res.get("rc"), "stderr": res.get("stderr"), "stdout": res.get("stdout")}


def enable(unit_name: str, user: bool = False) -> Dict[str, Any]:
    if not _has_systemctl():
        return {"ok": False, "error": "systemctl not found"}
    res = _run_systemctl(["enable", unit_name], capture_output=True, user=user)
    ok = res.get("rc") == 0
    return {"ok": ok, "rc": res.get("rc"), "stderr": res.get("stderr")}


def disable(unit_name: str, user: bool = False) -> Dict[str, Any]:
    if not _has_systemctl():
        return {"ok": False, "error": "systemctl not found"}
    res = _run_systemctl(["disable", unit_name], capture_output=True, user=user)
    ok = res.get("rc") == 0
    return {"ok": ok, "rc": res.get("rc"), "stderr": res.get("stderr")}
