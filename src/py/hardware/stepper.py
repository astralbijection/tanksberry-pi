import asyncio

from RPi import GPIO as gpio

from . import util

class Stepper:
    """A generic stepper motor."""

    def __init__(self, spr, min_delay=None):
        self.steps = 0
        self.enabled = False
        self.spr = spr
        self.min_delay = min_delay

    def init(self):
        pass

    def steps_to_degrees(self, n):
        return 360 * n / self.spr

    def degrees_to_steps(self, a):
        return self.spr * a / 360

    async def step_impl(self, direction):
        raise NotImplementedError

    async def set_enabled_impl(self, state):
        raise NotImplementedError

    async def set_enabled(self, state):
        await self.set_enabled_impl()
        self.enabled = state

    async def step(self, direction, rate, times=1):
        """
        Step the motor several times.

        :param direction: what direction to move in
        :param rate: how fast to step, in steps per second
        :param times: how many times to step
        """
        for _ in range(times):
            await self.step_impl()
            self.steps += direction.direction
            try:
                delay = max(1/rate, self.min_delay)
            except TypeError:
                delay = 1/rate
            await asyncio.sleep(delay)

    async def track_target(self, target, rate, *, degrees=False):
        """
        A periodic function. It will attempt to step towards the target until it is there.

        :param target: a callable that returns the target every time it is called.
        :param rate: how fast to track the target
        :param degrees: if we are using degrees instead of steps
        """
        track = target()
        if degrees:  # Convert to degrees if necessary
            track = track * self.spr / 360
        track = int(track)
        if self.steps == track:  # Leave if we're already there
            return
        direction = util.Direction.FORWARD if track > self.steps else util.Direction.REVERSE
        await self.step(direction, rate)

    async def step_to(self, target, rate, *, degrees=False):
        """
        Step to an angle.

        :param target: where to step to
        :param rate: how fast
        :param degrees: if we are using degrees instead of steps
        """
        while self.steps != target:
            await self.track_target(lambda: target, rate, degrees=degrees)

class StepstickStepper(Stepper):
    """A stepper motor hooked up to a stepstick."""
    def __init__(self, spr, en, dr, st, min_delay=None):
        super(StepstickStepper, self).__init__(spr, min_delay)
        self.pin_en = en
        self.pin_dir = dr
        self.pin_step = st

    def init(self):
        gpio.setup([self.pin_en, self.pin_dir, self.pin_step], gpio.OUT)
    
    async def step_impl(self, direction):
        gpio.output(self.pin_dir, direction.direction == 1)
        gpio.output(self.pin_step, True)
        await asyncio.sleep(0.001)
        gpio.output(self.pin_step, False)

    async def set_enabled_impl(self, state):
        gpio.output(self.pin_en, not state)
