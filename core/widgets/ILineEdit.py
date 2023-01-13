from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit


class ILineEdit(QLineEdit):
    def __init__(self, text=''):
        super().__init__(text)
        self.setAlignment(Qt.AlignRight)
