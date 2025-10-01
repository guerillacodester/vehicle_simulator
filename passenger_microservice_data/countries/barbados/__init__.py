"""
Barbados Passenger Behavior Plugin
Registration and initialization for Barbados-specific passenger modeling
"""

from .cultural_model import BarbadosCulturalModel
from passenger_microservice_data.base.country_plugin import CountryPlugin
import os
from pathlib import Path

class BarbadosPlugin(CountryPlugin):
    """Barbados country plugin for passenger simulation"""
    
    def __init__(self):
        super().__init__()
        self.country_code = "bb"
        self.country_name = "Barbados"
        self.plugin_dir = Path(__file__).parent
        self.cultural_model = BarbadosCulturalModel()
    
    def get_country_info(self):
        """Return basic country information"""
        return {
            "code": self.country_code,
            "name": self.country_name,
            "region": "Caribbean",
            "timezone": "America/Barbados",
            "coordinate_system": "WGS84",
            "currency": "BBD"
        }
    
    def get_config_path(self):
        """Return path to country-specific config file"""
        return self.plugin_dir / "config.ini"
    
    def get_geographic_data_paths(self):
        """Return paths to GeoJSON files"""
        geo_dir = self.plugin_dir / "geographic_data"
        return {
            "amenities": geo_dir / "barbados_amenities.geojson",
            "busstops": geo_dir / "barbados_busstops.geojson", 
            "landuse": geo_dir / "barbados_landuse.geojson",
            "highway": geo_dir / "barbados_highway.geojson",
            "names": geo_dir / "barbados_names.geojson"
        }
    
    def get_generated_models_dir(self):
        """Return directory for pre-computed models"""
        return self.plugin_dir / "generated_models"
    
    def get_cultural_model(self):
        """Return cultural behavior model instance"""
        return self.cultural_model
    
    def validate_plugin(self):
        """Validate that all required files exist"""
        errors = []
        
        # Check config file
        config_path = self.get_config_path()
        if not config_path.exists():
            errors.append(f"Missing config file: {config_path}")
        
        # Check geographic data files
        geo_paths = self.get_geographic_data_paths()
        for data_type, path in geo_paths.items():
            if not path.exists():
                errors.append(f"Missing {data_type} file: {path}")
        
        # Check models directory
        models_dir = self.get_generated_models_dir()
        if not models_dir.exists():
            errors.append(f"Missing models directory: {models_dir}")
        
        return len(errors) == 0, errors

# Plugin registration
def get_plugin():
    """Factory function to create plugin instance"""
    return BarbadosPlugin()

# Plugin metadata for discovery
PLUGIN_INFO = {
    "name": "Barbados",
    "code": "bb", 
    "version": "1.0.0",
    "description": "Passenger behavior modeling for Barbados",
    "author": "ArkNet Transit System",
    "requires_geojson": True,
    "supported_models": ["poisson", "gaussian"],
    "cultural_features": [
        "crop_over_festival",
        "caribbean_work_patterns", 
        "tropical_climate_adjustments",
        "tourism_impact_modeling"
    ]
}