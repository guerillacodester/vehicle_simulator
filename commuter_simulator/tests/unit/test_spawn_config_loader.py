"""
Unit tests for SpawnConfigLoader
---------------------------------
Tests the spawn configuration loading and caching functionality.

Run with:
    pytest commuter_simulator/tests/unit/test_spawn_config_loader.py -v
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader


# Sample config data matching Barbados seed data structure
SAMPLE_CONFIG = {
    "id": 2,
    "documentId": "5ae12eb7-7434-4599-9520-56d01e6a38a3",
    "name": "Barbados Typical Weekday",
    "description": "Default spawn configuration for Barbados commuter patterns",
    "is_active": True,
    "building_weights": [
        {"id": 1, "building_type": "residential", "weight": 2.0, "peak_multiplier": 2.5, "is_active": True},
        {"id": 2, "building_type": "commercial", "weight": 1.5, "peak_multiplier": 1.2, "is_active": True},
        {"id": 3, "building_type": "office", "weight": 1.8, "peak_multiplier": 1.5, "is_active": True},
        {"id": 4, "building_type": "school", "weight": 2.5, "peak_multiplier": 3.0, "is_active": True},
    ],
    "poi_weights": [
        {"id": 1, "poi_type": "bus_station", "weight": 5.0, "peak_multiplier": 1.0, "is_active": True},
        {"id": 2, "poi_type": "marketplace", "weight": 3.0, "peak_multiplier": 1.5, "is_active": True},
    ],
    "landuse_weights": [
        {"id": 1, "landuse_type": "residential", "weight": 2.0, "peak_multiplier": 1.5, "is_active": True},
        {"id": 2, "landuse_type": "commercial", "weight": 2.5, "peak_multiplier": 1.2, "is_active": True},
    ],
    "hourly_spawn_rates": [
        {"id": 1, "hour": 0, "spawn_rate": 0.2},
        {"id": 2, "hour": 1, "spawn_rate": 0.1},
        {"id": 8, "hour": 7, "spawn_rate": 2.5},
        {"id": 9, "hour": 8, "spawn_rate": 2.8},  # Morning peak
        {"id": 10, "hour": 9, "spawn_rate": 2.2},
        {"id": 18, "hour": 17, "spawn_rate": 2.3},  # Evening peak
        {"id": 19, "hour": 18, "spawn_rate": 1.8},
        {"id": 24, "hour": 23, "spawn_rate": 0.3},
    ] + [{"id": i+3, "hour": i, "spawn_rate": 1.0} for i in range(2, 7)] + \
        [{"id": i+11, "hour": i, "spawn_rate": 1.5} for i in range(10, 17)] + \
        [{"id": i+20, "hour": i, "spawn_rate": 0.8} for i in range(19, 23)],
    "day_multipliers": [
        {"id": 1, "day_of_week": "monday", "multiplier": 1.0},
        {"id": 2, "day_of_week": "tuesday", "multiplier": 1.0},
        {"id": 3, "day_of_week": "wednesday", "multiplier": 1.0},
        {"id": 4, "day_of_week": "thursday", "multiplier": 1.0},
        {"id": 5, "day_of_week": "friday", "multiplier": 1.0},
        {"id": 6, "day_of_week": "saturday", "multiplier": 0.7},
        {"id": 7, "day_of_week": "sunday", "multiplier": 0.5},
    ],
    "distribution_params": [
        {
            "id": 1,
            "poisson_lambda": 3.5,
            "max_spawns_per_cycle": 50,
            "spawn_radius_meters": 800,
            "min_spawn_interval_seconds": 60
        }
    ],
    "country": {
        "id": 29,
        "name": "Barbados"
    }
}


class TestSpawnConfigLoader:
    """Test suite for SpawnConfigLoader"""
    
    @pytest.fixture
    def loader(self):
        """Create a SpawnConfigLoader instance for testing"""
        return SpawnConfigLoader(
            api_base_url="http://localhost:1337/api",
            cache_ttl_seconds=3600
        )
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock API response with sample config data"""
        return {
            "data": [SAMPLE_CONFIG],
            "meta": {"pagination": {"total": 1}}
        }
    
    @pytest.mark.asyncio
    async def test_get_config_by_country_success(self, loader, mock_api_response):
        """Test successful config loading from API"""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            config = await loader.get_config_by_country("Barbados")
            
            assert config is not None
            assert config["name"] == "Barbados Typical Weekday"
            assert len(config["building_weights"]) == 4
            assert len(config["poi_weights"]) == 2
            assert len(config["hourly_spawn_rates"]) == 24
            assert len(config["day_multipliers"]) == 7
    
    @pytest.mark.asyncio
    async def test_get_config_caching(self, loader, mock_api_response):
        """Test that config is cached and reused"""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # First call - should hit API
            config1 = await loader.get_config_by_country("Barbados")
            assert mock_get.call_count == 1
            
            # Second call - should use cache
            config2 = await loader.get_config_by_country("Barbados")
            assert mock_get.call_count == 1  # Still 1 - no additional API call
            
            assert config1 == config2
    
    @pytest.mark.asyncio
    async def test_get_config_cache_expiration(self, loader, mock_api_response):
        """Test that expired cache triggers new API call"""
        loader.cache_ttl = timedelta(seconds=0)  # Instant expiration
        
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # First call
            await loader.get_config_by_country("Barbados")
            assert mock_get.call_count == 1
            
            # Wait a tiny bit (cache expired)
            await asyncio.sleep(0.01)
            
            # Second call - should hit API again
            await loader.get_config_by_country("Barbados")
            assert mock_get.call_count == 2
    
    def test_get_hourly_rate(self, loader):
        """Test hourly rate lookup"""
        # Morning peak
        rate = loader.get_hourly_rate(SAMPLE_CONFIG, 8)
        assert rate == 2.8
        
        # Evening peak
        rate = loader.get_hourly_rate(SAMPLE_CONFIG, 17)
        assert rate == 2.3
        
        # Late night
        rate = loader.get_hourly_rate(SAMPLE_CONFIG, 1)
        assert rate == 0.1
    
    def test_get_hourly_rate_invalid_hour(self, loader):
        """Test hourly rate with invalid hour raises error"""
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            loader.get_hourly_rate(SAMPLE_CONFIG, 24)
        
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            loader.get_hourly_rate(SAMPLE_CONFIG, -1)
    
    def test_get_building_weight(self, loader):
        """Test building weight calculation"""
        # With peak multiplier
        weight = loader.get_building_weight(SAMPLE_CONFIG, "residential", apply_peak_multiplier=True)
        assert weight == 2.0 * 2.5  # 5.0
        
        # Without peak multiplier
        weight = loader.get_building_weight(SAMPLE_CONFIG, "residential", apply_peak_multiplier=False)
        assert weight == 2.0
        
        # School with peak multiplier
        weight = loader.get_building_weight(SAMPLE_CONFIG, "school", apply_peak_multiplier=True)
        assert weight == 2.5 * 3.0  # 7.5
        
        # Non-existent type
        weight = loader.get_building_weight(SAMPLE_CONFIG, "nonexistent")
        assert weight == 0.0
    
    def test_get_poi_weight(self, loader):
        """Test POI weight calculation"""
        # Bus station (high priority)
        weight = loader.get_poi_weight(SAMPLE_CONFIG, "bus_station", apply_peak_multiplier=True)
        assert weight == 5.0 * 1.0  # 5.0
        
        # Marketplace with peak
        weight = loader.get_poi_weight(SAMPLE_CONFIG, "marketplace", apply_peak_multiplier=True)
        assert weight == 3.0 * 1.5  # 4.5
        
        # Without peak multiplier
        weight = loader.get_poi_weight(SAMPLE_CONFIG, "marketplace", apply_peak_multiplier=False)
        assert weight == 3.0
    
    def test_get_landuse_weight(self, loader):
        """Test landuse weight calculation"""
        # Residential with peak
        weight = loader.get_landuse_weight(SAMPLE_CONFIG, "residential", apply_peak_multiplier=True)
        assert weight == 2.0 * 1.5  # 3.0
        
        # Commercial
        weight = loader.get_landuse_weight(SAMPLE_CONFIG, "commercial", apply_peak_multiplier=True)
        assert weight == 2.5 * 1.2  # 3.0
    
    def test_get_day_multiplier(self, loader):
        """Test day-of-week multiplier"""
        # Weekday
        mult = loader.get_day_multiplier(SAMPLE_CONFIG, "monday")
        assert mult == 1.0
        
        mult = loader.get_day_multiplier(SAMPLE_CONFIG, "friday")
        assert mult == 1.0
        
        # Weekend
        mult = loader.get_day_multiplier(SAMPLE_CONFIG, "saturday")
        assert mult == 0.7
        
        mult = loader.get_day_multiplier(SAMPLE_CONFIG, "sunday")
        assert mult == 0.5
        
        # Case insensitive
        mult = loader.get_day_multiplier(SAMPLE_CONFIG, "MONDAY")
        assert mult == 1.0
    
    def test_get_distribution_params(self, loader):
        """Test distribution parameters extraction"""
        params = loader.get_distribution_params(SAMPLE_CONFIG)
        
        assert params["poisson_lambda"] == 3.5
        assert params["max_spawns_per_cycle"] == 50
        assert params["spawn_radius_meters"] == 800
        assert params["min_spawn_interval_seconds"] == 60
    
    def test_get_distribution_params_missing(self, loader):
        """Test distribution params with missing data uses defaults"""
        config_no_params = SAMPLE_CONFIG.copy()
        config_no_params["distribution_params"] = []
        
        params = loader.get_distribution_params(config_no_params)
        
        # Should use defaults
        assert params["poisson_lambda"] == 3.5
        assert params["max_spawns_per_cycle"] == 50
        assert params["spawn_radius_meters"] == 800
        assert params["min_spawn_interval_seconds"] == 60
    
    def test_calculate_spawn_probability(self, loader):
        """Test full spawn probability calculation"""
        # Residential building, Monday 8am
        # feature_weight = 2.0 × 2.5 = 5.0
        # hourly_rate = 2.8
        # day_mult = 1.0
        # final = 5.0 × 2.8 × 1.0 = 14.0
        
        residential_weight = loader.get_building_weight(SAMPLE_CONFIG, "residential")
        prob = loader.calculate_spawn_probability(
            SAMPLE_CONFIG,
            feature_weight=residential_weight,
            current_hour=8,
            day_of_week="monday"
        )
        
        assert prob == 5.0 * 2.8 * 1.0  # 14.0
    
    def test_calculate_spawn_probability_weekend(self, loader):
        """Test spawn probability on weekend"""
        # School, Sunday 8am (should be very low - no school on Sunday)
        # feature_weight = 2.5 × 3.0 = 7.5
        # hourly_rate = 2.8
        # day_mult = 0.5 (Sunday)
        # final = 7.5 × 2.8 × 0.5 = 10.5
        
        school_weight = loader.get_building_weight(SAMPLE_CONFIG, "school")
        prob = loader.calculate_spawn_probability(
            SAMPLE_CONFIG,
            feature_weight=school_weight,
            current_hour=8,
            day_of_week="sunday"
        )
        
        assert prob == 7.5 * 2.8 * 0.5  # 10.5
    
    def test_clear_cache(self, loader):
        """Test cache clearing"""
        # Manually add to cache
        loader._cache["Barbados"] = (SAMPLE_CONFIG, datetime.now())
        loader._cache["Trinidad"] = (SAMPLE_CONFIG, datetime.now())
        
        assert "Barbados" in loader._cache
        assert "Trinidad" in loader._cache
        
        # Clear specific country
        loader.clear_cache("Barbados")
        assert "Barbados" not in loader._cache
        assert "Trinidad" in loader._cache
        
        # Clear all
        loader.clear_cache()
        assert len(loader._cache) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
