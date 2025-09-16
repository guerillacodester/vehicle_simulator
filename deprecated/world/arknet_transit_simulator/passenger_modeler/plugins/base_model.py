"""
Base Statistical Model Interface
================================

Abstract base class for all passenger generation statistical models.
All plugins must inherit from this class and implement the required methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
import json
from pathlib import Path
import numpy as np
from datetime import datetime, time


class StatisticalModel(ABC):
    def get_distribution_statistics(self, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Generate summary statistics for the passenger distribution.
        Plugins should override this to provide model-specific statistics.
        Returns a dictionary with keys like 'mean', 'std', 'min', 'max', 'percentiles', 'peak_times', etc.
        """
        return {
            'note': 'No statistics available for this model.'
        }
    """Base class for all statistical passenger generation models"""
    
    def __init__(self, config_path: str):
        """
        Initialize the statistical model with configuration
        
        Args:
            config_path: Path to model-specific JSON configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.name = self.config.get('model_info', {}).get('name', 'Unknown Model')
        self.version = self.config.get('model_info', {}).get('version', '1.0.0')
        
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config from {self.config_path}: {e}")
    
    @abstractmethod
    def get_model_type(self) -> str:
        """Return the statistical model type (e.g., 'poisson', 'gaussian', 'gamma')"""
        pass
    
    @abstractmethod
    def calculate_base_rate(self, location_data: Dict[str, Any], 
                          environmental_factors: Dict[str, float]) -> float:
        """
        Calculate base passenger generation rate for a location
        
        Args:
            location_data: Information about the location (amenities, stop type, etc.)
            environmental_factors: Weather, events, seasonal factors
            
        Returns:
            Base passenger generation rate per time unit
        """
        pass
    
    @abstractmethod
    def apply_temporal_weights(self, base_rate: float, current_time: time, 
                             day_type: str = 'weekday') -> float:
        """
        Apply time-based weights to base rate (peak hours, day/night, etc.)
        
        Args:
            base_rate: Base generation rate
            current_time: Current time of day
            day_type: Type of day ('weekday', 'weekend', 'holiday')
            
        Returns:
            Time-weighted passenger generation rate
        """
        pass
    
    @abstractmethod
    def generate_passengers(self, weighted_rate: float, time_interval_seconds: int) -> int:
        """
        Generate actual number of passengers using the statistical model
        
        Args:
            weighted_rate: Time and environment weighted generation rate
            time_interval_seconds: Time interval for generation
            
        Returns:
            Number of passengers to generate
        """
        pass
    
    def apply_environmental_factors(self, base_rate: float, 
                                  environmental_factors: Dict[str, float]) -> float:
        """
        Apply environmental factors to base rate (default implementation)
        
        Args:
            base_rate: Base generation rate
            environmental_factors: Dict of environmental factors and their weights
            
        Returns:
            Environmentally adjusted rate
        """
        env_config = self.config.get('environmental_factors', {})
        
        total_multiplier = 1.0
        
        for factor, value in environmental_factors.items():
            if factor in env_config:
                factor_config = env_config[factor]
                # Apply factor based on configuration
                if factor_config.get('type') == 'linear':
                    multiplier = 1.0 + (value * factor_config.get('weight', 0.0))
                elif factor_config.get('type') == 'exponential':
                    multiplier = np.exp(value * factor_config.get('weight', 0.0))
                else:
                    multiplier = 1.0 + (value * factor_config.get('weight', 0.0))
                
                total_multiplier *= max(0.1, multiplier)  # Prevent negative rates
        
        return base_rate * total_multiplier
    
    def get_amenity_weights(self) -> Dict[str, float]:
        """Get amenity type weights from configuration"""
        return self.config.get('amenity_weights', {})
    
    def get_time_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get time-based patterns from configuration"""
        return self.config.get('time_patterns', {})
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get model-specific parameters from configuration"""
        return self.config.get('model_parameters', {})
    
    def validate_config(self) -> List[str]:
        """
        Validate the model configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required sections
        required_sections = ['model_info', 'amenity_weights', 'time_patterns', 'model_parameters']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Check model info
        if 'model_info' in self.config:
            model_info = self.config['model_info']
            if 'name' not in model_info:
                errors.append("Missing model_info.name")
            if 'version' not in model_info:
                errors.append("Missing model_info.version")
        
        return errors
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information summary"""
        return {
            'name': self.name,
            'version': self.version,
            'type': self.get_model_type(),
            'config_path': str(self.config_path),
            'amenity_types_count': len(self.get_amenity_weights()),
            'time_patterns_count': len(self.get_time_patterns()),
            'has_environmental_factors': 'environmental_factors' in self.config
        }