from RPi import GPIO as gpio


class OutputPin:
    """An abstract pin that outputs a signal."""

    def __init__(self):
        self.state = False

    def init(self):
        pass

    def set(self, state):
        self.state = state

    def get(self):
        return self.state


class PWMPin(OutputPin):
    """A pin that outputs a PWM signal"""
    def __init__(self):
        super().__init__()
        self.pwm = 0

    def set_pwm(self):
        self.pwm = pwm

    def get_pwm(self):
        return self.pwm

class GPIOOutputPin(OutputPin):
    """A pin connected directly to the GPIO."""

    def __init__(self, arg):
        super().__init__()
        if type(arg) == int:
            self.port = arg
        elif type(arg) == OutputPin:
            self.port = arg.port

    def init(self, state):
        gpio.setup(self.port, gpio.OUT)

    def set(self, state):
        super().set(state)
        gpio.output(self.port, state)


def pin_factory(cls, *args, **kwargs):
    if len(args) >= 0 and isinstance(args[0], OutputPin):
        return args[0]
    return cls(*args, **kwargs)


if __name__ == '__main__':
    p1 = pin_factory(GPIOOutputPin, 1)
    print(p1)
    p2 = pin_factory(GPIOOutputPin, 2)
    print(p2)
    p3 = pin_factory(GPIOOutputPin, p1)
    print(p3)
