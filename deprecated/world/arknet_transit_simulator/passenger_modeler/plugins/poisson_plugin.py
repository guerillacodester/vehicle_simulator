"""
Poisson Distribution Plugin
===========================

Statistical model using Poisson distribution for passenger generation.
Ideal for modeling discrete events (passenger arrivals) over time intervals.
"""

import numpy as np
import math
from datetime import time
from typing import Dict, Any
from base_model import StatisticalModel


class PoissonPlugin(StatisticalModel):
    def get_distribution_statistics(self, sample_size: int = 1000) -> dict:
        """
        Generate comprehensive user-friendly summary statistics for passenger distribution.
        """
        model_params = self.get_model_parameters()
        base_lambda = model_params.get('base_lambda', 5.0)
        time_patterns = self.get_time_patterns()
        amenity_weights = self.get_amenity_weights()
        
        # Generate statistics for different time periods
        hourly_stats = self._generate_hourly_statistics(base_lambda, sample_size)
        daily_stats = self._generate_daily_statistics(base_lambda, time_patterns, sample_size)
        weekly_stats = self._generate_weekly_statistics(base_lambda, time_patterns, sample_size)
        
        # Analyze peak times and patterns
        peak_analysis = self._analyze_peak_patterns(time_patterns, base_lambda)
        
        # Generate capacity and service recommendations
        service_recommendations = self._generate_service_recommendations(hourly_stats, daily_stats)
        
        # Analyze busiest locations based on amenity weights
        location_analysis = self._analyze_location_patterns(amenity_weights)
        
        return {
            'overview': {
                'model_type': 'Poisson Distribution',
                'base_rate': round(base_lambda, 2),
                'distribution_shape': 'Right-skewed (typical for arrival processes)',
                'statistical_properties': {
                    'mean_equals_variance': True,
                    'memoryless': True,
                    'good_for': 'Independent arrival events'
                }
            },
            'hourly_patterns': hourly_stats,
            'daily_patterns': daily_stats,
            'weekly_patterns': weekly_stats,
            'peak_analysis': peak_analysis,
            'location_analysis': location_analysis,
            'service_recommendations': service_recommendations,
            'capacity_planning': {
                'low_demand_capacity': hourly_stats['percentiles']['25th'],
                'normal_capacity': hourly_stats['percentiles']['75th'],
                'peak_capacity': hourly_stats['percentiles']['95th'],
                'surge_capacity': max(hourly_stats['max'], int(hourly_stats['mean'] * 2.5))
            },
            'operational_insights': {
                'predictability': 'Moderate - Poisson variability',
                'scheduling_difficulty': 'Medium',
                'resource_efficiency': 'Good for steady demand',
                'passenger_experience': 'Consistent wait times'
            }
        }
    
    def _generate_hourly_statistics(self, base_lambda: float, sample_size: int) -> dict:
        """Generate detailed hourly passenger statistics"""
        stats = self.predict_passengers_distribution(base_lambda, 3600, sample_size)
        
        # Helper to compute (truncated) CDF using direct summation; safe for moderate lambda (<100)
        def _poisson_cdf(k: int, lam: float) -> float:
            k = int(k)
            if k < 0:
                return 0.0
            # For large lambda, use normal approximation with continuity correction
            if lam > 80:  # heuristic threshold
                # Normal(mu=lam, sigma=sqrt(lam)) approximation
                mu = lam
                sigma = math.sqrt(lam)
                # continuity correction
                z = (k + 0.5 - mu) / sigma
                # standard normal CDF via error function
                return 0.5 * (1 + math.erf(z / math.sqrt(2)))
            # Direct summation for moderate/small lambda
            total = 0.0
            term = math.exp(-lam)  # P(X=0)
            total += term
            for i in range(1, k + 1):
                term *= lam / i  # recursive relation for Poisson pmf
                total += term
                if term < 1e-12:  # early break for tiny contributions
                    break
            return min(total, 1.0)

        # Tail probabilities
        prob_above_mean = 1 - _poisson_cdf(int(base_lambda), base_lambda)
        prob_very_busy = 1 - _poisson_cdf(int(base_lambda * 1.5), base_lambda)
        return {
            'mean': round(stats['mean'], 2),
            'std_dev': round(stats['std'], 2),
            'coefficient_of_variation': round(stats['std'] / stats['mean'], 3),
            'min': stats['min'],
            'max': stats['max'],
            'range': stats['max'] - stats['min'],
            'percentiles': stats['percentiles'],
            'probability_analysis': {
                'prob_zero_passengers': round(math.exp(-base_lambda), 3),
                'prob_above_mean': round(prob_above_mean, 3),
                'prob_very_busy': round(prob_very_busy, 3)
            },
            'description': f"Hourly averages: {round(stats['mean'], 1)} passengers/hour (σ={round(stats['std'], 1)})"
        }
    
    def _generate_daily_statistics(self, base_lambda: float, time_patterns: dict, sample_size: int) -> dict:
        """Generate daily passenger pattern statistics"""
        daily_total = 0
        hourly_breakdown = {}
        
        # Simulate 24 hours with time patterns
        for hour in range(24):
            # Apply time multipliers
            current_time = f"{hour:02d}:00"
            multiplier = self._get_time_multiplier(hour, time_patterns)
            hourly_rate = base_lambda * multiplier
            hourly_passengers = np.random.poisson(hourly_rate, 100).mean()
            
            daily_total += hourly_passengers
            hourly_breakdown[f"{hour:02d}:00"] = {
                'expected_passengers': round(hourly_passengers, 1),
                'rate_multiplier': round(multiplier, 2)
            }
        
        # Identify peak periods
        sorted_hours = sorted(hourly_breakdown.items(), key=lambda x: x[1]['expected_passengers'], reverse=True)
        
        return {
            'total_daily_passengers': round(daily_total, 0),
            'hourly_breakdown': hourly_breakdown,
            'peak_hours': {
                'busiest': sorted_hours[0][0],
                'second_busiest': sorted_hours[1][0],
                'quietest': sorted_hours[-1][0]
            },
            'rush_periods': {
                'morning_rush': [f"{h:02d}:00" for h in range(7, 10)],
                'evening_rush': [f"{h:02d}:00" for h in range(16, 19)],
                'lunch_peak': [f"{h:02d}:00" for h in range(12, 14)]
            }
        }
    
    def _generate_weekly_statistics(self, base_lambda: float, time_patterns: dict, sample_size: int) -> dict:
        """Generate weekly passenger pattern statistics"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_types = {
            'Monday': 'weekday', 'Tuesday': 'weekday', 'Wednesday': 'weekday',
            'Thursday': 'weekday', 'Friday': 'weekday',
            'Saturday': 'weekend', 'Sunday': 'weekend'
        }
        
        weekly_breakdown = {}
        total_weekly = 0
        
        for day in days:
            day_type = day_types[day]
            day_multiplier = 1.0 if day_type == 'weekday' else 0.7  # Weekend reduction
            daily_passengers = base_lambda * 24 * day_multiplier
            total_weekly += daily_passengers
            
            weekly_breakdown[day] = {
                'expected_passengers': round(daily_passengers, 0),
                'day_type': day_type,
                'relative_to_weekday': f"{day_multiplier*100:.0f}%"
            }
        
        return {
            'total_weekly_passengers': round(total_weekly, 0),
            'daily_breakdown': weekly_breakdown,
            'weekday_average': round(total_weekly * 5/7 / 5, 0),
            'weekend_average': round(total_weekly * 2/7 / 2, 0),
            'busiest_day': max(weekly_breakdown.keys(), key=lambda k: weekly_breakdown[k]['expected_passengers']),
            'quietest_day': min(weekly_breakdown.keys(), key=lambda k: weekly_breakdown[k]['expected_passengers'])
        }
    
    def _analyze_peak_patterns(self, time_patterns: dict, base_lambda: float) -> dict:
        """Analyze peak hour patterns and congestion"""
        peak_hours = []
        for pattern_name, pattern in time_patterns.items():
            if pattern.get('multiplier', 1.0) > 1.5:  # Significant peaks
                peak_hours.extend(pattern.get('hours', []))
        
        return {
            'identified_peaks': list(set(peak_hours)),
            'peak_intensity': {
                'light_peaks': [h for h in peak_hours if self._get_hour_intensity(h, time_patterns) < 2.0],
                'heavy_peaks': [h for h in peak_hours if self._get_hour_intensity(h, time_patterns) >= 2.0]
            },
            'congestion_risk': {
                'high_risk_hours': [h for h in peak_hours if self._get_hour_intensity(h, time_patterns) >= 2.5],
                'moderate_risk_hours': [h for h in peak_hours if 1.5 <= self._get_hour_intensity(h, time_patterns) < 2.5]
            },
            'peak_characteristics': {
                'morning_commute': 'Moderate intensity, predictable timing',
                'evening_commute': 'High intensity, extended duration',
                'lunch_rush': 'Short duration, moderate intensity'
            }
        }
    
    def _analyze_location_patterns(self, amenity_weights: dict) -> dict:
        """Analyze which types of locations generate most passengers"""
        sorted_amenities = sorted(amenity_weights.items(), key=lambda x: x[1], reverse=True)
        
        high_traffic = [(k, v) for k, v in sorted_amenities if v >= 10.0]
        medium_traffic = [(k, v) for k, v in sorted_amenities if 5.0 <= v < 10.0]
        low_traffic = [(k, v) for k, v in sorted_amenities if v < 5.0]
        
        return {
            'high_traffic_generators': {
                'locations': [k for k, v in high_traffic],
                'average_weight': round(np.mean([v for k, v in high_traffic]), 1),
                'description': 'Major passenger generators - require frequent service'
            },
            'medium_traffic_generators': {
                'locations': [k for k, v in medium_traffic],
                'average_weight': round(np.mean([v for k, v in medium_traffic]), 1),
                'description': 'Moderate generators - standard service intervals'
            },
            'low_traffic_generators': {
                'locations': [k for k, v in low_traffic],
                'average_weight': round(np.mean([v for k, v in low_traffic]), 1),
                'description': 'Light generators - can use longer intervals'
            },
            'top_5_generators': sorted_amenities[:5],
            'specialized_locations': {
                'educational': [k for k, v in sorted_amenities if 'school' in k or 'university' in k],
                'commercial': [k for k, v in sorted_amenities if any(term in k for term in ['mall', 'market', 'shop'])],
                'healthcare': [k for k, v in sorted_amenities if any(term in k for term in ['hospital', 'clinic', 'pharmacy'])]
            }
        }
    
    def _generate_service_recommendations(self, hourly_stats: dict, daily_stats: dict) -> dict:
        """Generate service planning recommendations"""
        mean_hourly = hourly_stats['mean']
        peak_hourly = hourly_stats['percentiles']['95th']
        
        return {
            'vehicle_capacity': {
                'minimum_recommended': max(15, int(mean_hourly * 0.8)),
                'optimal_capacity': max(25, int(peak_hourly * 1.2)),
                'explanation': 'Based on 95th percentile demand with 20% buffer'
            },
            'service_frequency': {
                'off_peak': f"Every {max(15, int(60/mean_hourly*2))} minutes",
                'peak_hours': f"Every {max(5, int(60/peak_hourly))} minutes",
                'rationale': 'Frequency based on passenger arrival rate'
            },
            'fleet_sizing': {
                'minimum_vehicles': max(2, int(daily_stats['total_daily_passengers'] / 200)),
                'optimal_fleet': max(3, int(daily_stats['total_daily_passengers'] / 150)),
                'explanation': 'Assumes 150-200 passengers per vehicle per day'
            },
            'operational_priorities': [
                'Monitor morning and evening peaks closely',
                'Maintain consistent service during off-peak',
                'Consider express services during high-demand periods',
                'Plan for variability with spare capacity'
            ]
        }
    
    def _get_time_multiplier(self, hour: int, time_patterns: dict) -> float:
        """Get time multiplier for a specific hour"""
        for pattern_name, pattern in time_patterns.items():
            if hour in pattern.get('hours', []):
                return pattern.get('multiplier', 1.0)
        return 1.0
    
    def _get_hour_intensity(self, hour: int, time_patterns: dict) -> float:
        """Get intensity multiplier for a specific hour"""
        return self._get_time_multiplier(hour, time_patterns)
    """
    Poisson distribution model for passenger generation
    
    The Poisson distribution is ideal for modeling:
    - Discrete passenger arrivals
    - Independent events over time
    - Low probability, high frequency events
    """
    
    def get_model_type(self) -> str:
        return "poisson"
    
    def calculate_base_rate(self, location_data: Dict[str, Any], 
                          environmental_factors: Dict[str, float]) -> float:
        """
        Calculate base rate using Poisson model parameters
        
        Rate is calculated based on:
        - Amenity types and their weights
        - Location characteristics (population density, accessibility)
        - Base lambda parameter for Poisson distribution
        """
        amenity_weights = self.get_amenity_weights()
        model_params = self.get_model_parameters()
        
        # Base lambda (average rate)
        base_lambda = model_params.get('base_lambda', 5.0)
        
        # Calculate amenity contribution
        amenity_factor = 1.0
        nearby_amenities = location_data.get('nearby_amenities', [])
        
        for amenity in nearby_amenities:
            amenity_type = amenity.get('type', 'unknown')
            amenity_weight = amenity_weights.get(amenity_type, amenity_weights.get('default', 1.0))
            distance_factor = amenity.get('distance_factor', 1.0)
            
            amenity_factor += amenity_weight * distance_factor
        
        # Apply location characteristics
        location_factor = self._calculate_location_factor(location_data)
        
        # Calculate base rate (lambda for Poisson)
        base_rate = base_lambda * amenity_factor * location_factor
        
        # Apply environmental factors
        base_rate = self.apply_environmental_factors(base_rate, environmental_factors)
        
        return max(0.1, base_rate)  # Ensure minimum rate
    
    def apply_temporal_weights(self, base_rate: float, current_time: time, 
                             day_type: str = 'weekday') -> float:
        """
        Apply time-based weights using Poisson intensity function
        
        Poisson intensity varies throughout the day based on configured patterns
        """
        time_patterns = self.get_time_patterns()
        model_params = self.get_model_parameters()
        
        # Get current hour
        current_hour = current_time.hour
        
        # Find matching time pattern
        time_multiplier = 1.0
        for pattern_name, pattern in time_patterns.items():
            if current_hour in pattern.get('hours', []):
                base_multiplier = pattern.get('multiplier', 1.0)
                
                # Apply day type adjustment
                day_adjustment = pattern.get('day_adjustments', {}).get(day_type, 1.0)
                time_multiplier = base_multiplier * day_adjustment
                break
        
        # Apply Poisson temporal scaling
        temporal_variance = model_params.get('temporal_variance', 0.1)
        if temporal_variance > 0:
            # Add some randomness to the temporal pattern
            noise = np.random.normal(0, temporal_variance)
            time_multiplier *= (1.0 + noise)
        
        return base_rate * max(0.1, time_multiplier)
    
    def generate_passengers(self, weighted_rate: float, time_interval_seconds: int) -> int:
        """
        Generate passengers using Poisson distribution
        
        Args:
            weighted_rate: Lambda parameter (expected arrivals per hour)
            time_interval_seconds: Time interval for generation
            
        Returns:
            Number of passengers (Poisson random variable)
        """
        model_params = self.get_model_parameters()
        
        # Convert rate to match time interval
        interval_hours = time_interval_seconds / 3600.0
        lambda_param = weighted_rate * interval_hours
        
        # Apply rate variation if configured
        rate_variation = model_params.get('rate_variation', 0.0)
        if rate_variation > 0:
            # Add variance to the rate itself
            lambda_param *= np.random.normal(1.0, rate_variation)
            lambda_param = max(0.01, lambda_param)  # Ensure positive
        
        # Generate Poisson random variable
        try:
            passengers = np.random.poisson(lambda_param)
            
            # Apply constraints
            max_passengers = model_params.get('max_passengers_per_interval', 100)
            passengers = min(passengers, max_passengers)
            
            return int(passengers)
            
        except Exception as e:
            # Fallback to deterministic approach if random generation fails
            return max(0, int(round(lambda_param)))
    
    def _calculate_location_factor(self, location_data: Dict[str, Any]) -> float:
        """Calculate location-specific factors for Poisson rate"""
        model_params = self.get_model_parameters()
        
        factor = 1.0
        
        # Population density factor
        population_density = location_data.get('population_density', 1.0)
        density_weight = model_params.get('population_density_weight', 0.3)
        factor += population_density * density_weight
        
        # Accessibility factor (distance to main roads, centers)
        accessibility = location_data.get('accessibility_score', 1.0)
        accessibility_weight = model_params.get('accessibility_weight', 0.2)
        factor += accessibility * accessibility_weight
        
        # Stop type factor
        stop_type = location_data.get('stop_type', 'bus_stop')
        stop_type_weights = model_params.get('stop_type_weights', {})
        stop_factor = stop_type_weights.get(stop_type, 1.0)
        factor *= stop_factor
        
        return max(0.1, factor)
    
    def get_model_statistics(self, weighted_rate: float) -> Dict[str, float]:
        """
        Get statistical properties of the Poisson model
        
        Args:
            weighted_rate: Current lambda parameter
            
        Returns:
            Dictionary of statistical properties
        """
        return {
            'lambda': weighted_rate,
            'mean': weighted_rate,
            'variance': weighted_rate,
            'std_dev': np.sqrt(weighted_rate),
            'coefficient_of_variation': 1.0 / np.sqrt(weighted_rate) if weighted_rate > 0 else float('inf')
        }
    
    def predict_passengers_distribution(self, weighted_rate: float, 
                                      time_interval_seconds: int, 
                                      num_samples: int = 1000) -> Dict[str, Any]:
        """
        Predict passenger distribution for planning purposes
        
        Args:
            weighted_rate: Lambda parameter
            time_interval_seconds: Time interval
            num_samples: Number of samples for distribution
            
        Returns:
            Distribution statistics and percentiles
        """
        interval_hours = time_interval_seconds / 3600.0
        lambda_param = weighted_rate * interval_hours
        
        # Generate samples
        samples = np.random.poisson(lambda_param, num_samples)
        
        return {
            'lambda': lambda_param,
            'mean': np.mean(samples),
            'std': np.std(samples),
            'min': int(np.min(samples)),
            'max': int(np.max(samples)),
            'percentiles': {
                '10th': int(np.percentile(samples, 10)),
                '25th': int(np.percentile(samples, 25)),
                '50th': int(np.percentile(samples, 50)),
                '75th': int(np.percentile(samples, 75)),
                '90th': int(np.percentile(samples, 90)),
                '95th': int(np.percentile(samples, 95))
            }
        }