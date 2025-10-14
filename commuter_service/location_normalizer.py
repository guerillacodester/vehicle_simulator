"""
Location Normalizer
===================

Normalizes location data to consistent format across the codebase.

Handles various input formats:
- Tuple: (lat, lon)
- Dict: {"lat": float, "lon": float}
- Dict: {"latitude": float, "longitude": float}
- List: [lat, lon]

Output: Always returns (lat, lon) tuple
"""

from typing import Dict, List, Union, Tuple


class LocationNormalizer:
    """
    Normalizes location data to consistent (lat, lon) tuple format.
    
    Examples:
        >>> norm = LocationNormalizer()
        >>> norm.normalize((13.0969, -59.6145))
        (13.0969, -59.6145)
        
        >>> norm.normalize({"lat": 13.0969, "lon": -59.6145})
        (13.0969, -59.6145)
        
        >>> norm.normalize([13.0969, -59.6145])
        (13.0969, -59.6145)
    """
    
    @staticmethod
    def normalize(location: Union[Tuple[float, float], Dict, List]) -> Tuple[float, float]:
        """
        Convert various location formats to (lat, lon) tuple.
        
        Args:
            location: Location in various formats (tuple, dict, or list)
        
        Returns:
            Tuple of (latitude, longitude)
        
        Raises:
            ValueError: If location format is invalid or cannot be parsed
        """
        # Already a tuple - return as-is
        if isinstance(location, tuple):
            if len(location) != 2:
                raise ValueError(f"Tuple must have exactly 2 elements, got {len(location)}")
            return (float(location[0]), float(location[1]))
        
        # Dictionary format
        if isinstance(location, dict):
            # Try {"lat": ..., "lon": ...}
            if "lat" in location and "lon" in location:
                return (float(location["lat"]), float(location["lon"]))
            
            # Try {"latitude": ..., "longitude": ...}
            if "latitude" in location and "longitude" in location:
                return (float(location["latitude"]), float(location["longitude"]))
            
            raise ValueError(
                f"Invalid location dict format: {location}. "
                "Expected keys: ('lat', 'lon') or ('latitude', 'longitude')"
            )
        
        # List format
        if isinstance(location, list):
            if len(location) != 2:
                raise ValueError(f"List must have exactly 2 elements, got {len(location)}")
            return (float(location[0]), float(location[1]))
        
        raise ValueError(
            f"Cannot normalize location of type {type(location)}. "
            "Expected tuple, dict, or list"
        )
    
    @staticmethod
    def to_dict(location: Tuple[float, float], format: str = "short") -> Dict[str, float]:
        """
        Convert (lat, lon) tuple to dictionary.
        
        Args:
            location: Tuple of (latitude, longitude)
            format: "short" for {"lat", "lon"} or "long" for {"latitude", "longitude"}
        
        Returns:
            Dictionary with location data
        """
        if format == "short":
            return {"lat": location[0], "lon": location[1]}
        elif format == "long":
            return {"latitude": location[0], "longitude": location[1]}
        else:
            raise ValueError(f"Invalid format '{format}'. Use 'short' or 'long'")
    
    @staticmethod
    def to_list(location: Tuple[float, float]) -> List[float]:
        """
        Convert (lat, lon) tuple to list.
        
        Args:
            location: Tuple of (latitude, longitude)
        
        Returns:
            List [latitude, longitude]
        """
        return [location[0], location[1]]
    
    @staticmethod
    def validate(location: Tuple[float, float]) -> bool:
        """
        Validate that location coordinates are within valid ranges.
        
        Args:
            location: Tuple of (latitude, longitude)
        
        Returns:
            True if valid, False otherwise
        """
        lat, lon = location
        
        # Latitude must be between -90 and 90
        if lat < -90 or lat > 90:
            return False
        
        # Longitude must be between -180 and 180
        if lon < -180 or lon > 180:
            return False
        
        return True
    
    @staticmethod
    def validate_or_raise(location: Tuple[float, float]) -> None:
        """
        Validate location and raise exception if invalid.
        
        Args:
            location: Tuple of (latitude, longitude)
        
        Raises:
            ValueError: If coordinates are out of valid range
        """
        lat, lon = location
        
        if lat < -90 or lat > 90:
            raise ValueError(f"Latitude {lat} out of range [-90, 90]")
        
        if lon < -180 or lon > 180:
            raise ValueError(f"Longitude {lon} out of range [-180, 180]")
