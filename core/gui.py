import os
import re
import sys
import traceback
import webbrowser

import mouse
import requests
from PyQt5.QtCore import Qt, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QPoint, QRect, QUrl, QPropertyAnimation, \
    QSize, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QIcon, QPixmap, QDesktopServices, QWheelEvent, QClipboard, QShowEvent, QHideEvent
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineSettings, QWebEngineView
from PyQt5.QtWidgets import QLineEdit, QSystemTrayIcon, QMainWindow, QApplication, QVBoxLayout, QLabel, QHBoxLayout, \
    QWidget, QPushButton, QLayout
from pyqtkeybind import keybinder
from qframelesswindow import FramelessMainWindow

from core import utils, update
from core.dicts import Dict, dicts
from core.languages import Lang
from core.widgets import BaseWindow, IPage, ILineEdit, IGroup, ISwitch, IMenu, IToast


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.trans_window = TransWindow()
        self.tray_icon = TrayIcon()
        self.setting_window = SettingWindow()

        @self.tray_icon.menu_open_setting_act.triggered.connect
        def show_setting_window():
            self.setting_window.show()
            self.setting_window.activateWindow()

        @self.setting_window.hotkey_edit.editingFinished.connect
        def change_hotkey():
            if self.setting_window.hotkey_edit.isModified():
                original_hotkey = utils.get_config().get('hotkey', 'Ctrl+Alt+Z').lower()
                new_hotkey = self.setting_window.hotkey_edit.text().lower()
                keybinder.unregister_hotkey(self.winId(), original_hotkey)
                keybinder.register_hotkey(self.winId(), new_hotkey, self.trans_window.on_hotkey)
                utils.update_config({'hotkey': new_hotkey})

        @self.tray_icon.menu_open_trans_act.triggered.connect
        def menu_open_trans_act_triggered():
            self.trans_window.content_widget.hide()
            self.trans_window.show()

        @self.tray_icon.activated.connect
        def tray_icon_activated(reason):
            if reason == QSystemTrayIcon.Trigger:
                self.trans_window.content_widget.hide()
                self.trans_window.show()

        for switch in self.setting_window.dict_switch_list:
            switch.toggled.connect(self.dict_on_switch_toggled)

        self.tray_icon.show()

    def dict_on_switch_toggled(self):
        toggled_switch = self.setting_window.sender()
        index = toggled_switch.property('index')
        on = toggled_switch.isToggled()
        dicts.setOn(index, on)
        self.trans_window.result_list_widget.reset()


