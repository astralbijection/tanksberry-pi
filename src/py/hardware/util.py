from enum import Enum

class Direction(Enum):
    FORWARD = (1, True, False)
    REVERSE = (-1, False, True)
    COAST = (0, False, False)
    BRAKE = (0, True, True)

    def __init__(self, direction, h_bridge_a, h_bridge_b):
        self.direction = direction
        self.h_bridge_a = h_bridge_a
        self.h_bridge_b = h_bridge_b

    @property    
    def h_bridge(self):
        return self.h_bridge_a, self.h_bridge_b
