import logging

from lib.creatures._sprite import Sprite
from lib.init_logging import init_logging

init_logging('debug')
logger = logging.getLogger(__name__)


class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.color = 0

        self.hit_points = 0

        self.direction = 'right'
        self.sprite_state = 'idle'

        self.is_visible = True

        self.sprite = Sprite('sprites/player.yaml')

    def tick_sprite_state(self, dt):
        """
        update sprite from game loop
        
        :param dt: 
        :return: 
        """
        self.sprite.tick(dt, self.sprite_state, self.direction)

    def update(self, update_data):
        """
        handle update from websocket
        
        :param update_data: 
        :return: 
        """
        self.x, self.y = update_data['coords']
        self.color = update_data['color']
        if update_data['hit_points'] < self.hit_points:
            self.sprite.add_current_effect(ms=100, color=196)
        self.hit_points = update_data['hit_points']
        self.sprite_state = update_data['sprite_state']
