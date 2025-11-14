class SpeedModel:
    """
    Base speed model.
    Stores current velocity, acceleration, and heading.
    Subclasses must implement update().
    """

    def __init__(self, initial: float = 0.0):
        self.velocity = float(initial)
        self.accel = 0.0
        self.velocity_dir = 0.0   # default heading
        self.accel_dir = 0.0      # default accel direction

    def update(self, **kwargs) -> dict:
        raise NotImplementedError("Subclasses must implement update()")
