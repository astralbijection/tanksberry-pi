import atexit
import json
import logging
import logging.config
import os
import sys

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver
from twisted.python import log as twistedLog

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

from RPi import GPIO as gpio

import drivebase
import devices


log = logging.getLogger(__name__)


class RobotControlProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        if self.factory.lock is None:
            self.factory.lock = self
            log.info('client connected')
        else:
            self.sendClose()
            log.warning('client rejected due to existing client')

    def onMessage(self, payload, isBinary):
        payload = json.loads(payload.decode('utf-8'))
        log.debug('received message {}'.format(payload))

        try:
            drive_control = payload['drive']
            drive_mode = drive_control['mode']
            drivebase = self.factory.drivebase
            left, right = 0, 0
            if drive_mode == 'tank':
                left = float(drive_control['left'])
                right = float(drive_control['right'])
            elif drive_mode == 'wasd':
                power = float(drive_control['power'])
                turn = drive_control['turn']
                left, right = 0, 0
                if turn == 'none':
                    left, right = power, power
                else:
                    if power == 0:
                        if turn == 'left':
                            left, right = -1, 1
                        elif turn == 'right':
                            left, right = 1, -1
                    elif (turn == 'left') ^ (power > 0):
                        left, right = power, power/5
                    else:
                        left, right = power/5, power
            drivebase.set_power(left, right) 
            log.debug('motor output: l=%s r=%s', left, right)
        except KeyError as e:
            log.warning('malformed data, key {} does not exist'.format(e))

    def onClose(self, wasClean, code, reason):
        if self.factory.lock is self:
            log.info('client disconnected, removing lock')
            self.factory.lock = None
        else:
            log.info('rejected client disconnected')


class TurretProtocol(LineReceiver):

    def dataReceived(self, data):
        pass
        

class RobotControlFactory(WebSocketServerFactory):

    def __init__(self, *args, turret=None, **kwargs):
        super(RobotControlFactory, self).__init__(*args, **kwargs)
        self.drivebase = drivebase.DriveBase(devices.left_drive, devices.right_drive)
        self.lock = None
        self.turret = turret
        self.drivebase.init()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log.setLevel(logging.DEBUG)
    log.info('Starting server')
    log.info('Args supplied: %s', sys.argv)
    try:
        serial_name = sys.argv[2]
        log.info('Serial opens on %s', serial_name)
    except (IndexError):
        serial_name = None
        log.info('No serial port supplied, turret will not function')

    try:
        ws_port = int(sys.argv[1])
    except (IndexError, ValueError):
        ws_port = 8081
    log.info('Websocket opens on port %s', ws_port)

    log.info('Initializing Raspberry Pi GPIO')
    gpio.setmode(gpio.BCM)

    log.info('Starting server')

    twistedLog.startLogging(sys.stdout)
    turret = None if serial_name is None else SerialPort(TurretProtocol(), 'p', 'dev/')
    control = RobotControlFactory(u'ws://127.0.0.1:{}'.format(ws_port), turret=turret)
    control.protocol = RobotControlProtocol
    reactor.listenTCP(ws_port, control)
    reactor.run()
    atexit.register(gpio.cleanup)
