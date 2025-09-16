"""
Passenger Modeler Plugin System
==============================

Plugin-based architecture for statistical passenger modeling with environmental 
factors, peak times, and various distribution models.
"""

from plugins.base_model import StatisticalModel
from plugins.plugin_loader import PluginLoader

__all__ = ['StatisticalModel', 'PluginLoader']