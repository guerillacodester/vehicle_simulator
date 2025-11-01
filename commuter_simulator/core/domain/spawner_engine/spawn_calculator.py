#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spawn Calculation Kernel
========================

Modular, testable implementation of the hybrid spawn model formula.
Isolated from spawner infrastructure for reusability and testing.

Formula:
    terminal_population = buildings_near_depot × base_rate × hourly_mult × day_mult
    route_attractiveness = buildings_along_route / total_buildings_all_routes
    passengers_per_route = terminal_population × route_attractiveness

For Poisson-based spawning:
    lambda = passengers_per_hour × (time_window_minutes / 60.0)
    spawn_count = Poisson(lambda)
"""

from datetime import datetime
from typing import Dict, Optional
import numpy as np


class SpawnCalculator:
    """
    Pure calculation kernel for hybrid spawn model.
    
    Separates business logic from infrastructure (API calls, logging, etc).
    Can be used by validation scripts, spawners, and unit tests.
    """
    
    @staticmethod
    def extract_temporal_multipliers(
        spawn_config: Dict,
        current_time: datetime
    ) -> tuple[float, float, float]:
        """
        Extract temporal multipliers from spawn config.
        
        Args:
            spawn_config: Spawn configuration dict from API
            current_time: Current simulation time
            
        Returns:
            (base_rate, hourly_multiplier, day_multiplier)
            
        Example:
            base_rate = 0.05 passengers/building/hour
            hourly_mult = 2.0 (morning peak)
            day_mult = 1.3 (Monday)
            → effective_rate = 0.05 × 2.0 × 1.3 = 0.130
        """
        # Extract base spawn rate
        dist_params = spawn_config.get('distribution_params', {})
        base_rate = float(dist_params.get('passengers_per_building_per_hour', 0.3))
        
        # Extract hourly rate multiplier (0-23)
        hourly_rates = spawn_config.get('hourly_rates', {})
        hour_str = str(current_time.hour)
        hourly_mult = float(hourly_rates.get(hour_str, 1.0))
        
        # Extract day multiplier (0=Monday, 6=Sunday)
        day_multipliers = spawn_config.get('day_multipliers', {})
        day_str = str(current_time.weekday())
        day_mult = float(day_multipliers.get(day_str, 1.0))
        
        return base_rate, hourly_mult, day_mult
    
    @staticmethod
    def calculate_effective_rate(
        base_rate: float,
        hourly_multiplier: float,
        day_multiplier: float
    ) -> float:
        """
        Calculate effective spawn rate with temporal weighting.
        
        Args:
            base_rate: Base passengers per building per hour (e.g., 0.05)
            hourly_multiplier: Hour-of-day multiplier (e.g., 2.0 for peak)
            day_multiplier: Day-of-week multiplier (e.g., 1.3 for weekday)
            
        Returns:
            Effective rate combining all factors
            
        Example:
            0.05 × 2.0 × 1.3 = 0.130 passengers/building/hour
        """
        return base_rate * hourly_multiplier * day_multiplier
    
    @staticmethod
    def calculate_terminal_population(
        buildings_near_depot: int,
        effective_rate: float
    ) -> float:
        """
        Calculate terminal population (total passengers/hour at depot).
        
        Args:
            buildings_near_depot: Number of buildings in depot catchment
            effective_rate: Effective spawn rate (base × hourly × day)
            
        Returns:
            Expected passengers per hour at this depot
            
        Example:
            1556 buildings × 0.130 rate = 202.28 passengers/hour
        """
        return buildings_near_depot * effective_rate
    
    @staticmethod
    def calculate_route_attractiveness(
        buildings_along_route: int,
        total_buildings_all_routes: int
    ) -> float:
        """
        Calculate route attractiveness (zero-sum distribution).
        
        Args:
            buildings_along_route: Buildings within buffer of this route
            total_buildings_all_routes: Sum of buildings for all routes at depot
            
        Returns:
            Attractiveness factor (0.0 to 1.0)
            
        Example:
            69 buildings / 69 total = 1.00 (100% when only 1 route)
            69 buildings / 389 total = 0.177 (17.7% when 5 routes)
        """
        if total_buildings_all_routes == 0:
            return 0.0
        return buildings_along_route / total_buildings_all_routes
    
    @staticmethod
    def calculate_passengers_per_route(
        terminal_population: float,
        route_attractiveness: float
    ) -> float:
        """
        Calculate passengers distributed to this specific route.
        
        Args:
            terminal_population: Total passengers/hour at depot
            route_attractiveness: This route's share (0.0 to 1.0)
            
        Returns:
            Expected passengers per hour for this route
            
        Example:
            202.28 pass/hr × 1.00 attractiveness = 202.28 pass/hr (solo route)
            202.28 pass/hr × 0.177 attractiveness = 35.80 pass/hr (5 routes)
        """
        return terminal_population * route_attractiveness
    
    @staticmethod
    def calculate_lambda_for_time_window(
        passengers_per_hour: float,
        time_window_minutes: int
    ) -> float:
        """
        Calculate Poisson lambda parameter for time window.
        
        Args:
            passengers_per_hour: Expected passengers per hour
            time_window_minutes: Spawn time window in minutes
            
        Returns:
            Lambda parameter for Poisson distribution
            
        Example:
            202.28 pass/hr × (15 min / 60) = 50.57 expected in 15-min window
        """
        return passengers_per_hour * (time_window_minutes / 60.0)
    
    @staticmethod
    def generate_poisson_spawn_count(lambda_param: float, seed: Optional[int] = None) -> int:
        """
        Generate Poisson-distributed spawn count.
        
        Args:
            lambda_param: Expected value (lambda)
            seed: Optional random seed for reproducibility
            
        Returns:
            Integer spawn count drawn from Poisson(lambda)
            
        Example:
            Poisson(50.57) → might return 48, 53, 51, etc (varies)
        """
        if lambda_param <= 0:
            return 0
        
        if seed is not None:
            np.random.seed(seed)
        
        return np.random.poisson(lambda_param)
    
    @classmethod
    def calculate_hybrid_spawn(
        cls,
        buildings_near_depot: int,
        buildings_along_route: int,
        total_buildings_all_routes: int,
        spawn_config: Dict,
        current_time: datetime,
        time_window_minutes: int,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Complete hybrid spawn calculation (full pipeline).
        
        Args:
            buildings_near_depot: Buildings in depot catchment
            buildings_along_route: Buildings along this route
            total_buildings_all_routes: Total buildings for all routes at depot
            spawn_config: Spawn configuration from API
            current_time: Current simulation time
            time_window_minutes: Spawn time window
            seed: Optional random seed
            
        Returns:
            Dictionary with all calculation components:
                - base_rate: Base spawn rate
                - hourly_mult: Hourly multiplier
                - day_mult: Day multiplier
                - effective_rate: Combined temporal rate
                - terminal_population: Total passengers/hour at depot
                - route_attractiveness: This route's share
                - passengers_per_hour: Passengers/hour for this route
                - lambda_param: Poisson lambda
                - spawn_count: Generated spawn count
                
        Example:
            >>> result = SpawnCalculator.calculate_hybrid_spawn(
            ...     buildings_near_depot=1556,
            ...     buildings_along_route=69,
            ...     total_buildings_all_routes=69,
            ...     spawn_config=config,
            ...     current_time=datetime(2024, 10, 28, 8, 0),  # Monday 8 AM
            ...     time_window_minutes=15
            ... )
            >>> result['spawn_count']  # e.g., 48 passengers
        """
        # Step 1: Extract temporal multipliers
        base_rate, hourly_mult, day_mult = cls.extract_temporal_multipliers(
            spawn_config, current_time
        )
        
        # Step 2: Calculate effective rate
        effective_rate = cls.calculate_effective_rate(
            base_rate, hourly_mult, day_mult
        )
        
        # Step 3: Calculate terminal population
        terminal_population = cls.calculate_terminal_population(
            buildings_near_depot, effective_rate
        )
        
        # Step 4: Calculate route attractiveness
        route_attractiveness = cls.calculate_route_attractiveness(
            buildings_along_route, total_buildings_all_routes
        )
        
        # Step 5: Calculate passengers for this route
        passengers_per_hour = cls.calculate_passengers_per_route(
            terminal_population, route_attractiveness
        )
        
        # Step 6: Calculate Poisson lambda
        lambda_param = cls.calculate_lambda_for_time_window(
            passengers_per_hour, time_window_minutes
        )
        
        # Step 7: Generate spawn count
        spawn_count = cls.generate_poisson_spawn_count(lambda_param, seed)
        
        return {
            'base_rate': base_rate,
            'hourly_mult': hourly_mult,
            'day_mult': day_mult,
            'effective_rate': effective_rate,
            'terminal_population': terminal_population,
            'route_attractiveness': route_attractiveness,
            'passengers_per_hour': passengers_per_hour,
            'lambda_param': lambda_param,
            'spawn_count': spawn_count,
            'buildings_near_depot': buildings_near_depot,
            'buildings_along_route': buildings_along_route,
            'total_buildings_all_routes': total_buildings_all_routes,
            'time_window_minutes': time_window_minutes
        }
    
    @classmethod
    def calculate_validation_hybrid_spawn(
        cls,
        buildings_near_depot: int,
        buildings_along_route: int,
        total_buildings_all_routes: int,
        base_rate: float,
        hourly_mult: float,
        day_mult: float
    ) -> Dict:
        """
        Simplified calculation for validation (no Poisson sampling).
        
        Used by validation scripts that want deterministic results.
        Returns passengers/hour without time-window conversion.
        
        Args:
            buildings_near_depot: Buildings in depot catchment
            buildings_along_route: Buildings along this route
            total_buildings_all_routes: Total buildings for all routes
            base_rate: Base spawn rate
            hourly_mult: Hourly multiplier
            day_mult: Day multiplier
            
        Returns:
            Dictionary with calculation breakdown (no spawn_count)
        """
        # Calculate effective rate
        effective_rate = cls.calculate_effective_rate(
            base_rate, hourly_mult, day_mult
        )
        
        # Calculate terminal population
        terminal_population = cls.calculate_terminal_population(
            buildings_near_depot, effective_rate
        )
        
        # Calculate route attractiveness
        route_attractiveness = cls.calculate_route_attractiveness(
            buildings_along_route, total_buildings_all_routes
        )
        
        # Calculate passengers for this route
        passengers_per_hour = cls.calculate_passengers_per_route(
            terminal_population, route_attractiveness
        )
        
        return {
            'base_rate': base_rate,
            'hourly_mult': hourly_mult,
            'day_mult': day_mult,
            'effective_rate': effective_rate,
            'terminal_population': terminal_population,
            'route_attractiveness': route_attractiveness,
            'passengers_per_hour': passengers_per_hour,
            'buildings_near_depot': buildings_near_depot,
            'buildings_along_route': buildings_along_route,
            'total_buildings_all_routes': total_buildings_all_routes
        }
