import os
import sys

import pin
import util


BLASTER_PATH = '/dev/pi-blaster'

class _BlasterImpl():

    def __init__(self, path=BLASTER_PATH):
        self.path = path
    
    def _echo(self, msg):
        os.system('echo "{msg}" > {path}'.format(msg=msg, path=self.path))

    def set(self, pin, level):
        self._echo('{pin}={level}'.format(pin=pin, level=level))

    def release(self, pin):
        self._echo('release {pin}'.format(pin=pin))

class _DummyBlaster(_BlasterImpl):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import logging
        self.logger = logging.getLogger('DummyBlaster')

    def _echo(self, msg):
        self.logger.debug('echo "{msg}" > {path}'.format(msg=msg, path=self.path))


if sys.platform in ('win32',):
    pyblaster = _DummyBlaster()
else:
    pyblaster = _BlasterImpl()
print(pyblaster.set)


class BlasterPin(pin.PWMPin):

    def __init__(self, pin):
        super().__init__(pin)
        self.pwm = pwm

    def init(self):
        pass

    def set_pwm(self):
        self.pwm = pwm
        pyblaster.set(self.pin, self.pwm)

    def get_pwm(self):
        return self.pwm