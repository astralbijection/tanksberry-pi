from smbus import SMBus

import util


bus = SMBus(1)

GIMBAL = ord('g')
GUN = ord('t')


class Turret:
    def __init__(self, i2c_addr):
        self.i2c_addr = i2c_addr

    def move_xgim(self, angle, speed):
        """
        :param angle: angle to move to, in degrees
        :param speed: rate to move at, in degrees/second
        """
        out_a = util.intbyte(util.lin_map(angle, 0, 360, 0, 32768), True)
        out_s = util.intbyte(util.lin_map(speed, 0, 360, 0, 32768))
        bus.write_i2c_block_data(self.i2c_addr, ord('m'), out_a + out_s)

    def stop_xgim(self):
        bus.write_byte(self.i2c_addr, ord('s'))

    def fire(self, times, delay):
        """
        :param times: bullets to fire
        :param delay: delay between shots, in seconds
        """
        out_d = util.intbyte(delay*10000000)
        bus.write_i2c_block_data(self.i2c_addr, ord('t'), [times] + out_d)

    def stop_firing(self):
        bus.write_byte(self.i2c_addr, ord('q'))

    def return_gun(self):
        bus.write_byte(self.i2c_addr, ord('r'))

    def disable_motor(self, motor):
        bus.write_byte_data(self.i2c_addr, ord('d'), motor)

    def enable_motor(self, motor):
        bus.write_byte_data(self.i2c_addr, ord('c'), motor)

