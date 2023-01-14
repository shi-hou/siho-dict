import sys
import time

import keyboard
import mouse
import pyperclip
from PyQt5.QtCore import Qt, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QLineEdit, QSystemTrayIcon, QMainWindow

from core import utils
from core.api import dict_list, baidu_trans
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

        @self.tray_icon.menu_open_trans_act.triggered.connect
        def menu_open_trans_act_triggered():
            self.trans_window.content_widget.hide()
            self.trans_window.show()

        @self.tray_icon.activated.connect
        def tray_icon_activated(reason):
            if reason == QSystemTrayIcon.Trigger:
                self.trans_window.content_widget.hide()
                self.trans_window.show()

        self.tray_icon.show()


class TransWindow(BaseWindow):
    trans_signal = pyqtSignal(str, str, int, int)

    def __init__(self):
        self.input_edit = QLineEdit()
        super().__init__(title_bar_slot=self.input_edit)
        self.result_view = QWebEngineView()
        self.trans_signal.connect(self.show_trans)
        self.thread_pool = QThreadPool(self)
        self.thread_pool.setMaxThreadCount(1)
        self.trans_loader = None
        self.init()

    def init(self):
        self.setFixedWidth(450)
        self.setFixedHeight(550)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.Tool)
        self.content_widget.hide()

        utils.addMouseEvent(self, self.mouse_on_click, mouse_btn=mouse.LEFT, btn_type=mouse.DOWN)

        @self.input_edit.editingFinished.connect
        def input_editing_finished():
            input_txt = self.input_edit.text().strip()
            if input_txt == '':
                return
            x, y = self.x(), self.y()
            self.trans_loader = TransLoader(self.trans_signal, x, y, input_txt=input_txt)
            self.thread_pool.start(self.trans_loader)

        fold_btn = self.addTitleBarButton(icon=fr'{utils.get_app_dir_path()}\asserts\折叠面板.svg')

        @fold_btn.clicked.connect
        def fold_button_on_click():
            self.content_widget.setHidden(not self.content_widget.isHidden())

        self.result_view.setProperty('class', 'trans-result-label')
        self.result_view.page().setBackgroundColor(QColor('#f2f1f6'))
        self.input_edit.setProperty('class', 'trans-input-edit')
        page = IPage()
        page.addWidget(self.result_view)
        self.setPage(page)

    def hide(self) -> None:
        self.input_edit.clear()
        self.result_view.setHtml('')
        self.content_widget.hide()
        BaseWindow.hide(self)

    @pyqtSlot(str, str, int, int)
    def show_trans(self, input_text, trans_result, x, y):
        self.input_edit.setText(input_text)
        self.input_edit.clearFocus()
        self.content_widget.setHidden(input_text == '')
        self.result_view.setHtml(trans_result)
        self.move(x, y)
        self.show()

    def on_hotkey(self):
        x, y = mouse.get_position()
        self.trans_loader = TransLoader(self.trans_signal, x, y)
        self.thread_pool.start(self.trans_loader)

    def mouse_on_click(self):
        x, y = mouse.get_position()
        if not self.isHidden() and (
                QPoint(x, y) not in self.geometry()
                or (
                        self.content_widget.isHidden()
                        and QPoint(x - self.x(), y - self.y()) not in self.title_bar.geometry())):
            self.hide()


class TransLoader(QRunnable):

    def __init__(self, trans_signal, x, y, input_txt=None):
        super().__init__()
        self.trans_signal = trans_signal
        self.x = x
        self.y = y
        self.input_txt = input_txt

    def run(self):
        if self.input_txt is not None:  # 来自输入框
            current_txt = self.input_txt
        else:   # 来自划词
            former_copy = pyperclip.paste()  # 用于还原剪切板
            keyboard.press_and_release('ctrl+c')
            time.sleep(0.1)
            current_txt = pyperclip.paste()
            pyperclip.copy(former_copy)  # 还原剪切版
        current_txt = current_txt.strip().replace('\n', ' ')
        show_x, show_y = self.x, self.y  # TODO 不超出显示器
        trans_result = ''
        if current_txt != '':
            trans_result = baidu_trans(current_txt)
        self.trans_signal.emit(current_txt, trans_result, show_x, show_y)


class SettingWindow(BaseWindow):
    def __init__(self):
        super().__init__(title='设置')
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

        config = utils.get_config()
        hotkey_edit = ILineEdit(config.get('hotkey'))

        @hotkey_edit.textEdited.connect
        def slot(text):
            config['hotkey'] = text
            utils.update_config(config)

        basic_setting_group.addRow('热键', hotkey_edit)

        setting_page.addWidget(basic_setting_group)

        dir_path = utils.get_app_dir_path()
        dict_setting_group = IGroup('词典设置', '目前仅支持百度翻译，因此暂时无法设置词典，后续将支持Moji辞書、必应词典等（咕咕咕）')
        dict_settings = config.get('dict', {dict_list[0]['name']: {'on': True}})
        for d in dict_list:
            name = d.get('name')
            enable = d.get('enable', False)
            switch = ISwitch(on=enable and dict_settings.get(name, {}).get("on", False))
            switch.setProperty('name', name)
            switch.setEnabled(False)  # TODO 等字典多了再开放更改

            @switch.toggled.connect
            def slot():
                toggled_switch = self.sender()
                dict_name = toggled_switch.property('name')
                one_dict_setting = dict_settings.get(dict_name, {})
                one_dict_setting['on'] = toggled_switch.isToggled()
                dict_settings[dict_name] = one_dict_setting
                config['dict'] = dict_settings
                utils.update_config(config)

            dict_setting_group.addRow(d.get('title'), switch, fr'{dir_path}\asserts\{d.get("icon")}')

        setting_page.addWidget(dict_setting_group)

        test_setting_group = IGroup('test')
        test_setting_group.addRow('test1', ISwitch())
        test_setting_group.addRow('test2', ISwitch())
        test_setting_group.addRow('test3', ISwitch())
        setting_page.addWidget(test_setting_group)

        setting_page.addSpacing(100)


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.setting_window = None
        dir_path = utils.get_app_dir_path()
        self.setIcon(QIcon(QPixmap(fr'{dir_path}\asserts\翻译.svg')))
        self.setToolTip('划词翻译')
        self.menu = IMenu()
        self.menu_open_trans_act = self.menu.addAction('显示翻译窗口')
        self.menu_open_setting_act = self.menu.addAction('设置', fr'{dir_path}\asserts\设置.svg')
        self.menu_quit_act = self.menu.addAction('退出', fr'{dir_path}\asserts\退出.svg')
        self.setContextMenu(self.menu)

        @self.menu_open_setting_act.triggered.connect
        def show_setting_window():
            if self.setting_window is None:
                self.setting_window = SettingWindow()
            self.setting_window.show()

        @self.menu_quit_act.triggered.connect
        def exit_app():
            self.hide()
            sys.exit()
