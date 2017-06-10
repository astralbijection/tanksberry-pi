from smbus import SMBus

import util


GIMBAL = ord('g')
GUN = ord('t')


class TurretMicrocontroller:
    """The Arduino, connected via I2C, that controls firing and pitch"""
    def __init__(self, i2c_addr, bus):
        self.i2c_addr = i2c_addr
        self.bus = bus

    def move_xgim(self, angle, speed):
        """
        :param angle: angle to move to, in degrees
        :param speed: rate to move at, in degrees/second
        """
        out_a = util.intbyte(int(util.lin_map(angle, 0, 360, 0, 32768)), True)
        out_s = util.intbyte(int(util.lin_map(speed, 0, 360, 0, 32768)))
        self.bus.write_i2c_block_data(self.i2c_addr, ord('m'), out_a + out_s)

    def stop_xgim(self):
        """
        Stop the gimbal where it is.
        """
        self.bus.write_byte(self.i2c_addr, ord('s'))

    def fire(self, times, delay):
        """
        :param times: bullets to fire
        :param delay: delay between shots, in seconds
        """
        out_d = util.intbyte(int(delay*10000000))
        self.bus.write_i2c_block_data(self.i2c_addr, ord('t'), [times] + out_d)

    def stop_firing(self):
        self.bus.write_byte(self.i2c_addr, ord('q'))

    def return_gun(self):
        self.bus.write_byte(self.i2c_addr, ord('r'))

    def disable_motor(self, motor):
        self.bus.write_byte_data(self.i2c_addr, ord('d'), motor)

    def enable_motor(self, motor):
        self.bus.write_byte_data(self.i2c_addr, ord('c'), motor)

    def set_laser(self, level):
        """
        Set the laser to be a certain level

        :param level: between 0 and 1
        """
        self.bus.write_byte_data(self.i2c_addr, ord('l'), int(util.lin_map(level, 0, 1, 0, 255)))


class Turret:
    """The whole, unified turret with microcontroller and stepper"""
    def __init__(self, uc, stepper):
        super(Turret, self).__init__()
        self.uc = uc
        self.stepper = stepper

    def init(self):
        self.stepper.init()

    async def mov_pos(self, y, p, speed):
        """
        Move the turret to a position.
        """
        self.uc.move_xgim(p, speed)
        await self.stepper.step_to(y, speed)
    
    def fire(self):
        self.uc.fire()