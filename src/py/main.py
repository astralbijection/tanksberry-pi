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

'''
def onMessage(self, payload, isBinary):
    payload = json.loads(payload.decode('utf-8'))
    log.debug('received message {}'.format(payload))

    try:

        # Drive control
        drive_control = payload['drive']
        drive_mode = drive_control['mode']
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

        devices.drivebase.set_power(left, right) 
        log.debug('motor output: l=%s r=%s', left, right)

        # Turret control
        turret_control = payload['turret']

        if turret_control['yaw'] == 'left':
            self.factory.yaw += 1
        elif turret_control['yaw'] == 'right':
            self.factory.yaw -= 1

        if turret_control['pitch'] == 'up':
            self.factory.pitch += 1
        elif turret_control['pitch'] == 'down':
            self.factory.pitch -= 1

        asyncio.get_event_loop().run_until_complete(devices.turret.mov_pos(self.factory.yaw, 
        self.factory.pitch, 180))

    except KeyError as e:
        log.warning('malformed data, key {} does not exist'.format(e))
'''

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
            log.debug(drive)
            devices.drivebase.set_power(drive.left, drive.right)
        
        elif cmd == 'turret':
            turret = control.TurretControl(**data['turret'])
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
