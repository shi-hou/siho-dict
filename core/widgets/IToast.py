from PyQt5.QtCore import Qt, QPropertyAnimation, QTimer
from PyQt5.QtWidgets import QLabel, QGraphicsOpacityEffect, QWidget, QVBoxLayout


class IToast(QWidget):

    def __init__(self, parent: QWidget, text: str = ''):
        super().__init__(parent)

        self.setStyleSheet('''
            background-color: #323232; 
            color: white;
            font-family: "PingFang SC Medium";
            border: none;
            border-radius: 5px;
        ''')

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 3, 10, 3)
        self.text_label = QLabel(text)
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)
        self.setLayout(layout)

        self.goe = QGraphicsOpacityEffect()
        self.goe.setOpacity(0.8)
        self.setGraphicsEffect(self.goe)
        self.setAutoFillBackground(True)

        self.setFixedWidth(self.sizeHint().width() + layout.contentsMargins().left() + layout.contentsMargins().right())
        x = (parent.width() - self.width()) * 0.5
        y = (parent.height() - self.height()) * 0.8
        self.move(x, y)

    def show(self) -> None:
        animation = QPropertyAnimation(self.goe, b"opacity", self)
        animation.setDuration(400)
        animation.setStartValue(0)
        animation.setEndValue(self.goe.opacity())
        animation.start()
        super().show()

    def close(self) -> None:
        animation = QPropertyAnimation(self.goe, b"opacity", self)
        animation.setDuration(800)
        animation.setStartValue(self.goe.opacity())
        animation.setEndValue(0)
        animation.finished.connect(super().close)
        animation.start()

    @classmethod
    def showToast(cls, parent: QWidget, text: str, duration: int = 2):
        toast = IToast(parent, text)
        toast.show()
        QTimer.singleShot(duration * 1000, toast.close)
