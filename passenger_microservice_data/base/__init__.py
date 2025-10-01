"""
Base Plugin System Package
Provides the foundation for country-specific passenger behavior plugins
"""

from .country_plugin import CountryPlugin
from .plugin_loader import PluginLoader, CountryPluginManager, get_plugin_manager

__all__ = [
    'CountryPlugin',
    'PluginLoader', 
    'CountryPluginManager',
    'get_plugin_manager'
]