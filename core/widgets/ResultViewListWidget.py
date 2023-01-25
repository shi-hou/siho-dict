import re

import requests
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl, QRunnable, QThreadPool
from PyQt5.QtGui import QDesktopServices, QWheelEvent
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from core import utils
from core.dicts import Dict, dicts
from core.widgets import IToast


class ResultViewListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.widget_list = []
        for d in dicts.on_dict:
            widget = ResultViewWidget(d)
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
            widget = ResultViewWidget(d)
            self.layout.insertWidget(index, widget)
            self.widget_list.append(widget)


class ResultViewWidget(QWidget):
    def __init__(self, dictionary: Dict):
        super().__init__()
        self.dictionary = dictionary
        self.layout = QVBoxLayout()
        self.trans_result_view = ResultView(dictionary, self)
        self.init()

    def init(self):
        self.setAttribute(Qt.WA_StyledBackground)

        title_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setFixedHeight(15)
        icon_label.setFixedWidth(15)
        icon = utils.get_resources_path('icon', self.dictionary.icon).replace('\\', '/')  # url()用“\”会不生效
        icon_label.setStyleSheet(f'border-image: url({icon}); border-radius: 3px;')
        title_layout.addWidget(icon_label)

        title_label = QLabel(self.dictionary.title)
        title_label.setProperty('class', 'title-label')
        title_layout.addWidget(title_label)

        title_layout.addStretch(1)
        self.layout.addLayout(title_layout)

        self.layout.addWidget(self.trans_result_view)
        self.layout.addStretch(1)
        self.setLayout(self.layout)

    def setResult(self, result_dict: dict):
        if not result_dict:
            self.clear()
        elif result_dict.get('message', ''):
            self.trans_result_view.setMessage(result_dict.get('message'))
        else:
            self.trans_result_view.setResult(result_dict)

    def loading(self):
        self.trans_result_view.setMessage('加载中...')

    def clear(self):
        self.trans_result_view.setMessage('')


class ResultView(QWebEngineView):
    result_signal = pyqtSignal(str, list)
    message_signal = pyqtSignal(str)
    anki_result_signal = pyqtSignal(str)

    def __init__(self, dictionary: Dict, parent=None):
        super().__init__(parent)
        self.dictionary = dictionary
        self.load_data_pattern = re.compile('\{\{[^\{\}]+?\}\}')
        self.script_label_pattern = re.compile('<script>[\s\S]+?</script>')
        self.audios = {}
        self.current_data = None
        self.voice_player = QMediaPlayer()
        self.last_play = ''

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)

        self.anki_result_signal.connect(self.showAnkiAddResult)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setPage(WebEnginePage(self))
        self.page().settings().setAttribute(QWebEngineSettings.ShowScrollBars, False)
        self.channel = QWebChannel(self)
        self.page().setWebChannel(self.channel)
        self.channel.registerObject('Bridge', self)
        self.load(QUrl.fromLocalFile(utils.get_resources_path('search_panel.html')))
        with open(utils.get_resources_path(dictionary.template), encoding="utf-8") as f:
            self.template = f.read()
            f.close()
        self.sound_icon = dictionary.audio_icon

        @self.loadFinished.connect
        def load_finished(ok: bool):
            # 加载CSS文件
            if ok:
                self.page().runJavaScript(f'''
                            new_element = document.createElement("link");
                            new_element.setAttribute("rel", "stylesheet");
                            new_element.setAttribute("type", "text/css");
                            new_element.setAttribute("href", "css/{dictionary.style_file}");
                            document.head.appendChild(new_element);
                        ''')

    # 使鼠标光标停在网页内时可以进行滚动
    def wheelEvent(self, event: QWheelEvent) -> None:
        delta_y = event.angleDelta().y() / 2
        # 获取IPage的滚动条
        page_scroll_bar = self.nativeParentWidget().page.verticalScrollBar()
        page_scroll_bar.setValue(page_scroll_bar.value() - delta_y)

    @pyqtSlot(str)
    def audioBtnOnclick(self, filename: str):
        if self.last_play != filename:
            file_path = utils.store_tmp_file(filename, self.audios.get(filename))
            self.voice_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.last_play = filename
        self.voice_player.play()

    @pyqtSlot(int)
    def setHeight(self, height: int):
        self.setFixedHeight(height)

    def setResult(self, result: dict):
        self.current_data = result
        self.last_play = ''
        self.audios = {}

        def loadData(m):
            data_title = m.group()[2:-2]
            data = result.get(data_title, '')

            if isinstance(data, dict):
                data_type = data.get('type')
                if data_type == 'audio':
                    filename = data.get('filename')
                    url = data.get('url')
                    self.audios[filename] = url
                    filename_in_js = filename.replace("'", "\\'")
                    return rf'''
                    <a class="soundLink" href="#" onclick="audioPlay('{filename_in_js}')" 
                       style="text-decoration: none; display: inline-flex; vertical-align: middle;">
                        <img src="icon/{self.sound_icon}" alt="{data_title}" />
                    </a>
                    '''
                else:
                    raise Exception('未定义的数据类型')

            if data_title == 'anki-btn':
                return f'''
                            <a class="anki-btn" href="#" onclick="addAnkiNote()" 
                                style="text-decoration: none; display: inline-flex; vertical-align: middle;">
                                <img title="添加到Anki" src="icon/anki-logo2.png" alt="添加到Anki" />
                            </a>
                        ''' if utils.get_config().get('anki-on', False) and self.dictionary.is_anki_able() else ''
            return data

        body_html = self.load_data_pattern.sub(loadData, self.template)
        scripts = []
        for script_with_label in self.script_label_pattern.findall(body_html):
            script = script_with_label[8:-9]
            scripts.append(script)
        self.result_signal.emit(body_html, scripts)

    def setMessage(self, message: str):
        self.current_data = None
        self.message_signal.emit(message)

    @pyqtSlot(str)
    def showAnkiAddResult(self, result: str):
        trans_window = self.nativeParentWidget()
        IToast.showToast(trans_window, result)

    @pyqtSlot()
    def addAnkiNote(self):
        anki_note_adder = self.AnkiNoteAdder(self.anki_result_signal, self.dictionary.anki_add_note_func,
                                             self.current_data)
        self.thread_pool.start(anki_note_adder)

    class AnkiNoteAdder(QRunnable):
        def __init__(self, signal, anki_func, data: dict):
            super().__init__()
            self.signal = signal
            self.anki_func = anki_func
            self.data = data

        def run(self) -> None:
            try:
                result = self.anki_func(self.data)
            except requests.exceptions.ConnectionError:
                result = '无法连接AnkiConnect, 请确认Anki已启动并重试'
            except Exception as err:
                result = str(err)
            self.signal.emit(result)


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super(WebEnginePage, self).__init__(parent)

    # 通过浏览器打开<a>链接
    def acceptNavigationRequest(self, url: QUrl, type: 'QWebEnginePage.NavigationType',
                                isMainFrame: bool) -> bool:
        if type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return True