class TransWindow(BaseWindow):
    on_mouse_signal = pyqtSignal()
    show_signal = pyqtSignal(str, int, int)

    def __init__(self):
        self.input_edit = QLineEdit()
        super().__init__(title_bar_slot=self.input_edit)
        self.fix_btn = self.addTitleBarButton(icon=utils.get_asset_path('icon', '??????_line.svg'))
        self.result_list_widget = ResultViewListWidget()
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(1)
        self.window_show_worker = None
        self.trans_loaders = []
        self.fix_not_hidden = False
        self.init()

    def init(self):
        self.on_mouse_signal.connect(self.mouse_on_click)
        self.show_signal.connect(self.show_window)

        self.setFixedSize(370, 560)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.Tool)
        self.content_widget.hide()

        self.close_btn.clicked.connect(self.hide)

        mouse.on_button(self.on_mouse_signal.emit, types=mouse.DOWN)

        @self.input_edit.returnPressed.connect
        def input_return_pressed():
            self.stopLoad()
            if self.input_edit.isModified():
                self.result_list_widget.clear()
                input_txt = self.input_edit.text().strip()
                if input_txt == '':
                    return
                self.show_window = self.WindowShowWorker(self.show_signal, self.frameGeometry(), input_txt)
                self.thread_pool.start(self.show_window)

        fold_btn = self.addTitleBarButton(icon=utils.get_asset_path('icon', '????????????.svg'))

        @fold_btn.clicked.connect
        def fold_button_on_click():
            self.content_widget.setHidden(not self.content_widget.isHidden())

        @self.fix_btn.clicked.connect
        def fix_button_on_click():
            self.setFixNotHidden(not self.fix_not_hidden)

        self.input_edit.setProperty('class', 'trans-input-edit')
        page = IPage()
        layout = QVBoxLayout()
        layout.addWidget(self.result_list_widget)
        page.addLayout(layout)
        self.setPage(page)

    def hide(self) -> None:
        self.setFixNotHidden(False)
        self.input_edit.clear()
        self.content_widget.hide()
        super().hide()
        self.stopLoad()

    @pyqtSlot(str, int, int)
    def show_window(self, input_text, x, y):
        self.input_edit.setText(input_text)
        self.input_edit.clearFocus()
        has_content = input_text != ''
        self.content_widget.setHidden(not has_content)
        if not self.fix_not_hidden:
            self.move(x, y)
        self.show()
        if has_content:
            self.result_list_widget.loading()
            self.trans_loaders = []
            lang = utils.check_language(input_text)
            for trans_widget in self.result_list_widget.widget_list:
                trans_widget.do_trans(input_text, lang)
        else:
            self.activateWindow()
            self.input_edit.setFocus()

    def on_hotkey(self):
        self.stopLoad()
        self.result_list_widget.clear()
        x, y = mouse.get_position()
        self.window_show_worker = self.WindowShowWorker(self.show_signal, QRect(x, y, self.width(), self.height()))
        self.thread_pool.start(self.window_show_worker)

    def mouse_on_click(self):
        """??????????????????????????????"""
        if self.fix_not_hidden:
            return
        x, y = mouse.get_position()
        if not self.isHidden() and (
                QPoint(x, y) not in self.geometry()
                or (
                        self.content_widget.isHidden()
                        and QPoint(x - self.x(), y - self.y()) not in self.title_bar.geometry())):
            self.hide()

    def setFixNotHidden(self, value: bool):
        self.fix_not_hidden = value
        self.fix_btn.setIcon(
            QIcon(QPixmap(utils.get_asset_path('icon', '??????_fill.svg' if value else '??????_line.svg'))))

    def stopLoad(self):
        for trans_widget in self.result_list_widget.widget_list:
            trans_widget.stop_trans()

    class WindowShowWorker(QRunnable):
        def __init__(self, show_signal, geometry: QRect, input_txt=None):
            super().__init__()
            self.show_signal = show_signal
            self.geometry = geometry
            self.input_txt = input_txt

        def run(self) -> None:
            if self.input_txt:  # ???????????????
                current_txt = self.input_txt
            else:  # ????????????
                if sys.platform.startswith('win32'):
                    import pyperclip
                    import keyboard
                    from time import sleep, time
                    former_copy = pyperclip.paste()  # ?????????????????????
                    timestamp = str(time())
                    pyperclip.copy(timestamp)
                    keyboard.release(utils.get_config().get('hotkey', 'Ctrl+Alt+Z').lower())
                    keyboard.send('ctrl+c')
                    sleep(.1)
                    current_txt = pyperclip.paste().replace('\r\n', '\n')
                    # fix: ?????????????????????????????????????????????????????????ctrl+c?????????????????????????????????????????????
                    if current_txt == timestamp:
                        # ctrl+c?????????????????????
                        current_txt = ''
                    pyperclip.copy(former_copy)  # ???????????????
                elif sys.platform.startswith('linux'):
                    clipboard = QApplication.clipboard()
                    current_txt = clipboard.text(QClipboard.Selection)
                    clipboard.setText('', QClipboard.Selection)
                else:
                    raise Exception('?????????????????????')
            current_txt = current_txt.strip()
            # ???????????????????????????
            current_txt = re.sub('[A-Za-z]-[\n|\r][A-Za-z]', lambda x: x.group(0)[0] + x.group(0)[-1], current_txt)
            # ??????????????????????????????????????????
            current_txt = re.sub('[^.|?|!|)|???|???|???|???]\s*[\n|\r]\S', lambda x: x.group(0)[0] + ' ' + x.group(0)[-1],
                                 current_txt)
            if current_txt == '':  # ?????????title_bar
                self.geometry.setHeight(BaseWindow.title_bar_height)

            # ???????????????????????????
            # 0 <= show_x <= desktop_width - window_width
            # 0 <= show_y <= desktop_height - window_height
            desktop_geometry = QApplication.desktop().availableGeometry()
            show_x = max(0, min(self.geometry.x(), desktop_geometry.width() - self.geometry.width()))
            show_y = max(0, min(self.geometry.y(), desktop_geometry.height() - self.geometry.height()))

            self.show_signal.emit(current_txt, show_x, show_y)


