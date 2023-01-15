import json
import os
import sys
import winreg

import mouse
import requests
from PyQt5.QtCore import QObject, pyqtSignal

from core.api import dict_list

REG_KEY_INTERNET_SETTINGS = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,
                                             r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                                             0, winreg.KEY_ALL_ACCESS)


def is_open_proxy() -> bool:
    """判断是否开启了代理"""
    try:
        if winreg.QueryValueEx(REG_KEY_INTERNET_SETTINGS, 'ProxyEnable')[0] == 1:
            return True
    except FileNotFoundError as err:
        print('没有找到代理信息：' + str(err))
    except Exception as err:
        print('有其他报错：' + str(err))
    return False


def get_proxy_url() -> str:
    """获取代理配置的url"""
    if is_open_proxy():
        try:
            return winreg.QueryValueEx(REG_KEY_INTERNET_SETTINGS, 'ProxyServer')[0]
        except FileNotFoundError as err:
            print('没有找到代理信息：' + str(err))
        except Exception as err:
            print('有其他报错：' + str(err))
    else:
        print('系统没有开启代理')
    return ''


def get_proxies():
    if not is_open_proxy():
        return None
    url = get_proxy_url()
    return {'https': url} if url else None


def request_get(url, params=None):
    return requests.get(url, params)


def request_post(url, data=None, json=None):
    return requests.post(url, data, json, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
    }, proxies=get_proxies())


def get_app_dir_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def get_resources_path(resource_name=""):
    return os.path.join(get_app_dir_path(), "assets", resource_name)


def get_app_exe_path():
    return os.path.realpath(os.path.abspath(sys.argv[0]))


def read_qss_file(qss_file_name):
    with open(qss_file_name, 'r', encoding='UTF-8') as file:
        return file.read()


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
    default_config = {
        'hotkey': 'Ctrl+Alt+Z',
        'dict': {
            dict_list[0].get('name'): {
                'on': True
            }
        }
    }
    try:
        config_file = os.path.join(get_app_dir_path(), 'config.json')
        with open(config_file, 'r') as f:
            config = json.loads(f.read())
        if not config:
            config = default_config
    except IOError:
        config = default_config
    return config


def update_config(config: dict):
    origin = get_config()
    origin.update(config)
    config_file = os.path.join(get_app_dir_path(), 'config.json')
    with open(config_file, 'w') as f:
        json.dump(origin, f, sort_keys=True, indent=2)
