"""
People Simulator Plugin Models
=============================

This package contains the plugin models for the people simulator,
each implementing the IPeopleDistributionModel interface.

Available Models:
- PoissonDistributionModel: Realistic passenger generation with peak hours
"""

from .base import IPeopleDistributionModel
from .poisson import PoissonDistributionModel

__all__ = [
    'IPeopleDistributionModel',
    'PoissonDistributionModel'
]