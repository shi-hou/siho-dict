from time import sleep

import keyboard
import mouse
import pyperclip
from PyQt5.QtCore import Qt, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QLineEdit, QSystemTrayIcon, QMainWindow, QApplication, QVBoxLayout, QWidget, QLabel, \
    QHBoxLayout
from pyqtkeybind import keybinder

from core import utils
from core.api import dict_server
from core.widgets.AudioButton import AudioButton
from core.widgets.BaseWindow import BaseWindow
from core.widgets.IGroup import IGroup
from core.widgets.ILineEdit import ILineEdit
from core.widgets.IMenu import IMenu
from core.widgets.IPage import IPage
from core.widgets.ISwitch import ISwitch


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
        def slot():
            if self.setting_window.hotkey_edit.isModified():
                original_hotkey = utils.get_config().get('hotkey', 'Ctrl+Alt+Z')
                new_hotkey = self.setting_window.hotkey_edit.text()
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
        dict_server.setOn(index, on)
        self.trans_window.result_list_widget.reset()


class TransWindow(BaseWindow):
    trans_signal = pyqtSignal(str, list, int, int)

    def __init__(self):
        self.input_edit = QLineEdit()
        super().__init__(title_bar_slot=self.input_edit)
        self.fix_btn = self.addTitleBarButton(icon=utils.get_resources_path('固定_line.svg'))
        self.result_list_widget = self.ResultListWidget()
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(1)
        self.trans_loader = None
        self.fix_not_hidden = False
        self.init()

    def init(self):
        self.trans_signal.connect(self.show_trans)

        self.setFixedWidth(309)
        self.setFixedHeight(500)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.Tool)
        self.content_widget.hide()

        self.close_btn.clicked.connect(self.hide)

        utils.addMouseEvent(self, self.mouse_on_click, mouse_btn=mouse.LEFT, btn_type=mouse.DOWN)

        @self.input_edit.returnPressed.connect
        def input_return_pressed():
            if self.input_edit.isModified():
                input_txt = self.input_edit.text().strip()
                if input_txt == '':
                    return
                self.trans_loader = self.TransLoader(self.trans_signal, self.frameGeometry(), input_txt)
                self.thread_pool.start(self.trans_loader)

        fold_btn = self.addTitleBarButton(icon=utils.get_resources_path('折叠面板.svg'))

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
        BaseWindow.hide(self)

    @pyqtSlot(str, list, int, int)
    def show_trans(self, input_text, result_list, x, y):
        self.input_edit.setText(input_text)
        self.input_edit.clearFocus()
        self.content_widget.setHidden(input_text == '')
        self.result_list_widget.setResult(result_list)
        if not self.fix_not_hidden:
            self.move(x, y)
        self.show()

    def on_hotkey(self):
        x, y = mouse.get_position()
        self.trans_loader = self.TransLoader(self.trans_signal, QRect(x, y, self.width(), self.height()))
        self.thread_pool.start(self.trans_loader)

    def mouse_on_click(self):
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
        self.fix_btn.setIcon(QIcon(QPixmap(utils.get_resources_path('固定_fill.svg' if value else '固定_line.svg'))))

    class TransLoader(QRunnable):

        def __init__(self, trans_signal, geometry: QRect, input_txt=None):
            super().__init__()
            self.trans_signal = trans_signal
            self.geometry = geometry
            self.input_txt = input_txt

        def run(self):
            if self.input_txt is not None:  # 来自输入框
                current_txt = self.input_txt
            else:  # 来自划词
                former_copy = pyperclip.paste()  # 用于还原剪切板
                keyboard.press_and_release('ctrl+c')
                sleep(0.1)
                current_txt = pyperclip.paste()
                pyperclip.copy(former_copy)  # 还原剪切版
            current_txt = current_txt.strip().replace('\n', ' ')
            if current_txt == '':  # 只显示title_bar, 不翻译
                self.geometry.setHeight(BaseWindow.title_bar_height)
                result_list = []
            else:
                from_lang = utils.check_language(current_txt)
                result_list = dict_server.do_trans(current_txt, from_lang)

            desktop_geometry = QApplication.desktop().availableGeometry()

            # 0 <= show_x <= desktop_width - window_width
            show_x = max(0, min(self.geometry.x(), desktop_geometry.width() - self.geometry.width()))
            # 0 <= show_y <= desktop_height - window_height
            show_y = max(0, min(self.geometry.y(), desktop_geometry.height() - self.geometry.height()))

            self.trans_signal.emit(current_txt, result_list, show_x, show_y)

    class ResultListWidget(QWidget):
        def __init__(self):
            super().__init__()
            self.layout = QVBoxLayout()
            self.widget_list = []
            for d in dict_server.on_dicts:
                widget = self.ResultWidget(d.title, d.icon, audio_btn_color=d.color)
                self.layout.addWidget(widget)
                self.widget_list.append(widget)
            self.layout.addStretch(1)
            self.setLayout(self.layout)

        def setResult(self, result_list):
            for index, widget in enumerate(self.widget_list):
                if result_list[index]:
                    widget.setResult(result_list[index])
                    widget.show()
                else:
                    widget.hide()

        def reset(self):
            for widget in self.widget_list:
                self.layout.removeWidget(widget)
            self.widget_list = []
            for index, d in enumerate(dict_server.on_dicts):
                widget = self.ResultWidget(d.title, d.icon, audio_btn_color=d.color)
                self.layout.insertWidget(index, widget)
                self.widget_list.append(widget)

        class ResultWidget(QWidget):
            def __init__(self, title: str, icon: str, audio_btn_color: str):
                super().__init__()
                self.audio_btn_color = audio_btn_color
                self.layout = QVBoxLayout()
                self.setLayout(self.layout)

                title_layout = QHBoxLayout()
                title_layout.addWidget(QLabel(title))
                icon_label = QLabel()
                icon_label.setFixedHeight(15)
                icon_label.setFixedWidth(15)
                icon = utils.get_resources_path(icon).replace('\\', '/')  # url()用“\”会不生效
                icon_label.setStyleSheet(f'border-image: url({icon}); border-radius: 3px;')
                title_layout.addWidget(icon_label)
                title_layout.addStretch(1)
                self.layout.addLayout(title_layout)

                self.text_label = QLabel()
                self.text_label.setWordWrap(True)
                self.layout.addWidget(self.text_label)
                self.audio_buttons = []
                self.trans_result_label = QLabel()
                self.trans_result_label.setWordWrap(True)
                self.layout.addWidget(self.trans_result_label)
                self.layout.addStretch(1)

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
                        self.layout.insertWidget(index + 2, audio_btn)

                if result_dict.get('type') == 1:
                    trans_result = ''
                    for pre in result_dict.get('pre'):
                        trans_result += f"{pre.get('title')}\n"
                        trans_result += f"{';'.join(pre.get('trans'))}\n"
                    self.trans_result_label.setText(trans_result)
                else:
                    self.trans_result_label.setText(result_dict.get('trans'))


