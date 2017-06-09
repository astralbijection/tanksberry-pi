import asyncio

from RPi import GPIO as gpio


class Stepper:

    def __init__(self, spr):
        self.steps = 0
        self.enabled = False
        self.spr = spr

    def init(self):
        pass

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
            await asyncio.sleep(1/rate)


class StepstickStepper(Stepper):
    """A stepper motor hooked up to a stepstick."""
    def __init__(self, spr, en, dr, st):
        super(StepstickStepper, self).__init__(spr)
        self.en = en
        self.dir = dr
        self.step = st

    def init(self):
        gpio.setup([self.en, self.dir, self.step], gpio.OUT)
    
    async def step_impl(self, direction):
        gpio.output(self.dir, direction.direction == 1)
        gpio.output(self.dir, True)
        await asyncio.sleep(0.001)
        gpio.output(self.dir, False)

    async def set_enabled_impl(self, state):
        gpio.output(self.en, not state)