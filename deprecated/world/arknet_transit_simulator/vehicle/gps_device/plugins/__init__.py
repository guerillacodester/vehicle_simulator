"""
GPS Device Plugin System
------------------------
Plugin architecture for 100% agnostic telemetry data sources.
Supports simulation, hardware ESP32, file replay, and any future sources.
"""

from .interface import ITelemetryPlugin
from .manager import PluginManager

__all__ = ["ITelemetryPlugin", "PluginManager"]
