"""OS adapters for arknet-transit-launcher.
Expose a consistent interface for system service detection and control.
"""
from . import systemd, windows_service

__all__ = ["systemd", "windows_service"]
