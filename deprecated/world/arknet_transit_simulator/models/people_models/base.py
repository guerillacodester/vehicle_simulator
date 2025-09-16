#!/usr/bin/env python3
"""
Base Distribution Model Interface
================================

Base interface for passenger distribution models.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IPeopleDistributionModel(ABC):
    """Interface for people distribution models."""
    
    @abstractmethod
    def generate_passengers(self, count: int) -> List[Dict[str, Any]]:
        """Generate passenger data."""
        pass


class PoissonDistributionModel(IPeopleDistributionModel):
    """Simple Poisson distribution model."""
    
    def __init__(self, rate: float = 1.0):
        self.rate = rate
        
    def generate_passengers(self, count: int) -> List[Dict[str, Any]]:
        """Generate simple passenger data."""
        return [{'id': f'PASS_{i}', 'type': 'regular'} for i in range(count)]