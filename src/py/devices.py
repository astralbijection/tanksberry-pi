import smbus

import drivebase
import hardware
import turret


i2c_bus = smbus.SMBus(1)

left_drive = hardware.HBridgeMotor(5, 17, 27)
right_drive = hardware.HBridgeMotor(6, 22, 23)
drivebase = drivebase.DriveBase(left_drive, right_drive)

yaw_turret = hardware.StepstickStepper(2048, 26, 25, 24, 0.002)  # TODO: CHANGE THESE PINS
turret_uc = turret.TurretMicrocontroller(0x32, i2c_bus)
turret = turret.Turret(turret_uc, yaw_turret)
