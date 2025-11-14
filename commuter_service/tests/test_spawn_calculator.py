#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Spawn Calculation Kernel
========================================

Tests the modular spawn calculation logic in isolation.
"""

import pytest
from datetime import datetime
from commuter_service.core.domain.spawner_engine.spawn_calculator import SpawnCalculator


class TestTemporalMultipliers:
    """Test temporal multiplier extraction."""
    
    def test_extract_temporal_multipliers_peak_weekday(self):
        """Test extraction during Monday morning peak."""
        spawn_config = {
            'distribution_params': {
                'passengers_per_building_per_hour': 0.05
            },
            'hourly_rates': {
                '8': 2.0,  # Morning peak
            },
            'day_multipliers': {
                '0': 1.3,  # Monday
            }
        }
        
        current_time = datetime(2024, 10, 28, 8, 0)  # Monday 8 AM
        
        base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
            spawn_config, current_time
        )
        
        assert base_rate == 0.05
        assert hourly_mult == 2.0
        assert day_mult == 1.3
    
    def test_extract_temporal_multipliers_night_weekend(self):
        """Test extraction during Sunday night (minimal service)."""
        spawn_config = {
            'distribution_params': {
                'passengers_per_building_per_hour': 0.05
            },
            'hourly_rates': {
                '2': 0.05,  # Night
            },
            'day_multipliers': {
                '6': 0.3,  # Sunday
            }
        }
        
        current_time = datetime(2024, 11, 3, 2, 0)  # Sunday 2 AM
        
        base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
            spawn_config, current_time
        )
        
        assert base_rate == 0.05
        assert hourly_mult == 0.05
        assert day_mult == 0.3
    
    def test_defaults_when_missing(self):
        """Test default values when config missing."""
        spawn_config = {}
        current_time = datetime(2024, 10, 28, 8, 0)
        
        base_rate, hourly_mult, day_mult = SpawnCalculator.extract_temporal_multipliers(
            spawn_config, current_time
        )
        
        assert base_rate == 0.3  # Default
        assert hourly_mult == 1.0  # Default
        assert day_mult == 1.0  # Default


class TestEffectiveRate:
    """Test effective rate calculation."""
    
    def test_calculate_effective_rate_peak(self):
        """Test peak hour calculation."""
        effective_rate = SpawnCalculator.calculate_effective_rate(
            base_rate=0.05,
            hourly_multiplier=2.0,
            day_multiplier=1.3
        )
        assert effective_rate == pytest.approx(0.13, abs=0.001)
    
    def test_calculate_effective_rate_night(self):
        """Test night calculation."""
        effective_rate = SpawnCalculator.calculate_effective_rate(
            base_rate=0.05,
            hourly_multiplier=0.05,
            day_multiplier=1.3
        )
        assert effective_rate == pytest.approx(0.00325, abs=0.00001)
    
    def test_calculate_effective_rate_neutral(self):
        """Test neutral multipliers (no change)."""
        effective_rate = SpawnCalculator.calculate_effective_rate(
            base_rate=0.05,
            hourly_multiplier=1.0,
            day_multiplier=1.0
        )
        assert effective_rate == 0.05


class TestTerminalPopulation:
    """Test terminal population calculation."""
    
    def test_calculate_terminal_population_peak(self):
        """Test Speightstown peak hour."""
        terminal_pop = SpawnCalculator.calculate_terminal_population(
            buildings_near_depot=1556,
            effective_rate=0.13
        )
        assert terminal_pop == pytest.approx(202.28, abs=0.01)
    
    def test_calculate_terminal_population_night(self):
        """Test night hours."""
        terminal_pop = SpawnCalculator.calculate_terminal_population(
            buildings_near_depot=1556,
            effective_rate=0.00325
        )
        assert terminal_pop == pytest.approx(5.057, abs=0.01)
    
    def test_calculate_terminal_population_zero_buildings(self):
        """Test with no buildings."""
        terminal_pop = SpawnCalculator.calculate_terminal_population(
            buildings_near_depot=0,
            effective_rate=0.13
        )
        assert terminal_pop == 0.0


class TestRouteAttractiveness:
    """Test route attractiveness calculation."""
    
    def test_solo_route_gets_100_percent(self):
        """Test single route gets all passengers."""
        attractiveness = SpawnCalculator.calculate_route_attractiveness(
            buildings_along_route=69,
            total_buildings_all_routes=69
        )
        assert attractiveness == 1.0
    
    def test_distributed_among_5_routes(self):
        """Test Route 1 with 5 routes at depot."""
        attractiveness = SpawnCalculator.calculate_route_attractiveness(
            buildings_along_route=69,
            total_buildings_all_routes=389  # 5 routes total
        )
        assert attractiveness == pytest.approx(0.1774, abs=0.0001)
    
    def test_zero_total_buildings(self):
        """Test edge case: no buildings."""
        attractiveness = SpawnCalculator.calculate_route_attractiveness(
            buildings_along_route=0,
            total_buildings_all_routes=0
        )
        assert attractiveness == 0.0
    
    def test_zero_sum_property(self):
        """Test that attractiveness sums to 1.0."""
        route_buildings = [69, 80, 100, 50, 90]
        total = sum(route_buildings)
        
        attractiveness_values = [
            SpawnCalculator.calculate_route_attractiveness(b, total)
            for b in route_buildings
        ]
        
        assert sum(attractiveness_values) == pytest.approx(1.0, abs=0.0001)


class TestPassengersPerRoute:
    """Test passengers per route calculation."""
    
    def test_solo_route_gets_all_passengers(self):
        """Test Route 1 as only route."""
        passengers = SpawnCalculator.calculate_passengers_per_route(
            terminal_population=202.28,
            route_attractiveness=1.0
        )
        assert passengers == pytest.approx(202.28, abs=0.01)
    
    def test_distributed_passengers(self):
        """Test Route 1 with 5 routes."""
        passengers = SpawnCalculator.calculate_passengers_per_route(
            terminal_population=202.28,
            route_attractiveness=0.1774
        )
        assert passengers == pytest.approx(35.88, abs=0.01)
    
    def test_zero_attractiveness(self):
        """Test route with no buildings."""
        passengers = SpawnCalculator.calculate_passengers_per_route(
            terminal_population=202.28,
            route_attractiveness=0.0
        )
        assert passengers == 0.0


class TestLambdaCalculation:
    """Test Poisson lambda calculation."""
    
    def test_15_minute_window(self):
        """Test standard 15-minute spawn window."""
        lambda_param = SpawnCalculator.calculate_lambda_for_time_window(
            passengers_per_hour=202.28,
            time_window_minutes=15
        )
        assert lambda_param == pytest.approx(50.57, abs=0.01)
    
    def test_60_minute_window(self):
        """Test 1-hour window (should equal passengers/hour)."""
        lambda_param = SpawnCalculator.calculate_lambda_for_time_window(
            passengers_per_hour=202.28,
            time_window_minutes=60
        )
        assert lambda_param == pytest.approx(202.28, abs=0.01)
    
    def test_5_minute_window(self):
        """Test short 5-minute window."""
        lambda_param = SpawnCalculator.calculate_lambda_for_time_window(
            passengers_per_hour=202.28,
            time_window_minutes=5
        )
        assert lambda_param == pytest.approx(16.857, abs=0.01)


class TestPoissonGeneration:
    """Test Poisson spawn count generation."""
    
    def test_zero_lambda_returns_zero(self):
        """Test lambda=0 always returns 0."""
        count = SpawnCalculator.generate_poisson_spawn_count(0.0)
        assert count == 0
    
    def test_negative_lambda_returns_zero(self):
        """Test negative lambda returns 0."""
        count = SpawnCalculator.generate_poisson_spawn_count(-5.0)
        assert count == 0
    
    def test_reproducible_with_seed(self):
        """Test same seed gives same result."""
        count1 = SpawnCalculator.generate_poisson_spawn_count(50.57, seed=42)
        count2 = SpawnCalculator.generate_poisson_spawn_count(50.57, seed=42)
        assert count1 == count2
    
    def test_reasonable_range_for_lambda_50(self):
        """Test lambda=50 produces reasonable counts (30-70)."""
        counts = [
            SpawnCalculator.generate_poisson_spawn_count(50.57, seed=i)
            for i in range(100)
        ]
        
        # 95% of Poisson samples should be within 2 std devs
        # For Poisson, std = sqrt(lambda) = sqrt(50) ≈ 7.1
        # So 95% should be in [36, 64]
        assert min(counts) >= 30  # Very unlikely to be below 30
        assert max(counts) <= 70  # Very unlikely to be above 70
        assert 45 <= sum(counts) / len(counts) <= 55  # Mean should be ~50


class TestFullHybridCalculation:
    """Test complete hybrid spawn pipeline."""
    
    def test_route_1_solo_monday_8am(self):
        """Test Route 1 as only route, Monday 8 AM peak."""
        spawn_config = {
            'distribution_params': {
                'passengers_per_building_per_hour': 0.05
            },
            'hourly_rates': {'8': 2.0},
            'day_multipliers': {'0': 1.3}
        }
        
        result = SpawnCalculator.calculate_hybrid_spawn(
            buildings_near_depot=1556,
            buildings_along_route=69,
            total_buildings_all_routes=69,
            spawn_config=spawn_config,
            current_time=datetime(2024, 10, 28, 8, 0),  # Monday 8 AM
            time_window_minutes=15,
            seed=42
        )
        
        assert result['base_rate'] == 0.05
        assert result['hourly_mult'] == 2.0
        assert result['day_mult'] == 1.3
        assert result['effective_rate'] == pytest.approx(0.13, abs=0.001)
        assert result['terminal_population'] == pytest.approx(202.28, abs=0.01)
        assert result['route_attractiveness'] == 1.0
        assert result['passengers_per_hour'] == pytest.approx(202.28, abs=0.01)
        assert result['lambda_param'] == pytest.approx(50.57, abs=0.01)
        assert 30 <= result['spawn_count'] <= 70  # Reasonable Poisson range
    
    def test_route_1_with_5_routes_monday_8am(self):
        """Test Route 1 with 5 routes at depot."""
        spawn_config = {
            'distribution_params': {
                'passengers_per_building_per_hour': 0.05
            },
            'hourly_rates': {'8': 2.0},
            'day_multipliers': {'0': 1.3}
        }
        
        result = SpawnCalculator.calculate_hybrid_spawn(
            buildings_near_depot=1556,
            buildings_along_route=69,
            total_buildings_all_routes=389,  # 5 routes
            spawn_config=spawn_config,
            current_time=datetime(2024, 10, 28, 8, 0),
            time_window_minutes=15,
            seed=42
        )
        
        # Terminal population same as before
        assert result['terminal_population'] == pytest.approx(202.28, abs=0.01)
        
        # Attractiveness reduced to 17.74%
        assert result['route_attractiveness'] == pytest.approx(0.1774, abs=0.0001)
        
        # Passengers reduced proportionally
        assert result['passengers_per_hour'] == pytest.approx(35.88, abs=0.01)
        
        # Lambda reduced proportionally
        assert result['lambda_param'] == pytest.approx(8.97, abs=0.01)
        
        # Spawn count should be lower
        assert 0 <= result['spawn_count'] <= 25  # Poisson(9) typically 0-20
    
    def test_night_hours_minimal_spawning(self):
        """Test Monday 2 AM (night hours)."""
        spawn_config = {
            'distribution_params': {
                'passengers_per_building_per_hour': 0.05
            },
            'hourly_rates': {'2': 0.05},
            'day_multipliers': {'0': 1.3}
        }
        
        result = SpawnCalculator.calculate_hybrid_spawn(
            buildings_near_depot=1556,
            buildings_along_route=69,
            total_buildings_all_routes=69,
            spawn_config=spawn_config,
            current_time=datetime(2024, 10, 28, 2, 0),  # Monday 2 AM
            time_window_minutes=15,
            seed=42
        )
        
        assert result['effective_rate'] == pytest.approx(0.00325, abs=0.00001)
        assert result['terminal_population'] == pytest.approx(5.057, abs=0.01)
        assert result['passengers_per_hour'] == pytest.approx(5.057, abs=0.01)
        assert result['lambda_param'] == pytest.approx(1.264, abs=0.01)
        assert 0 <= result['spawn_count'] <= 10  # Poisson(1.3) typically 0-5


class TestValidationCalculation:
    """Test simplified validation calculation (no Poisson)."""
    
    def test_validation_calculation_deterministic(self):
        """Test validation calculation returns deterministic passengers/hour."""
        result = SpawnCalculator.calculate_validation_hybrid_spawn(
            buildings_near_depot=1556,
            buildings_along_route=69,
            total_buildings_all_routes=69,
            base_rate=0.05,
            hourly_mult=2.0,
            day_mult=1.3
        )
        
        assert result['effective_rate'] == pytest.approx(0.13, abs=0.001)
        assert result['terminal_population'] == pytest.approx(202.28, abs=0.01)
        assert result['route_attractiveness'] == 1.0
        assert result['passengers_per_hour'] == pytest.approx(202.28, abs=0.01)
        
        # No spawn_count or lambda in validation results
        assert 'spawn_count' not in result
        assert 'lambda_param' not in result
    
    def test_validation_multiple_scenarios(self):
        """Test validation across multiple time scenarios."""
        scenarios = [
            (2.0, 1.3, 202.28),  # Monday 8 AM
            (2.2, 1.3, 222.51),  # Monday 5 PM
            (0.9, 1.3, 91.03),   # Monday 12 PM
            (0.05, 1.3, 5.06),   # Monday 2 AM
        ]
        
        for hourly_mult, day_mult, expected_terminal in scenarios:
            result = SpawnCalculator.calculate_validation_hybrid_spawn(
                buildings_near_depot=1556,
                buildings_along_route=69,
                total_buildings_all_routes=69,
                base_rate=0.05,
                hourly_mult=hourly_mult,
                day_mult=day_mult
            )
            
            assert result['terminal_population'] == pytest.approx(
                expected_terminal, abs=0.01
            )


class TestConservationProperty:
    """Test that hybrid model conserves total passengers (zero-sum)."""
    
    def test_passengers_conserved_across_routes(self):
        """Test total passengers stays constant as routes added."""
        spawn_config = {
            'distribution_params': {
                'passengers_per_building_per_hour': 0.05
            },
            'hourly_rates': {'8': 2.0},
            'day_multipliers': {'0': 1.3}
        }
        
        # 5 routes with different building counts
        routes = [
            {'buildings': 69, 'name': 'Route 1'},
            {'buildings': 80, 'name': 'Route 2'},
            {'buildings': 100, 'name': 'Route 3'},
            {'buildings': 50, 'name': 'Route 4'},
            {'buildings': 90, 'name': 'Route 5'},
        ]
        total_buildings = sum(r['buildings'] for r in routes)
        
        # Calculate passengers for each route
        route_passengers = []
        for route in routes:
            result = SpawnCalculator.calculate_hybrid_spawn(
                buildings_near_depot=1556,
                buildings_along_route=route['buildings'],
                total_buildings_all_routes=total_buildings,
                spawn_config=spawn_config,
                current_time=datetime(2024, 10, 28, 8, 0),
                time_window_minutes=60,  # Use 60 min to avoid Poisson variance
                seed=None
            )
            route_passengers.append(result['passengers_per_hour'])
        
        # Sum should equal terminal population
        total = sum(route_passengers)
        expected_terminal = 1556 * 0.05 * 2.0 * 1.3  # 202.28
        
        assert total == pytest.approx(expected_terminal, abs=0.01)
