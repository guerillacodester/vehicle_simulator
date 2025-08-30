from abc import ABC, abstractmethod

class SpeedModel(ABC):
    """
    Abstract base class for speed models.
    Every speed model must implement update() which returns the speed in km/h.
    """

    def __init__(self, min_speed: float = 30.0, max_speed: float = 80.0, initial: float = None):
        self.min_speed = min_speed
        self.max_speed = max_speed
        if initial is not None:
            self.speed = float(initial)
        else:
            # Default: midpoint
            self.speed = (self.min_speed + self.max_speed) / 2.0

    @abstractmethod
    def update(self) -> float:
        """Return the updated speed for this tick."""
        raise NotImplementedError
