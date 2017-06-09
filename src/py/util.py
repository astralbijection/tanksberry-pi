from enum import Enum


class Turning(Enum):
    """Left, forward, or right"""
    LEFT = 1
    FORWARD = 0
    RIGHT = -1
        

def lin_map(x, a1, b1, a2, b2):
    return (b2 - a2) * (x - a1) / (b1 - a1) + a2;

def intbyte(n, signed=False, size=2):
    return list(bytearray((n).to_bytes(size, 'big', signed=signed)))
