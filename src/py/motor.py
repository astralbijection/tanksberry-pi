import asyncio

from RPi import GPIO as gpio


import pin
import util
import pyblaster


class DCMotor:

    def init(self):
        pass

    def set_power(self):
        raise NotImplementedError

    async def run_for_time(power, duration, end=0):
        self.set_power(power)
        await asyncio.sleep(duration)
        self.set_power(end)


class HBridgeMotor(DCMotor):
    """
    A DC Motor driven by a H-bridge
    """

    def __init__(self, en, a, b, reverse=False):
        self.en = en
        self.a = pin.pin_factory(pin.GPIOOutputPin, a if not reverse else b)
        self.b = pin.pin_factory(pin.GPIOOutputPin, b if not reverse else a)

        self.power = 0
        self.direction = util.Direction.BRAKE

    def init(self):
        self.a.init()
        self.b.init()

    def set_power(self, power):
        if power > 0:
            self._set_direction(util.Direction.FORWARD)
        else:
            self._set_direction(util.Direction.REVERSE)
        pyblaster.pyblaster.set(self.en, abs(power))

    def _set_direction(self, direction):
        a, b = direction.h_bridge
        self.a.set(a)
        self.b.set(b)
