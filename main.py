import asyncio
import json
import time
import logging
import uuid
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
        self.char = '@'
        self.x = 0
        self.y = 0

    def update(self, update_data):
        logger.info(update_data)
        self.x, self.y = update_data['coords']


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

    def _set_tile(self, x, y, name, seen, is_visible):
        if not self.tiles.get(y, False):
            self.tiles[y] = {}

        char = TILE_CHARS.get(name, 'X')
        self.tiles[y][x] = Tile(char, seen, is_visible)

    def update_room(self, update_data):
        for tile in update_data:
            logger.info(tile)
            (x, y), name, (seen, is_visible) = tile
            self._set_tile(x, y, name, seen, is_visible)


class SendQueue:
    def __init__(self):
        self.queue = asyncio.Queue()

    def add_action(self, action):
        self.queue.put_nowait(action)

    async def get_all_actions(self):
        actions = []
        for _ in range(self.queue.qsize()):
            actions.append(await self.queue.get())
        return actions


send_queue = SendQueue()
current_room = Room()
player = Player()
other_players = {}

class Client:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.package_queue = asyncio.Queue()

    async def run(self, url):
        async with self.session.ws_connect(url) as ws:
            async for msg in ws:
                # await ws.send_str('tick!')
                
                if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    pass
                if msg.type == aiohttp.WSMsgType.text:
                    logger.debug('got msg: %s' % msg.data)
                    packet = json.loads(msg.data)
                    if packet['type'] == 'init':
                        logger.debug("Got init package")
                        logger.debug(json.dumps(packet, indent=2))

                        current_room.update_room(packet['data']['map'])

                        player.update(packet['data']['self'])

                        other_players_data = packet['data'].get('players', False)
                        if other_players_data:
                            for uid, player_data in other_players_data.items():
                                other_player = other_players.get(uid, False)
                                if not other_player:
                                    other_players[uid] = Player()
                                other_players[uid].update(player_data)

                    elif packet['type'] == 'update':
                        map = packet['data'].get('map', False)
                        if map:
                            current_room.update_room(map)
                        player_data = packet['data'].get('self', False)
                        if player_data:
                            player.update(player_data)

                        other_players_data = packet['data'].get('players', False)
                        if other_players_data:
                            for uid, player_data in other_players_data.items():
                                other_player = other_players.get(uid, False)
                                if not other_player:
                                    other_players[uid] = Player()
                                other_players[uid].update(player_data)
                    else:
                        logger.debug("Got undefined message %s" % msg.data)

                    # await ws.send_str("Pressed key code: {}".format(msg.data))
                else:
                    logger.info('got message of type %s' % msg.type)

                actions = await send_queue.get_all_actions()
                if actions:
                    logger.info('sending actions: %s' % actions)
                    await ws.send_str(json.dumps({'type': 'actions', 'data': actions}))
                logger.info('ticking...')


class ScreenManager:
    def __init__(self):
        self.send_queue = SendQueue()
        self.screen = None

    def screen_print_with_player_offset(self, s, x, y, colour=7, attr=0, bg=0):
        centre_x = (self.screen.width // 2) - player.x
        centre_y = (self.screen.height // 2) - player.y
        self.screen.print_at(s, centre_x + x, centre_y + y, colour=colour, attr=attr, bg=bg)

    def handle_input(self):
        event = self.screen.get_event()
        if event and type(event) == KeyboardEvent:
            if event.key_code == KEYS['quit']:
                return False
            action = KEY_ACTIONS.get(event.key_code, False)
            logger.info(action)
            if action:
                send_queue.add_action(action)
        return True

    def tick(self):
        pass

    async def run(self):
        FPS = 1/20
        with ManagedScreen() as screen:
            self.screen = screen
            while True:
                _continue = True
                # clear screen

                self.screen.clear_buffer(self.screen.COLOUR_WHITE, self.screen.A_NORMAL, self.screen.COLOUR_BLACK)
                self.screen.print_at('%s whoo!!' % time.time(), 0, 0)

                # render map, player is center
                for y_coord, row in current_room.tiles.items():
                    for x_coord, tile in row.items():
                        tile_char = ' '
                        draw_colour = self.screen.COLOUR_WHITE
                        if tile.is_visible:
                            tile_char = tile.char
                            draw_colour = self.screen.COLOUR_WHITE
                        elif tile.seen:
                            tile_char = tile.char
                            draw_colour = self.screen.COLOUR_MAGENTA
                        self.screen_print_with_player_offset(tile_char, x_coord, y_coord, colour=draw_colour)

                self.screen_print_with_player_offset(player.char, player.x, player.y)
                for uid, other_player in other_players.items():
                    self.screen_print_with_player_offset(other_player.char, other_player.x, other_player.y)
                self.handle_input()
                '''
                for creature in self.player.room.creatures:
                    if creature.current_tile.is_visible:
                        creature.draw(self, dt=fps)'''

                # draw the screen!
                self.screen.refresh()

                await asyncio.sleep(FPS)


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
