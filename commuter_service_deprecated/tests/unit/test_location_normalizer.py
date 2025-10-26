"""
Unit Tests for Location Normalizer
===================================

Tests for location_normalizer.py module.
"""

import pytest
from commuter_service.location_normalizer import LocationNormalizer


class TestNormalize:
    """Test location normalization"""
    
    def test_normalize_tuple(self):
        """Tuple input should return same tuple"""
        location = (13.0969, -59.6145)
        result = LocationNormalizer.normalize(location)
        assert result == (13.0969, -59.6145)
        assert isinstance(result, tuple)
    
    def test_normalize_dict_short_format(self):
        """Dict with 'lat'/'lon' keys should normalize"""
        location = {"lat": 13.0969, "lon": -59.6145}
        result = LocationNormalizer.normalize(location)
        assert result == (13.0969, -59.6145)
    
    def test_normalize_dict_long_format(self):
        """Dict with 'latitude'/'longitude' keys should normalize"""
        location = {"latitude": 13.0969, "longitude": -59.6145}
        result = LocationNormalizer.normalize(location)
        assert result == (13.0969, -59.6145)
    
    def test_normalize_list(self):
        """List input should normalize to tuple"""
        location = [13.0969, -59.6145]
        result = LocationNormalizer.normalize(location)
        assert result == (13.0969, -59.6145)
        assert isinstance(result, tuple)
    
    def test_normalize_integer_values(self):
        """Integer coordinates should convert to float"""
        location = (13, -59)
        result = LocationNormalizer.normalize(location)
        assert result == (13.0, -59.0)
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)
    
    def test_normalize_string_numbers(self):
        """String numbers should convert to float"""
        location = ("13.0969", "-59.6145")
        result = LocationNormalizer.normalize(location)
        assert result == (13.0969, -59.6145)
    
    def test_normalize_invalid_dict_keys(self):
        """Dict with wrong keys should raise ValueError"""
        location = {"x": 13.0969, "y": -59.6145}
        with pytest.raises(ValueError, match="Invalid location dict format"):
            LocationNormalizer.normalize(location)
    
    def test_normalize_invalid_tuple_length(self):
        """Tuple with wrong length should raise ValueError"""
        location = (13.0969, -59.6145, 100)  # 3 elements
        with pytest.raises(ValueError, match="must have exactly 2 elements"):
            LocationNormalizer.normalize(location)
    
    def test_normalize_invalid_list_length(self):
        """List with wrong length should raise ValueError"""
        location = [13.0969]  # Only 1 element
        with pytest.raises(ValueError, match="must have exactly 2 elements"):
            LocationNormalizer.normalize(location)
    
    def test_normalize_invalid_type(self):
        """Invalid type should raise ValueError"""
        location = "13.0969,-59.6145"  # String
        with pytest.raises(ValueError, match="Cannot normalize location of type"):
            LocationNormalizer.normalize(location)
    
    def test_normalize_none(self):
        """None should raise ValueError"""
        with pytest.raises(ValueError, match="Cannot normalize location of type"):
            LocationNormalizer.normalize(None)


class TestToDict:
    """Test conversion to dictionary"""
    
    def test_to_dict_short_format(self):
        """Convert to short format dict"""
        location = (13.0969, -59.6145)
        result = LocationNormalizer.to_dict(location, format="short")
        assert result == {"lat": 13.0969, "lon": -59.6145}
    
    def test_to_dict_long_format(self):
        """Convert to long format dict"""
        location = (13.0969, -59.6145)
        result = LocationNormalizer.to_dict(location, format="long")
        assert result == {"latitude": 13.0969, "longitude": -59.6145}
    
    def test_to_dict_default_format(self):
        """Default format should be short"""
        location = (13.0969, -59.6145)
        result = LocationNormalizer.to_dict(location)
        assert result == {"lat": 13.0969, "lon": -59.6145}
    
    def test_to_dict_invalid_format(self):
        """Invalid format should raise ValueError"""
        location = (13.0969, -59.6145)
        with pytest.raises(ValueError, match="Invalid format"):
            LocationNormalizer.to_dict(location, format="invalid")


