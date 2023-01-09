import pyautogui
import pyperclip
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget, QMainWindow, QPushButton
from pynput import mouse
from core.api.baidu import trans


class TransWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.mouse_controller = mouse.Controller()
        self.last_txt = ''
        self.show()
        self.hide()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool | Qt.Popup)
        self.setFixedWidth(309)
        self.setFixedHeight(500)
        w = QWidget()
        w.setLayout(QVBoxLayout())
        self.input_edit = QLineEdit()
        w.layout().addWidget(self.input_edit)
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(Qt.AlignTop)
        w.layout().addWidget(self.result_label)
        self.setCentralWidget(w)

    def is_click_in_window(self, x, y):
        geometry = self.frameGeometry()
        return geometry.x() < x < geometry.right() and geometry.y() < y < geometry.bottom()

    def hide_window(self):
        self.input_edit.setText('')
        self.result_label.setText('')
        self.hide()

    def show_trans(self):
        former_copy = pyperclip.paste()  # 用于还原剪切板
        pyautogui.hotkey('ctrl', 'c')
        current_txt = pyperclip.paste().strip().replace("\n", "").replace("\t", "")  # 获取剪切板
        print(current_txt)
        pyperclip.copy(former_copy)  # 还原剪切版
        if current_txt == '':
            self.hide()
            return
        self.last_txt = current_txt
        x, y = self.mouse_controller.position
        self.move(x + 10, y + 10)
        self.show()
        self.input_edit.setText(current_txt)
        # TODO 不在self.input_edit.setText(current_txt)前show的话，第一次显示会特别卡
        # x, y = self.mouse_controller.position
        # self.move(x + 10, y + 10)
        # self.show()
        self.result_label.setText(trans(current_txt))
