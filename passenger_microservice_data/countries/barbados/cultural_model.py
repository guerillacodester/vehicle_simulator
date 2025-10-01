"""
Barbados Cultural Model Plugin
Implements country-specific passenger behavior patterns for Barbados
"""

from datetime import datetime, time
from typing import Dict, List, Tuple, Optional
import math

class BarbadosCulturalModel:
    """Cultural behavior model specific to Barbados"""
    
    def __init__(self):
        self.country_code = "bb"
        self.country_name = "Barbados"
        
        # Cultural calendar events that affect travel
        self.cultural_events = {
            "crop_over": {"month": 8, "duration_days": 5, "travel_multiplier": 2.0},
            "independence_day": {"month": 11, "day": 30, "travel_multiplier": 1.5},
            "emancipation_day": {"month": 8, "day": 1, "travel_multiplier": 1.3},
            "kadooment_day": {"month": 8, "day": 5, "travel_multiplier": 2.5},  # Peak of Crop Over
        }
        
        # Workplace patterns
        self.work_patterns = {
            "standard_start": time(8, 0),
            "standard_end": time(17, 0),
            "government_start": time(8, 30),
            "government_end": time(16, 30),
            "retail_start": time(9, 0),
            "retail_end": time(18, 0),
            "tourism_start": time(7, 0),
            "tourism_end": time(22, 0)
        }
        
        # Social patterns
        self.social_patterns = {
            "lunch_time": time(12, 0),
            "after_work_socializing": time(17, 30),
            "church_time_sunday": time(9, 0),
            "market_day_saturday": time(8, 0),
            "beach_weekend_peak": time(14, 0)
        }
        
    def get_spawn_rate_modifier(self, current_time: datetime, location_type: str = "general") -> float:
        """
        Calculate spawn rate modifier based on time and cultural patterns
        
        Args:
            current_time: Current simulation time
            location_type: Type of location (bus_stop, commercial, residential, etc.)
            
        Returns:
            Multiplier for base spawn rate (1.0 = normal, >1.0 = increased, <1.0 = decreased)
        """
        base_modifier = 1.0
        hour = current_time.hour
        minute = current_time.minute
        weekday = current_time.weekday()  # 0=Monday, 6=Sunday
        
        # Time-based patterns
        time_modifier = self._get_time_based_modifier(hour, minute, weekday)
        
        # Cultural event modifier
        event_modifier = self._get_cultural_event_modifier(current_time)
        
        # Location-specific modifier
        location_modifier = self._get_location_modifier(location_type, hour, weekday)
        
        return base_modifier * time_modifier * event_modifier * location_modifier
    
    def _get_time_based_modifier(self, hour: int, minute: int, weekday: int) -> float:
        """Calculate time-based spawn rate modifier"""
        
        # Weekend pattern (Saturday=5, Sunday=6)
        if weekday >= 5:
            return self._get_weekend_modifier(hour, weekday)
        
        # Weekday patterns
        if 6 <= hour < 9:  # Morning rush
            # Peak at 7:30 AM
            peak_hour = 7.5
            current_decimal_hour = hour + minute / 60.0
            distance_from_peak = abs(current_decimal_hour - peak_hour)
            return 2.5 * math.exp(-0.5 * (distance_from_peak ** 2))
            
        elif 12 <= hour < 14:  # Lunch time
            return 1.8 if hour == 12 else 1.4
            
        elif 16 <= hour < 19:  # Evening rush
            # Peak at 5:00 PM
            peak_hour = 17.0
            current_decimal_hour = hour + minute / 60.0
            distance_from_peak = abs(current_decimal_hour - peak_hour)
            return 2.0 * math.exp(-0.3 * (distance_from_peak ** 2))
            
        elif 9 <= hour < 12 or 14 <= hour < 16:  # Mid-day
            return 1.0
            
        elif 19 <= hour < 22:  # Evening social
            return 1.2
            
        else:  # Night/early morning
            return 0.3
    
    def _get_weekend_modifier(self, hour: int, weekday: int) -> float:
        """Calculate weekend-specific spawn rate modifier"""
        
        if weekday == 6:  # Sunday
            if 8 <= hour < 11:  # Church time
                return 1.8
            elif 11 <= hour < 16:  # Post-church social/family time
                return 1.3
            else:
                return 0.6
                
        else:  # Saturday
            if 8 <= hour < 12:  # Market/shopping time
                return 2.0
            elif 12 <= hour < 18:  # Recreational activities
                return 1.5
            elif 18 <= hour < 23:  # Saturday night social
                return 1.7
            else:
                return 0.4
    
    def _get_cultural_event_modifier(self, current_time: datetime) -> float:
        """Calculate modifier based on cultural events"""
        
        for event_name, event_info in self.cultural_events.items():
            if self._is_cultural_event_active(current_time, event_info):
                return event_info["travel_multiplier"]
        
        return 1.0
    
    def _is_cultural_event_active(self, current_time: datetime, event_info: Dict) -> bool:
        """Check if a cultural event is currently active"""
        
        if "day" in event_info:
            # Specific date event
            return (current_time.month == event_info["month"] and 
                   current_time.day == event_info["day"])
        
        elif "duration_days" in event_info:
            # Multi-day event (simplified - assumes first week of month)
            return (current_time.month == event_info["month"] and 
                   current_time.day <= event_info["duration_days"])
        
        return False
    
    def _get_location_modifier(self, location_type: str, hour: int, weekday: int) -> float:
        """Calculate location-specific spawn rate modifier"""
        
        location_modifiers = {
            "residential": self._get_residential_modifier(hour, weekday),
            "commercial": self._get_commercial_modifier(hour, weekday),
            "business": self._get_business_modifier(hour, weekday),
            "tourist": self._get_tourist_modifier(hour, weekday),
            "educational": self._get_educational_modifier(hour, weekday),
            "medical": self._get_medical_modifier(hour, weekday),
            "recreational": self._get_recreational_modifier(hour, weekday),
        }
        
        return location_modifiers.get(location_type, 1.0)
    
    def _get_residential_modifier(self, hour: int, weekday: int) -> float:
        """Residential area spawn patterns"""
        if weekday < 5:  # Weekdays
            if 6 <= hour < 9:  # Morning departure
                return 2.0
            elif 17 <= hour < 19:  # Evening return
                return 1.8
            else:
                return 0.8
        else:  # Weekends
            if 9 <= hour < 18:
                return 1.2
            else:
                return 0.9
    
    def _get_commercial_modifier(self, hour: int, weekday: int) -> float:
        """Commercial area spawn patterns"""
        if weekday < 5:  # Weekdays
            if 9 <= hour < 18:
                return 1.5
            else:
                return 0.7
        else:  # Weekends
            if 9 <= hour < 19:
                return 2.0  # Weekend shopping
            else:
                return 0.5
    
    def _get_business_modifier(self, hour: int, weekday: int) -> float:
        """Business district spawn patterns"""
        if weekday < 5:  # Weekdays only
            if 8 <= hour < 9 or 17 <= hour < 18:
                return 2.5
            elif 9 <= hour < 17:
                return 1.2
            else:
                return 0.3
        else:  # Weekends - minimal business activity
            return 0.2
    
    def _get_tourist_modifier(self, hour: int, weekday: int) -> float:
        """Tourist area spawn patterns"""
        if 9 <= hour < 22:
            return 1.8 if weekday >= 5 else 1.4  # Higher on weekends
        else:
            return 0.6
    
    def _get_educational_modifier(self, hour: int, weekday: int) -> float:
        """Educational facility spawn patterns"""
        if weekday < 5:  # School days
            if 7 <= hour < 9 or 15 <= hour < 17:
                return 3.0  # School start/end times
            elif 9 <= hour < 15:
                return 0.5  # During school hours
            else:
                return 0.3
        else:  # Weekends
            return 0.1
    
    def _get_medical_modifier(self, hour: int, weekday: int) -> float:
        """Medical facility spawn patterns"""
        if weekday < 5:  # Weekdays
            if 8 <= hour < 17:
                return 1.3
            else:
                return 0.8
        else:  # Weekends
            if 9 <= hour < 15:
                return 0.9
            else:
                return 0.6
    
    def _get_recreational_modifier(self, hour: int, weekday: int) -> float:
        """Recreational area spawn patterns"""
        if weekday >= 5:  # Weekends
            if 10 <= hour < 18:
                return 2.2
            else:
                return 1.0
        else:  # Weekdays
            if 17 <= hour < 21:
                return 1.5
            else:
                return 0.8
    
    def get_trip_purpose_distribution(self, current_time: datetime, origin_type: str) -> Dict[str, float]:
        """
        Get trip purpose distribution based on time and origin
        
        Returns:
            Dictionary mapping trip purposes to probabilities (sum = 1.0)
        """
        hour = current_time.hour
        weekday = current_time.weekday()
        
        base_distribution = {
            "work": 0.35,
            "school": 0.15,
            "shopping": 0.20,
            "medical": 0.08,
            "recreation": 0.12,
            "social": 0.10
        }
        
        # Adjust based on time patterns
        if weekday < 5:  # Weekdays
            if 6 <= hour < 9:  # Morning rush
                base_distribution.update({
                    "work": 0.60,
                    "school": 0.25,
                    "shopping": 0.05,
                    "medical": 0.03,
                    "recreation": 0.02,
                    "social": 0.05
                })
            elif 15 <= hour < 17:  # School ending
                base_distribution.update({
                    "work": 0.20,
                    "school": 0.40,
                    "shopping": 0.15,
                    "medical": 0.10,
                    "recreation": 0.10,
                    "social": 0.05
                })
            elif 17 <= hour < 19:  # Evening rush
                base_distribution.update({
                    "work": 0.15,  # Going home from work
                    "school": 0.05,
                    "shopping": 0.30,
                    "medical": 0.05,
                    "recreation": 0.25,
                    "social": 0.20
                })
        
        else:  # Weekends
            base_distribution.update({
                "work": 0.10,
                "school": 0.02,
                "shopping": 0.35,
                "medical": 0.08,
                "recreation": 0.30,
                "social": 0.15
            })
        
        return base_distribution
    
    def get_cultural_metadata(self) -> Dict:
        """Return cultural metadata for this country"""
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "work_patterns": self.work_patterns,
            "social_patterns": self.social_patterns,
            "cultural_events": self.cultural_events,
            "timezone": "America/Barbados",
            "currency": "BBD",
            "driving_side": "left",
            "public_transport_culture": "moderate_usage",
            "walking_tolerance_km": 0.8,
            "heat_factor": "high_impact"  # Affects waiting time tolerance
        }