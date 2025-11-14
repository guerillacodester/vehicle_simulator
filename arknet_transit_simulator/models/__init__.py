"""
Vehicle Simulator Models Package

Contains simulation model components:
- speed_models/: Vehicle physics and speed models for movement simulation

Note: Commuter models have been moved to the independent commuter microservice
      with plugin-based country-specific behavior modeling.
"""

# Speed models are dynamically loaded via sim_speed_model.load_speed_model()
# Available models: fixed, kinematic, aggressive, random_walk, physics

# Commuter models now handled by independent microservice
__all__ = []