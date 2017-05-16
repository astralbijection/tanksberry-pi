import json
import os
import sys

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.protocols.basic import LineReceiver
from twisted.python import log

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

import drivebase
import hardware


try:
    PORT = int(sys.argv[1])
except (IndexError, ValueError):
    PORT = 8081

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

    def __init__(self, *args, **kwargs):
        super(RobotControlFactory, self).__init__(*args, **kwargs)
        self.drivebase = drivebase.DriveBase(hardware.left_drive, hardware.right_drive)
        self.lock = None


if __name__ == "__main__":
    log.startLogging(sys.stdout)

    #turret = SerialPort(TurretProtocol(), 'p', 'dev/')
    control = RobotControlFactory(u'ws://127.0.0.1:{}'.format(PORT))
    control.protocol = RobotControlProtocol
    reactor.listenTCP(PORT, control)
    reactor.run()