import json
import os

from PyQt5.QtCore import QObject, QThreadPool, QRunnable

from core import utils


class Setting(QObject):
    config_file_path = os.path.join(utils.get_app_dir_path(), 'config.json')

    def __init__(self, auto_save: bool = True):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.config = self._load_config_file()
        self.auto_save = auto_save

    def _load_config_file(self):
        try:
            with open(self.config_file_path, 'r') as f:
                config = json.loads(f.read())
            if not config:
                config = {}
        except IOError:
            config = {}
        return config

    def _save_config_file(self):
        with open(self.config_file_path, 'w') as f:
            json.dump(self.config, f, sort_keys=True, indent=2)

    def _set(self, key, value):
        self.config[key] = value
        if self.auto_save:
            self._save_config_file()

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.thread_pool.start(Task(lambda: self._set(key, value)))


setting = Setting()


class Task(QRunnable):
    def __init__(self, callback):
        super().__init__()
        self.run = callback
