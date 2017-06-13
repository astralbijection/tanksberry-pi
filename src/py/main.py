import json
import logging
import logging.config
import threading

import aiohttp
from aiohttp import web

from RPi import GPIO as gpio 

import constants
import control
import devices
import hardware
import util


log = logging.getLogger(__name__)


async def index_handler(request):
    log.info('webpage request')
    return web.FileResponse('views/index.html')

class SocketHandler:
    
    def __init__(self, yaw_thread):
        self.yaw_thread = yaw_thread
    
    async def handler(self, request):
    
        log.info('websocket request')
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            log.debug('received message: %s', msg.data)
            data = json.loads(msg.data)
        
            cmd, ctrl = data
        
            if cmd == 'drive':
                drive = control.DriveControl(ctrl['left'], ctrl['right'])
                log.debug('drive input received: %s', drive)
                devices.drivebase.set_power(drive.left, drive.right)
        
            elif cmd == 'turret':
                turret = control.TurretControl(ctrl['pitch'], ctrl['yaw'])
                log.debug('turret input received: %s', turret)
                devices.turret_uc.move_xgim(turret.pitch, constants.GIMBAL_SPEED)
                self.yaw_thread.yaw_target = turret.yaw
                log.debug('yt=%s', self.yaw_thread.yaw_target)

            elif cmd == 'laser':
                devices.turret_uc.set_laser(ctrl)
                log.debug('laser input received: %s', ctrl)
    
        log.debug('websocket closed')

        return ws

class YawThread(threading.Thread):
    
    def __init__(self):
        super().__init__()
        self.yaw_target = 0

    def run(self):
        log.info('Yaw handler started.')
        while True:
            track = self.yaw_target * devices.yaw_turret.spr / 360
            track = int(track)
            if devices.yaw_turret.steps == track:  # Leave if we're already there
#                log.debug('yaw target reached')
                continue
            direction = hardware.Direction.FORWARD if track > devices.yaw_turret.steps else hardware.Direction.REVERSE
            devices.yaw_turret.step(direction, constants.GIMBAL_SPEED)

_yaw_thread = None

async def cleanup(event):
    gpio.cleanup()

def main():

    logging.basicConfig(level=logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.debug('debug enabled')
    log.info('Initializing Raspberry Pi GPIO')
    gpio.setmode(gpio.BCM)

    log.info('Initializing devices')
    devices.drivebase.init()
    devices.yaw_turret.init()

    log.info('Initializing yaw thread')
    _yaw_thread = YawThread()
    
    log.info('Starting yaw thread')
    _yaw_thread.start()
    log.debug('initialized %s', _yaw_thread)
    
    log.info('Initializing server')
    
    socket_handler = SocketHandler(_yaw_thread)

    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/socket', socket_handler.handler)
    app.router.add_static('/static', 'static')
    
    app.on_cleanup.append(cleanup)

    log.info('Starting server')

    web.run_app(app, port=8080)

if __name__ == "__main__":
    main()
