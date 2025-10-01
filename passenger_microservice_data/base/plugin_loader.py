"""
Plugin System for Country-Specific Passenger Behavior
Handles discovery, loading, and management of country plugins
"""

import os
import importlib
import configparser
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from .country_plugin import CountryPlugin

class PluginLoader:
    """Loads and manages country plugins"""
    
    def __init__(self, plugins_base_dir: str = None):
        if plugins_base_dir is None:
            # Default to countries directory relative to this file
            self.plugins_dir = Path(__file__).parent.parent / "countries"
        else:
            self.plugins_dir = Path(plugins_base_dir)
        
        self.loaded_plugins: Dict[str, CountryPlugin] = {}
        self.plugin_registry: Dict[str, Dict] = {}
        
    def discover_plugins(self) -> List[str]:
        """
        Discover available country plugins
        
        Returns:
            List of country codes for available plugins
        """
        available_countries = []
        
        if not self.plugins_dir.exists():
            logging.warning(f"Plugins directory not found: {self.plugins_dir}")
            return available_countries
        
        for country_dir in self.plugins_dir.iterdir():
            if country_dir.is_dir() and not country_dir.name.startswith('.'):
                # Check if it's a valid plugin (has __init__.py)
                init_file = country_dir / "__init__.py"
                if init_file.exists():
                    available_countries.append(country_dir.name)
                    logging.info(f"Discovered country plugin: {country_dir.name}")
        
        return sorted(available_countries)
    
    def load_plugin(self, country_code: str) -> Optional[CountryPlugin]:
        """
        Load a specific country plugin
        
        Args:
            country_code: Country code (e.g., 'bb', 'jm', 'tt')
            
        Returns:
            Loaded plugin instance or None if failed
        """
        if country_code in self.loaded_plugins:
            return self.loaded_plugins[country_code]
        
        try:
            # Import the plugin module
            plugin_module_path = f"passenger_microservice_data.countries.{country_code}"
            plugin_module = importlib.import_module(plugin_module_path)
            
            # Get the plugin instance
            if hasattr(plugin_module, 'get_plugin'):
                plugin_instance = plugin_module.get_plugin()
                
                # Validate the plugin
                is_valid, errors = plugin_instance.validate_plugin()
                if not is_valid:
                    logging.error(f"Plugin validation failed for {country_code}: {errors}")
                    return None
                
                # Store plugin info
                if hasattr(plugin_module, 'PLUGIN_INFO'):
                    self.plugin_registry[country_code] = plugin_module.PLUGIN_INFO
                
                self.loaded_plugins[country_code] = plugin_instance
                logging.info(f"Successfully loaded plugin for {country_code}")
                return plugin_instance
            
            else:
                logging.error(f"Plugin {country_code} missing get_plugin() function")
                return None
                
        except Exception as e:
            logging.error(f"Failed to load plugin {country_code}: {e}")
            return None
    
    def get_plugin(self, country_code: str) -> Optional[CountryPlugin]:
        """
        Get a loaded plugin or load it if not already loaded
        
        Args:
            country_code: Country code
            
        Returns:
            Plugin instance or None
        """
        if country_code in self.loaded_plugins:
            return self.loaded_plugins[country_code]
        
        return self.load_plugin(country_code)
    
    def get_available_countries(self) -> Dict[str, str]:
        """
        Get mapping of available country codes to names
        
        Returns:
            Dict mapping country codes to country names
        """
        countries = {}
        discovered = self.discover_plugins()
        
        for country_code in discovered:
            plugin = self.get_plugin(country_code)
            if plugin:
                info = plugin.get_country_info()
                countries[country_code] = info.get('name', country_code.upper())
        
        return countries
    
    def get_plugin_info(self, country_code: str) -> Optional[Dict]:
        """
        Get plugin metadata information
        
        Args:
            country_code: Country code
            
        Returns:
            Plugin metadata dict or None
        """
        if country_code in self.plugin_registry:
            return self.plugin_registry[country_code]
        
        # Try loading plugin to get info
        plugin = self.get_plugin(country_code)
        if plugin and country_code in self.plugin_registry:
            return self.plugin_registry[country_code]
        
        return None
    
    def validate_all_plugins(self) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all discovered plugins
        
        Returns:
            Dict mapping country codes to (is_valid, errors) tuples
        """
        results = {}
        discovered = self.discover_plugins()
        
        for country_code in discovered:
            plugin = self.get_plugin(country_code)
            if plugin:
                results[country_code] = plugin.validate_plugin()
            else:
                results[country_code] = (False, ["Failed to load plugin"])
        
        return results


class CountryPluginManager:
    """High-level manager for country plugins"""
    
    def __init__(self, plugins_dir: str = None):
        self.loader = PluginLoader(plugins_dir)
        self.current_country: Optional[str] = None
        self.current_plugin: Optional[CountryPlugin] = None
    
    def set_country(self, country_code: str) -> bool:
        """
        Set the active country for passenger simulation
        
        Args:
            country_code: Country code to activate
            
        Returns:
            True if successfully set, False otherwise
        """
        plugin = self.loader.get_plugin(country_code)
        if plugin:
            self.current_country = country_code
            self.current_plugin = plugin
            logging.info(f"Set active country to: {country_code}")
            return True
        
        logging.error(f"Failed to set country to: {country_code}")
        return False
    
    def get_current_plugin(self) -> Optional[CountryPlugin]:
        """Get the currently active plugin"""
        return self.current_plugin
    
    def get_available_countries(self) -> Dict[str, str]:
        """Get available countries"""
        return self.loader.get_available_countries()
    
    def get_country_config(self, country_code: str = None) -> Optional[configparser.ConfigParser]:
        """
        Get configuration for a country
        
        Args:
            country_code: Country code, or None for current country
            
        Returns:
            ConfigParser instance or None
        """
        if country_code is None:
            country_code = self.current_country
        
        if country_code is None:
            return None
        
        plugin = self.loader.get_plugin(country_code)
        if plugin:
            config_path = plugin.get_config_path()
            if config_path.exists():
                config = configparser.ConfigParser()
                config.read(config_path)
                return config
        
        return None
    
    def get_spawn_rate_modifier(self, current_time, location_type: str = "general") -> float:
        """Get spawn rate modifier from current plugin"""
        if self.current_plugin:
            return self.current_plugin.get_spawn_rate_modifier(current_time, location_type)
        return 1.0
    
    def get_trip_purpose_distribution(self, current_time, origin_type: str) -> Dict[str, float]:
        """Get trip purpose distribution from current plugin"""
        if self.current_plugin:
            return self.current_plugin.get_trip_purpose_distribution(current_time, origin_type)
        
        # Default fallback
        return {
            "work": 0.40,
            "school": 0.15, 
            "shopping": 0.20,
            "medical": 0.10,
            "recreation": 0.10,
            "social": 0.05
        }


# Global plugin manager instance
_plugin_manager: Optional[CountryPluginManager] = None

def get_plugin_manager(plugins_dir: str = None) -> CountryPluginManager:
    """Get global plugin manager instance"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = CountryPluginManager(plugins_dir)
    return _plugin_manager