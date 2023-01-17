from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core import utils
from core.dicts import Dict, dicts
from core.widgets import AudioButton


class ResultListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.widget_list = []
        for d in dicts.on_dict:
            widget = self.ResultWidget(d)
            self.layout.addWidget(widget)
            self.widget_list.append(widget)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def loading(self):
        for w in self.widget_list:
            w.loading()

    def clear(self):
        for w in self.widget_list:
            w.clear()

    def reset(self):
        """
        在修改了词典开关后执行该方法
        重置翻译窗口显示的词典
        """
        for widget in self.widget_list:
            self.layout.removeWidget(widget)
        self.widget_list = []
        for index, d in enumerate(dicts.on_dict):
            widget = self.ResultWidget(d)
            self.layout.insertWidget(index, widget)
            self.widget_list.append(widget)

    class ResultWidget(QWidget):
        def __init__(self, dictionary: Dict):
            super().__init__()
            self.dictionary = dictionary
            self.layout = QVBoxLayout()
            self.trans_result_label = QLabel()
            self.audio_buttons = []
            self.text_label = QLabel()
            self.init()

        def init(self):
            if self.dictionary.style_file:
                self.setStyleSheet(utils.read_qss_file(utils.get_resources_path(self.dictionary.style_file)))

            self.setAttribute(Qt.WA_StyledBackground)

            title_layout = QHBoxLayout()

            icon_label = QLabel()
            icon_label.setFixedHeight(15)
            icon_label.setFixedWidth(15)
            icon = utils.get_resources_path(self.dictionary.icon).replace('\\', '/')  # url()用“\”会不生效
            icon_label.setStyleSheet(f'border-image: url({icon}); border-radius: 3px;')
            title_layout.addWidget(icon_label)

            title_label = QLabel(self.dictionary.title)
            title_label.setProperty('class', 'title-label')
            title_layout.addWidget(title_label)

            title_layout.addStretch(1)
            self.layout.addLayout(title_layout)

            self.text_label.setWordWrap(True)
            self.text_label.setProperty('class', 'text-label')
            self.layout.addWidget(self.text_label)
            self.trans_result_label.setWordWrap(True)
            self.trans_result_label.setProperty('class', 'trans-result-label')
            self.layout.addWidget(self.trans_result_label)
            self.layout.addStretch(1)
            self.setLayout(self.layout)

        def setResult(self, result_dict: dict):
            if not result_dict:
                self.clear()
                return

            self.text_label.setText(result_dict.get('text'))

            for btn in self.audio_buttons:
                self.layout.removeWidget(btn)
            self.audio_buttons = []
            if result_dict.get('voice'):
                for index, voice in enumerate(result_dict.get('voice')):
                    audio_btn = AudioButton(voice.get('url'), self.dictionary.audio_icon, voice.get('pron', ''))
                    self.audio_buttons.append(audio_btn)
                    self.layout.insertWidget(index + 2, audio_btn)

            if result_dict.get('type') == 1:
                trans_result = ''
                for pre in result_dict.get('pre'):
                    trans_result += f"{pre.get('title')}\n"
                    trans_result += f"{self.dictionary.delimiter.join(pre.get('trans'))}\n\n"
                self.trans_result_label.setText(trans_result)
            else:
                self.trans_result_label.setText(result_dict.get('trans'))

        def loading(self):
            self.setResult(Dict.message_result('加载中...'))

        def clear(self):
            self.setResult(Dict.message_result())
