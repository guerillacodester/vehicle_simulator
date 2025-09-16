"""
Vehicle Performance Service

Handles database lookups for vehicle performance characteristics
used by the physics kernel.
"""
from dataclasses import dataclass
from typing import Optional
import os
import sys
from pathlib import Path

# Add fleet_manager to path for database access
project_root = Path(__file__).resolve().parent.parent.parent
fleet_manager_path = project_root / "fleet_manager"
sys.path.insert(0, str(fleet_manager_path))

try:
    from database import get_session
    from models.vehicle import Vehicle as VehicleModel
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


@dataclass
class VehiclePerformanceCharacteristics:
    """Vehicle performance characteristics for physics simulation"""
    max_speed_kmh: float
    acceleration_mps2: float
    braking_mps2: float
    eco_mode: bool
    performance_profile: Optional[str] = None
    
    @property
    def max_speed_mps(self) -> float:
        """Convert max speed to m/s for physics kernel"""
        return self.max_speed_kmh / 3.6
    
    @classmethod
    def default(cls) -> 'VehiclePerformanceCharacteristics':
        """Default performance characteristics"""
        return cls(
            max_speed_kmh=25.0,
            acceleration_mps2=1.2,
            braking_mps2=1.8,
            eco_mode=False,
            performance_profile="standard"
        )


class VehiclePerformanceService:
    """Service for retrieving vehicle performance characteristics"""
    
    @staticmethod
    def get_performance_by_reg_code(reg_code: str) -> VehiclePerformanceCharacteristics:
        """
        Get vehicle performance characteristics by registration code.
        
        Falls back to environment variables, then defaults if database unavailable.
        """
        # Try database lookup first  
        if DATABASE_AVAILABLE:
            try:
                db = get_session()
                vehicle = db.query(VehicleModel).filter(VehicleModel.reg_code == reg_code).first()
                
                if vehicle:
                    result = VehiclePerformanceCharacteristics(
                        max_speed_kmh=vehicle.max_speed_kmh,
                        acceleration_mps2=vehicle.acceleration_mps2,
                        braking_mps2=vehicle.braking_mps2,
                        eco_mode=vehicle.eco_mode,
                        performance_profile=vehicle.performance_profile
                    )
                    db.close()
                    return result
                else:
                    print(f"Warning: Vehicle '{reg_code}' not found in database, using defaults")
                    db.close()
            except Exception as e:
                print(f"Warning: Database lookup failed for vehicle '{reg_code}': {e}")
        
        # Fallback to environment variables
        try:
            return VehiclePerformanceCharacteristics(
                max_speed_kmh=float(os.getenv("PHYSICS_V_MAX_KMH", "25.0")),
                acceleration_mps2=float(os.getenv("PHYSICS_A_MAX", "1.2")),
                braking_mps2=float(os.getenv("PHYSICS_D_MAX", "1.8")),
                eco_mode=os.getenv("PHYSICS_ECO_MODE", "false").lower() == "true",
                performance_profile=os.getenv("PHYSICS_PROFILE", "standard")
            )
        except (ValueError, TypeError):
            print("Warning: Invalid environment variables, using default performance characteristics")
            return VehiclePerformanceCharacteristics.default()
    
    @staticmethod
    def is_database_available() -> bool:
        """Check if database connection is available"""
        return DATABASE_AVAILABLE