class TestToList:
    """Test conversion to list"""
    
    def test_to_list(self):
        """Convert tuple to list"""
        location = (13.0969, -59.6145)
        result = LocationNormalizer.to_list(location)
        assert result == [13.0969, -59.6145]
        assert isinstance(result, list)


class TestValidate:
    """Test location validation"""
    
    def test_validate_valid_location(self):
        """Valid location should return True"""
        location = (13.0969, -59.6145)
        assert LocationNormalizer.validate(location) is True
    
    def test_validate_equator_prime_meridian(self):
        """Equator and prime meridian should be valid"""
        location = (0.0, 0.0)
        assert LocationNormalizer.validate(location) is True
    
    def test_validate_north_pole(self):
        """North pole should be valid"""
        location = (90.0, 0.0)
        assert LocationNormalizer.validate(location) is True
    
    def test_validate_south_pole(self):
        """South pole should be valid"""
        location = (-90.0, 0.0)
        assert LocationNormalizer.validate(location) is True
    
    def test_validate_date_line(self):
        """International date line should be valid"""
        location = (0.0, 180.0)
        assert LocationNormalizer.validate(location) is True
        
        location = (0.0, -180.0)
        assert LocationNormalizer.validate(location) is True
    
    def test_validate_latitude_too_high(self):
        """Latitude > 90 should be invalid"""
        location = (91.0, 0.0)
        assert LocationNormalizer.validate(location) is False
    
    def test_validate_latitude_too_low(self):
        """Latitude < -90 should be invalid"""
        location = (-91.0, 0.0)
        assert LocationNormalizer.validate(location) is False
    
    def test_validate_longitude_too_high(self):
        """Longitude > 180 should be invalid"""
        location = (0.0, 181.0)
        assert LocationNormalizer.validate(location) is False
    
    def test_validate_longitude_too_low(self):
        """Longitude < -180 should be invalid"""
        location = (0.0, -181.0)
        assert LocationNormalizer.validate(location) is False


class TestValidateOrRaise:
    """Test validation with exceptions"""
    
    def test_validate_or_raise_valid(self):
        """Valid location should not raise"""
        location = (13.0969, -59.6145)
        LocationNormalizer.validate_or_raise(location)  # Should not raise
    
    def test_validate_or_raise_invalid_latitude(self):
        """Invalid latitude should raise ValueError"""
        location = (91.0, 0.0)
        with pytest.raises(ValueError, match="Latitude .* out of range"):
            LocationNormalizer.validate_or_raise(location)
    
    def test_validate_or_raise_invalid_longitude(self):
        """Invalid longitude should raise ValueError"""
        location = (0.0, 181.0)
        with pytest.raises(ValueError, match="Longitude .* out of range"):
            LocationNormalizer.validate_or_raise(location)


class TestRoundTrip:
    """Test round-trip conversions"""
    
    def test_round_trip_tuple_dict_tuple(self):
        """Tuple -> Dict -> Tuple should preserve values"""
        original = (13.0969, -59.6145)
        as_dict = LocationNormalizer.to_dict(original)
        back_to_tuple = LocationNormalizer.normalize(as_dict)
        assert back_to_tuple == original
    
    def test_round_trip_tuple_list_tuple(self):
        """Tuple -> List -> Tuple should preserve values"""
        original = (13.0969, -59.6145)
        as_list = LocationNormalizer.to_list(original)
        back_to_tuple = LocationNormalizer.normalize(as_list)
        assert back_to_tuple == original
    
    def test_round_trip_dict_tuple_dict(self):
        """Dict -> Tuple -> Dict should preserve values"""
        original = {"lat": 13.0969, "lon": -59.6145}
        as_tuple = LocationNormalizer.normalize(original)
        back_to_dict = LocationNormalizer.to_dict(as_tuple)
        assert back_to_dict == original


# Run with: pytest commuter_service/tests/unit/test_location_normalizer.py -v
