import sys

from PyQt5.QtWidgets import QMenu
from pynput import mouse


class IconRButtonMenu(QMenu):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.mouse_controller = mouse.Controller()
        self.hide()

    def init_ui(self):
        self.setFixedSize(120, 50)
        self.open_main_act = self.addAction('设置')
        self.open_main_act.triggered.connect(lambda: print('设置'))
        self.quit_act = self.addAction('退出')
        self.quit_act.triggered.connect(sys.exit)

    def show_(self):
        x, y = self.mouse_controller.position
        self.move(x - self.width(), y - self.height())
        self.show()
        # super()
