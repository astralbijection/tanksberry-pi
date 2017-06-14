import time

from RPi import GPIO as gpio


class Stepper:
    """A generic stepper motor."""

    def __init__(self, spr, min_delay=None):
        self.steps = 0
        self.enabled = False
        self.spr = spr
        self.min_delay = min_delay

    def init(self):
        pass

    def step_impl(self, direction):
        raise NotImplementedError

    def set_enabled_impl(self, state):
        raise NotImplementedError

    def steps_to_degrees(self, n):
        return 360 * n / self.spr

    def degrees_to_steps(self, a):
        return self.spr *a  / 360

    def set_enabled(self, state):
        self.set_enabled_impl(state)
        self.enabled = state

    def step(self, direction, rate):
        """
        Step the motor. This method blocks for the rate.

        :param direction: what direction to move in
        :param rate: how fast to step, in steps per second
        """
        self.step_impl(direction)
        self.steps += direction.direction
        try:
            delay = max(1/rate, self.min_delay)
        except TypeError:
            delay = 1/rate
        time.sleep(delay)


class StepstickStepper(Stepper):
    """A stepper motor hooked up to a stepstick."""
    def __init__(self, spr, en, dr, st, min_delay=None):  #pylint: disable=too-many-arguments
        super(StepstickStepper, self).__init__(spr, min_delay)
        self.pin_en = en
        self.pin_dir = dr
        self.pin_step = st

    def init(self):
        gpio.setup([self.pin_en, self.pin_dir, self.pin_step], gpio.OUT)
    
    def step_impl(self, direction):
        gpio.output(self.pin_dir, direction.direction == 1)
        gpio.output(self.pin_step, True)
        time.sleep(0.001)
        gpio.output(self.pin_step, False)

    def set_enabled_impl(self, state):
        gpio.output(self.dspin_en, not state)
