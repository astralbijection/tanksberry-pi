import smbus

import drivebase
import hardware
import turret


i2c_bus = smbus.SMBus(1)

left_drive = hardware.HBridgeMotor(17, 5, 27)
right_drive = hardware.HBridgeMotor(23, 22, 6)
drivebase = drivebase.DriveBase(left_drive, right_drive)

yaw_turret = hardware.StepstickStepper(2048, 0, 0, 0, 0.002)  # TODO: CHANGE THESE PINS
turret_uc = turret.TurretMicrocontroller(0x32, i2c_bus)
turret = turret.Turret(turret_uc, yaw_turret)
