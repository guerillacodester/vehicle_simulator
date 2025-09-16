"""
Model and Landuse Package Loader

This module provides a unified loader for model.json + landuse.geojson packages.
It loads both files together and provides integrated functionality for
passenger simulation systems.
"""

import json
import os
import geopandas as gpd
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from pathlib import Path

class ModelLandusePackage:
    """
    Represents a complete model + landuse package
    """
    
    def __init__(self, model_data: Dict[str, Any], landuse_gdf: gpd.GeoDataFrame, package_path: str):
        self.model_data = model_data
        self.landuse_gdf = landuse_gdf
        self.package_path = package_path
        self.model_name = model_data.get('model_info', {}).get('name', 'unnamed')
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata"""
        return self.model_data.get('model_info', {})
    
    def get_locations(self) -> Dict[str, Any]:
        """Get all model locations"""
        return self.model_data.get('locations', {})
    
    def get_landuse_data(self) -> gpd.GeoDataFrame:
        """Get landuse GeoDataFrame"""
        return self.landuse_gdf
    
    def get_peak_time_patterns(self) -> Dict[str, Any]:
        """Get peak time configuration"""
        return self.model_data.get('peak_time_patterns', {})
    
    def get_landuse_config(self) -> Dict[str, Any]:
        """Get landuse processing configuration"""
        return self.model_data.get('landuse_processing_config', {})
    
    def get_route_config(self) -> Dict[str, Any]:
        """Get route generation configuration"""
        return self.model_data.get('route_generation_config', {})

class ModelLanduseLoader:
    """
    Unified loader for model + landuse packages
    """
    
    @staticmethod
    def load_package(model_path: str) -> ModelLandusePackage:
        """
        Load a complete model + landuse package
        
        Args:
            model_path: Path to the model.json file
            
        Returns:
            ModelLandusePackage: Complete package with model and landuse data
            
        Raises:
            FileNotFoundError: If model or landuse file not found
            ValueError: If model doesn't specify landuse file
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load model data
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        # Get landuse file reference
        landuse_filename = model_data.get('model_info', {}).get('landuse_data_file')
        if not landuse_filename:
            raise ValueError(f"Model {model_path} doesn't specify landuse_data_file")
        
        # Landuse file should be in same directory as model
        landuse_path = model_path.parent / landuse_filename
        
        if not landuse_path.exists():
            raise FileNotFoundError(f"Landuse file not found: {landuse_path}")
        
        # Load landuse data
        try:
            landuse_gdf = gpd.read_file(landuse_path)
        except Exception as e:
            raise ValueError(f"Failed to load landuse data from {landuse_path}: {e}")
        
        return ModelLandusePackage(
            model_data=model_data,
            landuse_gdf=landuse_gdf,
            package_path=str(model_path.parent)
        )

# Convenience function for quick loading
def load_model_package(model_path: str) -> ModelLandusePackage:
    """
    Load a model package by path
    
    Args:
        model_path: Full path to model file
        
    Returns:
        ModelLandusePackage: Loaded package
    """
    return ModelLanduseLoader.load_package(model_path)