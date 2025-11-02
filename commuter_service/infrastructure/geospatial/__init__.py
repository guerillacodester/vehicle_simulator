"""
Geospatial Infrastructure - Single Source of Truth for GIS Operations

This module provides the ONLY interface for geospatial operations in commuter_service.
All spatial queries must go through this infrastructure layer.

Architecture:
- client.py: API client for geospatial service
- utils.py: Spatial calculation utilities (when API not needed)
"""
