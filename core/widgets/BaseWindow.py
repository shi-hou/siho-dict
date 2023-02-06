import win32con
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QMainWindow
from win32api import SendMessage
from win32gui import ReleaseCapture

from core import utils
from core.widgets import IPage


class BaseWindow(QMainWindow):
    title_bar_height = 32

    def __init__(self, title="", title_bar_slot=None):
        super().__init__()
        self.page = None
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.close_btn = QPushButton("✕")
        self.title_bar_layout = QHBoxLayout()
        self.title_bar = QWidget()
        self.Point = (0, 0)
        self.Move = False
        self.init_window(title, title_bar_slot)

    def init_window(self, title="", title_bar_slot=None):

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(QPixmap(utils.get_asset_path('icon', 'logo-icon.ico'))))
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_widget = QWidget()
        main_widget.setProperty('class', 'main-widget')

        self.title_bar.setProperty('class', 'title-bar')
        self.title_bar.setFixedHeight(self.title_bar_height)
        self.title_bar_layout.setContentsMargins(20, 0, 0, 0)
        self.title_bar_layout.setSpacing(0)
        title_bar_widget = QLabel(title) if title_bar_slot is None else title_bar_slot
        self.title_bar_layout.addWidget(title_bar_widget)
        self.title_bar_layout.addSpacing(50)
        self.close_btn.setProperty('class', 'close-btn')
        self.close_btn.setFixedSize(self.title_bar_height, self.title_bar_height)
        self.close_btn.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.close_btn, alignment=Qt.AlignRight)
        self.title_bar.setLayout(self.title_bar_layout)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.title_bar, alignment=Qt.AlignTop)
        main_layout.setSpacing(0)

        self.content_layout.setContentsMargins(1, 0, 1, 10)
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setProperty('class', 'content-widget')
        main_layout.addWidget(self.content_widget)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def mousePressEvent(self, event):
        if event.pos() not in self.title_bar.geometry():
            return
        ReleaseCapture()
        SendMessage(self.window().winId(), win32con.WM_SYSCOMMAND,
                    win32con.SC_MOVE + win32con.HTCAPTION, 0)
        event.ignore()

    def setPage(self, page: IPage):
        self.page = page
        self.content_layout.addWidget(page, Qt.AlignTop)

    def addTitleBarButton(self, text: str = '', icon: str = None) -> QPushButton:
        btn = QPushButton(text)
        height = self.title_bar.height()
        btn.setFixedHeight(height)
        btn.setFixedWidth(height)
        if icon is not None:
            btn.setIcon(QIcon(QPixmap(icon)))
        index = self.title_bar_layout.count() - 1
        self.title_bar_layout.insertWidget(index, btn)
        return btn
