import asyncio
import json
import time
import logging
from time import sleep

import aiohttp
import click

from lib.init_logging import init_logging
from asciimatics.event import KeyboardEvent
from asciimatics.screen import ManagedScreen

init_logging('debug')
logger = logging.getLogger(__name__)

# keys needed for local stuff
KEYS = dict(
    # action: key code
    quit=ord('q')
)

# actions sent to server
KEY_ACTIONS = {
    ord('w'): 'up',
    ord('s'): 'down',
    ord('a'): 'left',
    ord('d'): 'right',
    0xa: 'fire',  # return
}


class Player:
    def __init__(self):
        self.x = 0
        self.y = 0


class Tile:
    def __init__(self, char, seen, is_visible):
        self.char = char
        self.seen = seen
        self.is_visible = is_visible


TILE_CHARS = {
    'wall': '#',
    'floor': '.'
}


class Room:
    def __init__(self):
        self.tiles = {}

    def set_tile(self, x, y, name, seen, is_visible):
        if not self.tiles.get(y, False):
            self.tiles[y] = {}

        char = TILE_CHARS.get(name, 'X')
        self.tiles[y][x] = Tile(char, seen, is_visible)

    def update_room(self, update_data):
        for tile in update_data:
            logger.info(tile)
            (x, y), name, (seen, is_visible) = tile
            self.set_tile(x, y, name, seen, is_visible)


class SendQueue:
    def __init__(self):
        self.key_actions = []


current_room = Room()


class Client:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.package_queue = asyncio.Queue()
        self.keys_pressed_queue = asyncio.Queue()

    async def run(self, url):
        async with self.session.ws_connect(url) as ws:
            async for msg in ws:
                # await ws.send_str('tick!')
                if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    pass
                if msg.type == aiohttp.WSMsgType.text:

                    packet = json.loads(msg.data)
                    if packet['type'] == 'init':
                        logger.debug("Got init package")
                        logger.debug(json.dumps(packet, indent=2))
                        current_room.update_room(packet['data']['map'])

                        pass
                    elif packet['type'] == 'update':
                        pass
                    else:
                        logger.debug("Got undefined message %s" % msg.data)

                    # await ws.send_str("Pressed key code: {}".format(msg.data))
                else:
                    logger.info('got message of type %s' % msg.type)
                logger.info('ticking...')

    async def add_key_action(self, key):
        action = KEY_ACTIONS.get(key, False)
        if action:
            await self.keys_pressed_queue.put(action)


class ScreenManager:
    def __init__(self):
        self.player = Player()
        self.send_queue = SendQueue()
        self.screen = None

    def screen_print_with_player_offset(self, s, x, y, colour=7, attr=0, bg=0):
        centre_x = (self.screen.width // 2) - self.player.x
        centre_y = (self.screen.height // 2) - self.player.y
        self.screen.print_at(s, centre_x + x, centre_y + y, colour=colour, attr=attr, bg=bg)

    def handle_input(self):
        event = self.screen.get_event()
        if event and type(event) == KeyboardEvent:
            if event.key_code == KEYS['quit']:
                return False

        return True

    def tick(self):
        pass

    async def run(self):
        with ManagedScreen() as screen:
            self.screen = screen
            while True:
                _continue = True
                # clear screen

                self.screen.clear_buffer(self.screen.COLOUR_WHITE, self.screen.A_NORMAL, self.screen.COLOUR_BLACK)
                self.screen.print_at('%s whoo!!' % time.time(), 0, 0)

                # render map, player is center
                logger.info(current_room.tiles)
                for y_coord, row in current_room.tiles.items():
                    for x_coord, tile in row.items():
                        tile_char = ' '
                        draw_colour = self.screen.COLOUR_WHITE
                        logger.info(tile)
                        if tile.is_visible:
                            tile_char = tile.char
                            draw_colour = self.screen.COLOUR_WHITE
                        elif tile.seen:
                            tile_char = tile.char
                            draw_colour = self.screen.COLOUR_MAGENTA
                        self.screen_print_with_player_offset(tile_char, x_coord, y_coord, colour=draw_colour)
                '''
                self.player.draw(self, dt=fps)
                for creature in self.player.room.creatures:
                    if creature.current_tile.is_visible:
                        creature.draw(self, dt=fps)'''

                # draw the screen!
                self.screen.refresh()

                await asyncio.sleep(.1)

            if _continue:
                # handle network input
                self.tick()

                # handle player input
                _continue = self.handle_input()

                # clear screen buffer
                self.screen.clear_buffer(self.screen.COLOUR_WHITE, self.screen.A_NORMAL, self.screen.COLOUR_BLACK)





                # draw the screen!
                self.screen.refresh()


@click.group()
def cli():
    pass


async def wait():
    while True:
        await asyncio.sleep(1)
        print('waiting!!')


@cli.command()
@click.argument('url')
def connect(url):
    c = Client()
    screen_manager = ScreenManager()
    loop = asyncio.get_event_loop()

    loop.create_task(c.run(url))
    loop.create_task(screen_manager.run())
    loop.run_forever()


cli()
