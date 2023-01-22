from PyQt5.QtCore import QTimer, Qt
from pyqt5Custom import Toast


class IToast(Toast):

    def __init__(self, parent, text: str = ''):
        super(IToast, self).__init__(parent, text, closeButton=False)
        self.setFixedHeight(30)
        self.setStyleSheet('font-family: "PingFang SC Medium"')
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(self.conwdt, Qt.AlignCenter)
        self.close_btn.hide()  # closeButton=False dose not work

        self.timer = QTimer()

        @self.timer.timeout.connect
        def timeout():
            self.fall()

    # [Bug] Timeout for Toast does not work
    # https://github.com/kadir014/pyqt5-custom-widgets/issues/5
    def rise(self, sec: int):
        super(IToast, self).rise(sec)
        self.timer.start(sec * 1000)
