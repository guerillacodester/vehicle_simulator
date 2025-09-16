"""
Gaussian (Normal) Distribution Plugin
=====================================

Statistical model using Gaussian/Normal distribution for passenger generation.
Ideal for modeling continuous phenomena with symmetric distributions around a mean.
"""

import numpy as np
from datetime import time
from typing import Dict, Any
from base_model import StatisticalModel


class GaussianPlugin(StatisticalModel):
    def get_distribution_statistics(self, sample_size: int = 1000) -> dict:
        """
        Generate comprehensive user-friendly summary statistics for Gaussian passenger distribution.
        """
        model_params = self.get_model_parameters()
        base_mean = model_params.get('base_mean', 10.0)
        base_std = model_params.get('base_std', 3.0)
        time_patterns = self.get_time_patterns()
        amenity_weights = self.get_amenity_weights()
        
        # Generate statistics for different time periods
        hourly_stats = self._generate_hourly_statistics(base_mean, base_std, sample_size)
        daily_stats = self._generate_daily_statistics(base_mean, base_std, time_patterns, sample_size)
        weekly_stats = self._generate_weekly_statistics(base_mean, base_std, time_patterns, sample_size)
        
        # Analyze peak times and patterns
        peak_analysis = self._analyze_peak_patterns(time_patterns, base_mean, base_std)
        
        # Generate capacity and service recommendations
        service_recommendations = self._generate_service_recommendations(hourly_stats, daily_stats)
        
        # Analyze busiest locations based on amenity weights
        location_analysis = self._analyze_location_patterns(amenity_weights)
        
        # Generate confidence and reliability metrics
        reliability_metrics = self._generate_reliability_metrics(base_mean, base_std)
        
        return {
            'overview': {
                'model_type': 'Gaussian (Normal) Distribution',
                'base_mean': round(base_mean, 2),
                'base_std': round(base_std, 2),
                'distribution_shape': 'Bell-shaped (symmetric)',
                'statistical_properties': {
                    'symmetric': True,
                    'predictable_variability': True,
                    'good_for': 'Stable demand with natural variation'
                }
            },
            'hourly_patterns': hourly_stats,
            'daily_patterns': daily_stats,
            'weekly_patterns': weekly_stats,
            'peak_analysis': peak_analysis,
            'location_analysis': location_analysis,
            'service_recommendations': service_recommendations,
            'reliability_metrics': reliability_metrics,
            'capacity_planning': {
                'conservative_capacity': hourly_stats['confidence_intervals']['95%_upper'],
                'normal_capacity': hourly_stats['percentiles']['75th'],
                'minimum_capacity': hourly_stats['percentiles']['50th'],
                'surge_capacity': hourly_stats['confidence_intervals']['99%_upper']
            },
            'operational_insights': {
                'predictability': 'High - Gaussian reliability',
                'scheduling_difficulty': 'Low',
                'resource_efficiency': 'Excellent for steady operations',
                'passenger_experience': 'Very consistent service levels'
            }
        }

    def _generate_hourly_statistics(self, mean: float, std: float, sample_size: int) -> dict:
        """Generate detailed hourly passenger statistics for Gaussian distribution"""
        samples = np.random.normal(mean, std, sample_size)
        samples = np.maximum(samples, 0)  # Ensure non-negative
        
        percentiles = {
            '5th': int(np.percentile(samples, 5)),
            '10th': int(np.percentile(samples, 10)),
            '25th': int(np.percentile(samples, 25)),
            '50th': int(np.percentile(samples, 50)),
            '75th': int(np.percentile(samples, 75)),
            '90th': int(np.percentile(samples, 90)),
            '95th': int(np.percentile(samples, 95)),
            '99th': int(np.percentile(samples, 99))
        }
        
        return {
            'mean': round(np.mean(samples), 2),
            'std_dev': round(np.std(samples), 2),
            'coefficient_of_variation': round(np.std(samples) / np.mean(samples), 3),
            'min': int(np.min(samples)),
            'max': int(np.max(samples)),
            'range': int(np.max(samples) - np.min(samples)),
            'percentiles': percentiles,
            'confidence_intervals': {
                '68%_lower': max(0, int(mean - std)),
                '68%_upper': int(mean + std),
                '95%_lower': max(0, int(mean - 1.96 * std)),
                '95%_upper': int(mean + 1.96 * std),
                '99%_lower': max(0, int(mean - 2.58 * std)),
                '99%_upper': int(mean + 2.58 * std)
            },
            'normality_tests': {
                'expected_within_1_std': '68%',
                'expected_within_2_std': '95%',
                'expected_within_3_std': '99.7%'
            },
            'description': f"Normal distribution: μ={round(mean,1)}, σ={round(std,1)} passengers/hour"
        }
    
    def _generate_daily_statistics(self, mean: float, std: float, time_patterns: dict, sample_size: int) -> dict:
        """Generate daily passenger pattern statistics for Gaussian distribution"""
        daily_total = 0
        hourly_breakdown = {}
        daily_variance = 0
        
        # Simulate 24 hours with time patterns
        for hour in range(24):
            multiplier = self._get_time_multiplier(hour, time_patterns)
            hourly_mean = mean * multiplier
            hourly_std = std * multiplier  # Scale std with mean
            
            # Sample for this hour
            hourly_samples = np.random.normal(hourly_mean, hourly_std, 100)
            hourly_samples = np.maximum(hourly_samples, 0)
            hourly_passengers = np.mean(hourly_samples)
            
            daily_total += hourly_passengers
            daily_variance += hourly_std ** 2
            
            hourly_breakdown[f"{hour:02d}:00"] = {
                'expected_passengers': round(hourly_passengers, 1),
                'std_dev': round(hourly_std, 1),
                'rate_multiplier': round(multiplier, 2),
                'confidence_range': f"{max(0, int(hourly_mean - hourly_std))}-{int(hourly_mean + hourly_std)}"
            }
        
        # Identify peak periods with confidence
        sorted_hours = sorted(hourly_breakdown.items(), 
                            key=lambda x: x[1]['expected_passengers'], reverse=True)
        
        return {
            'total_daily_passengers': round(daily_total, 0),
            'daily_std_dev': round(np.sqrt(daily_variance), 1),
            'hourly_breakdown': hourly_breakdown,
            'peak_hours': {
                'busiest': sorted_hours[0][0],
                'second_busiest': sorted_hours[1][0],
                'third_busiest': sorted_hours[2][0],
                'quietest': sorted_hours[-1][0]
            },
            'predictable_periods': {
                'morning_commute': [f"{h:02d}:00" for h in range(7, 10)],
                'lunch_period': [f"{h:02d}:00" for h in range(12, 14)],
                'evening_commute': [f"{h:02d}:00" for h in range(16, 19)],
                'off_peak': [f"{h:02d}:00" for h in range(20, 24)] + [f"{h:02d}:00" for h in range(0, 7)]
            },
            'variability_analysis': {
                'most_variable_hours': [h for h, data in hourly_breakdown.items() 
                                      if data['std_dev'] > mean * 0.8],
                'most_stable_hours': [h for h, data in hourly_breakdown.items() 
                                    if data['std_dev'] < mean * 0.3]
            }
        }
    
    def _generate_weekly_statistics(self, mean: float, std: float, time_patterns: dict, sample_size: int) -> dict:
        """Generate weekly passenger pattern statistics"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_types = {
            'Monday': 'weekday', 'Tuesday': 'weekday', 'Wednesday': 'weekday',
            'Thursday': 'weekday', 'Friday': 'weekday',
            'Saturday': 'weekend', 'Sunday': 'weekend'
        }
        
        weekly_breakdown = {}
        total_weekly = 0
        weekly_variance = 0
        
        for day in days:
            day_type = day_types[day]
            day_multiplier = 1.0 if day_type == 'weekday' else 0.75  # Weekend reduction
            daily_mean = mean * 24 * day_multiplier
            daily_std = std * np.sqrt(24) * day_multiplier  # Scale for 24 hours
            
            total_weekly += daily_mean
            weekly_variance += daily_std ** 2
            
            weekly_breakdown[day] = {
                'expected_passengers': round(daily_mean, 0),
                'std_dev': round(daily_std, 1),
                'day_type': day_type,
                'relative_to_weekday': f"{day_multiplier*100:.0f}%",
                'confidence_range': f"{max(0, int(daily_mean - daily_std))}-{int(daily_mean + daily_std)}"
            }
        
        return {
            'total_weekly_passengers': round(total_weekly, 0),
            'weekly_std_dev': round(np.sqrt(weekly_variance), 1),
            'daily_breakdown': weekly_breakdown,
            'weekday_average': round(np.mean([weekly_breakdown[day]['expected_passengers'] 
                                           for day in days[:5]]), 0),
            'weekend_average': round(np.mean([weekly_breakdown[day]['expected_passengers'] 
                                            for day in days[5:]]), 0),
            'consistency_metrics': {
                'weekday_coefficient_of_variation': round(
                    np.std([weekly_breakdown[day]['expected_passengers'] for day in days[:5]]) /
                    np.mean([weekly_breakdown[day]['expected_passengers'] for day in days[:5]]), 3),
                'most_predictable_day': min(days, key=lambda d: weekly_breakdown[d]['std_dev']),
                'least_predictable_day': max(days, key=lambda d: weekly_breakdown[d]['std_dev'])
            }
        }
    
    def _analyze_peak_patterns(self, time_patterns: dict, mean: float, std: float) -> dict:
        """Analyze peak hour patterns with Gaussian characteristics"""
        peak_hours = []
        peak_intensities = {}
        
        for pattern_name, pattern in time_patterns.items():
            if pattern.get('multiplier', 1.0) > 1.3:  # Significant peaks for Gaussian
                hours = pattern.get('hours', [])
                peak_hours.extend(hours)
                for h in hours:
                    peak_intensities[h] = pattern.get('multiplier', 1.0)
        
        return {
            'identified_peaks': list(set(peak_hours)),
            'peak_reliability': {
                'highly_predictable': [h for h, mult in peak_intensities.items() if mult < 1.8],
                'moderately_predictable': [h for h, mult in peak_intensities.items() if 1.8 <= mult < 2.5],
                'variable_peaks': [h for h, mult in peak_intensities.items() if mult >= 2.5]
            },
            'confidence_levels': {
                'peak_hour_confidence': '95% (Gaussian reliability)',
                'capacity_planning_confidence': '99% (2.58σ buffer)',
                'service_level_confidence': '90% (operational target)'
            },
            'gaussian_advantages': {
                'symmetric_variation': 'Equal likelihood of above/below mean demand',
                'predictable_extremes': 'Rare events follow known probability rules',
                'planning_reliability': 'Confidence intervals provide planning certainty'
            }
        }
    
    def _analyze_location_patterns(self, amenity_weights: dict) -> dict:
        """Analyze location patterns with Gaussian distribution characteristics"""
        sorted_amenities = sorted(amenity_weights.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate statistics for amenity weights
        weights = list(amenity_weights.values())
        if not weights:
            return {'error': 'No amenity weights available'}
            
        weight_mean = np.mean(weights)
        weight_std = np.std(weights)
        
        # Categorize based on standard deviations from mean
        high_traffic = [(k, v) for k, v in sorted_amenities if v > weight_mean + weight_std]
        medium_traffic = [(k, v) for k, v in sorted_amenities 
                         if weight_mean - 0.5*weight_std <= v <= weight_mean + weight_std]
        low_traffic = [(k, v) for k, v in sorted_amenities if v < weight_mean - 0.5*weight_std]
        
        return {
            'statistical_categorization': {
                'high_traffic_generators': {
                    'locations': [k for k, v in high_traffic],
                    'threshold': f">{round(weight_mean + weight_std, 1)} (mean + 1σ)",
                    'average_weight': round(np.mean([v for k, v in high_traffic]), 1) if high_traffic else 0,
                    'reliability': 'Consistently high demand'
                },
                'normal_traffic_generators': {
                    'locations': [k for k, v in medium_traffic],
                    'threshold': f"{round(weight_mean - 0.5*weight_std, 1)}-{round(weight_mean + weight_std, 1)}",
                    'average_weight': round(np.mean([v for k, v in medium_traffic]), 1) if medium_traffic else 0,
                    'reliability': 'Predictable standard demand'
                },
                'low_traffic_generators': {
                    'locations': [k for k, v in low_traffic],
                    'threshold': f"<{round(weight_mean - 0.5*weight_std, 1)} (below mean)",
                    'average_weight': round(np.mean([v for k, v in low_traffic]), 1) if low_traffic else 0,
                    'reliability': 'Consistently low demand'
                }
            },
            'gaussian_location_insights': {
                'weight_distribution': {
                    'mean_weight': round(weight_mean, 1),
                    'std_weight': round(weight_std, 1),
                    'coefficient_of_variation': round(weight_std / weight_mean, 3) if weight_mean > 0 else 0
                },
                'outlier_analysis': {
                    'exceptional_generators': [k for k, v in sorted_amenities 
                                             if v > weight_mean + 2*weight_std],
                    'exceptional_threshold': round(weight_mean + 2*weight_std, 1)
                }
            },
            'top_generators_with_confidence': [
                {
                    'location': k,
                    'weight': v,
                    'confidence_category': 'High' if v > weight_mean + weight_std 
                                         else 'Medium' if v > weight_mean 
                                         else 'Low'
                } for k, v in sorted_amenities[:10]
            ]
        }
    
    def _generate_service_recommendations(self, hourly_stats: dict, daily_stats: dict) -> dict:
        """Generate service planning recommendations based on Gaussian reliability"""
        mean_hourly = hourly_stats['mean']
        ci_95_upper = hourly_stats['confidence_intervals']['95%_upper']
        ci_99_upper = hourly_stats['confidence_intervals']['99%_upper']
        
        return {
            'capacity_recommendations': {
                'standard_capacity': {
                    'size': max(20, int(ci_95_upper * 1.1)),
                    'confidence': '95%',
                    'explanation': 'Handles 95% of demand scenarios with 10% buffer'
                },
                'peak_capacity': {
                    'size': max(30, int(ci_99_upper * 1.2)),
                    'confidence': '99%',
                    'explanation': 'Handles extreme demand with high reliability'
                },
                'minimum_capacity': {
                    'size': max(15, int(mean_hourly)),
                    'confidence': '50%',
                    'explanation': 'Covers average demand only'
                }
            },
            'service_frequency': {
                'base_frequency': f"Every {max(10, int(60/(mean_hourly/2)))} minutes",
                'peak_frequency': f"Every {max(5, int(60/(ci_95_upper/3)))} minutes",
                'reliability_note': 'Gaussian patterns allow predictable scheduling'
            },
            'reliability_planning': {
                'service_reliability_target': '95% on-time performance',
                'capacity_utilization_target': '75% average, 90% peak',
                'passenger_satisfaction': 'High due to predictable service',
                'operational_efficiency': 'Excellent - minimal unexpected variations'
            },
            'gaussian_advantages_for_operations': [
                'Highly predictable demand patterns',
                'Symmetric variations allow balanced planning',
                'Statistical confidence intervals guide capacity decisions',
                'Rare extreme events are mathematically quantifiable',
                'Easy to calculate service level probabilities'
            ]
        }
    
    def _generate_reliability_metrics(self, mean: float, std: float) -> dict:
        """Generate reliability and confidence metrics specific to Gaussian distribution"""
        cv = std / mean if mean > 0 else 0
        
        return {
            'predictability_score': {
                'coefficient_of_variation': round(cv, 3),
                'predictability_rating': (
                    'Excellent' if cv < 0.2 else
                    'Good' if cv < 0.4 else
                    'Fair' if cv < 0.6 else 'Poor'
                ),
                'interpretation': f"Standard deviation is {cv*100:.1f}% of mean"
            },
            'service_level_probabilities': {
                'prob_demand_within_normal_capacity': '68%',
                'prob_demand_within_enhanced_capacity': '95%',
                'prob_demand_within_surge_capacity': '99.7%',
                'prob_extreme_demand_event': '0.3%'
            },
            'planning_confidence': {
                'short_term_forecast_accuracy': 'Very High',
                'medium_term_planning_reliability': 'High',
                'long_term_trend_prediction': 'Good',
                'seasonal_adjustment_ease': 'Straightforward'
            },
            'operational_kpis': {
                'expected_service_consistency': '95%+',
                'capacity_utilization_predictability': 'Very High',
                'resource_allocation_efficiency': 'Optimal',
                'passenger_wait_time_variability': 'Low'
            }
        }
    
    def _get_time_multiplier(self, hour: int, time_patterns: dict) -> float:
        """Get time multiplier for a specific hour"""
        for pattern_name, pattern in time_patterns.items():
            if hour in pattern.get('hours', []):
                return pattern.get('multiplier', 1.0)
        return 1.0
    """
    Gaussian (Normal) distribution model for passenger generation
    
    The Gaussian distribution is ideal for modeling:
    - Continuous passenger flow rates
    - Symmetric distributions around peak times
    - Natural variation with defined mean and variance
    """
    
    def get_model_type(self) -> str:
        return "gaussian"
    
    def calculate_base_rate(self, location_data: Dict[str, Any], 
                          environmental_factors: Dict[str, float]) -> float:
        """
        Calculate base rate using Gaussian model parameters
        
        Rate is calculated as the mean (μ) of the Gaussian distribution
        based on location and amenity characteristics
        """
        amenity_weights = self.get_amenity_weights()
        model_params = self.get_model_parameters()
        
        # Base mean (μ)
        base_mean = model_params.get('base_mean', 10.0)
        
        # Calculate amenity contribution
        amenity_factor = 1.0
        nearby_amenities = location_data.get('nearby_amenities', [])
        
        for amenity in nearby_amenities:
            amenity_type = amenity.get('type', 'unknown')
            amenity_weight = amenity_weights.get(amenity_type, amenity_weights.get('default', 1.0))
            distance_factor = amenity.get('distance_factor', 1.0)
            
            # Gaussian uses additive contributions
            amenity_factor += amenity_weight * distance_factor * 0.1
        
        # Apply location characteristics
        location_factor = self._calculate_location_factor(location_data)
        
        # Calculate base rate (mean μ for Gaussian)
        base_rate = base_mean * amenity_factor * location_factor
        
        # Apply environmental factors
        base_rate = self.apply_environmental_factors(base_rate, environmental_factors)
        
        return max(0.5, base_rate)  # Ensure minimum rate
    
    def apply_temporal_weights(self, base_rate: float, current_time: time, 
                             day_type: str = 'weekday') -> float:
        """
        Apply time-based weights using Gaussian temporal functions
        
        Time patterns are applied as shifts to the mean of the distribution
        """
        time_patterns = self.get_time_patterns()
        model_params = self.get_model_parameters()
        
        # Get current hour
        current_hour = current_time.hour
        current_minute = current_time.minute
        time_decimal = current_hour + current_minute / 60.0
        
        # Calculate time-based multiplier using Gaussian peaks
        time_multiplier = self._calculate_gaussian_time_multiplier(
            time_decimal, time_patterns, day_type
        )
        
        # Apply temporal smoothing
        temporal_smoothing = model_params.get('temporal_smoothing', 0.1)
        if temporal_smoothing > 0:
            # Add smooth variation to avoid sharp transitions
            smooth_factor = 1.0 + np.sin(time_decimal * np.pi / 12) * temporal_smoothing
            time_multiplier *= smooth_factor
        
        return base_rate * max(0.1, time_multiplier)
    
    def generate_passengers(self, weighted_rate: float, time_interval_seconds: int) -> int:
        """
        Generate passengers using Gaussian distribution
        
        Args:
            weighted_rate: Mean (μ) parameter for the distribution
            time_interval_seconds: Time interval for generation
            
        Returns:
            Number of passengers (rounded Gaussian random variable)
        """
        model_params = self.get_model_parameters()
        
        # Convert rate to match time interval
        interval_hours = time_interval_seconds / 3600.0
        mean_passengers = weighted_rate * interval_hours
        
        # Calculate standard deviation
        base_std = model_params.get('base_std_dev', 2.0)
        std_multiplier = model_params.get('std_dev_multiplier', 0.3)
        std_dev = base_std + (mean_passengers * std_multiplier)
        
        # Apply rate variation if configured
        rate_variation = model_params.get('rate_variation', 0.0)
        if rate_variation > 0:
            mean_passengers *= np.random.normal(1.0, rate_variation)
            mean_passengers = max(0.1, mean_passengers)
        
        # Generate Gaussian random variable
        try:
            passengers_float = np.random.normal(mean_passengers, std_dev)
            
            # Ensure non-negative and apply constraints
            passengers = max(0, int(round(passengers_float)))
            
            max_passengers = model_params.get('max_passengers_per_interval', 200)
            passengers = min(passengers, max_passengers)
            
            return passengers
            
        except Exception as e:
            # Fallback to deterministic approach
            return max(0, int(round(mean_passengers)))
    
    def _calculate_gaussian_time_multiplier(self, time_decimal: float, 
                                          time_patterns: Dict[str, Dict], 
                                          day_type: str) -> float:
        """
        Calculate time multiplier using Gaussian peaks for different time periods
        """
        model_params = self.get_model_parameters()
        
        # Default multiplier
        base_multiplier = 1.0
        
        # Define Gaussian peaks for different periods
        peak_definitions = model_params.get('time_peaks', {
            'morning_peak': {'center': 8.0, 'width': 1.5, 'intensity': 2.8},
            'lunch_peak': {'center': 13.0, 'width': 1.0, 'intensity': 1.4},
            'evening_peak': {'center': 17.5, 'width': 1.8, 'intensity': 2.5},
            'night_low': {'center': 2.0, 'width': 3.0, 'intensity': 0.2}
        })
        
        total_multiplier = 0.5  # Base level
        
        # Calculate contribution from each Gaussian peak
        for peak_name, peak_config in peak_definitions.items():
            center = peak_config['center']
            width = peak_config['width']
            intensity = peak_config['intensity']
            
            # Apply day type adjustment
            day_adjustment = 1.0
            if peak_name in time_patterns:
                day_adjustments = time_patterns[peak_name].get('day_adjustments', {})
                day_adjustment = day_adjustments.get(day_type, 1.0)
            
            # Calculate Gaussian contribution
            gaussian_value = intensity * np.exp(-0.5 * ((time_decimal - center) / width) ** 2)
            total_multiplier += gaussian_value * day_adjustment
        
        return max(0.1, total_multiplier)
    
    def _calculate_location_factor(self, location_data: Dict[str, Any]) -> float:
        """Calculate location-specific factors for Gaussian mean"""
        model_params = self.get_model_parameters()
        
        factor = 1.0
        
        # Population density factor (additive for Gaussian)
        population_density = location_data.get('population_density', 1.0)
        density_weight = model_params.get('population_density_weight', 0.2)
        factor += population_density * density_weight
        
        # Accessibility factor
        accessibility = location_data.get('accessibility_score', 1.0)
        accessibility_weight = model_params.get('accessibility_weight', 0.15)
        factor += accessibility * accessibility_weight
        
        # Stop type factor (multiplicative)
        stop_type = location_data.get('stop_type', 'bus_stop')
        stop_type_weights = model_params.get('stop_type_weights', {})
        stop_factor = stop_type_weights.get(stop_type, 1.0)
        factor *= stop_factor
        
        return max(0.1, factor)
    
    def get_model_statistics(self, weighted_rate: float) -> Dict[str, float]:
        """
        Get statistical properties of the Gaussian model
        
        Args:
            weighted_rate: Current mean (μ) parameter
            
        Returns:
            Dictionary of statistical properties
        """
        model_params = self.get_model_parameters()
        
        base_std = model_params.get('base_std_dev', 2.0)
        std_multiplier = model_params.get('std_dev_multiplier', 0.3)
        std_dev = base_std + (weighted_rate * std_multiplier)
        
        return {
            'mean': weighted_rate,
            'std_dev': std_dev,
            'variance': std_dev ** 2,
            'coefficient_of_variation': std_dev / weighted_rate if weighted_rate > 0 else float('inf'),
            'expected_range_68pct': (weighted_rate - std_dev, weighted_rate + std_dev),
            'expected_range_95pct': (weighted_rate - 2*std_dev, weighted_rate + 2*std_dev)
        }
    
    def predict_passengers_distribution(self, weighted_rate: float, 
                                      time_interval_seconds: int, 
                                      num_samples: int = 1000) -> Dict[str, Any]:
        """
        Predict passenger distribution for planning purposes
        
        Args:
            weighted_rate: Mean parameter
            time_interval_seconds: Time interval
            num_samples: Number of samples for distribution
            
        Returns:
            Distribution statistics and percentiles
        """
        model_params = self.get_model_parameters()
        
        interval_hours = time_interval_seconds / 3600.0
        mean_passengers = weighted_rate * interval_hours
        
        base_std = model_params.get('base_std_dev', 2.0)
        std_multiplier = model_params.get('std_dev_multiplier', 0.3)
        std_dev = base_std + (mean_passengers * std_multiplier)
        
        # Generate samples (ensure non-negative)
        raw_samples = np.random.normal(mean_passengers, std_dev, num_samples)
        samples = np.maximum(0, raw_samples).astype(int)
        
        return {
            'mean_parameter': mean_passengers,
            'std_dev_parameter': std_dev,
            'actual_mean': np.mean(samples),
            'actual_std': np.std(samples),
            'min': int(np.min(samples)),
            'max': int(np.max(samples)),
            'percentiles': {
                '10th': int(np.percentile(samples, 10)),
                '25th': int(np.percentile(samples, 25)),
                '50th': int(np.percentile(samples, 50)),
                '75th': int(np.percentile(samples, 75)),
                '90th': int(np.percentile(samples, 90)),
                '95th': int(np.percentile(samples, 95))
            },
            'negative_samples_clipped': int(np.sum(raw_samples < 0))
        }
    
    def calculate_confidence_intervals(self, weighted_rate: float, 
                                     time_interval_seconds: int,
                                     confidence_level: float = 0.95) -> Dict[str, tuple]:
        """
        Calculate confidence intervals for passenger predictions
        
        Args:
            weighted_rate: Mean parameter
            time_interval_seconds: Time interval
            confidence_level: Confidence level (0.95 for 95%)
            
        Returns:
            Dictionary with confidence intervals
        """
        from scipy import stats
        
        model_params = self.get_model_parameters()
        
        interval_hours = time_interval_seconds / 3600.0
        mean_passengers = weighted_rate * interval_hours
        
        base_std = model_params.get('base_std_dev', 2.0)
        std_multiplier = model_params.get('std_dev_multiplier', 0.3)
        std_dev = base_std + (mean_passengers * std_multiplier)
        
        # Calculate z-score for confidence level
        alpha = 1 - confidence_level
        z_score = stats.norm.ppf(1 - alpha/2)
        
        # Calculate intervals
        margin_of_error = z_score * std_dev
        
        return {
            'mean_estimate': (
                max(0, mean_passengers - margin_of_error),
                mean_passengers + margin_of_error
            ),
            'prediction_interval': (
                max(0, mean_passengers - 2*std_dev),
                mean_passengers + 2*std_dev
            ),
            'confidence_level': confidence_level
        }