class SettingWindow(FramelessMainWindow):
    def __init__(self):
        super().__init__()
        self.hotkey_edit = ILineEdit()
        self.dict_switch_list = []
        self.init()

    def init(self):
        self.setWindowTitle('??????')
        self.setWindowIcon(QIcon(utils.get_asset_path('icon', 'logo-icon.ico')))
        self.titleBar.setAttribute(Qt.WA_StyledBackground)
        self.setMenuWidget(self.titleBar)
        self.resize(800, 500)
        self.setMinimumWidth(550)

        config = utils.get_config()
        setting_page = IPage()
        self.setCentralWidget(setting_page)

        basic_setting_group = IGroup('????????????')
        auto_run_switch = ISwitch(on=utils.get_auto_run())

        @auto_run_switch.toggled.connect
        def slot():
            utils.set_auto_run(auto_run_switch.isToggled())

        basic_setting_group.addRow('????????????', auto_run_switch)

        self.hotkey_edit.setText(config.get('hotkey', 'Ctrl+Alt+Z'))
        basic_setting_group.addRow('??????', self.hotkey_edit)

        setting_page.addWidget(basic_setting_group)

        dict_setting_group = IGroup('????????????')
        for i, d in enumerate(dicts.all_dict):
            switch = ISwitch(on=d.on)
            switch.setProperty('index', i)
            switch.setEnabled(d.able)
            self.dict_switch_list.append(switch)

            dict_setting_group.addRow(d.title, switch, d.icon)

        setting_page.addWidget(dict_setting_group)

        anki_setting_group = IGroup('Anki Connect', '???????????????Anki Connect?????????????????????????????????Anki???????????????, ?????????????????????????????????????????????')

        anki_on_switch = ISwitch(on=config.get('anki-on', False))
        anki_on_switch.toggled.connect(lambda: utils.update_config({'anki-on': anki_on_switch.isToggled()}))
        anki_setting_group.addRow('??????', anki_on_switch, 'anki.png')

        anki_address_input = ILineEdit(config.get('anki-address', '127.0.0.1'))
        anki_address_input.editingFinished.connect(
            lambda: utils.update_config({'anki-address': anki_address_input.text()}))
        anki_setting_group.addRow('??????', anki_address_input)

        anki_port_input = ILineEdit(config.get('anki-port', '8765'))
        anki_port_input.editingFinished.connect(lambda: utils.update_config({'anki-port': anki_port_input.text()}))
        anki_setting_group.addRow('??????', anki_port_input)

        anki_key_input = ILineEdit(config.get('anki-key', ''))
        anki_key_input.editingFinished.connect(lambda: utils.update_config({'anki-key': anki_key_input.text()}))
        anki_setting_group.addRow('Key', anki_key_input)

        for dictionary in dicts.all_dict:
            if dictionary.is_anki_able():
                dict_name = dictionary.name
                dict_title = dictionary.title
                deck_name_config_key = f'anki-{dict_name}-deck'
                model_name_config_key = f'anki-{dict_name}-model'
                anki_deck_input = ILineEdit(config.get(deck_name_config_key, dict_name.title()))
                anki_deck_input.editingFinished.connect(
                    lambda: utils.update_config({deck_name_config_key: anki_deck_input.text()}))
                anki_setting_group.addRow(f'{dict_title}??????', anki_deck_input)
                anki_model_input = ILineEdit(config.get(model_name_config_key, dict_name.title()))
                anki_model_input.editingFinished.connect(
                    lambda: utils.update_config({model_name_config_key: anki_model_input.text()}))
                anki_setting_group.addRow(f'{dict_title}????????????', anki_model_input)

        anki_sync_switch = ISwitch(on=config.get('anki-auto-sync', False))
        anki_sync_switch.toggled.connect(lambda: utils.update_config({'anki-auto-sync': anki_sync_switch.isToggled()}))
        anki_setting_group.addRow('???????????????????????????', anki_sync_switch)

        def create_anki_deck_and_model():
            try:
                for on_dict in dicts.on_dict:
                    if on_dict.is_anki_able:
                        on_dict.anki_create_deck_and_model_func()
                IToast.showToast(self, '???????????????????????????????????????')
            except requests.exceptions.ConnectionError:
                IToast.showToast(self, '????????????AnkiConnect, ?????????Anki??????????????????')

        anki_setting_group.addButton('??????Anki Connect', create_anki_deck_and_model)

        setting_page.addWidget(anki_setting_group)

        tmp_file_group = IGroup('????????????')

        tmp_file_size_input = ILineEdit()
        tmp_file_size_input.setEnabled(False)

        def load_tmp_file_size():
            tmp_file_bytes = utils.get_tmp_size()
            tmp_file_size_input.setText("{:.2f}KB".format(tmp_file_bytes / 1024))
            clear_tmp_btn.setEnabled(tmp_file_bytes > 0)

        def clear_tmp_file():
            utils.clear_tmp_file()
            tmp_file_size_input.setText("0.00KB")
            clear_tmp_btn.setEnabled(False)
            IToast.showToast(self, '????????????')

        tmp_file_group.addRow('????????????', tmp_file_size_input)
        tmp_file_group.addButton('????????????????????????', load_tmp_file_size)
        clear_tmp_btn = tmp_file_group.addButton('????????????', clear_tmp_file)
        load_tmp_file_size()

        setting_page.addWidget(tmp_file_group)

        about_group = IGroup('??????')
        tag_label = ILineEdit(update.TAG)
        tag_label.setEnabled(False)
        about_group.addRow('????????????', tag_label)

        def check_for_update():
            update_info = update.check_for_update()
            if not update_info.get('success'):
                IToast.showToast(self, '????????????????????????')
                return
            if update_info.get('is_latest'):
                IToast.showToast(self, '?????????????????????????????????')
                return
            webbrowser.open(update_info.get('latest_download_url'))

        about_group.addButton('????????????', check_for_update)

        def open_github_page():
            webbrowser.open(update.GITHUB_URL)

        about_group.addButton('??????Github??????', open_github_page)
        setting_page.addWidget(about_group)

        setting_page.addSpacing(100)


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon(QPixmap(utils.get_asset_path('icon', 'logo-icon.ico'))))
        self.setToolTip('????????????')
        self.menu = IMenu()
        self.menu_open_trans_act = self.menu.addAction('??????????????????')
        self.menu_open_setting_act = self.menu.addAction('??????', utils.get_asset_path('icon', '??????.svg'))
        self.menu_quit_act = self.menu.addAction('??????', utils.get_asset_path('icon', '??????.svg'))
        self.setContextMenu(self.menu)

        @self.menu_quit_act.triggered.connect
        def exit_app():
            self.hide()
            QApplication.exit()


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
        ??????????????????????????????????????????
        ?????????????????????????????????
        """
        for widget in self.widget_list:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.widget_list = []
        for index, d in enumerate(dicts.on_dict):
            widget = ResultViewWidget(d)
            self.layout.insertWidget(index, widget)
            self.widget_list.append(widget)


class ResultViewWidget(QWidget):
    trans_signal = pyqtSignal(dict)

    def __init__(self, dictionary: Dict):
        super().__init__()
        self.title_widget = QWidget()
        self.fold_btn = QPushButton(QIcon(utils.get_asset_path('icon', 'left-outlined.svg')), '')
        self.dictionary = dictionary
        self.layout = QVBoxLayout()
        self.trans_result_view = ResultView(dictionary, self)
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.trans_signal.connect(self.setResult)
        self.trans_loader = None
        self.init()

    def init(self):
        self.setAttribute(Qt.WA_StyledBackground)

        self.trans_result_view.hide()

        title_layout = QHBoxLayout()

        icon_label = QLabel()
        icon_label.setFixedHeight(15)
        icon_label.setFixedWidth(15)
        icon = utils.get_asset_path('icon', self.dictionary.icon).replace('\\', '/')  # url()??????\???????????????
        icon_label.setStyleSheet(f'border-image: url({icon}); border-radius: 3px;')
        title_layout.addWidget(icon_label)
        title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_widget.setLayout(title_layout)

        title_label = QLabel(self.dictionary.title)
        title_label.setProperty('class', 'title-label')
        title_layout.addWidget(title_label)

        title_layout.addStretch(1)

        @self.fold_btn.clicked.connect
        def fold_btn_on_click():
            self.setFolded(not self.trans_result_view.isHidden())

        self.fold_btn.setEnabled(False)
        self.fold_btn.setProperty('class', 'panel-fold-btn')
        title_layout.addWidget(self.fold_btn)
        self.layout.addWidget(self.title_widget)

        self.layout.addWidget(self.trans_result_view)
        self.layout.setSpacing(0)
        self.layout.addStretch(1)
        self.layout.setSizeConstraint(QLayout.SetNoConstraint)
        self.setLayout(self.layout)

    def do_trans(self, text: str, from_lang: Lang):
        self.trans_loader = self.TransLoader(self.dictionary, self.trans_signal, text, from_lang)
        self.thread_pool.start(self.trans_loader)

    def stop_trans(self):
        if self.trans_loader:
            self.trans_loader.stop()

    @pyqtSlot(dict)
    def setResult(self, result_dict: dict):
        if not result_dict:
            self.trans_result_view.setMessage('????????????')
        elif result_dict.get('message', ''):
            self.trans_result_view.setMessage(result_dict.get('message'))
        else:
            self.trans_result_view.setResult(result_dict)
        self.fold_btn.setEnabled(True)
        self.setFolded(False)

    def setFolded(self, isFolded):
        if isFolded:
            self.fold_btn.setIcon(QIcon(utils.get_asset_path('icon', 'left-outlined.svg')))
        else:
            self.fold_btn.setIcon(QIcon(utils.get_asset_path('icon', 'down-outlined.svg')))
        self.trans_result_view.setHidden(isFolded)

    def loading(self):
        self.fold_btn.setEnabled(False)
        self.trans_result_view.hide()
        # self.trans_result_view.setMessage('?????????...')

    def clear(self):
        self.fold_btn.setEnabled(False)
        self.trans_result_view.setMessage('')

    class TransLoader(QRunnable):

        def __init__(self, dictionary, trans_signal, text: str, from_lang: Lang):
            super().__init__()
            self.dictionary = dictionary
            self.trans_signal = trans_signal
            self.text = text
            self.from_lang = from_lang
            self.is_running = True

        def run(self):
            retries = 3
            for i in range(retries):
                if not self.is_running:
                    return
                try:
                    result = self.dictionary.do_trans(self.text, self.from_lang)
                    self.trans_signal.emit(result)
                    return
                except Exception:
                    traceback.print_exc()
            self.trans_signal.emit(Dict.message_result('??????????????????'))

        def stop(self):
            self.is_running = False


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
        self.load(QUrl.fromLocalFile(utils.get_asset_path('search_panel.html')))
        with open(utils.get_asset_path(dictionary.template), encoding="utf-8") as f:
            self.template = f.read()
            f.close()
        self.sound_icon = dictionary.audio_icon

        @self.loadFinished.connect
        def load_finished(ok: bool):
            # ??????CSS??????
            if ok:
                self.page().runJavaScript(f'''
                            new_element = document.createElement("link");
                            new_element.setAttribute("rel", "stylesheet");
                            new_element.setAttribute("type", "text/css");
                            new_element.setAttribute("href", "css/{dictionary.style_file}");
                            document.head.appendChild(new_element);
                        ''')

    # ???????????????????????????????????????????????????
    def wheelEvent(self, event: QWheelEvent) -> None:
        self.nativeParentWidget().page.wheelEvent(event)

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
                    raise Exception('????????????????????????')

            if data_title == 'anki-btn':
                if result.get('support-anki') \
                        and utils.get_config().get('anki-on', False) and self.dictionary.is_anki_able():
                    return f'''
                            <a class="anki-btn" href="#" onclick="addAnkiNote()" 
                                style="text-decoration: none; display: inline-flex; vertical-align: middle;">
                                <img title="?????????Anki" src="icon/anki-logo2.png" alt="?????????Anki" />
                            </a>
                        '''
                else:
                    return ''
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
        anki_note_adder = self.AnkiNoteAdder(self.anki_result_signal, self.dictionary,
                                             self.current_data)
        self.thread_pool.start(anki_note_adder)

    class AnkiNoteAdder(QRunnable):
        def __init__(self, signal, dictionary: Dict, data: dict):
            super().__init__()
            self.signal = signal
            self.dictionary = dictionary
            self.data = data

        def run(self) -> None:
            self.signal.emit(self.dictionary.add_anki_note(self.data))


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super(WebEnginePage, self).__init__(parent)

    # ?????????????????????<a>??????
    def acceptNavigationRequest(self, url: QUrl, type: 'QWebEnginePage.NavigationType',
                                isMainFrame: bool) -> bool:
        if type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return True
