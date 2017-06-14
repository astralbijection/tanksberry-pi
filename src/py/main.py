import click
import json
import logging
import logging.config
import subprocess
import threading
import time

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
    log.info('received index request')
    return web.FileResponse('views/index.html')

class SocketHandler:
    
    def __init__(self, yaw_thread):
        self.yaw_thread = yaw_thread
    
    async def handler(self, request):
    
        log.info('received websocket request')
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            log.debug('message received: %s', msg.data)
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
    
        log.info('websocket closed')

        return ws


class YawThread(threading.Thread):
    
    def __init__(self, stop_event):
        super().__init__()
        self.stop_event = stop_event
        self.yaw_target = 0

    def run(self):
        log.debug('Yaw handler started')
        while not self.stop_event.is_set():
            track = self.yaw_target * devices.yaw_turret.spr / 360
            track = int(track)
            if devices.yaw_turret.steps == track:  # Leave if we're already there
                time.sleep(0.01) 
            direction = hardware.Direction.FORWARD if track > devices.yaw_turret.steps else hardware.Direction.REVERSE
            devices.yaw_turret.step(direction, constants.GIMBAL_SPEED)
        log.debug('Yaw handler stopped')


def get_cleaup_callback(stop_event, front_camera, scope_camera):
    async def cb(event):
        log.info('Stopping robot')

        log.info('Stopping camera subprocesses')
        front_camera.kill()
        scope_camera.kill()

        log.info('Sending stop_event to yaw_thread')
        stop_event.set()

        log.info('Clearing GPIO pins')
        gpio.cleanup()
    return cb


@click.command()
@click.option('-p', '--port', default=8080, help='server port')
@click.option('-c', '--camera-port', default=8081, help='camera port start')
@click.option('-m', '--mjpg-streamer', default=None, type=click.Path(exists=True), help='mjpg-streamer directory')
def main(port, camera_port, mjpg_streamer):

    logging.basicConfig(level=logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.debug('Debug messages enabled')
    log.info('Initializing tank')
    log.info('Server will start on port %s', port)
    log.info('Camera port numbering will start at %s', camera_port)
    if mjpg_streamer is None:
        log.warning('No mjpg-streamer path supplied, camera will not be started')
    else:
        log.info('mjpg-streamer path: %s', mjpg_streamer)

    log.info('Initializing Raspberry Pi GPIO')
    gpio.setmode(gpio.BCM)

    log.info('Initializing devices')
    devices.drivebase.init()
    devices.yaw_turret.init()

    log.info('Starting mjpg-streamer subprocesses')
    front_camera = subprocess.Popen(('scripts/camfront.sh', mjpg_streamer, camera_port))
    scope_camera = subprocess.Popen(('scripts/camscope.sh', mjpg_streamer, camera_port))

    log.info('Starting yaw thread')
    stop_event = threading.Event()
    yaw_thread = YawThread(stop_event)
    yaw_thread.start()
    
    log.info('Initializing server')
    socket_handler = SocketHandler(yaw_thread)

    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/socket', socket_handler.handler)
    app.router.add_static('/static', 'static')
    
    app.on_cleanup.append(get_cleaup_callback(stop_event, front_camera, scope_camera))

    log.info('Starting server')

    web.run_app(app, port=8080)


if __name__ == "__main__":
    main()
