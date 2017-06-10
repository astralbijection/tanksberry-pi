from . import util
from .pyblaster import pyblaster

class Servo:

    def __init__(self, pin, period=10000, min=1000, max=2000):
        """
        Servo parameters are in milliseconds
        """
        self.pin = pin

        self.period = period
        self.min = min
        self.max = max

    def set(self, signal):
        power = util.lin_map(signal, 0, 1, self.min/self.period, self.max/self.period)
        pyblaster.set(self.pin, power)
