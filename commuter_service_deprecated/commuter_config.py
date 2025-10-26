"""
Commuter Configuration System
============================

Externalized configuration for commuter behavior parameters.
Supports environment-specific settings and runtime adjustment.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
import json


@dataclass
class CommuterBehaviorConfig:
    """Configuration for commuter behavior and preferences."""
    
    # Walking and mobility settings
    default_walking_speed_ms: float = 1.4          # Average human walking speed
    slow_walking_speed_ms: float = 1.0             # Elderly/mobility impaired
    fast_walking_speed_ms: float = 1.8             # Young/athletic
    
    # Distance thresholds by priority level
    max_walking_distance_low_priority: float = 400     # Low priority willing to walk further
    max_walking_distance_medium_priority: float = 300   # Standard walking distance
    max_walking_distance_high_priority: float = 200     # High priority expects closer pickup
    max_walking_distance_critical_priority: float = 100 # Emergency/medical - minimal walk
    
    # Disembark detection thresholds
    disembark_threshold_urban: float = 50          # Dense urban areas - precise stops
    disembark_threshold_suburban: float = 100      # Suburban areas - more flexible
    disembark_threshold_rural: float = 200         # Rural areas - wider tolerance
    
    # Flexibility and patience settings
    pickup_flexibility_impatient: float = 0.3      # Low tolerance for delays
    pickup_flexibility_standard: float = 0.6       # Normal patience
    pickup_flexibility_patient: float = 0.9        # High tolerance for optimization
    
    # Priority-based service levels
    priority_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.priority_thresholds is None:
            self.priority_thresholds = {
                'low': 0.0,
                'medium': 0.4,
                'high': 0.7,
                'critical': 0.9
            }
    
    def get_walking_distance_for_priority(self, priority: float) -> float:
        """Get appropriate walking distance based on priority level."""
        if priority >= self.priority_thresholds['critical']:
            return self.max_walking_distance_critical_priority
        elif priority >= self.priority_thresholds['high']:
            return self.max_walking_distance_high_priority
        elif priority >= self.priority_thresholds['medium']:
            return self.max_walking_distance_medium_priority
        else:
            return self.max_walking_distance_low_priority
    
    def get_disembark_threshold_for_area(self, area_type: str = 'suburban') -> float:
        """Get disembark threshold based on area density."""
        thresholds = {
            'urban': self.disembark_threshold_urban,
            'suburban': self.disembark_threshold_suburban,
            'rural': self.disembark_threshold_rural
        }
        return thresholds.get(area_type, self.disembark_threshold_suburban)
    
    def get_flexibility_for_personality(self, personality: str = 'standard') -> float:
        """Get pickup flexibility based on commuter personality."""
        flexibility_map = {
            'impatient': self.pickup_flexibility_impatient,
            'standard': self.pickup_flexibility_standard,
            'patient': self.pickup_flexibility_patient
        }
        return flexibility_map.get(personality, self.pickup_flexibility_standard)


class CommuterConfigLoader:
    """Loads commuter configuration from various sources."""
    
    @staticmethod
    def load_from_env() -> CommuterBehaviorConfig:
        """Load configuration from environment variables."""
        config = CommuterBehaviorConfig()
        
        # Override with environment values if present
        config.default_walking_speed_ms = float(os.getenv('COMMUTER_WALKING_SPEED', config.default_walking_speed_ms))
        config.max_walking_distance_medium_priority = float(os.getenv('COMMUTER_MAX_WALK_DISTANCE', config.max_walking_distance_medium_priority))
        config.disembark_threshold_suburban = float(os.getenv('COMMUTER_DISEMBARK_THRESHOLD', config.disembark_threshold_suburban))
        config.pickup_flexibility_standard = float(os.getenv('COMMUTER_PICKUP_FLEXIBILITY', config.pickup_flexibility_standard))
        
        return config
    
    @staticmethod
    def load_from_file(config_path: str) -> CommuterBehaviorConfig:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            config = CommuterBehaviorConfig()
            
            # Update configuration with file values
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            return config
            
        except FileNotFoundError:
            print(f"Config file {config_path} not found, using defaults")
            return CommuterBehaviorConfig()
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config file: {e}")
            return CommuterBehaviorConfig()
    
    @staticmethod
    def get_default_config() -> CommuterBehaviorConfig:
        """Get default configuration for development/testing."""
        return CommuterBehaviorConfig()


# Global configuration instance
_commuter_config: Optional[CommuterBehaviorConfig] = None


def get_commuter_config() -> CommuterBehaviorConfig:
    """Get the global commuter configuration instance."""
    global _commuter_config
    if _commuter_config is None:
        # Try to load from environment first, then fall back to defaults
        _commuter_config = CommuterConfigLoader.load_from_env()
    return _commuter_config


def set_commuter_config(config: CommuterBehaviorConfig) -> None:
    """Set the global commuter configuration (for testing/override)."""
    global _commuter_config
    _commuter_config = config


# Priority level explanations for documentation
PRIORITY_EXPLANATIONS = {
    0.0: "Leisure travel - flexible timing, can wait longer",
    0.1: "Shopping, social visits - some flexibility",
    0.2: "Entertainment, recreation - low urgency", 
    0.3: "Personal errands - moderate importance",
    0.4: "General appointments - standard priority",
    0.5: "Regular commuting - balanced needs",
    0.6: "Work meetings - higher importance",
    0.7: "Education, school - time-sensitive",
    0.8: "Important appointments - minimal delays",
    0.9: "Medical appointments - critical timing",
    1.0: "Emergency travel - highest priority"
}


def explain_priority(priority: float) -> str:
    """Get human-readable explanation of priority level."""
    # Find closest priority level
    closest_priority = min(PRIORITY_EXPLANATIONS.keys(), 
                          key=lambda x: abs(x - priority))
    return PRIORITY_EXPLANATIONS[closest_priority]