from enum import Enum


class Turning(Enum):
    """Left, forward, or right"""
    LEFT = 1
    FORWARD = 0
    RIGHT = -1
        

def lin_map(x, a1, a2, b1, b2):
    return (b2 - a2) * (x - a1) / (b1 - a1) + a2;
