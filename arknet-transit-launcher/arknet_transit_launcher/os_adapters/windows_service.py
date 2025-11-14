"""Windows service adapter stub using sc.exe and PowerShell.

Best-effort; requires Windows runtime to fully test. Uses subprocess to avoid extra deps.
Functions return structured dicts similar to the systemd adapter.
"""
from typing import Dict, Any
import shutil
import subprocess


def _has_powershell() -> bool:
    return shutil.which("powershell") is not None


def _has_sc() -> bool:
    return shutil.which("sc") is not None


def detect(service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Try to find a Windows service by exact name or prefix.

    Returns: {exists: bool, service_name: Optional[str], reason: Optional[str]}
    """
    if _has_powershell():
        try:
            ps = subprocess.run([
                "powershell",
                "-NoProfile",
                "-Command",
                f"Get-Service -Name '{service_name}*' | Select-Object -First 1 -ExpandProperty Name"
            ], capture_output=True, text=True)
            if ps.returncode == 0 and ps.stdout.strip():
                return {"exists": True, "service_name": ps.stdout.strip().splitlines()[0], "reason": None}
        except FileNotFoundError:
            pass
    return {"exists": False, "service_name": None, "reason": "powershell or service not found"}


def is_active(win_service_name: str) -> bool:
    if not _has_powershell():
        return False
    try:
        ps = subprocess.run([
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-Service -Name '{win_service_name}').Status -eq 'Running'"
        ], capture_output=True, text=True)
        return ps.returncode == 0 and ps.stdout.strip().lower() in ("true", "1")
    except Exception:
        return False


def start(win_service_name: str) -> Dict[str, Any]:
    if _has_sc():
        try:
            rc = subprocess.call(["sc", "start", win_service_name])
            return {"ok": rc == 0, "rc": rc}
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
    if _has_powershell():
        ps = subprocess.run([
            "powershell",
            "-NoProfile",
            "-Command",
            f"Start-Service -Name '{win_service_name}'"
        ], capture_output=True, text=True)
        return {"ok": ps.returncode == 0, "rc": ps.returncode, "stderr": ps.stderr}
    return {"ok": False, "error": "no suitable tooling (sc/powershell) found"}


def stop(win_service_name: str) -> Dict[str, Any]:
    if _has_sc():
        try:
            rc = subprocess.call(["sc", "stop", win_service_name])
            return {"ok": rc == 0, "rc": rc}
        except FileNotFoundError as e:
            return {"ok": False, "error": str(e)}
    if _has_powershell():
        ps = subprocess.run([
            "powershell",
            "-NoProfile",
            "-Command",
            f"Stop-Service -Name '{win_service_name}' -Force"
        ], capture_output=True, text=True)
        return {"ok": ps.returncode == 0, "rc": ps.returncode, "stderr": ps.stderr}
    return {"ok": False, "error": "no suitable tooling (sc/powershell) found"}


def enable(win_service_name: str) -> Dict[str, Any]:
    # Make service start automatically.
    if _has_powershell():
        ps = subprocess.run([
            "powershell",
            "-NoProfile",
            "-Command",
            f"Set-Service -Name '{win_service_name}' -StartupType Automatic"
        ], capture_output=True, text=True)
        return {"ok": ps.returncode == 0, "rc": ps.returncode, "stderr": ps.stderr}
    return {"ok": False, "error": "powershell not found"}


def disable(win_service_name: str) -> Dict[str, Any]:
    if _has_powershell():
        ps = subprocess.run([
            "powershell",
            "-NoProfile",
            "-Command",
            f"Set-Service -Name '{win_service_name}' -StartupType Disabled"
        ], capture_output=True, text=True)
        return {"ok": ps.returncode == 0, "rc": ps.returncode, "stderr": ps.stderr}
    return {"ok": False, "error": "powershell not found"}
