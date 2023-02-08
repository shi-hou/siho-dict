import json
import os
import shutil
import sys
import winreg

import langid
import mouse
import requestsp as requests
from PyQt5.QtCore import QObject, pyqtSignal

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}


def request_get(url, params=None):
    return requests.get(url, params, headers=headers, timeout=(5, 5))


def request_post(url, data=None, json=None):
    return requests.post(url, data, json, headers=headers, timeout=(5, 5))


def get_app_dir_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def get_asset_path(*resource_name: str):
    return os.path.join(get_app_dir_path(), "assets", *resource_name)


def get_app_exe_path():
    return os.path.realpath(os.path.abspath(sys.argv[0]))


def read_asset_file(*file_path: str) -> str:
    with open(get_asset_path(*file_path), 'r', encoding='UTF-8') as f:
        result_txt = f.read()
        f.close()
    return result_txt


def addMouseEvent(parent, callback, mouse_btn=mouse.LEFT, btn_type=mouse.UP):
    manager = MouseEventManager(parent, mouse_btn, btn_type)
    manager.signal.connect(callback)
    manager.start()


class MouseEventManager(QObject):
    signal = pyqtSignal()

    def __init__(self, parent, mouse_btn, btn_type):
        super().__init__(parent)
        self.mouse_btn = mouse_btn
        self.btn_type = btn_type

    def start(self):
        buttons = [self.mouse_btn]
        types = [self.btn_type]
        mouse.on_button(callback=self.signal.emit, buttons=buttons, types=types)


REG_KEY_RUN = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run',
                             0, winreg.KEY_ALL_ACCESS)

AUTO_RUN_NAME = 'SihoDict'


def get_auto_run() -> bool:
    try:
        return winreg.QueryValueEx(REG_KEY_RUN, AUTO_RUN_NAME)[0] == get_app_exe_path()
    except FileNotFoundError:
        return False
    except Exception as err:
        print("获取开机自启设置异常", err)
        return False


def set_auto_run(new_value: bool) -> bool:
    exe_path = get_app_exe_path()
    try:
        has_auto_run = get_auto_run()
        if new_value and not has_auto_run:
            winreg.SetValueEx(REG_KEY_RUN, AUTO_RUN_NAME, 0, winreg.REG_SZ, exe_path)
        elif has_auto_run:
            winreg.DeleteValue(REG_KEY_RUN, AUTO_RUN_NAME)
        return True
    except Exception as err:
        print("修改开机自启设置异常", err)
        return False


def get_config():
    try:
        config_file = os.path.join(get_app_dir_path(), 'config.json')
        with open(config_file, 'r') as f:
            config = json.loads(f.read())
        if not config:
            config = {}
    except IOError:
        config = {}
    return config


def update_config(config: dict):
    origin = get_config()
    origin.update(config)
    config_file = os.path.join(get_app_dir_path(), 'config.json')
    with open(config_file, 'w') as f:
        json.dump(origin, f, sort_keys=True, indent=2)


def check_language(string: str) -> str:
    return langid.classify(string)[0]


def store_tmp_file(filename: str, url: str) -> str:
    tmp_dir_path = os.path.join(get_app_dir_path(), 'tmp')
    os.makedirs(tmp_dir_path, exist_ok=True)
    file_path = os.path.join(tmp_dir_path, filename)
    if not os.path.exists(file_path):
        content = request_get(url).content
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()
    return file_path


def clear_tmp_file():
    shutil.rmtree(os.path.join(get_app_dir_path(), 'tmp'), ignore_errors=True)


def get_tmp_size() -> int:
    """
    获取缓存文件大小, 单位byte

    :return: 缓存文件大小, 单位byte
    """
    total_size = 0
    for dir_path, dir_names, filenames in os.walk('tmp'):
        for f in filenames:
            fp = os.path.join(dir_path, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
