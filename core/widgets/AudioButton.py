from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel, QWidget

from core import utils


class AudioButton(QWidget):

    def __init__(self, url: str, color: str, text: str = ''):
        super().__init__()

        player = QMediaPlayer()
        player.setMedia(QMediaContent(QUrl(url)))
        player.setVolume(50)

        label = QLabel(text)

        btn = QPushButton()
        btn.setIcon(QIcon(QPixmap(utils.get_resources_path(f'audio-{color}.svg'))))
        btn.setStyleSheet('border: none;')

        @btn.clicked.connect
        def slot():
            player.play()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(label)
        layout.addWidget(btn)
        layout.addStretch(1)
        self.setLayout(layout)