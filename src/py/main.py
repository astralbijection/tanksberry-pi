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

async def socket_handler(request):

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
            turret = control.TurretControl(ctrl['yaw'], ctrl['pitch'])
            log.debug('turret input received: %s', turret)
            devices.turret_uc.move_xgim(turret.pitch, constants.GIMBAL_SPEED)
            yaw_target = turret.yaw

    log.debug('websocket closed')

    return ws


def yaw_handler(target):
    log.info('Yaw handler started.')
    while True:
        track = target() * devices.yaw_turret.spr / 360
        track = int(track)
        if devices.yaw_turret.steps == track:  # Leave if we're already there
            continue
        direction = hardware.Direction.FORWARD if track > devices.yaw_turret.steps else util.Direction.REVERSE
        devices.yaw_turret.step(direction, constants.GIMBAL_SPEED)

async def cleanup():
    gpio.cleanup()

def main():

    global yaw_thread, yaw_target

    logging.basicConfig(level=logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.debug('debug enabled')
    log.info('Initializing Raspberry Pi GPIO')
    gpio.setmode(gpio.BCM)

    log.info('Initializing devices')
    devices.drivebase.init()
    devices.yaw_turret.init()

    log.info('Initializing yaw thread')
    yaw_target = 0
    yaw_thread = threading.Thread(target=yaw_handler, args=(lambda: yaw_target,))
    
    log.info('Starting yaw thread')
    yaw_thread.start()
    
    log.info('Initializing server')

    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/socket', socket_handler)
    app.router.add_static('/static', 'static')
    
    app.on_cleanup.append(cleanup)

    log.info('Starting server')

    web.run_app(app, port=8080)

if __name__ == "__main__":
    main()
