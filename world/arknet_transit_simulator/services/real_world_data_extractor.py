#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-World Data Extraction Utility

Helps users extract and structure real-world information for route and depot simulation.
Provides templates, validation, and data collection guidance.
"""

import json
import csv
import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import math


@dataclass
class StopSurveyData:
    """Structure for stop survey data collection."""
    stop_id: str
    stop_name: str
    survey_time: datetime.datetime
    boarding_count: int
    alighting_count: int
    group_sizes: List[int]
    wait_times_seconds: List[int]
    boarding_times_seconds: List[int]
    trip_purposes: List[str]
    weather_condition: str
    notes: str = ""


@dataclass
class RouteTimingData:
    """Structure for route timing data."""
    route_id: str
    stop_id: str
    arrival_time: datetime.datetime
    departure_time: datetime.datetime
    dwell_time_seconds: int
    passenger_load: int
    distance_from_previous_km: float
    travel_time_from_previous_seconds: int
    delays_seconds: int = 0
    traffic_condition: str = "normal"


@dataclass
class DistanceAnalysisData:
    """Structure for distance-based analysis."""
    stop_id: str
    walking_distances_to_stop_m: List[int]
    passenger_origins: List[Tuple[float, float]]  # (lat, lon) coordinates
    competing_stops_distances_m: List[int]
    accessibility_barriers: List[str]
    land_use_types: List[str]


class RealWorldDataExtractor:
    """Utility for extracting and structuring real-world transit data."""
    
    def __init__(self):
        self.survey_data: List[StopSurveyData] = []
        self.timing_data: List[RouteTimingData] = []
        self.distance_data: List[DistanceAnalysisData] = []
        
        # Templates for data collection
        self.trip_purposes = [
            "commute_work", "commute_school", "shopping", "medical", 
            "leisure", "visiting", "business", "tourism", "other"
        ]
        
        self.weather_conditions = [
            "pleasant_weather", "light_rain", "heavy_rain", 
            "extreme_heat", "cloudy", "windy"
        ]
        
        self.traffic_conditions = [
            "free_flow", "light_traffic", "moderate_traffic", 
            "heavy_traffic", "congested", "stopped"
        ]
    
    def create_survey_template(self, route_ids: List[str], stops: List[str]) -> Dict[str, Any]:
        """Create a data collection template for field surveys."""
        template = {
            "survey_metadata": {
                "survey_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "surveyor_name": "",
                "route_ids": route_ids,
                "survey_period_start": "",
                "survey_period_end": "",
                "weather_condition": "",
                "special_circumstances": ""
            },
            "data_collection_instructions": {
                "passenger_counting": {
                    "count_interval_minutes": 15,
                    "observation_points": [
                        "Count passengers boarding",
                        "Count passengers alighting", 
                        "Note group sizes (1, 2, 3-4, 5+)",
                        "Estimate wait times for boarding passengers",
                        "Time how long boarding takes per passenger"
                    ]
                },
                "timing_measurements": {
                    "record_for_each_stop": [
                        "Vehicle arrival time",
                        "Door opening time", 
                        "Last passenger board/alight time",
                        "Door closing time",
                        "Departure time"
                    ]
                },
                "passenger_surveys": {
                    "ask_boarding_passengers": [
                        "Where are you traveling to?",
                        "What is the purpose of this trip?",
                        "How long did you wait for this bus?",
                        "Are you traveling alone or in a group?"
                    ]
                }
            },
            "stops_to_survey": [
                {
                    "stop_id": stop_id,
                    "stop_name": f"Stop {stop_id}",
                    "survey_periods": [
                        {"start_time": "07:00", "end_time": "09:00", "period_type": "morning_peak"},
                        {"start_time": "12:00", "end_time": "14:00", "period_type": "midday"},
                        {"start_time": "16:00", "end_time": "18:00", "period_type": "evening_peak"}
                    ],
                    "data_to_collect": {
                        "passenger_counts": [],
                        "group_observations": [],
                        "timing_data": [],
                        "walking_distances": [],
                        "nearby_attractions": []
                    }
                } for stop_id in stops
            ],
            "trip_purpose_codes": {purpose: i for i, purpose in enumerate(self.trip_purposes)},
            "weather_condition_codes": {weather: i for i, weather in enumerate(self.weather_conditions)}
        }
        
        return template
    
    def create_distance_analysis_template(self, stops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create template for distance-based passenger flow analysis."""
        template = {
            "distance_analysis_guide": {
                "methodology": "Collect data on passenger origins and walking distances to understand catchment areas",
                "tools_needed": [
                    "GPS device or smartphone with mapping app",
                    "Measuring tape or laser distance meter",
                    "Survey forms",
                    "Camera for documentation"
                ],
                "data_collection_steps": [
                    "1. Interview passengers about their origin points",
                    "2. Measure walking distances from key origins to stops",
                    "3. Identify competing transport options and their distances",
                    "4. Document accessibility barriers (stairs, curbs, etc.)",
                    "5. Note land use types around each stop"
                ]
            },
            "stops_analysis": [
                {
                    "stop_id": stop["stop_id"],
                    "stop_name": stop["stop_name"],
                    "coordinates": stop.get("coordinates", [0, 0]),
                    "distance_analysis": {
                        "primary_catchment_radius_m": 400,
                        "secondary_catchment_radius_m": 600,
                        "passenger_origins_to_survey": 20,
                        "walking_distance_measurements": [],
                        "competing_stops": {
                            "other_bus_stops": [],
                            "taxi_stands": [],
                            "private_transport_hubs": []
                        },
                        "accessibility_assessment": {
                            "wheelchair_accessible": None,
                            "steps_or_curbs": [],
                            "lighting_quality": "",
                            "weather_protection": "",
                            "safety_perception": ""
                        },
                        "land_use_survey": {
                            "residential_density": "",
                            "commercial_activity": "",
                            "institutional_buildings": [],
                            "employment_centers": [],
                            "major_attractors": []
                        }
                    }
                } for stop in stops
            ]
        }
        
        return template
    
    def add_survey_data(self, survey_data: StopSurveyData) -> None:
        """Add survey data from field collection."""
        self.survey_data.append(survey_data)
        print(f"📊 Added survey data for {survey_data.stop_name} at {survey_data.survey_time}")
    
    def add_timing_data(self, timing_data: RouteTimingData) -> None:
        """Add route timing data."""
        self.timing_data.append(timing_data)
        print(f"⏱️ Added timing data for {timing_data.route_id} at {timing_data.stop_id}")
    
    def add_distance_data(self, distance_data: DistanceAnalysisData) -> None:
        """Add distance analysis data."""
        self.distance_data.append(distance_data)
        print(f"📏 Added distance analysis for {distance_data.stop_id}")
    
    def calculate_distance_decay_parameters(self, stop_id: str) -> Dict[str, float]:
        """Calculate distance decay parameters from collected data."""
        stop_distance_data = [d for d in self.distance_data if d.stop_id == stop_id]
        
        if not stop_distance_data:
            print(f"⚠️ No distance data found for {stop_id}")
            return {}
        
        distance_data = stop_distance_data[0]
        walking_distances = distance_data.walking_distances_to_stop_m
        
        if len(walking_distances) < 5:
            print(f"⚠️ Insufficient distance data for {stop_id} (need at least 5 observations)")
            return {}
        
        # Simple exponential decay model fitting
        # In real implementation, would use proper regression
        sorted_distances = sorted(walking_distances)
        median_distance = sorted_distances[len(sorted_distances) // 2]
        max_reasonable_distance = sorted_distances[int(len(sorted_distances) * 0.9)]
        
        alpha = 0.15  # Base decay rate
        beta = 1.0 / median_distance  # Distance sensitivity
        threshold = max_reasonable_distance
        
        return {
            "decay_function": "exponential",
            "alpha": alpha,
            "beta": beta,
            "threshold_distance_m": threshold,
            "primary_radius_m": median_distance * 0.7,
            "secondary_radius_m": median_distance * 1.2,
            "tertiary_radius_m": max_reasonable_distance
        }
    
    def analyze_group_patterns(self, stop_id: str = None) -> Dict[str, Any]:
        """Analyze group boarding patterns from survey data."""
        relevant_data = self.survey_data
        if stop_id:
            relevant_data = [d for d in self.survey_data if d.stop_id == stop_id]
        
        if not relevant_data:
            return {}
        
        all_group_sizes = []
        for survey in relevant_data:
            all_group_sizes.extend(survey.group_sizes)
        
        if not all_group_sizes:
            return {}
        
        total_groups = len(all_group_sizes)
        solo_count = sum(1 for size in all_group_sizes if size == 1)
        pair_count = sum(1 for size in all_group_sizes if size == 2)
        small_group_count = sum(1 for size in all_group_sizes if 3 <= size <= 4)
        large_group_count = sum(1 for size in all_group_sizes if size >= 5)
        
        return {
            "group_size_distribution": {
                "solo": solo_count / total_groups,
                "pair": pair_count / total_groups,
                "small_group_3_4": small_group_count / total_groups,
                "large_group_5_plus": large_group_count / total_groups
            },
            "average_group_size": sum(all_group_sizes) / len(all_group_sizes),
            "total_observations": total_groups
        }
    
    def calculate_passenger_rates(self, stop_id: str) -> Dict[str, Any]:
        """Calculate passenger boarding/alighting rates from survey data."""
        stop_surveys = [s for s in self.survey_data if s.stop_id == stop_id]
        
        if not stop_surveys:
            return {}
        
        # Separate by time of day (simplified peak/off-peak)
        peak_surveys = []
        off_peak_surveys = []
        
        for survey in stop_surveys:
            hour = survey.survey_time.hour
            if (7 <= hour <= 9) or (16 <= hour <= 18):
                peak_surveys.append(survey)
            else:
                off_peak_surveys.append(survey)
        
        def calculate_rates(surveys):
            if not surveys:
                return {"rate_per_hour": 0, "variance": 0, "confidence_level": 0}
            
            boarding_counts = [s.boarding_count for s in surveys]
            alighting_counts = [s.alighting_count for s in surveys]
            
            avg_boarding = sum(boarding_counts) / len(boarding_counts)
            avg_alighting = sum(alighting_counts) / len(alighting_counts)
            
            # Assume 15-minute survey periods, scale to hourly
            boarding_rate = avg_boarding * 4
            alighting_rate = avg_alighting * 4
            
            # Simple variance calculation
            boarding_variance = (sum((x - avg_boarding) ** 2 for x in boarding_counts) / len(boarding_counts)) ** 0.5 / avg_boarding if avg_boarding > 0 else 0
            alighting_variance = (sum((x - avg_alighting) ** 2 for x in alighting_counts) / len(alighting_counts)) ** 0.5 / avg_alighting if avg_alighting > 0 else 0
            
            confidence = min(1.0, len(surveys) / 10)  # Higher confidence with more data
            
            return {
                "boarding": {
                    "rate_per_hour": boarding_rate,
                    "variance": min(0.5, boarding_variance),
                    "confidence_level": confidence
                },
                "alighting": {
                    "rate_per_hour": alighting_rate,
                    "variance": min(0.5, alighting_variance),
                    "confidence_level": confidence
                }
            }
        
        return {
            "peak_hours": calculate_rates(peak_surveys),
            "off_peak_hours": calculate_rates(off_peak_surveys),
            "total_observations": len(stop_surveys)
        }
    
    def export_to_model_format(self, output_file: str, route_ids: List[str]) -> bool:
        """Export collected data to passenger model format."""
        try:
            model_data = {
                "model_info": {
                    "name": f"extracted_model_{datetime.datetime.now().strftime('%Y%m%d')}",
                    "version": "1.0.0",
                    "route_ids": route_ids,
                    "description": "Model generated from real-world data extraction",
                    "data_sources": ["Field surveys", "Manual counts", "Timing measurements"],
                    "last_calibrated": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "validation_period": "Based on survey data"
                },
                "locations": {},
                "distance_analytics": {
                    "distance_decay_models": {},
                    "stop_spacing_effects": {
                        "close_stops_threshold_m": 300,
                        "medium_stops_threshold_m": 800,
                        "far_stops_threshold_m": 1500,
                        "spacing_multipliers": {
                            "close_stops": 0.85,
                            "medium_stops": 1.0,
                            "far_stops": 1.15
                        }
                    }
                }
            }
            
            # Process each stop with data
            unique_stops = set(s.stop_id for s in self.survey_data)
            
            for stop_id in unique_stops:
                # Calculate passenger rates
                rates = self.calculate_passenger_rates(stop_id)
                
                # Calculate distance parameters
                distance_params = self.calculate_distance_decay_parameters(stop_id)
                
                # Analyze group patterns
                group_patterns = self.analyze_group_patterns(stop_id)
                
                if rates:
                    model_data["locations"][stop_id] = {
                        "stop_id": stop_id,
                        "stop_name": f"Stop {stop_id}",
                        "passenger_rates": rates,
                        "group_characteristics": {
                            "typical_group_size": group_patterns.get("average_group_size", 1.5),
                            "group_frequency_peak": 0.3,
                            "group_frequency_off_peak": 0.4
                        },
                        "real_world_calibration": {
                            "observed_data_points": len([s for s in self.survey_data if s.stop_id == stop_id]),
                            "validation_accuracy": 0.8,
                            "data_sources": ["Field surveys"]
                        }
                    }
                
                if distance_params:
                    model_data["distance_analytics"]["distance_decay_models"][stop_id] = {
                        "stop_id": stop_id,
                        **distance_params
                    }
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported model data to {output_file}")
            print(f"📊 Included {len(unique_stops)} stops with survey data")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export model data: {e}")
            return False
    
    def export_survey_data_csv(self, output_file: str) -> bool:
        """Export survey data to CSV for analysis."""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                if not self.survey_data:
                    print("⚠️ No survey data to export")
                    return False
                
                fieldnames = [
                    'stop_id', 'stop_name', 'survey_time', 'boarding_count', 
                    'alighting_count', 'average_group_size', 'average_wait_time_s',
                    'average_boarding_time_s', 'dominant_trip_purpose', 'weather_condition', 'notes'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for survey in self.survey_data:
                    writer.writerow({
                        'stop_id': survey.stop_id,
                        'stop_name': survey.stop_name,
                        'survey_time': survey.survey_time.isoformat(),
                        'boarding_count': survey.boarding_count,
                        'alighting_count': survey.alighting_count,
                        'average_group_size': sum(survey.group_sizes) / len(survey.group_sizes) if survey.group_sizes else 0,
                        'average_wait_time_s': sum(survey.wait_times_seconds) / len(survey.wait_times_seconds) if survey.wait_times_seconds else 0,
                        'average_boarding_time_s': sum(survey.boarding_times_seconds) / len(survey.boarding_times_seconds) if survey.boarding_times_seconds else 0,
                        'dominant_trip_purpose': max(set(survey.trip_purposes), key=survey.trip_purposes.count) if survey.trip_purposes else '',
                        'weather_condition': survey.weather_condition,
                        'notes': survey.notes
                    })
            
            print(f"✅ Exported survey data to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export CSV: {e}")
            return False
    
    def generate_data_collection_guide(self, output_file: str) -> bool:
        """Generate a comprehensive data collection guide."""
        guide = {
            "title": "Real-World Transit Data Collection Guide",
            "purpose": "Extract accurate passenger flow, timing, and distance data for transit simulation",
            "preparation": {
                "equipment_needed": [
                    "Clipboard and paper forms",
                    "Stopwatch or smartphone timer",
                    "GPS device or mapping app",
                    "Camera for documentation",
                    "Measuring tape (optional)",
                    "Weather protection gear"
                ],
                "team_requirements": [
                    "Minimum 2 people per survey location",
                    "One person for passenger counting",
                    "One person for timing measurements",
                    "Additional person for passenger interviews (optional)"
                ],
                "scheduling": [
                    "Plan surveys during peak and off-peak periods",
                    "Include weekday and weekend data",
                    "Account for weather conditions",
                    "Consider special events or holidays"
                ]
            },
            "data_collection_procedures": {
                "passenger_counting": {
                    "method": "Count passengers boarding and alighting at each stop",
                    "time_intervals": "15-minute observation periods",
                    "group_identification": "Note if passengers are traveling together",
                    "recording_format": "Tally marks on prepared forms"
                },
                "timing_measurements": {
                    "vehicle_arrival": "Record when bus/vehicle arrives at stop",
                    "door_operations": "Time door opening and closing",
                    "passenger_boarding": "Measure boarding time per passenger",
                    "departure_time": "Record when vehicle leaves stop",
                    "dwell_time": "Calculate total time stopped"
                },
                "passenger_surveys": {
                    "approach": "Politely ask boarding passengers brief questions",
                    "key_questions": [
                        "Where are you traveling to?",
                        "What brings you on this trip?",
                        "How long did you wait?",
                        "Are you traveling with others?"
                    ],
                    "sampling": "Aim for 20-30% of passengers during survey period"
                },
                "distance_analysis": {
                    "walking_surveys": "Follow passengers to determine origin points",
                    "catchment_mapping": "Identify area passengers walk from",
                    "competing_options": "Note other transport alternatives",
                    "barriers": "Document accessibility challenges"
                }
            },
            "data_quality": {
                "accuracy_targets": [
                    "Passenger counts: ±5%",
                    "Timing measurements: ±10 seconds", 
                    "Distance estimates: ±50 meters"
                ],
                "validation_methods": [
                    "Compare counts between team members",
                    "Cross-check timing measurements",
                    "Verify distances with mapping apps"
                ],
                "common_errors": [
                    "Missing passengers during busy periods",
                    "Confusing boarding vs. alighting",
                    "Not accounting for through passengers",
                    "Inconsistent timing start/stop points"
                ]
            },
            "safety_considerations": [
                "Stay in safe, visible locations",
                "Wear reflective vests if near traffic",
                "Work in pairs, especially in isolated areas",
                "Have emergency contact information",
                "Respect passenger privacy"
            ],
            "data_processing": {
                "immediate_steps": [
                    "Review forms for completeness",
                    "Calculate basic statistics",
                    "Note any unusual observations",
                    "Store data securely"
                ],
                "analysis_preparation": [
                    "Enter data into standardized format",
                    "Validate against quality checks",
                    "Calculate confidence intervals",
                    "Prepare for model integration"
                ]
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(guide, f, indent=2, ensure_ascii=False)
            
            print(f"📋 Generated data collection guide: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate guide: {e}")
            return False


# Global instance
real_world_extractor = RealWorldDataExtractor()