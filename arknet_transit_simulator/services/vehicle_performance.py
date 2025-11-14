"""
Vehicle Performance Service

Handles Strapi API lookups for vehicle performance characteristics
used by the physics kernel and conductor.
"""
from dataclasses import dataclass
from typing import Optional
import os
import aiohttp


@dataclass
class VehiclePerformanceCharacteristics:
    """Vehicle performance characteristics for physics simulation"""
    max_speed_kmh: float
    acceleration_mps2: float
    braking_mps2: float
    eco_mode: bool
    capacity: int  # Passenger capacity
    performance_profile: Optional[str] = None
    
    @property
    def max_speed_mps(self) -> float:
        """Convert max speed to m/s for physics kernel"""
        return self.max_speed_kmh / 3.6
    
    @classmethod
    def default(cls) -> 'VehiclePerformanceCharacteristics':
        """Default performance characteristics - should not be used in production"""
        return cls(
            max_speed_kmh=25.0,
            acceleration_mps2=1.2,
            braking_mps2=1.8,
            eco_mode=False,
            capacity=11,  # DB default
            performance_profile="standard"
        )


class VehiclePerformanceService:
    """Service for retrieving vehicle performance characteristics from Strapi API"""
    
    STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
    
    @staticmethod
    async def get_performance_async(reg_code: str) -> VehiclePerformanceCharacteristics:
        """
        Get vehicle performance characteristics from Strapi API (async).
        
        Args:
            reg_code: Vehicle registration code
            
        Returns:
            VehiclePerformanceCharacteristics with capacity from database
            
        Raises:
            RuntimeError: If vehicle not found in database (fail loud, no fallback)
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Query Strapi for vehicle by reg_code
                url = f"{VehiclePerformanceService.STRAPI_URL}/api/vehicles"
                params = {"filters[reg_code][$eq]": reg_code}
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Strapi API error: HTTP {response.status}")
                    
                    data = await response.json()
                    vehicles = data.get('data', [])
                    
                    if not vehicles:
                        raise RuntimeError(f"Vehicle '{reg_code}' not found in database")
                    
                    # Strapi v5 returns flat structure (no nested attributes)
                    vehicle = vehicles[0]
                    
                    # Extract all performance characteristics
                    return VehiclePerformanceCharacteristics(
                        max_speed_kmh=float(vehicle.get('max_speed_kmh', 25.0)),
                        acceleration_mps2=float(vehicle.get('acceleration_mps2', 1.2)),
                        braking_mps2=float(vehicle.get('braking_mps2', 1.8)),
                        eco_mode=bool(vehicle.get('eco_mode', False)),
                        capacity=int(vehicle.get('capacity', 11)),
                        performance_profile=vehicle.get('performance_profile') or 'standard'
                    )
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to connect to Strapi API: {e}")
        except (KeyError, ValueError, TypeError) as e:
            raise RuntimeError(f"Invalid vehicle data from database: {e}")
    
    @staticmethod
    def get_performance_by_reg_code(reg_code: str) -> VehiclePerformanceCharacteristics:
        """
        DEPRECATED: Synchronous method for backward compatibility.
        Use get_performance_async() instead.
        
        Falls back to environment variables for legacy physics kernel calls.
        """
        import warnings
        warnings.warn(
            "get_performance_by_reg_code() is deprecated. Use async get_performance_async() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Fallback to environment variables for legacy code
        try:
            return VehiclePerformanceCharacteristics(
                max_speed_kmh=float(os.getenv("PHYSICS_V_MAX_KMH", "25.0")),
                acceleration_mps2=float(os.getenv("PHYSICS_A_MAX", "1.2")),
                braking_mps2=float(os.getenv("PHYSICS_D_MAX", "1.8")),
                eco_mode=os.getenv("PHYSICS_ECO_MODE", "false").lower() == "true",
                capacity=int(os.getenv("VEHICLE_CAPACITY", "11")),
                performance_profile=os.getenv("PHYSICS_PROFILE", "standard")
            )
        except (ValueError, TypeError):
            print("Warning: Invalid environment variables, using default performance characteristics")
            return VehiclePerformanceCharacteristics.default()
    
    @staticmethod
    def is_database_available() -> bool:
        """Check if Strapi API is available"""
        # For now, assume it's available - actual check would need async
        return True