#!/usr/bin/env python3
"""
People Models Package
====================

Package for passenger distribution models.
"""

from .base import IPeopleDistributionModel, PoissonDistributionModel

__all__ = ['IPeopleDistributionModel', 'PoissonDistributionModel']