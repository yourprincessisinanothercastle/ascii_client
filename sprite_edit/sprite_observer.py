import logging
import os

from ruamel.yaml import YAML
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lib.creatures._sprite import Sprite
from lib.init_logging import init_logging

init_logging('debug')

logger = logging.getLogger(__name__)

yaml = YAML()



class EventHandler(FileSystemEventHandler):
    def __init__(self, filename, callback):
        self.filename = filename
        self.callback = callback

    def on_modified(self, event):
        super(EventHandler, self).on_modified(event)
        logging.info(event)
        if not event.is_directory \
                and os.path.basename(event.src_path) == self.filename:
            self.callback(event.src_path)


class SpriteObserver:
    def __init__(self, path):
        self.load_exceptions = []
        self.observer = self._setup_observer(path)

    def _setup_observer(self, path):
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)

        observer = Observer()
        observer.schedule(EventHandler(filename, self._load_file), dirname, recursive=True)
        return observer

    def _add_exception(self, e):
        self.load_exceptions.append(e)
        while len(self.load_exceptions) > 1:
            self.load_exceptions.pop(0)

    def _clear_exceptions(self):
        while self.load_exceptions:
            self.load_exceptions.pop(0)

    def _load_file(self, path):
        try:
            sprite = Sprite(path)
            self.sprite = sprite
            self._clear_exceptions()
        except Exception as e:
            logger.warning(e, exc_info=True)
            self._add_exception(e)

