import logging
from time import sleep

from asciimatics.event import KeyboardEvent
from asciimatics.screen import ManagedScreen
from ruamel.yaml import YAML

from lib.init_logging import init_logging
from sprite_edit.sprite_observer import SpriteObserver

init_logging('debug')

logger = logging.getLogger(__name__)

yaml = YAML()
# keys needed for local stuff
KEYS = dict(
    # action: key code
    quit=ord('q'),
    iter_sprite_state=32,  # space
    up=ord('w'),
    down=ord('s'),
    left=ord('a'),
    right=ord('d')
)


class SpriteEdit(SpriteObserver):
    def __init__(self, path):
        super().__init__(path)

        self.sprite = None
        self._load_file(path)

        self.active_state = None
        self.iter_sprite_state()  # get first state

        self.active_direction = None
        self.change_sprite_direction()

    def draw_load_error(self):
        if self.load_exceptions:
            errors = ', '.join([str(e) for e in self.load_exceptions])
            errors = errors.replace('\n', ' ').replace('\r', '').strip()
            self.screen.print_at('error loading json: %s' % errors, 3, self.screen.height - 3,
                                 colour=self.screen.COLOUR_RED)
            self.screen.print_at('(see logs for more info)', 3, self.screen.height - 2,
                                 colour=self.screen.COLOUR_RED)

    def draw_sprite(self):
        offset = (20, 3)
        cells = self.sprite.get_cells()
        for row_idx, row in enumerate(cells):
            for col_idx, char in enumerate(row):
                if char:
                    self.screen.print_at(char, offset[0] + col_idx, offset[1] + row_idx)

    def handle_input(self):
        event = self.screen.get_event()
        if event and type(event) == KeyboardEvent:
            logger.info(event.key_code)
            if event.key_code == KEYS['quit']:
                return False
            if event.key_code == KEYS['iter_sprite_state']:
                self.iter_sprite_state()
            if event.key_code == KEYS['up']:
                self.change_sprite_direction('up')
            if event.key_code == KEYS['down']:
                self.change_sprite_direction('down')
            if event.key_code == KEYS['left']:
                self.change_sprite_direction('left')
            if event.key_code == KEYS['right']:
                self.change_sprite_direction('right')

    def change_sprite_direction(self, direction=None):
        if direction in self.sprite.states[self.active_state].keys():
            self.active_direction = direction
        else:
            directions = list(self.sprite.states[self.active_state].keys())
            if directions:
                self.active_direction = directions[0]
            else:
                self.active_direction = False

    def iter_sprite_state(self):
        states = list(self.sprite.states.keys())
        if self.active_state in states:
            active_index = states.index(self.active_state)
            next_state_idx = (active_index + 1) % len(states)
            self.active_state = states[next_state_idx]
        else:
            if states:
                self.active_state = states[0]
            else:
                self.active_state = False
        self.change_sprite_direction()

    def tick(self, dt):
        if self.sprite:
            if self.sprite.states.get(self.active_state, False) \
                    and self.sprite.states[self.active_state].get(self.active_direction, False):
                self.sprite.tick(dt, self.active_state, self.active_direction)

    def draw_states(self):
        offset = (0, 0)
        self.screen.print_at('states:  ([space] to change)', offset[0], offset[1], )
        states = self.sprite.states.keys()
        for idx, state in enumerate(states):
            if state == self.active_state:
                attr = self.screen.A_BOLD
            else:
                attr = 0
            self.screen.print_at('%s' % (state), 1 + offset[0], 1 + idx + offset[1], attr=attr)

    def draw_directions(self):
        offset = (0, 20)
        if not self.sprite.states.get(self.active_state, False):
            self.iter_sprite_state()
        self.screen.print_at('directions:  ([wasd] to change)', offset[0], offset[1])
        directions = self.sprite.states[self.active_state].keys()
        for idx, direction in enumerate(directions):
            if direction == self.active_direction:
                attr = self.screen.A_BOLD
            else:
                attr = 0
            self.screen.print_at('%s' % (direction), 1 + offset[0], 1 + idx + offset[1], attr=attr)


    def run_animation(self):
        FPS = 1 / 20
        with ManagedScreen() as screen:
            self.screen = screen
            while True:
                # clear self.screen
                self.screen.clear_buffer(self.screen.COLOUR_WHITE, self.screen.A_NORMAL, self.screen.COLOUR_BLACK)

                _continue = True
                self.handle_input()

                self.draw_load_error()

                if self.sprite and self.active_state and self.active_direction:
                    self.draw_states()
                    self.draw_directions()
                    self.draw_sprite()
                else:
                    self.iter_sprite_state()
                    self.change_sprite_direction()

                # draw the self.screen!
                self.screen.refresh()

                sleep(FPS)

                self.tick(FPS)

    def run(self):
        self.observer.start()
        try:
            self.run_animation()
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
