# -*- coding: UTF-8 -*-

import os
import sys
import traceback

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QAbstractEventDispatcher, QAbstractNativeEventFilter
from PyQt5.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from langid import langid
from pyqtkeybind import keybinder

from core import utils
from core.gui import MainWindow
from core.languages import ALL_LANG


class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


def except_hook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb)
    QMessageBox.critical(None, "出现异常", tb)


if __name__ == '__main__':
    sys.excepthook = except_hook

    # 加载langid(防止第一次翻译卡顿问题)并设置支持的语言列表
    langid.set_languages(ALL_LANG)

    # os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9966'  # 打开QWebEngineView调试控制台 http://localhost:9966

    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    QApplication.setQuitOnLastWindowClosed(False)
    sys.argv.append('--no-sandbox')
    app = QApplication(sys.argv)
    app.setStyleSheet(utils.read_asset_file('qss', 'global-style.qss'))
    for font_filename in os.listdir(utils.get_asset_path('fonts')):
        QtGui.QFontDatabase.addApplicationFont(utils.get_asset_path('fonts', font_filename))

    window = MainWindow()
    keybinder.init()
    unregistered = False
    hotkey = utils.get_config().get('hotkey', 'Ctrl+Alt+Z').lower()
    keybinder.register_hotkey(window.winId(), hotkey, window.trans_window.on_hotkey)
    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)

    window.tray_icon.showMessage('启动成功', f'按下快捷键{hotkey}进行翻译', QSystemTrayIcon.MessageIcon.NoIcon, 5000)

    app.exec_()
    keybinder.unregister_hotkey(window.winId(), utils.get_config().get('hotkey', 'Ctrl+Alt+Z').lower())
