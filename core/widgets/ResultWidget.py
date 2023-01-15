from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton

from core import utils


class AudioButton(QWidget):

    def __init__(self, url: str, color, text: str = ''):
        super().__init__()

        player = QMediaPlayer()
        player.setMedia(QMediaContent(QUrl(url)))
        player.setVolume(50)

        label = QLabel(text)

        btn = QPushButton()
        if color is None:
            color = self.BLUE
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

    BLUE = 'blue'
    RED = 'red'


class ResultWidget(QWidget):
    def __init__(self, result_dict: dict = None, audio_btn_color: str = AudioButton.BLUE):
        super().__init__()
        self.audio_btn_color = audio_btn_color
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.layout.addWidget(self.text_label)
        self.audio_buttons = []
        self.trans_result_label = QLabel()
        self.trans_result_label.setWordWrap(True)
        self.layout.addWidget(self.trans_result_label)
        self.layout.addStretch(1)
        self.setResult(result_dict)

    def setResult(self, result_dict: dict):
        if not result_dict:
            return

        self.text_label.setText(result_dict.get('text'))

        for btn in self.audio_buttons:
            self.layout.removeWidget(btn)
        self.audio_buttons = []
        if result_dict.get('voice'):
            for index, voice in enumerate(result_dict.get('voice')):
                audio_btn = AudioButton(voice.get('url'), self.audio_btn_color, voice.get('pron', ''))
                self.audio_buttons.append(audio_btn)
                self.layout.insertWidget(index + 1, audio_btn)

        if result_dict.get('type') == 1:
            trans_result = ''
            for pre in result_dict.get('pre'):
                trans_result += f"{pre.get('title')}\n"
                trans_result += f"{';'.join(pre.get('trans'))}\n"
            self.trans_result_label.setText(trans_result)
        else:
            self.trans_result_label.setText(result_dict.get('trans'))