class SettingWindow(BaseWindow):
    def __init__(self):
        super().__init__(title='设置')
        self.hotkey_edit = ILineEdit()
        self.dict_switch_list = []
        self.init()

    def init(self):
        self.setFixedSize(800, 500)

        setting_page = IPage()
        self.setPage(setting_page)

        basic_setting_group = IGroup('基础设置')
        auto_run_switch = ISwitch(on=utils.get_auto_run())

        @auto_run_switch.toggled.connect
        def slot():
            utils.set_auto_run(auto_run_switch.isToggled())

        basic_setting_group.addRow('开机自启', auto_run_switch)

        self.hotkey_edit.setText(utils.get_config().get('hotkey', 'Ctrl+Alt+Z'))
        basic_setting_group.addRow('热键', self.hotkey_edit)

        setting_page.addWidget(basic_setting_group)

        dict_setting_group = IGroup('词典设置', '目前仅支持百度翻译，因此暂时无法设置词典，后续将支持Moji辞書、必应词典等（咕咕咕）')
        for i, d in enumerate(dict_server.dicts):
            switch = ISwitch(on=d.on)
            switch.setProperty('index', i)
            switch.setEnabled(d.able)
            self.dict_switch_list.append(switch)

            dict_setting_group.addRow(d.title, switch, utils.get_resources_path(d.icon))

        setting_page.addWidget(dict_setting_group)

        setting_page.addSpacing(100)


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setIcon(QIcon(QPixmap(utils.get_resources_path('翻译.svg'))))
        self.setToolTip('划词翻译')
        self.menu = IMenu()
        self.menu_open_trans_act = self.menu.addAction('显示翻译窗口')
        self.menu_open_setting_act = self.menu.addAction('设置', utils.get_resources_path('设置.svg'))
        self.menu_quit_act = self.menu.addAction('退出', utils.get_resources_path('退出.svg'))
        self.setContextMenu(self.menu)

        @self.menu_quit_act.triggered.connect
        def exit_app():
            self.hide()
            QApplication.exit()
