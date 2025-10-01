"""
Base Country Plugin Abstract Class
Defines the interface that all country plugins must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

class CountryPlugin(ABC):
    """Abstract base class for country-specific passenger behavior plugins"""
    
    def __init__(self):
        self.country_code: str = ""
        self.country_name: str = ""
        self.plugin_dir: Path = Path()
    
    @abstractmethod
    def get_country_info(self) -> Dict[str, str]:
        """
        Return basic country information
        
        Returns:
            Dict with country code, name, region, timezone, etc.
        """
        pass
    
    @abstractmethod
    def get_config_path(self) -> Path:
        """
        Return path to country-specific configuration file
        
        Returns:
            Path object pointing to config.ini file
        """
        pass
    
    @abstractmethod
    def get_geographic_data_paths(self) -> Dict[str, Path]:
        """
        Return paths to GeoJSON data files
        
        Returns:
            Dict mapping data types to file paths
        """
        pass
    
    @abstractmethod
    def get_generated_models_dir(self) -> Path:
        """
        Return directory containing pre-computed models
        
        Returns:
            Path to generated models directory
        """
        pass
    
    @abstractmethod
    def get_cultural_model(self):
        """
        Return cultural behavior model instance
        
        Returns:
            Cultural model object with country-specific behaviors
        """
        pass
    
    @abstractmethod
    def validate_plugin(self) -> Tuple[bool, List[str]]:
        """
        Validate that plugin has all required files and configuration
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    # Optional methods with default implementations
    
    def get_spawn_rate_modifier(self, current_time: datetime, location_type: str = "general") -> float:
        """
        Get spawn rate modifier based on cultural patterns
        
        Args:
            current_time: Current simulation time
            location_type: Type of location
            
        Returns:
            Multiplier for base spawn rate
        """
        cultural_model = self.get_cultural_model()
        if hasattr(cultural_model, 'get_spawn_rate_modifier'):
            return cultural_model.get_spawn_rate_modifier(current_time, location_type)
        return 1.0
    
    def get_trip_purpose_distribution(self, current_time: datetime, origin_type: str) -> Dict[str, float]:
        """
        Get trip purpose distribution
        
        Args:
            current_time: Current simulation time
            origin_type: Type of origin location
            
        Returns:
            Dict mapping trip purposes to probabilities
        """
        cultural_model = self.get_cultural_model()
        if hasattr(cultural_model, 'get_trip_purpose_distribution'):
            return cultural_model.get_trip_purpose_distribution(current_time, origin_type)
        
        # Default distribution
        return {
            "work": 0.40,
            "school": 0.15,
            "shopping": 0.20,
            "medical": 0.10,
            "recreation": 0.10,
            "social": 0.05
        }
    
    def get_cultural_metadata(self) -> Dict[str, Any]:
        """
        Get cultural metadata for this country
        
        Returns:
            Dict with cultural patterns, events, and behaviors
        """
        cultural_model = self.get_cultural_model()
        if hasattr(cultural_model, 'get_cultural_metadata'):
            return cultural_model.get_cultural_metadata()
        return {}
    
    def supports_feature(self, feature_name: str) -> bool:
        """
        Check if plugin supports a specific feature
        
        Args:
            feature_name: Name of feature to check
            
        Returns:
            True if feature is supported
        """
        # Override in specific plugins
        return False