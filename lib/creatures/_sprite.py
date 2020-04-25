import logging
import random

from lib.init_logging import init_logging
from ruamel.yaml import YAML


init_logging('debug')
logger = logging.getLogger(__name__)

yaml = YAML()


class Frame:
    def __init__(self, ms, cells, is_random, idx):
        self.ms = ms
        self.cells = cells
        self.is_random = is_random
        self.idx = idx

    def make_current_frame(self):
        if self.is_random:
            ms = random.randint(self.ms[0], self.ms[1])
        else:
            ms = self.ms
        return CurrentFrame(ms=ms, cells=self.cells, idx=self.idx, timer=0)


class CurrentFrame:
    def __init__(self, ms, cells, idx, timer):
        self.ms = ms
        self.cells = cells
        self.idx = idx
        self.timer = timer


class Sprite:
    def __init__(self, path):
        self.states = {}
        self.load(path)

        self.current_state = 'idle'
        self.current_direction = 'right'

        self.current_frame = self.current_state_frames[0].make_current_frame()

    @property
    def current_state_frames(self):
        return self.states[self.current_state][self.current_direction]

    def tick(self, dt, state, direction):
        # if we are doing this for the first time or something changed
        if not self.current_frame \
                or state != self.current_state \
                or direction != self.current_direction:
            self.current_state = state
            self.current_direction = direction
            frame: Frame = self.current_state_frames[0]
            self.current_frame = frame.make_current_frame()

        # the actual tick
        self.current_frame.timer += dt
        #logger.debug('timer %s / %s' % (self.current_frame.timer, self.current_frame.ms / 1000))

        # set next frame, if timer over ms for this frame
        if self.current_frame.timer > (self.current_frame.ms / 1000):
            next_frame_idx = (self.current_frame.idx + 1) % len(self.current_state_frames)
            logger.info('new current frame, idx %s!' % next_frame_idx)
            frame: Frame = self.current_state_frames[next_frame_idx]
            self.current_frame = frame.make_current_frame()

    def get_cells(self):
        return self.current_frame.cells

    def load(self, path):
        with open(path, 'r') as f:
            sprite_data = yaml.load(f)
            for state, directions in sprite_data.items():
                self.states[state] = {}
                for direction, frames in directions.items():
                    self.states[state][direction] = []
                    for idx, frame in enumerate(frames):
                        is_random = frame.get('random', False)
                        ms = frame['ms']
                        cells = frame['cells']
                        f = Frame(ms=ms, is_random=is_random, cells=cells, idx=idx)
                        self.states[state][direction].append(f)
