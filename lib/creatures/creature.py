import logging

from lib.creatures._sprite import Sprite
from lib.init_logging import init_logging

init_logging('debug')
logger = logging.getLogger(__name__)

CREATURE_SPRITES = {
    'blob': 'sprites/blob.yaml',
    'skeleton': 'sprites/skeleton.yaml',
    'level_exit': 'sprites/level_exit.yaml'  # TODO not a creature, but just throwing it in here for now
}


class Creature:
    def __init__(self, type):
        self.x = 0
        self.y = 0
        self.color = 0

        self.type = type

        self.direction = 'right'
        self.state = 'idle'

        self.is_visible = True

        self.sprite = Sprite(CREATURE_SPRITES[type])

    def tick_sprite_state(self, dt):
        """
        update sprite from game loop
        
        :param dt: 
        :return: 
        """
        if self.is_visible:
            self.sprite.tick(dt, self.state, self.direction)

    def update(self, update_data):
        """
        handle update from websocket
        
        :param update_data: 
        :return: 
        """
        logger.info(update_data)
        self.x, self.y = update_data['coords']
        self.color = update_data['color']
        self.is_visible = update_data['is_visible']

        # todo: direction, state
