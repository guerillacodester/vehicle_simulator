#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Passenger Model Loader

Loads and processes JSON-based passenger models with real-time factor adjustments.
Handles complex passenger flow calculations based on time, location, events, and conditions.
"""

import json
import os
import datetime
import math
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import jsonschema
from pathlib import Path


@dataclass
class PassengerFlowResult:
    """Result of passenger flow calculation."""
    location_id: str
    timestamp: datetime.datetime
    boarding_rate: float  # passengers per hour
    alighting_rate: float  # passengers per hour
    expected_boarding_count: int
    expected_alighting_count: int
    confidence_level: float
    applied_factors: Dict[str, float]
    trip_purposes: Dict[str, float]  # percentage breakdown


class PassengerModelLoader:
    """Dynamic loader for passenger analytics models."""
    
    def __init__(self, model_directory: str = None):
        self.model_directory = model_directory or self._get_default_model_dir()
        self.loaded_models: Dict[str, Dict] = {}
        self.schema: Optional[Dict] = None
        self.current_conditions: Dict[str, Any] = {}
        
        # Load schema for validation
        self._load_schema()
    
    def _get_default_model_dir(self) -> str:
        """Get default model directory."""
        current_dir = Path(__file__).parent
        return str(current_dir / "models" / "passenger_analytics")
    
    def _load_schema(self) -> bool:
        """Load JSON schema for model validation."""
        try:
            schema_path = os.path.join(self.model_directory, "schema.json")
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self.schema = json.load(f)
                return True
        except Exception as e:
            print(f"⚠️ Could not load schema: {e}")
        return False
    
    def load_model(self, model_file: str, validate: bool = True) -> bool:
        """Load a passenger model from JSON file."""
        try:
            model_path = os.path.join(self.model_directory, model_file)
            if not os.path.exists(model_path):
                model_path = model_file  # Try as absolute path
            
            with open(model_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            # Validate against schema if available
            if validate and self.schema:
                try:
                    jsonschema.validate(model_data, self.schema)
                    print(f"✅ Model validation passed: {model_file}")
                except jsonschema.ValidationError as e:
                    print(f"❌ Model validation failed: {e.message}")
                    return False
            
            # Store loaded model
            model_name = model_data["model_info"]["name"]
            self.loaded_models[model_name] = model_data
            
            print(f"📊 Loaded passenger model: {model_name} v{model_data['model_info']['version']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model {model_file}: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available model files."""
        try:
            if not os.path.exists(self.model_directory):
                return []
            return [f for f in os.listdir(self.model_directory) 
                   if f.endswith('.json') and f != 'schema.json']
        except Exception:
            return []
    
    def list_loaded_models(self) -> List[str]:
        """List currently loaded models."""
        return list(self.loaded_models.keys())
    
    def update_conditions(self, conditions: Dict[str, Any]) -> None:
        """Update current real-time conditions."""
        self.current_conditions.update(conditions)
        print(f"🔄 Updated conditions: {list(conditions.keys())}")
    
    def calculate_passenger_flow(self, 
                               model_name: str,
                               location_id: str,
                               target_time: datetime.datetime,
                               duration_minutes: int = 60) -> Optional[PassengerFlowResult]:
        """Calculate passenger flow for a specific location and time."""
        
        if model_name not in self.loaded_models:
            print(f"❌ Model '{model_name}' not loaded")
            return None
        
        model = self.loaded_models[model_name]
        
        if location_id not in model["locations"]:
            print(f"❌ Location '{location_id}' not found in model")
            return None
        
        location = model["locations"][location_id]
        
        # Calculate all applicable factors
        factors = self._calculate_time_factors(model, target_time)
        factors.update(self._calculate_seasonal_factors(model, location, target_time))
        factors.update(self._calculate_event_factors(model, location, target_time))
        factors.update(self._calculate_realtime_factors(model))
        
        # Base passenger rates
        base_boarding = self._get_base_rate(location, "boarding", factors.get("is_peak", False))
        base_alighting = self._get_base_rate(location, "alighting", factors.get("is_peak", False))
        
        # Apply all factors
        final_boarding_rate = base_boarding["rate"]
        final_alighting_rate = base_alighting["rate"]
        
        for factor_name, factor_value in factors.items():
            if factor_name not in ["is_peak", "day_type"]:
                final_boarding_rate *= factor_value
                final_alighting_rate *= factor_value
        
        # Add variance
        boarding_variance = random.uniform(1 - base_boarding["variance"], 1 + base_boarding["variance"])
        alighting_variance = random.uniform(1 - base_alighting["variance"], 1 + base_alighting["variance"])
        
        final_boarding_rate *= boarding_variance
        final_alighting_rate *= alighting_variance
        
        # Calculate expected counts for the duration
        duration_hours = duration_minutes / 60.0
        expected_boarding = int(final_boarding_rate * duration_hours)
        expected_alighting = int(final_alighting_rate * duration_hours)
        
        # Calculate trip purpose breakdown
        trip_purposes = self._calculate_trip_purposes(model, target_time, factors.get("is_peak", False))
        
        # Calculate confidence
        confidence = min(base_boarding["confidence"], base_alighting["confidence"])
        
        return PassengerFlowResult(
            location_id=location_id,
            timestamp=target_time,
            boarding_rate=final_boarding_rate,
            alighting_rate=final_alighting_rate,
            expected_boarding_count=expected_boarding,
            expected_alighting_count=expected_alighting,
            confidence_level=confidence,
            applied_factors=factors,
            trip_purposes=trip_purposes
        )
    
    def _calculate_time_factors(self, model: Dict, target_time: datetime.datetime) -> Dict[str, float]:
        """Calculate time-based factors (peak hours, day type)."""
        factors = {}
        
        # Check peak hours
        is_peak = False
        peak_multiplier = 1.0
        
        time_patterns = model.get("time_patterns", {})
        peak_hours = time_patterns.get("peak_hours", [])
        
        current_time = target_time.strftime("%H:%M")
        current_day = target_time.strftime("%A").lower()
        
        for peak_period in peak_hours:
            if current_day in peak_period.get("days_of_week", []):
                start_time = peak_period["start_time"]
                end_time = peak_period["end_time"]
                
                if self._time_in_range(current_time, start_time, end_time):
                    is_peak = True
                    peak_multiplier = peak_period["multiplier"]
                    break
        
        factors["is_peak"] = is_peak
        factors["peak_multiplier"] = peak_multiplier
        
        # Day type factors
        day_types = time_patterns.get("day_types", {})
        if self._is_holiday(target_time):
            factors["day_type_multiplier"] = day_types.get("holiday", 1.0)
            factors["day_type"] = "holiday"
        elif current_day == "sunday":
            factors["day_type_multiplier"] = day_types.get("sunday", 1.0)
            factors["day_type"] = "sunday"
        elif current_day == "saturday":
            factors["day_type_multiplier"] = day_types.get("saturday", 1.0)
            factors["day_type"] = "saturday"
        else:
            factors["day_type_multiplier"] = day_types.get("weekday", 1.0)
            factors["day_type"] = "weekday"
        
        return factors
    
    def _calculate_seasonal_factors(self, model: Dict, location: Dict, target_time: datetime.datetime) -> Dict[str, float]:
        """Calculate seasonal adjustment factors."""
        factors = {}
        
        seasonal_factors = location.get("seasonal_factors", {})
        month = target_time.month
        
        if month in [3, 4, 5]:  # Spring
            factors["seasonal_multiplier"] = seasonal_factors.get("spring", 1.0)
        elif month in [6, 7, 8]:  # Summer
            factors["seasonal_multiplier"] = seasonal_factors.get("summer", 1.0)
        elif month in [9, 10, 11]:  # Autumn
            factors["seasonal_multiplier"] = seasonal_factors.get("autumn", 1.0)
        else:  # Winter
            factors["seasonal_multiplier"] = seasonal_factors.get("winter", 1.0)
        
        return factors
    
    def _calculate_event_factors(self, model: Dict, location: Dict, target_time: datetime.datetime) -> Dict[str, float]:
        """Calculate special event factors."""
        factors = {}
        event_multiplier = 1.0
        
        special_events = location.get("special_events", [])
        
        for event in special_events:
            if self._event_applies(event, target_time):
                event_multiplier *= event["multiplier"]
                factors[f"event_{event['name'].lower().replace(' ', '_')}"] = event["multiplier"]
        
        factors["event_multiplier"] = event_multiplier
        return factors
    
    def _calculate_realtime_factors(self, model: Dict) -> Dict[str, float]:
        """Calculate real-time adjustment factors based on current conditions."""
        factors = {}
        
        real_time_adjustments = model.get("real_time_adjustments", {})
        
        # Weather impact
        weather_impact = real_time_adjustments.get("weather_impact", {})
        current_weather = self.current_conditions.get("weather", "pleasant_weather")
        factors["weather_multiplier"] = weather_impact.get(current_weather, 1.0)
        
        # Service disruptions
        service_disruptions = real_time_adjustments.get("service_disruptions", {})
        current_service = self.current_conditions.get("service_status", "normal")
        factors["service_multiplier"] = service_disruptions.get(current_service, 1.0)
        
        # Economic factors
        economic_factors = real_time_adjustments.get("economic_factors", {})
        current_economic = self.current_conditions.get("economic_condition", "normal")
        factors["economic_multiplier"] = economic_factors.get(current_economic, 1.0)
        
        # Infrastructure events
        infrastructure_events = real_time_adjustments.get("infrastructure_events", {})
        current_infrastructure = self.current_conditions.get("infrastructure_status", "normal")
        factors["infrastructure_multiplier"] = infrastructure_events.get(current_infrastructure, 1.0)
        
        return factors
    
    def _get_base_rate(self, location: Dict, rate_type: str, is_peak: bool) -> Dict[str, float]:
        """Get base passenger rate for location."""
        rates = location["passenger_rates"][rate_type]
        
        if is_peak:
            rate_data = rates["peak_hours"]
        else:
            rate_data = rates["off_peak_hours"]
        
        return {
            "rate": rate_data["rate_per_hour"],
            "variance": rate_data["variance"],
            "confidence": rate_data["confidence_level"]
        }
    
    def _calculate_trip_purposes(self, model: Dict, target_time: datetime.datetime, is_peak: bool) -> Dict[str, float]:
        """Calculate trip purpose breakdown."""
        demand_profiles = model.get("demand_profiles", {})
        trip_purposes = {}
        
        for purpose, profile in demand_profiles.items():
            base_percentage = profile["percentage"]
            
            # Adjust based on peak preference
            if profile.get("peak_preference", False) and is_peak:
                adjusted_percentage = base_percentage * 1.3
            elif not profile.get("peak_preference", False) and not is_peak:
                adjusted_percentage = base_percentage * 1.2
            else:
                adjusted_percentage = base_percentage * 0.8
            
            trip_purposes[purpose] = adjusted_percentage
        
        # Normalize to 100%
        total = sum(trip_purposes.values())
        if total > 0:
            trip_purposes = {k: (v/total) * 100 for k, v in trip_purposes.items()}
        
        return trip_purposes
    
    def _time_in_range(self, current_time: str, start_time: str, end_time: str) -> bool:
        """Check if current time is within range."""
        try:
            current = datetime.datetime.strptime(current_time, "%H:%M").time()
            start = datetime.datetime.strptime(start_time, "%H:%M").time()
            end = datetime.datetime.strptime(end_time, "%H:%M").time()
            
            if start <= end:
                return start <= current <= end
            else:  # Overnight range
                return current >= start or current <= end
        except:
            return False
    
    def _is_holiday(self, target_time: datetime.datetime) -> bool:
        """Check if date is a holiday (simplified)."""
        # This should be enhanced with actual holiday calendar
        holidays = [
            (1, 1),   # New Year
            (4, 28),  # National Heroes Day
            (5, 1),   # Labour Day
            (8, 1),   # Emancipation Day
            (11, 30), # Independence Day
            (12, 25), # Christmas
            (12, 26)  # Boxing Day
        ]
        
        return (target_time.month, target_time.day) in holidays
    
    def _event_applies(self, event: Dict, target_time: datetime.datetime) -> bool:
        """Check if special event applies to target time."""
        date_pattern = event["date_pattern"]
        
        # Simple pattern matching - this could be enhanced
        if date_pattern == "july_august_weekends":
            return (target_time.month in [7, 8] and 
                   target_time.weekday() >= 5)
        elif date_pattern == "november_30":
            return (target_time.month == 11 and target_time.day == 30)
        elif date_pattern == "first_saturday_monthly":
            return (target_time.weekday() == 5 and 
                   1 <= target_time.day <= 7)
        elif date_pattern == "weekday_mornings":
            return (target_time.weekday() < 5 and 
                   6 <= target_time.hour <= 10)
        
        return False
    
    def generate_passenger_schedule(self, 
                                  model_name: str,
                                  start_time: datetime.datetime,
                                  end_time: datetime.datetime,
                                  interval_minutes: int = 30) -> List[PassengerFlowResult]:
        """Generate passenger flow schedule for time range."""
        results = []
        current_time = start_time
        
        if model_name not in self.loaded_models:
            print(f"❌ Model '{model_name}' not loaded")
            return results
        
        model = self.loaded_models[model_name]
        locations = list(model["locations"].keys())
        
        while current_time < end_time:
            for location_id in locations:
                flow_result = self.calculate_passenger_flow(
                    model_name, location_id, current_time, interval_minutes
                )
                if flow_result:
                    results.append(flow_result)
            
            current_time += datetime.timedelta(minutes=interval_minutes)
        
        return results


# Global instance
passenger_model_loader = PassengerModelLoader()