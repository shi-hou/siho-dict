import os
import sys
import traceback

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QAbstractEventDispatcher, QAbstractNativeEventFilter
from PyQt5.QtWidgets import QApplication, QMessageBox
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


def except_hook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb)
    QMessageBox.critical(None, "出现异常", tb)


sys.excepthook = except_hook
# os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9966'  # 打开QWebEngineView调试控制台 http://localhost:9966
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
app.setStyleSheet(utils.read_qss_file(utils.get_resources_path('qss', 'global-style.qss')))
QtGui.QFontDatabase.addApplicationFont(utils.get_resources_path('fonts', 'PingFang SC Medium.ttf'))
QtGui.QFontDatabase.addApplicationFont(utils.get_resources_path('fonts', 'PingFang SC Regular.ttf'))
QtGui.QFontDatabase.addApplicationFont(utils.get_resources_path('fonts', 'HiraMinProN-W6.ttf'))
window = MainWindow()
keybinder.init()
unregistered = False
hotkey = utils.get_config().get('hotkey', 'Ctrl+Alt+Z')
keybinder.register_hotkey(window.winId(), hotkey, window.trans_window.on_hotkey)
win_event_filter = WinEventFilter(keybinder)
event_dispatcher = QAbstractEventDispatcher.instance()
event_dispatcher.installNativeEventFilter(win_event_filter)
app.exec_()
keybinder.unregister_hotkey(window.winId(), hotkey)
