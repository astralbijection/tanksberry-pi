import json
import logging
import os
import sys

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver
from twisted.python import twistedLog

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

import drivebase
import hardware


log = logging.getLogger(__name__)


class RobotControlProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        if self.factory.lock is None:
            self.factory.lock = self
            print('Client connected')
        else:
            self.sendClose()
            print('Client rejected')

    def onMessage(self, payload, isBinary):
        payload = json.loads(payload.decode('utf-8'))
        print('Received message {}'.format(payload))

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
                if power == 0:
                    if turn == 'left':
                        left, right = -power, power
                    elif turn == 'right':
                        left, right = power, -power
                if (turn == 'left') ^ (power > 0):
                    left, right = power, power/2
                else:
                    left, right = power/2, power
            drivebase.set_power(left, right) 
        except KeyError as e:
            print('Malformed data, key {} does not exist'.format(e))

    def onClose(self, wasClean, code, reason):
        self.factory.lock = None if self.factory.lock is self else self.factory.lock


class TurretProtocol(LineReceiver):

    def dataReceived(self, data):
        pass
        

class RobotControlFactory(WebSocketServerFactory):

    def __init__(self, *args, turret=None, **kwargs):
        super(RobotControlFactory, self).__init__(*args, **kwargs)
        self.drivebase = drivebase.DriveBase(hardware.left_drive, hardware.right_drive)
        self.lock = None
        self.turret = turret


if __name__ == "__main__":
    try:
        serial_name = sys.argv[1]
        log.info('Serial opens on %s', serial_name)
    except (IndexError):
        serial_name = None
        log.info('No serial port supplied, turret will not function')

    try:
        ws_port = int(sys.argv[2])
    except (IndexError, ValueError):
        ws_port = 8081
    log.info('Websocket opens on port %s', ws_port)

    log.info('Starting server')

    twistedLog.startLogging(sys.stdout)
    turret = None if serial_name is None else SerialPort(TurretProtocol(), 'p', 'dev/')
    control = RobotControlFactory(u'ws://127.0.0.1:{}'.format(ws_port), turret=turret)
    control.protocol = RobotControlProtocol
    reactor.listenTCP(ws_port, control)
    reactor.run()