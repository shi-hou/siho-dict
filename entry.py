import sys

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QAbstractEventDispatcher, QAbstractNativeEventFilter
from PyQt5.QtWidgets import QApplication
from pyqtkeybind import keybinder

from core import utils
from core.gui import MainWindow


class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
dir_path = utils.get_app_dir_path()
app.setStyleSheet(utils.read_qss_file(fr'{dir_path}\asserts\custom.qss'))
QtGui.QFontDatabase.addApplicationFont(fr'{dir_path}\asserts\PingFang SC Medium.ttf')

window = MainWindow()
keybinder.init()
unregistered = False
keybinder.register_hotkey(window.winId(), utils.get_config().get('hotkey', 'Ctrl+Alt+Z'), window.trans_window.on_hotkey)
win_event_filter = WinEventFilter(keybinder)
event_dispatcher = QAbstractEventDispatcher.instance()
event_dispatcher.installNativeEventFilter(win_event_filter)
app.exec_()
# print('test---------------------------')
# keybinder.unregister_hotkey(window.winId(), "Ctrl+Alt+Z")
