import random
from .speed_model import SpeedModel

class RandomWalkSpeed(SpeedModel):
    """
    Random walk speed model.
    Speed wanders between min_speed and max_speed with small random adjustments.
    """

    def __init__(
        self,
        min_speed: float = 30.0,
        max_speed: float = 80.0,
        initial: float = None,
        step: float = 2.0,
        **kwargs
    ):
        super().__init__(min_speed=min_speed, max_speed=max_speed, initial=initial)
        # If no initial provided, pick random start between min and max
        if initial is None:
            self.speed = random.uniform(self.min_speed, self.max_speed)
        self.step = float(step)  # maximum delta change per tick

    def update(self) -> float:
        """
        Update speed by a small random amount within bounds.
        """
        delta = random.uniform(-self.step, self.step)
        self.speed = max(self.min_speed, min(self.max_speed, self.speed + delta))
        return self.speed
