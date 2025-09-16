"""
Vehicle Simulator Models Package

Contains simulation model components:
- people.py: People simulator with pluggable distribution models
- people_models/: Plugin models for passenger generation
- speed_models/: Vehicle physics and speed models for movement simulation
"""

from .people import PeopleSimulator, PoissonDistributionModel, IPeopleDistributionModel

# Speed models are dynamically loaded via sim_speed_model.load_speed_model()
# Available models: fixed, kinematic, aggressive, random_walk, physics

__all__ = ['PeopleSimulator', 'PoissonDistributionModel', 'IPeopleDistributionModel']