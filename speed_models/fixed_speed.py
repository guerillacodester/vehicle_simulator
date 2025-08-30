from speed_models.aggressive_speed import BaseSSpeedModelpeed
from speed_models.speed_model import SpeedModel

class FixedSpeed(SpeedModel):
    """
    Fixed constant speed model. Useful for testing and deterministic simulation.
    """

    def __init__(self,
                 min_speed: float = 30.0,
                 max_speed: float = 80.0,
                 **kwargs):
        self.min_speed = float(min_speed)
        self.max_speed = float(max_speed)
        # fixed speed = midpoint
        self.speed = (self.min_speed + self.max_speed) / 2.0

    def update(self, **_) -> float:
        return self.speed
